from typing import Optional

from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.contract import contract_controller
from app.schemas import Success, Fail
from app.schemas.contract import (
    CreateContract, 
    EarlyTerminationRequest,
    ContractConditionUpdate,
    ContractAmendmentCreate,
    ContractAmendmentApproval
)

router = APIRouter()


@router.get("/list", summary="契約一覧取得")
async def get_contract_list(
    keyword: Optional[str] = Query(None, max_length=50),
    staff_id: Optional[int] = Query(None, ge=1, description="要員ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    case_id: Optional[int] = Query(None, ge=1)
):
    try:
        q = Q()
        if keyword:
            q &= Q(contract_number__icontains=keyword) | Q(case__title__icontains=keyword)
        if staff_id:
            q &= Q(personnel_id=staff_id)
        if case_id:
            q &= Q(case_id=case_id)


        contracts, total = await contract_controller.list_contracts(
            page=page, page_size=pageSize,search=q
        )
        data = await contract_controller.contracts_to_dict(contracts, include_relations=True)
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="IDで契約取得")
async def get_contract(id: int = Query(..., description="案件ID")):
    try:
        contract = await contract_controller.get_contract(id=id)
        if contract:
            data = await contract_controller.contract_to_dict(contract=contract, include_relations=True)
            return Success(data= data)
        else:
            return Fail(msg="契約見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/create", summary="契約作成")
async def create_contract(data: CreateContract):
    try:
        contract = await contract_controller.create_contract(contract_data=data)
        result = await contract.to_dict()
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


# 契約変更関連のAPI
@router.post("/terminate-early", summary="契約早期解約")
async def terminate_contract_early(data: EarlyTerminationRequest):
    """契約の早期解約処理"""
    try:
        from app.models.contract import Contract
        from app.models.enums import ContractChangeReason
        
        # 契約を取得
        contract = await Contract.get_or_none(id=data.contract_id)
        if not contract:
            return Fail(msg="契約が見つかりません")
            
        # 解約理由をEnumに変換
        reason_mapping = {
            "クライアント要望": ContractChangeReason.CLIENT_REQUEST,
            "人材要望": ContractChangeReason.PERSONNEL_REQUEST, 
            "パフォーマンス問題": ContractChangeReason.PERFORMANCE_ISSUE,
            "プロジェクト変更": ContractChangeReason.PROJECT_CHANGE,
            "その他": ContractChangeReason.OTHER
        }
        reason_enum = reason_mapping.get(data.reason, ContractChangeReason.OTHER)
        
        # 早期解約処理を実行
        await contract.terminate_early(
            reason=reason_enum,
            termination_date=data.termination_date,
            requested_by=data.requested_by,
            description=data.description
        )
        
        return Success(msg="契約の早期解約が完了しました")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/update-conditions", summary="契約条件変更")
async def update_contract_conditions(data: ContractConditionUpdate):
    """契約条件の変更処理（精算項目も含む）"""
    try:
        contract = await contract_controller.update_contract_conditions(data)
        result = await contract_controller.contract_to_dict(contract, include_relations=True)
        return Success(data=result, msg="契約条件の変更が完了しました")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/{contract_id}/history", summary="契約変更履歴取得")
