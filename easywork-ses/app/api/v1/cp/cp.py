from typing import Optional

from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.cp import cp_controller
from app.schemas import Fail, Success
from app.schemas.cp import AddClientCompanySchema, UpdateClientCompanySchema

router = APIRouter()


@router.get("/list", summary="取り先会社一覧を取得")
async def get_cp_list(
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1),
    company_name: Optional[str] = Query(None),
    representative: Optional[str] = Query(None),
):
    try:
        q = Q()
        if company_name:
            q &= Q(company_name__icontains=company_name)
        if representative:
            q &= Q(representative__icontains=representative)

        companies, total = await cp_controller.list_client_companies(page=page, page_size=pageSize, search=q)
        data = [await company.to_dict() for company in companies]

        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/add", summary="取り先会社新規")
async def add_cp_company(company_data: AddClientCompanySchema):
    await cp_controller.add_client_company(company_data=company_data)
    return Success()


@router.put("/update", summary="取り先会社更新")
async def update_cp_company(company_data: UpdateClientCompanySchema):
    await cp_controller.update_client_company(company_data=company_data)
    return Success()


@router.delete("/delete", summary="取り先会社削除")
async def delete_cp_company(id: Optional[int] = Query(...)):
    result = await cp_controller.delete_client_company(id=id)
    if result:
        return Success()
    else:
        return Fail()
