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
    personnel_id: Optional[int] = Query(None, ge=1, description="要員ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    case_id: Optional[int] = Query(None, ge=1)
):
    try:
        q = Q()
        if keyword:
            q &= Q(contract_number__icontains=keyword) | Q(case__title__icontains=keyword)
        if personnel_id:
            q &= Q(personnel_id=personnel_id)
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
    """契約条件の変更処理"""
    try:
        from app.models.contract import Contract
        from app.models.enums import ContractChangeReason
        
        # 契約を取得
        contract = await Contract.get_or_none(id=data.contract_id)
        if not contract:
            return Fail(msg="契約が見つかりません")
            
        # 変更理由をEnumに変換
        reason_mapping = {
            "クライアント要望": ContractChangeReason.CLIENT_REQUEST,
            "人材要望": ContractChangeReason.PERSONNEL_REQUEST,
            "プロジェクト変更": ContractChangeReason.PROJECT_CHANGE,
            "予算変更": ContractChangeReason.BUDGET_CHANGE,
            "市場状況": ContractChangeReason.MARKET_CONDITION,
            "その他": ContractChangeReason.OTHER
        }
        reason_enum = reason_mapping.get(data.reason, ContractChangeReason.CLIENT_REQUEST)
        
        # 契約期間の変更処理
        if data.new_contract_end_date:
            contract.contract_end_date = data.new_contract_end_date
            await contract.save()
        
        # 契約条件変更処理を実行
        await contract.update_conditions(
            new_unit_price=data.new_unit_price,
            new_working_hours=data.new_working_hours,
            reason=reason_enum,
            effective_date=data.effective_date,
            requested_by=data.requested_by
        )
        
        return Success(msg="契約条件の変更が完了しました")
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
        histories = await ContractChangeHistory.filter(
            contract=contract
        ).order_by("-created_at").limit(limit)
        
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