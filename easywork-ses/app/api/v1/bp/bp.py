from typing import Optional

from fastapi import APIRouter, Query

from app.controllers.bp_company import bp_company_controller as bp_controller
from app.schemas import Fail, Success
from app.schemas.bp import AddBPCompanySchema, UpdateBPCompanySchema

router = APIRouter()


@router.get("/list", summary="協力会社一覧取得")
async def get_bp_list(
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
    representative: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    try:
        data, total = await bp_controller.get_bp_companies_with_filters(
            page=page, page_size=pageSize, name=name, representative=representative, status=status
        )
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="idで協力会社取得")
async def get_bp_company(id: int = Query(...)):
    try:
        data = await bp_controller.get_bp_company_dict_by_id(bp_company_id=id)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="協力会社が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/add", summary="協力会社新規")
async def add_bp_company(company_data: AddBPCompanySchema):
    try:
        data = await bp_controller.create_bp_company_dict(bp_company=company_data)
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/update", summary="協力会社更新")
async def update_bp_company(company_data: UpdateBPCompanySchema):
    try:
        data = await bp_controller.update_bp_company_dict(bp_company=company_data)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="協力会社が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/delete", summary="協力会社削除")
async def delete_bp_company(id: int = Query(...)):
    try:
        await bp_controller.delete_bp_company(bp_company_id=id)
        return Success()
    except Exception as e:
        return Fail(msg=str(e))
