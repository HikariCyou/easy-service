from datetime import datetime
from app.models.contract import Contract
from tortoise.expressions import Q

from app.schemas.contract import CreateContract, UpdateContract
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

    async def list_contracts(self, page:int = 1, page_size:int = 10 , search: Q = Q(), orders:list = []):
        query = Contract.filter(search).prefetch_related(
            'case', 'bp_employee', 'employee', 'freelancer'
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
                
                # 根据契约类型添加对应的员工信息
                if contract.bp_employee:
                    contract_dict['bp_employee'] = await contract.bp_employee.to_dict()
                elif contract.employee:
                    contract_dict['employee'] = await contract.employee.to_dict()
                elif contract.freelancer:
                    contract_dict['freelancer'] = await contract.freelancer.to_dict()
                
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
            
            # 根据契约类型添加对应的员工信息
            if contract.bp_employee:
                contract_dict['bp_employee'] = await contract.bp_employee.to_dict()
            elif contract.employee:
                contract_dict['employee'] = await contract.employee.to_dict()
            elif contract.freelancer:
                contract_dict['freelancer'] = await contract.freelancer.to_dict()
            
            # 添加计算属性
            contract_dict['is_active'] = contract.is_active
            contract_dict['contractor_name'] = contract.contractor_name
        
        return contract_dict

    async  def get_contract(self, id):
        contract = await Contract.get_or_none(id=id).prefetch_related(
            'case', 'bp_employee', 'employee', 'freelancer'
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

    async def check_bp_employee_contract(self, bp_employee_id):
        return await self.check_active_contract(bp_employee_id=bp_employee_id)

    async def check_employee_contract(self, employee_id):
        return await self.check_active_contract(employee_id=employee_id)

    async def check_freelancer_contract(self, freelancer_id):
        return await self.check_active_contract(freelancer_id=freelancer_id)



    async def create_contract(self, contract_data:CreateContract):
        # 契約者は有効状態の契約をあるかどうかを確認する
        can_contract = False
        if contract_data.bp_employee_id:
           can_contract = await self.check_bp_employee_contract(contract_data.bp_employee_id)
        elif contract_data.employee_id:
            can_contract = await self.check_employee_contract(contract_data.employee_id)
        elif contract_data.freelancer_id:
            can_contract = await self.check_freelancer_contract(contract_data.freelancer_id)

        if not can_contract:
            raise Exception("契約者が有効な契約を保有しています。")

        # 自動的にcontract_number契約番号を生成する
        contract_number = await self.generate_contract_number()

        data_dict = clean_dict(contract_data.model_dump(exclude_unset=True))
        data_dict['contract_number'] = contract_number
        contract = await Contract.create(**data_dict)
        return contract


    async def update_contract(self, id, contract_data:UpdateContract):
        data_dict = clean_dict(contract_data.model_dump(exclude_unset=True))
        contract = await Contract.get_or_none(id=id)
        if contract:
            await contract.update_from_dict(data_dict)
            await contract.save()
            return contract
        else:
            raise Exception("Contract not found")

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




contract_controller = ContractController()

