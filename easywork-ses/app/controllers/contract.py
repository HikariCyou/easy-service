from datetime import datetime
from typing import List
from tortoise.transactions import in_transaction
from app.models.contract import Contract, ContractCalculationItem
from tortoise.expressions import Q

from app.schemas.contract import CreateContract, UpdateContract, ContractCalculationItemCreate
from app.utils.common import clean_dict


class ContractController:
    def __init__(self):
        pass

    async def generate_contract_number(self) -> str:
        """
        自動的に契約番号を生成する
        フォーマット: TOB-CONTRACT-YYYYMMDD-XXXX
        """
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"TOB-CONTRACT-{today}-"
        
        # 今日作成された契約の最大番号を取得
        latest_contract = await Contract.filter(
            contract_number__startswith=prefix
        ).order_by("-contract_number").first()
        
        if latest_contract:
            # 既存の番号から連番部分を抽出して+1
            last_number = int(latest_contract.contract_number.split("-")[-1])
            next_number = last_number + 1
        else:
            # 今日初回の場合は1から開始
            next_number = 1
        
        # 4桁のゼロパディング
        contract_number = f"{prefix}{next_number:04d}"
        
        # 重複確認（念のため）
        while await Contract.exists(contract_number=contract_number):
            next_number += 1
            contract_number = f"{prefix}{next_number:04d}"
        
        return contract_number

    async def _handle_calculation_items(self, contract: Contract, calculation_items: List[ContractCalculationItemCreate]) -> None:
        """
        合同精算項目の処理
        """
        if not calculation_items:
            return
            
        # 項目種別と支払単位のマッピング
        from app.models.enums import ContractItemType, PaymentUnit
        
        item_type_mapping = {
            "BASIC_SALARY": ContractItemType.BASIC_SALARY,
            "OVERTIME_FEE": ContractItemType.OVERTIME_FEE,
            "ABSENCE_DEDUCTION": ContractItemType.ABSENCE_DEDUCTION,
            "ALLOWANCE": ContractItemType.ALLOWANCE,
            "OTHER_FEE": ContractItemType.OTHER_FEE,
        }
        
        unit_mapping = {
            "円/月": PaymentUnit.YEN_PER_MONTH,
            "万円/月": PaymentUnit.TEN_THOUSAND_YEN_PER_MONTH,
            "円/時間": PaymentUnit.YEN_PER_HOUR,
            "円/日": PaymentUnit.YEN_PER_DAY,
            "円/分": PaymentUnit.YEN_PER_MINUTE,
            "％": PaymentUnit.PERCENTAGE,
            "固定額": PaymentUnit.FIXED_AMOUNT,
        }
        
        # 既存の精算項目を削除
        await ContractCalculationItem.filter(contract=contract).delete()
        
        # 新しい精算項目を作成
        for i, item in enumerate(calculation_items):
            item_type = item_type_mapping.get(item.type, ContractItemType.OTHER_FEE)
            payment_unit = unit_mapping.get(item.unit, PaymentUnit.YEN_PER_MONTH)
            
            await ContractCalculationItem.create(
                contract=contract,
                item_name=item.name,
                item_type=item_type,
                amount=item.amount,
                payment_unit=payment_unit,
                comment=item.comment,
                sort_order=i
            )

    async def list_contracts(self, page:int = 1, page_size:int = 10 , search: Q = Q(), orders:list = []):
        query = Contract.filter(search).prefetch_related(
            'case', 'personnel'
        )
        total = await Contract.filter(search).count()
        contracts = await query.order_by(*orders).limit(page_size).offset((page - 1) * page_size).all()
        return  contracts, total

    async def contracts_to_dict(self, contracts, include_relations: bool = False):
        """
        将契约列表转换为字典，可选择是否包含关联数据
        """
        result = []
        for contract in contracts:
            contract_dict = await contract.to_dict()
            
            if include_relations:
                # 添加关联数据
                if contract.case:
                    contract_dict['case'] = await contract.case.to_dict()
                
                # 添加统一Personnel信息
                if contract.personnel:
                    contract_dict['personnel'] = await contract.personnel.to_dict()
                
                # 添加精算項目
                calculation_items = await ContractCalculationItem.filter(contract=contract).order_by('sort_order').all()
                contract_dict['calculation_items'] = [await item.to_dict() for item in calculation_items]
                
                # 添加计算属性
                contract_dict['is_active'] = contract.is_active
                contract_dict['contractor_name'] = contract.contractor_name
            
            result.append(contract_dict)
        return result

    async def contract_to_dict(self, contract, include_relations: bool = False):
        """
        将单个契约转换为字典，可选择是否包含关联数据
        """
        if not contract:
            return None
            
        contract_dict = await contract.to_dict()
        
        if include_relations:
            # 添加关联数据
            if contract.case:
                contract_dict['case'] = await contract.case.to_dict()
            
            # 添加统一Personnel信息
            if contract.personnel:
                contract_dict['personnel'] = await contract.personnel.to_dict()
            
            # 添加精算項目
            calculation_items = await ContractCalculationItem.filter(contract=contract).order_by('sort_order').all()
            contract_dict['calculation_items'] = [await item.to_dict() for item in calculation_items]
            
            # 添加计算属性
            contract_dict['is_active'] = contract.is_active
            contract_dict['contractor_name'] = contract.contractor_name
        
        return contract_dict

    async  def get_contract(self, id):
        contract = await Contract.get_or_none(id=id).prefetch_related(
            'case', 'personnel'
        )
        return contract

    async def check_active_contract(self, **kwargs) -> bool:
        """
        检查是否存在有效的合同
        返回True表示可以签约，False表示已有有效合同
        """
        from app.models.enums import ContractStatus
        today = datetime.now().date()
        
        contract = await Contract.get_or_none(
            **kwargs,
            status=ContractStatus.ACTIVE,
            contract_end_date__gte=today
        )
        return contract is None

    async def check_personnel_contract(self, personnel_id):
        return await self.check_active_contract(personnel_id=personnel_id)



    async def create_contract(self, contract_data: CreateContract):
        # 契約者は有効状態の契約をあるかどうかを確認する
        can_contract = await self.check_personnel_contract(contract_data.personnel_id)

        if not can_contract:
            raise Exception("契約者が有効な契約を保有しています。")

        async with in_transaction():
            # 自動的にcontract_number契約番号を生成する
            contract_number = await self.generate_contract_number()

            # calculation_itemsを除外してcontractを作成
            data_dict = clean_dict(contract_data.model_dump(exclude_unset=True, exclude={'calculation_items'}))
            data_dict['contract_number'] = contract_number
            contract = await Contract.create(**data_dict)
            
            # 精算項目の処理
            if contract_data.calculation_items:
                await self._handle_calculation_items(contract, contract_data.calculation_items)
                
            return contract


    async def update_contract(self, id, contract_data: UpdateContract):
        contract = await Contract.get_or_none(id=id)
        if not contract:
            raise Exception("Contract not found")
            
        async with in_transaction():
            # calculation_itemsを除外してcontractを更新
            data_dict = clean_dict(contract_data.model_dump(exclude_unset=True, exclude={'calculation_items'}))
            await contract.update_from_dict(data_dict)
            await contract.save()
            
            # 精算項目の処理
            if contract_data.calculation_items is not None:
                await self._handle_calculation_items(contract, contract_data.calculation_items)
                
            return contract

    async def delete_contract(self, id):
        contract = await Contract.get_or_none(id=id)
        if contract:
            await contract.delete()
            return True
        else:
            raise Exception("Contract not found")

    async def delete_contracts(self, ids):
        contracts = await Contract.filter(id__in=ids).all()
        if contracts:
            await Contract.filter(id__in=ids).delete()
            return True
        else:
            raise Exception("Contracts not found")




    async def update_contract_conditions(self, contract_condition_data):
        """契約条件変更の処理"""
        from app.models.enums import ContractChangeReason
        
        # 契約を取得（関連データも含む）
        contract = await Contract.get_or_none(id=contract_condition_data.contract_id).prefetch_related(
            'case', 'personnel'
        )
        if not contract:
            raise Exception("契約が見つかりません")
        
        async with in_transaction():
            # 変更理由をEnumに変換
            reason_mapping = {
                "クライアント要望": ContractChangeReason.CLIENT_REQUEST,
                "人材要望": ContractChangeReason.PERSONNEL_REQUEST,
                "プロジェクト変更": ContractChangeReason.PROJECT_CHANGE,
                "予算変更": ContractChangeReason.BUDGET_CHANGE,
                "市場状況": ContractChangeReason.MARKET_CONDITION,
                "その他": ContractChangeReason.OTHER
            }
            reason_enum = reason_mapping.get(contract_condition_data.reason, ContractChangeReason.CLIENT_REQUEST)
            
            # 変更前の精算項目を取得（履歴記録用）
            before_calculation_items = []
            if contract_condition_data.calculation_items is not None:
                existing_items = await ContractCalculationItem.filter(contract=contract).order_by('sort_order').all()
                before_calculation_items = [await item.to_dict() for item in existing_items]
            
            # 契約条件変更処理を実行（履歴記録込み）
            await contract.update_conditions(
                new_unit_price=contract_condition_data.new_unit_price,
                new_working_hours=contract_condition_data.new_working_hours,
                reason=reason_enum,
                effective_date=contract_condition_data.effective_date,
                requested_by=contract_condition_data.requested_by
            )
            
            # 精算項目の処理
            if contract_condition_data.calculation_items is not None:
                await self._handle_calculation_items(contract, contract_condition_data.calculation_items)
                
                # 精算項目変更の履歴を追加記録
                from app.models.contract import ContractChangeHistory
                from app.models.enums import ContractChangeType
                
                after_calculation_items = [
                    {
                        "type": item.type,
                        "name": item.name, 
                        "amount": item.amount,
                        "unit": item.unit,
                        "comment": item.comment
                    }
                    for item in contract_condition_data.calculation_items
                ]
                
                await ContractChangeHistory.create(
                    contract=contract,
                    change_type=ContractChangeType.CONDITION_CHANGE,
                    change_reason=reason_enum,
                    before_values={"calculation_items": before_calculation_items},
                    after_values={"calculation_items": after_calculation_items},
                    change_description=f"精算項目変更: {len(contract_condition_data.calculation_items)}項目",
                    effective_date=contract_condition_data.effective_date,
                    requested_by=contract_condition_data.requested_by
                )
            
            return contract


contract_controller = ContractController()