async def get_contract_history(contract_id: int, limit: int = Query(10, ge=1, le=100)):
    """契約の変更履歴を取得"""
    try:
        from app.models.contract import Contract, ContractChangeHistory
        
        # 契約を取得
        contract = await Contract.get_or_none(id=contract_id)
        if not contract:
            return Fail(msg="契約が見つかりません")
            
        # 変更履歴を取得
        try:
            histories = await ContractChangeHistory.filter(
                contract=contract
            ).order_by("-created_at").limit(limit)
        except Exception as e:
            # テーブルが存在しない場合の対応
            return Success(data=[], msg="変更履歴テーブルが初期化されていません")
        
        # レスポンス形式に変換
        data = []
        for history in histories:
            data.append({
                "id": history.id,
                "contract_id": contract_id,
                "change_type": history.change_type,
                "change_reason": history.change_reason,
                "before_values": history.before_values,
                "after_values": history.after_values,
                "change_description": history.change_description,
                "effective_date": history.effective_date,
                "requested_by": history.requested_by,
                "approved_by": history.approved_by,
                "approval_date": history.approval_date,
                "created_at": history.created_at
            })
        
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/{contract_id}/calculation-items", summary="契約精算項目取得")
async def get_contract_calculation_items(contract_id: int):
    """契約の精算項目一覧を取得"""
    try:
        from app.models.contract import Contract, ContractCalculationItem
        
        # 契約を取得
        contract = await Contract.get_or_none(id=contract_id)
        if not contract:
            return Fail(msg="契約が見つかりません")
            
        # 精算項目を取得
        calculation_items = await ContractCalculationItem.filter(contract=contract).order_by('sort_order')
        data = [await item.to_dict() for item in calculation_items]
        
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/amendment/create", summary="契約修正書作成")
async def create_contract_amendment(data: ContractAmendmentCreate):
    """契約修正書を作成"""
    try:
        from app.models.contract import Contract, ContractAmendment
        from app.models.enums import ContractChangeType, ContractChangeReason
        import uuid
        
        # 元契約を取得
        original_contract = await Contract.get_or_none(id=data.original_contract_id)
        if not original_contract:
            return Fail(msg="元契約が見つかりません")
            
        # 修正書番号を生成
        amendment_number = f"AMD-{original_contract.contract_number}-{uuid.uuid4().hex[:8].upper()}"
        
        # 修正種別・理由をEnumに変換
        type_mapping = {
            "契約更新": ContractChangeType.CONTRACT_RENEWAL,
            "条件変更": ContractChangeType.CONDITION_CHANGE,
            "期間延長": ContractChangeType.PERIOD_EXTENSION,
            "期間短縮": ContractChangeType.PERIOD_SHORTENING,
            "契約修正": ContractChangeType.AMENDMENT
        }
        reason_mapping = {
            "クライアント要望": ContractChangeReason.CLIENT_REQUEST,
            "人材要望": ContractChangeReason.PERSONNEL_REQUEST,
            "プロジェクト変更": ContractChangeReason.PROJECT_CHANGE,
            "予算変更": ContractChangeReason.BUDGET_CHANGE,
            "その他": ContractChangeReason.OTHER
        }
        
        type_enum = type_mapping.get(data.amendment_type, ContractChangeType.AMENDMENT)
        reason_enum = reason_mapping.get(data.amendment_reason, ContractChangeReason.CLIENT_REQUEST)
        
        # 契約修正書を作成
        amendment = await ContractAmendment.create(
            original_contract=original_contract,
            amendment_number=amendment_number,
            amendment_title=data.amendment_title,
            amendment_type=type_enum,
            amendment_reason=reason_enum,
            amendment_details=data.amendment_details,
            effective_start_date=data.effective_start_date,
            effective_end_date=data.effective_end_date,
            new_unit_price=data.new_unit_price,
            new_contract_end_date=data.new_contract_end_date,
            new_working_hours=data.new_working_hours,
            status="草案"
        )
        
        result = await amendment.to_dict()
        return Success(data=result, msg="契約修正書が作成されました")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/amendment/approve", summary="契約修正書承認")
async def approve_contract_amendment(data: ContractAmendmentApproval):
    """契約修正書の承認処理"""
    try:
        from app.models.contract import ContractAmendment
        from datetime import datetime
        
        # 修正書を取得
        amendment = await ContractAmendment.get_or_none(id=data.amendment_id)
        if not amendment:
            return Fail(msg="契約修正書が見つかりません")
            
        # 承認種別に応じて処理
        now = datetime.now()
        
        if data.approval_type == "client":
            amendment.client_approved = True
            amendment.client_approved_date = now
            amendment.client_signature = data.signature
        elif data.approval_type == "company":
            amendment.company_approved = True
            amendment.company_approved_date = now
            amendment.company_signature = data.signature
        elif data.approval_type == "personnel":
            amendment.personnel_acknowledged = True
            amendment.personnel_acknowledged_date = now
        else:
            return Fail(msg="無効な承認種別です")
            
        # ステータス更新
        if amendment.all_parties_approved:
            amendment.status = "承認済み"
            
        await amendment.save()
        
        return Success(msg=f"{data.approval_type}による承認が完了しました")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/amendment/{amendment_id}", summary="契約修正書詳細取得") 
async def get_contract_amendment(amendment_id: int):
    """契約修正書の詳細を取得"""
    try:
        from app.models.contract import ContractAmendment
        
        amendment = await ContractAmendment.get_or_none(id=amendment_id)
        if not amendment:
            return Fail(msg="契約修正書が見つかりません")
            
        result = await amendment.to_dict()
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/{contract_id}/amendments", summary="契約修正書一覧取得")
async def get_contract_amendments(contract_id: int):
    """指定契約の修正書一覧を取得"""
    try:
        from app.models.contract import Contract, ContractAmendment
        
        # 契約を取得
        contract = await Contract.get_or_none(id=contract_id)
        if not contract:
            return Fail(msg="契約が見つかりません")
            
        # 修正書一覧を取得
        amendments = await ContractAmendment.filter(
            original_contract=contract
        ).order_by("-created_at")
        
        data = []
        for amendment in amendments:
            data.append(await amendment.to_dict())
            
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/{contract_id}/calculate", summary="契約精算計算")
async def calculate_contract_payment(contract_id: int, actual_hours: float = Query(..., description="実稼働時間")):
    """契約の月額精算を計算"""
    try:
        from app.models.contract import Contract
        
        # 契約を取得
        contract = await Contract.get_or_none(id=contract_id)
        if not contract:
            return Fail(msg="契約が見つかりません")
            
        # 精算計算を実行
        calculation_result = await contract.calculate_monthly_payment(actual_hours)
        
        return Success(data=calculation_result)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/{contract_id}/items", summary="契約精算項目一覧取得")
