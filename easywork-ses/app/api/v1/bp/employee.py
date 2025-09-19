from typing import Optional

from fastapi import APIRouter, Query

from app.controllers.personnel_unified import personnel_controller
from app.schemas import Fail, Success
from app.schemas.bp import ActiveBpEmployeeSchema, UpdateBPEmployeeSchema
from app.schemas.skill import AddBPEmployeeSkillSchema, UpdateBPEmployeeSkillSchema

router = APIRouter()


@router.get("/list", summary="協力会社要員一覧取得")
async def get_bp_employees_list(
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
    bp_company_id: Optional[int] = Query(None),
):
    try:
        search_params = {"name": name} if name else {}
        if bp_company_id:
            search_params["bp_company_id"] = bp_company_id
        bp_employee_data, total = await personnel_controller.list_bp_employees(
            page=page, page_size=pageSize, search_params=search_params
        )
        return Success(data=bp_employee_data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="idで協力会社要員取得")
async def get_bp_employee(id: int):
    try:
        bp_employee_data = await personnel_controller.get_bp_employee_by_id(id)
        if bp_employee_data:
            return Success(data=bp_employee_data)
        else:
            return Fail(msg="要員が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/add", summary="協力会社要員の新規")
async def add_bp_employee(bp_employee_data: UpdateBPEmployeeSchema):
    try:
        bp_employee_dict = bp_employee_data.model_dump(exclude_none=True)
        bp_employee = await personnel_controller.create_bp_employee(bp_employee_dict)
        data = await bp_employee.to_dict()
        return Success(msg="要員情報を登録しました", data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/active", summary="協力会社要員の有効化")
async def active_bp_employee(schema: ActiveBpEmployeeSchema):
    pass


@router.put("/update", summary="協力会社の要員情報更新")
async def update_bp_employee(bp_employee_data: UpdateBPEmployeeSchema):
    try:
        bp_employee_dict = bp_employee_data.model_dump(exclude_none=True)
        bp_employee_id = bp_employee_dict.pop("id", None)
        if not bp_employee_id:
            return Fail(msg="要員IDが必要です")

        bp_employee = await personnel_controller.update_bp_employee(bp_employee_id, bp_employee_dict)
        if bp_employee:
            data = await bp_employee.to_dict()
            return Success(msg="要員情報を更新しました", data=data)
        else:
            return Fail(msg="要員が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/delete", summary="協力会社の要員情報削除")
async def delete_bp_employee(id: int):
    try:
        success = await personnel_controller.delete_bp_employee(id)
        if success:
            return Success(msg="要員情報を削除しました")
        else:
            return Fail(msg="要員が見つかりません")
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
        bp_employee = await personnel_controller.get_bp_employee_by_id(employee_id)
        if not bp_employee:
            return Fail(msg="要員が見つかりません")

        skills, total = await personnel_controller.get_personnel_skills(employee_id, page=page, page_size=pageSize)

        # スキルデータを辞書形式に変換
        skills_data = []
        for skill_relation in skills:
            skill_dict = await skill_relation.to_dict()
            if hasattr(skill_relation, "skill") and skill_relation.skill:
                skill_dict["skill"] = await skill_relation.skill.to_dict()
            skills_data.append(skill_dict)

        return Success(data=skills_data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/skills/get", summary="IDで協力会社要員のスキル取得")
async def get_bp_employee_skill(skill_id: int):
    try:
        from app.models.personnel import PersonnelSkill

        skill_relation = await PersonnelSkill.get_or_none(id=skill_id).select_related("skill", "personnel")
        if not skill_relation:
            return Fail(msg="スキル記録が見つかりません")

        skill_dict = await skill_relation.to_dict()
        if hasattr(skill_relation, "skill") and skill_relation.skill:
            skill_dict["skill"] = await skill_relation.skill.to_dict()

        return Success(data=skill_dict)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/skills/add", summary="協力会社要員のスキル追加")
async def add_bp_employee_skill(skill_data: AddBPEmployeeSkillSchema):
    try:
        skill_dict = skill_data.model_dump(exclude_none=True)
        employee_id = skill_dict.get("employee_id") or skill_dict.get("bp_employee_id")

        if not employee_id:
            return Fail(msg="要員IDが必要です")

        bp_employee = await personnel_controller.get_bp_employee_by_id(employee_id)
        if not bp_employee:
            return Fail(msg="要員が見つかりません")

        skill_relation = await personnel_controller.add_personnel_skill(employee_id, skill_dict)

        result = await skill_relation.to_dict()
        if hasattr(skill_relation, "skill") and skill_relation.skill:
            result["skill"] = await skill_relation.skill.to_dict()

        return Success(msg="スキルを追加しました", data=result)
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/skills/update", summary="協力会社要員のスキル更新")
async def update_bp_employee_skill(skill_data: UpdateBPEmployeeSkillSchema):
    try:
        skill_dict = skill_data.model_dump(exclude_none=True)
        skill_id = skill_dict.pop("id", None)

        if not skill_id:
            return Fail(msg="スキルIDが必要です")

        skill_relation = await personnel_controller.update_personnel_skill(skill_id, skill_dict)

        result = await skill_relation.to_dict()
        if hasattr(skill_relation, "skill") and skill_relation.skill:
            result["skill"] = await skill_relation.skill.to_dict()

        return Success(msg="スキルを更新しました", data=result)
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/skills/delete", summary="協力会社要員のスキル削除")
async def delete_bp_employee_skill(skill_id: int):
    try:
        success = await personnel_controller.delete_personnel_skill(skill_id)
        if success:
            return Success(msg="スキルを削除しました")
        else:
            return Fail(msg="スキルが見つかりません")
    except Exception as e:
        return Fail(msg=str(e))
