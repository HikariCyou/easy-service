from typing import Optional

from fastapi import APIRouter, Query

from app.controllers.bp import bp_employee_controller
from app.schemas import Fail, Success
from app.schemas.bp import ActiveBpEmployeeSchema, UpdateBPEmployeeSchema
from app.schemas.skill import (AddBPEmployeeSkillSchema, UpdateBPEmployeeSkillSchema)

router = APIRouter()


@router.get("/list", summary="協力会社要員一覧取得")
async def get_bp_employees_list(
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
):
    try:
        data, total = await bp_employee_controller.list_bp_employees_with_filters(
            page=page, page_size=pageSize, name=name
        )
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="idで協力会社要員取得")
async def get_bp_employee(id: int):
    try:
        data = await bp_employee_controller.get_bp_employee_dict_by_id(bp_employee_id=id)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="要員が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/add", summary="協力会社要員の新規")
async def add_bp_employee(bp_employee_data: UpdateBPEmployeeSchema):
    try:
        data = await bp_employee_controller.add_bp_employee_dict(bp_employee=bp_employee_data)
        if data:
            return Success(msg="要員情報を登録しました", data=data)
        else:
            return Fail(msg="要員情報の登録に失敗しました")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/active", summary="協力会社要員の有効化")
async def active_bp_employee(schema: ActiveBpEmployeeSchema):
    pass


@router.put("/update", summary="協力会社の要員情報更新")
async def update_bp_employee(bp_employee_data: UpdateBPEmployeeSchema):
    try:
        data = await bp_employee_controller.update_bp_employee_dict(bp_employee=bp_employee_data)
        if data:
            return Success(msg="要員情報を更新しました", data=data)
        else:
            return Fail(msg="要員が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/delete", summary="協力会社の要員情報削除")
async def delete_bp_employee(id: int):
    try:
        await bp_employee_controller.delete_bp_employee(bp_employee_id=id)
        return Success(msg="要員情報を削除しました")
    except Exception as e:
        return Fail(msg=str(e))


# =============================================================================
# BP社員のスキル関連API
# =============================================================================


@router.get("/skills/list", summary="協力会社要員のスキル一覧取得")
async def get_bp_employee_skills_list(
    employee_id: int = Query(..., description="協力会社要員ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    try:
        data, total = await bp_employee_controller.get_skills_with_details(
            employee_id=employee_id, page=page, pageSize=pageSize
        )
        if data is None:
            return Fail(msg="要員が見つかりません")
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/skills/get", summary="IDで協力会社要員のスキル取得")
async def get_bp_employee_skill(skill_id: int):
    try:
        data = await bp_employee_controller.get_skill_by_id(skill_id=skill_id)
        if not data:
            return Fail(msg="スキル記録が見つかりません")
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/skills/add", summary="協力会社要員のスキル追加")
async def add_bp_employee_skill(skill_data: AddBPEmployeeSkillSchema):
    try:
        data, error_msg = await bp_employee_controller.add_skill_with_validation(skill_data=skill_data)
        if error_msg:
            return Fail(msg=error_msg)
        return Success(msg="スキルを追加しました", data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/skills/update", summary="協力会社要員のスキル更新")
async def update_bp_employee_skill(skill_data: UpdateBPEmployeeSkillSchema):
    try:
        data, error_msg = await bp_employee_controller.update_skill(skill_data)
        if error_msg:
            return Fail(msg=error_msg)
        return Success(msg="スキルを更新しました", data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/skills/delete", summary="協力会社要員のスキル削除")
async def delete_bp_employee_skill(skill_id: int):
    try:
        success, error_msg = await bp_employee_controller.delete_skill(skill_id=skill_id)
        if not success:
            return Fail(msg=error_msg)
        return Success(msg="スキルを削除しました")
    except Exception as e:
        return Fail(msg=str(e))