async def get_contract_calculation_items(contract_id: int):
    """契約の精算項目一覧を取得"""
    try:
        from app.models.contract import Contract, ContractCalculationItem
        
        # 契約を取得
        contract = await Contract.get_or_none(id=contract_id)
        if not contract:
            return Fail(msg="契約が見つかりません")
            
        # 精算項目一覧を取得
        items = await ContractCalculationItem.filter(
            contract=contract
        ).order_by("sort_order", "created_at")
        
        data = []
        for item in items:
            data.append({
                "id": item.id,
                "item_name": item.item_name,
                "item_type": item.item_type,
                "amount": item.amount,
                "payment_unit": item.payment_unit,
                "comment": item.comment,
                "is_active": item.is_active,
                "is_deduction": item.is_deduction,
                "sort_order": item.sort_order,
                "created_at": item.created_at
            })
            
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/{contract_id}/items", summary="契約精算項目作成")
async def create_contract_calculation_item(contract_id: int, data: dict):
    """契約精算項目を作成"""
    try:
        from app.models.contract import Contract, ContractCalculationItem
        
        # 契約を取得
        contract = await Contract.get_or_none(id=contract_id)
        if not contract:
            return Fail(msg="契約が見つかりません")
            
        # 精算項目を作成
        item = await ContractCalculationItem.create(
            contract=contract,
            item_name=data.get("item_name"),
            item_type=data.get("item_type"),
            amount=float(data.get("amount", 0)),
            payment_unit=data.get("payment_unit"),
            comment=data.get("comment"),
            is_active=data.get("is_active", True),
            sort_order=data.get("sort_order", 0)
        )
        
        result = {
            "id": item.id,
            "item_name": item.item_name,
            "item_type": item.item_type,
            "amount": item.amount,
            "payment_unit": item.payment_unit,
            "comment": item.comment,
            "is_active": item.is_active,
            "is_deduction": item.is_deduction,
            "sort_order": item.sort_order,
            "created_at": item.created_at
        }
        
        return Success(data=result, msg="契約精算項目が作成されました")
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/items/{item_id}", summary="契約精算項目更新")
async def update_contract_calculation_item(item_id: int, data: dict):
    """契約精算項目を更新"""
    try:
        from app.models.contract import ContractCalculationItem
        
        # 精算項目を取得
        item = await ContractCalculationItem.get_or_none(id=item_id)
        if not item:
            return Fail(msg="精算項目が見つかりません")
            
        # 項目を更新
        if "item_name" in data:
            item.item_name = data["item_name"]
        if "item_type" in data:
            item.item_type = data["item_type"]
        if "amount" in data:
            item.amount = float(data["amount"])
        if "payment_unit" in data:
            item.payment_unit = data["payment_unit"]
        if "comment" in data:
            item.comment = data["comment"]
        if "is_active" in data:
            item.is_active = data["is_active"]
        if "sort_order" in data:
            item.sort_order = data["sort_order"]
            
        await item.save()
        
        result = {
            "id": item.id,
            "item_name": item.item_name,
            "item_type": item.item_type,
            "amount": item.amount,
            "payment_unit": item.payment_unit,
            "comment": item.comment,
            "is_active": item.is_active,
            "is_deduction": item.is_deduction,
            "sort_order": item.sort_order,
            "updated_at": item.updated_at
        }
        
        return Success(data=result, msg="契約精算項目が更新されました")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/items/{item_id}", summary="契約精算項目削除")
async def delete_contract_calculation_item(item_id: int):
    """契約精算項目を削除"""
    try:
        from app.models.contract import ContractCalculationItem
        
        # 精算項目を取得
        item = await ContractCalculationItem.get_or_none(id=item_id)
        if not item:
            return Fail(msg="精算項目が見つかりません")
            
        await item.delete()
        
        return Success(msg="契約精算項目が削除されました")
    except Exception as e:
        return Fail(msg=str(e))