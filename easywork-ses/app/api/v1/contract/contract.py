from typing import Optional

from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.contract import contract_controller
from app.schemas import Success, Fail
from app.schemas.contract import CreateContract

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
        data = await contract.to_dict()
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))