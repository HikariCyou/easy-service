from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from app.controllers.personnel_unified import personnel_controller
from app.schemas import Fail, Success
from app.schemas.employee import (
    BatchUpdateEmployeeSkillsSchema,
    CreateEmployeeEvaluationSchema,
    CreateEmployeeSchema,
    CreateEmployeeSkillSchema,
    EmployeeSearchSchema,
    UpdateEmployeeSchema,
    UpdateEmployeeSkillSchema,
)

router = APIRouter()


# ===== 员工基本管理 =====
@router.get("/list", summary="従業員一覧取得")
async def get_employee_list(
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    include_skills: Optional[bool] = Query(False, description="技能情報を含むかどうか"),
):
    """従業員一覧を取得"""
    try:
        employee_data, total = await personnel_controller.list_employees(page=page, page_size=pageSize)
        return Success(data=employee_data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/search", summary="従業員高度検索")
async def search_employees(
    search_params: EmployeeSearchSchema,
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """従業員の高度検索"""
    try:
        employee_data, total = await personnel_controller.list_employees(
            page=page, page_size=pageSize, search_params=search_params.model_dump(exclude_none=True)
        )
        return Success(data=employee_data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="IDで従業員取得")
async def get_employee(
    id: int = Query(..., description="従業員ID"),
    include_relations: Optional[bool] = Query(True, description="関連情報を含むかどうか"),
):
    """IDで従業員を取得"""
    try:
        employee_data = await personnel_controller.get_employee_by_id(id)
        if employee_data:
            return Success(data=employee_data)
        else:
            return Fail(msg="従業員が見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get-by-user", summary="ユーザーIDで従業員取得")
async def get_employee_by_user(
    user_id: int = Query(..., description="ユーザーID"),
    include_relations: Optional[bool] = Query(True, description="関連情報を含むかどうか"),
):
    """ユーザーIDで従業員を取得"""
    try:
        employee = await personnel_controller.get_employee_by_user_id(user_id)
        if employee:
            data = await employee.to_dict()
            return Success(data=data)
        else:
            return Fail(msg="従業員が見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/create", summary="従業員作成")
async def create_employee(data: CreateEmployeeSchema):
    """従業員を作成"""
    try:
        employee_data = data.model_dump(exclude_none=True)
        personnel = await personnel_controller.create_employee(employee_data)
        result = await personnel.to_dict()
        return Success(data=result, msg="従業員が正常に作成されました")
    except ValidationError as e:
        return Fail(msg=f"バリデーションエラー: {e}")
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/update", summary="従業員更新")
async def update_employee(
    id: int = Query(..., description="従業員ID"),
    data: UpdateEmployeeSchema = None,
):
    """従業員情報を更新"""
    try:
        employee_data = data.model_dump(exclude_none=True) if data else {}
        employee = await personnel_controller.update_employee(id, employee_data)
        if employee:
            result = await employee.to_dict()
            return Success(data=result, msg="従業員情報が正常に更新されました")
        else:
            return Fail(msg="従業員が見つかりません")
    except ValidationError as e:
        return Fail(msg=f"バリデーションエラー: {e}")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/delete", summary="従業員削除")
async def delete_employee(id: int = Query(..., description="従業員ID")):
    """従業員を削除"""
    try:
        success = await personnel_controller.delete_employee(id)
        if success:
            return Success(msg="従業員が正常に削除されました")
        else:
            return Fail(msg="従業員が見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


# ===== 技能管理 =====
@router.get("/skills", summary="従業員技能一覧取得")
async def get_employee_skills(
    employee_id: int = Query(..., description="従業員ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """従業員の技能一覧を取得"""
    try:
        employee = await personnel_controller.get_employee_by_id(employee_id)
        if not employee:
            return Fail(msg="従業員が見つかりません")

        skills, total = await personnel_controller.get_personnel_skills(employee_id, page=page, page_size=pageSize)

        # 技能データを辞書形式に変換
        skills_data = []
        for skill_relation in skills:
            skill_dict = await skill_relation.to_dict()
            if hasattr(skill_relation, "skill") and skill_relation.skill:
                skill_dict["skill"] = await skill_relation.skill.to_dict()
            skills_data.append(skill_dict)

        return Success(data=skills_data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/skills/add", summary="従業員技能追加")
async def add_employee_skill(
    employee_id: int = Query(..., description="従業員ID"),
    data: CreateEmployeeSkillSchema = None,
):
    """従業員に技能を追加"""
    try:
        employee = await personnel_controller.get_employee_by_id(employee_id)
        if not employee:
            return Fail(msg="従業員が見つかりません")

        skill_data = data.model_dump(exclude_none=True) if data else {}
        skill_relation = await personnel_controller.add_personnel_skill(employee_id, skill_data)

        # 結果を辞書形式に変換
        result = await skill_relation.to_dict()
        if hasattr(skill_relation, "skill") and skill_relation.skill:
            result["skill"] = await skill_relation.skill.to_dict()

        return Success(data=result, msg="技能が正常に追加されました")
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/skills/update", summary="従業員技能更新")
async def update_employee_skill(
    skill_id: int = Query(..., description="技能関連ID"),
    data: UpdateEmployeeSkillSchema = None,
):
    """従業員技能を更新"""
    try:
        skill_data = data.model_dump(exclude_none=True) if data else {}
        skill_relation = await personnel_controller.update_personnel_skill(skill_id, skill_data)

        # 結果を辞書形式に変換
        result = await skill_relation.to_dict()
        if hasattr(skill_relation, "skill") and skill_relation.skill:
            result["skill"] = await skill_relation.skill.to_dict()

        return Success(data=result, msg="技能が正常に更新されました")
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/skills/delete", summary="従業員技能削除")
async def delete_employee_skill(skill_id: int = Query(..., description="技能関連ID")):
    """従業員技能を削除"""
    try:
        success = await personnel_controller.delete_personnel_skill(skill_id)
        if success:
            return Success(msg="技能が正常に削除されました")
        else:
            return Fail(msg="技能が見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/skills/batch-update", summary="従業員技能一括更新")
async def batch_update_employee_skills(
    employee_id: int = Query(..., description="従業員ID"),
    data: BatchUpdateEmployeeSkillsSchema = None,
):
    """従業員技能を一括更新"""
    try:
        employee = await personnel_controller.get_employee_by_id(employee_id)
        if not employee:
            return Fail(msg="従業員が見つかりません")

        skills_data = data.skills if data else []

        # 統一Controllerには一括更新メソッドがないので、手動実装
        from tortoise.transactions import in_transaction

        from app.models.personnel import PersonnelSkill

        async with in_transaction():
            # 既存スキル削除
            await PersonnelSkill.filter(personnel_id=employee_id).delete()

            # 新しいスキル追加
            for skill_item in skills_data:
                try:
                    await personnel_controller.add_personnel_skill(employee_id, skill_item)
                except ValueError:
                    continue

        # 更新後の技能一覧を取得
        skills, total = await personnel_controller.get_personnel_skills(employee_id)
        skills_dict = []
        for skill_relation in skills:
            skill_dict = await skill_relation.to_dict()
            if hasattr(skill_relation, "skill") and skill_relation.skill:
                skill_dict["skill"] = await skill_relation.skill.to_dict()
            skills_dict.append(skill_dict)

        return Success(data=skills_dict, msg="技能が正常に一括更新されました")
    except Exception as e:
        return Fail(msg=str(e))


# ===== 評価管理 =====
@router.get("/evaluations", summary="従業員評価一覧取得")
async def get_employee_evaluations(
    employee_id: int = Query(..., description="従業員ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """従業員の評価一覧を取得"""
    try:
        from app.models.evaluation import PersonEvaluation

        employee = await personnel_controller.get_employee_by_id(employee_id)
        if not employee:
            return Fail(msg="従業員が見つかりません")

        # 統一評価テーブルから取得
        query = PersonEvaluation.filter(personnel_id=employee_id).select_related("case", "contract")
        total = await query.count()
        evaluations = (
            await query.order_by("-evaluation_date", "-created_at").limit(pageSize).offset((page - 1) * pageSize).all()
        )

        # 評価データを辞書形式に変換
        evaluations_data = []
        for evaluation in evaluations:
            evaluation_dict = await evaluation.to_dict()
            if hasattr(evaluation, "case") and evaluation.case:
                evaluation_dict["case"] = await evaluation.case.to_dict()
            if hasattr(evaluation, "contract") and evaluation.contract:
                evaluation_dict["contract"] = await evaluation.contract.to_dict()
            evaluations_data.append(evaluation_dict)

        return Success(data=evaluations_data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/evaluations/create", summary="従業員評価作成")
async def create_employee_evaluation(
    employee_id: int = Query(..., description="従業員ID"),
    evaluator_id: int = Query(..., description="評価者ID"),
    data: CreateEmployeeEvaluationSchema = None,
):
    """従業員評価を作成"""
    try:
        from tortoise.transactions import in_transaction

        from app.models.evaluation import PersonEvaluation

        employee = await personnel_controller.get_employee_by_id(employee_id)
        if not employee:
            return Fail(msg="従業員が見つかりません")

        evaluation_data = data.model_dump(exclude_none=True) if data else {}
        evaluation_data["personnel_id"] = employee_id
        evaluation_data["evaluator_id"] = evaluator_id

        async with in_transaction():
            evaluation = await PersonEvaluation.create(**evaluation_data)

        result = await evaluation.to_dict()
        return Success(data=result, msg="評価が正常に作成されました")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/evaluations/summary", summary="従業員評価サマリー取得")
async def get_employee_evaluation_summary(employee_id: int = Query(..., description="従業員ID")):
    """従業員評価のサマリーを取得"""
    try:
        from app.models.evaluation import PersonEvaluation

        employee = await personnel_controller.get_employee_by_id(employee_id)
        if not employee:
            return Fail(msg="従業員が見つかりません")

        # 評価サマリー計算
        evaluations = await PersonEvaluation.filter(personnel_id=employee_id).all()

        if not evaluations:
            summary = {
                "total_evaluations": 0,
                "average_overall_rating": 0,
                "average_technical_skill": 0,
                "average_communication": 0,
                "average_reliability": 0,
                "recommendation_rate": 0,
            }
        else:
            total = len(evaluations)
            summary = {
                "total_evaluations": total,
                "average_overall_rating": round(sum(e.overall_rating for e in evaluations) / total, 2),
                "average_technical_skill": round(sum(e.technical_skill for e in evaluations) / total, 2),
                "average_communication": round(sum(e.communication for e in evaluations) / total, 2),
                "average_reliability": round(sum(e.reliability for e in evaluations) / total, 2),
                "recommendation_rate": round(sum(1 for e in evaluations if e.recommendation) / total * 100, 1),
            }

        return Success(data=summary)
    except Exception as e:
        return Fail(msg=str(e))


# ===== 業務ロジック =====
@router.get("/available", summary="利用可能従業員取得")
async def get_available_employees(
    project_start_date: Optional[date] = Query(None, description="プロジェクト開始日"),
    required_skills: Optional[List[str]] = Query(None, description="必要技能リスト"),
    min_experience_years: Optional[float] = Query(None, description="最低経験年数", ge=0),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """利用可能な従業員を取得（プロジェクト需求に基づく）"""
    try:
        from app.models.enums import PersonType

        employees, total = await personnel_controller.get_available_personnel(
            person_type=PersonType.EMPLOYEE,
            project_start_date=project_start_date,
            required_skills=required_skills,
            min_experience_years=min_experience_years,
            page=page,
            page_size=pageSize,
        )

        data = [await p.to_dict() for p in employees]
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/visa-expiring", summary="ビザ期限切れ警告")
async def get_visa_expiring_employees(days: Optional[int] = Query(90, description="警告日数", ge=1, le=365)):
    """ビザが期限切れになる従業員を取得"""
    try:
        employees = await personnel_controller.check_visa_expiring_soon(days=days)
        data = [await p.to_dict() for p in employees]
        return Success(data=data, total=len(employees))
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/dashboard", summary="従業員ダッシュボード統計")
async def get_employee_dashboard(employee_id: int = Query(..., description="従業員ID")):
    """従業員のダッシュボード統計情報を取得"""
    try:
        from app.models.evaluation import PersonEvaluation
        from app.models.personnel import PersonnelSkill

        employee = await personnel_controller.get_employee_by_id(employee_id)
        if not employee:
            return Fail(msg="従業員が見つかりません")

        # スキル統計
        skills_count = await PersonnelSkill.filter(personnel_id=employee_id).count()
        primary_skills_count = await PersonnelSkill.filter(personnel_id=employee_id, is_primary_skill=True).count()

        # 評価統計
        evaluations = await PersonEvaluation.filter(personnel_id=employee_id).all()
        total_evaluations = len(evaluations)

        evaluation_summary = {
            "total_evaluations": total_evaluations,
            "average_overall_rating": 0,
            "average_technical_skill": 0,
            "average_communication": 0,
            "average_reliability": 0,
            "recommendation_rate": 0,
        }

        if evaluations:
            evaluation_summary.update(
                {
                    "average_overall_rating": round(sum(e.overall_rating for e in evaluations) / total_evaluations, 2),
                    "average_technical_skill": round(
                        sum(e.technical_skill for e in evaluations) / total_evaluations, 2
                    ),
                    "average_communication": round(sum(e.communication for e in evaluations) / total_evaluations, 2),
                    "average_reliability": round(sum(e.reliability for e in evaluations) / total_evaluations, 2),
                    "recommendation_rate": round(
                        sum(1 for e in evaluations if e.recommendation) / total_evaluations * 100, 1
                    ),
                }
            )

        dashboard_stats = {
            "basic_info": {
                "name": employee.name,
                "code": employee.code,
                "current_age": employee.current_age,
                "employment_status": employee.employment_status,
                "is_visa_expiring": employee.is_visa_expiring_soon(),
            },
            "skills_stats": {
                "total_skills": skills_count,
                "primary_skills": primary_skills_count,
            },
            "contract_stats": {
                "total_contracts": 0,  # TODO: Contractモデル統一後に実装
                "active_contracts": 0,
            },
            "evaluation_stats": evaluation_summary,
        }

        return Success(data=dashboard_stats)
    except Exception as e:
        return Fail(msg=str(e))
