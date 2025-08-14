from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from app.controllers.freelancer import freelancer_controller
from app.schemas import Fail, Success
from app.schemas.freelancer import (
    CreateFreelancerSchema,
    UpdateFreelancerSchema,
    FreelancerSearchSchema,
    CreateFreelancerSkillSchema,
    UpdateFreelancerSkillSchema,
    BatchUpdateFreelancerSkillsSchema,
    CreateFreelancerEvaluationSchema,
    FreelancerProjectMatchingSchema,
    FreelancerBusinessStatsSchema,
)
from app.utils.common import clean_dict

router = APIRouter()


# ===== フリーランサー基本管理 =====
@router.get("/list", summary="フリーランサー一覧取得")
async def get_freelancer_list(
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """フリーランサー一覧を取得"""
    try:
        freelancers, total = await freelancer_controller.list_freelancers(
            page=page, page_size=pageSize
        )
        data = await freelancer_controller.freelancers_to_dict(freelancers)
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/search", summary="フリーランサー高度検索")
async def search_freelancers(
    search_params: FreelancerSearchSchema,
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """フリーランサーの高度検索"""
    try:
        freelancers, total = await freelancer_controller.search_freelancers(
            search_params.model_dump(exclude_none=True), page=page, page_size=pageSize
        )
        data = await freelancer_controller.freelancers_to_dict(freelancers, include_relations=True)
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="IDでフリーランサー取得")
async def get_freelancer(
    id: int = Query(..., description="フリーランサーID"),
    include_relations: Optional[bool] = Query(True, description="関連情報を含むかどうか"),
):
    """IDでフリーランサーを取得"""
    try:
        freelancer = await freelancer_controller.get_freelancer_by_id(id, include_relations=include_relations)
        if freelancer:
            data = await freelancer_controller.freelancer_to_dict(freelancer, include_relations=include_relations)
            return Success(data=data)
        else:
            return Fail(msg="フリーランサーが見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/create", summary="フリーランサー作成")
async def create_freelancer(data: CreateFreelancerSchema):
    """フリーランサーを作成"""
    try:
        freelancer_data = data.model_dump(exclude_none=True)
        freelancer = await freelancer_controller.create_freelancer(freelancer_data)
        result = await freelancer_controller.freelancer_to_dict(freelancer, include_relations=True)
        return Success(data=result, msg="フリーランサーが正常に作成されました")
    except ValidationError as e:
        return Fail(msg=f"バリデーションエラー: {e}")
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/update", summary="フリーランサー更新")
async def update_freelancer(
    id: int = Query(..., description="フリーランサーID"),
    data: UpdateFreelancerSchema = None,
):
    """フリーランサー情報を更新"""
    try:
        freelancer_data = data.model_dump(exclude_none=True) if data else {}
        freelancer = await freelancer_controller.update_freelancer(id, freelancer_data)
        if freelancer:
            result = await freelancer_controller.freelancer_to_dict(freelancer, include_relations=True)
            return Success(data=result, msg="フリーランサー情報が正常に更新されました")
        else:
            return Fail(msg="フリーランサーが見つかりません")
    except ValidationError as e:
        return Fail(msg=f"バリデーションエラー: {e}")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/delete", summary="フリーランサー削除")
async def delete_freelancer(id: int = Query(..., description="フリーランサーID")):
    """フリーランサーを削除（論理削除）"""
    try:
        freelancer = await freelancer_controller.delete_freelancer(id)
        if freelancer:
            return Success(msg="フリーランサーが正常に削除されました")
        else:
            return Fail(msg="フリーランサーが見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


# ===== スキル管理 =====
@router.get("/skills", summary="フリーランサースキル一覧取得")
async def get_freelancer_skills(
    freelancer_id: int = Query(..., description="フリーランサーID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """フリーランサーのスキル一覧を取得"""
    try:
        freelancer = await freelancer_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        skills, total = await freelancer_controller.get_freelancer_skills(freelancer, page=page, page_size=pageSize)
        
        # スキルデータを辞書形式に変換
        skills_data = []
        for skill_relation in skills:
            skill_dict = await skill_relation.to_dict()
            if hasattr(skill_relation, 'skill') and skill_relation.skill:
                skill_dict['skill'] = await skill_relation.skill.to_dict()
            skills_data.append(skill_dict)
        
        return Success(data=skills_data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/skills/add", summary="フリーランサースキル追加")
async def add_freelancer_skill(
    data: CreateFreelancerSkillSchema = None,
):
    """フリーランサーにスキルを追加"""
    try:
        freelancer_id = data.freelancer_id
        freelancer = await freelancer_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        skill_data = clean_dict( data.model_dump(exclude_none=True) ) if data else {}
        skill_relation = await freelancer_controller.add_freelancer_skill(freelancer, skill_data)
        
        # 結果を辞書形式に変換
        result = await skill_relation.to_dict()
        if hasattr(skill_relation, 'skill') and skill_relation.skill:
            result['skill'] = await skill_relation.skill.to_dict()
        
        return Success(data=result, msg="スキルが正常に追加されました")
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/skills/update", summary="フリーランサースキル更新")
async def update_freelancer_skill(
    skill_id: int = Query(..., description="スキル関連ID"),
    data: UpdateFreelancerSkillSchema = None,
):
    """フリーランサースキルを更新"""
    try:
        skill_data = data.model_dump(exclude_none=True) if data else {}
        skill_relation = await freelancer_controller.update_freelancer_skill(skill_id, skill_data)
        
        # 結果を辞書形式に変換
        result = await skill_relation.to_dict()
        if hasattr(skill_relation, 'skill') and skill_relation.skill:
            result['skill'] = await skill_relation.skill.to_dict()
        
        return Success(data=result, msg="スキルが正常に更新されました")
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/skills/delete", summary="フリーランサースキル削除")
async def delete_freelancer_skill(skill_id: int = Query(..., description="スキル関連ID")):
    """フリーランサースキルを削除"""
    try:
        skill_relation = await freelancer_controller.delete_freelancer_skill(skill_id)
        if skill_relation:
            return Success(msg="スキルが正常に削除されました")
        else:
            return Fail(msg="スキルが見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/skills/batch-update", summary="フリーランサースキル一括更新")
async def batch_update_freelancer_skills(
    freelancer_id: int = Query(..., description="フリーランサーID"),
    data: BatchUpdateFreelancerSkillsSchema = None,
):
    """フリーランサースキルを一括更新"""
    try:
        freelancer = await freelancer_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        skills_data = data.skills if data else []
        await freelancer_controller.batch_update_freelancer_skills(freelancer, skills_data)
        
        # 更新後のスキル一覧を取得
        skills, total = await freelancer_controller.get_freelancer_skills(freelancer)
        skills_dict = []
        for skill_relation in skills:
            skill_dict = await skill_relation.to_dict()
            if hasattr(skill_relation, 'skill') and skill_relation.skill:
                skill_dict['skill'] = await skill_relation.skill.to_dict()
            skills_dict.append(skill_dict)
        
        return Success(data=skills_dict, msg="スキルが正常に一括更新されました")
    except Exception as e:
        return Fail(msg=str(e))


# ===== 評価管理 =====
@router.get("/evaluations", summary="フリーランサー評価一覧取得")
async def get_freelancer_evaluations(
    freelancer_id: int = Query(..., description="フリーランサーID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """フリーランサーの評価一覧を取得"""
    try:
        freelancer = await freelancer_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        evaluations, total = await freelancer_controller.get_freelancer_evaluations(freelancer, page=page, page_size=pageSize)
        
        # 評価データを辞書形式に変換
        evaluations_data = []
        for evaluation in evaluations:
            evaluation_dict = await evaluation.to_dict()
            if hasattr(evaluation, 'case') and evaluation.case:
                evaluation_dict['case'] = await evaluation.case.to_dict()
            if hasattr(evaluation, 'contract') and evaluation.contract:
                evaluation_dict['contract'] = await evaluation.contract.to_dict()
            evaluations_data.append(evaluation_dict)
        
        return Success(data=evaluations_data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/evaluations/create", summary="フリーランサー評価作成")
async def create_freelancer_evaluation(
    freelancer_id: int = Query(..., description="フリーランサーID"),
    evaluator_id: int = Query(..., description="評価者ID"),
    data: CreateFreelancerEvaluationSchema = None,
):
    """フリーランサー評価を作成"""
    try:
        freelancer = await freelancer_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        evaluation_data = data.model_dump(exclude_none=True) if data else {}
        evaluation = await freelancer_controller.create_freelancer_evaluation(freelancer, evaluation_data, evaluator_id)
        
        result = await evaluation.to_dict()
        return Success(data=result, msg="評価が正常に作成されました")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/evaluations/summary", summary="フリーランサー評価サマリー取得")
async def get_freelancer_evaluation_summary(freelancer_id: int = Query(..., description="フリーランサーID")):
    """フリーランサー評価のサマリーを取得"""
    try:
        freelancer = await freelancer_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        summary = await freelancer_controller.get_freelancer_evaluation_summary(freelancer)
        return Success(data=summary)
    except Exception as e:
        return Fail(msg=str(e))


# ===== 業務ロジック =====
@router.get("/available", summary="利用可能フリーランサー取得")
async def get_available_freelancers(
    project_start_date: Optional[date] = Query(None, description="プロジェクト開始日"),
    required_skills: Optional[List[str]] = Query(None, description="必要スキルリスト"),
    min_experience_years: Optional[float] = Query(None, description="最低経験年数", ge=0),
    budget_min: Optional[float] = Query(None, description="予算下限", ge=0),
    budget_max: Optional[float] = Query(None, description="予算上限", ge=0),
    location: Optional[str] = Query(None, description="希望勤務地"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """利用可能なフリーランサーを取得"""
    try:
        from decimal import Decimal
        min_exp = Decimal(str(min_experience_years)) if min_experience_years else None
        budget_range = None
        if budget_min or budget_max:
            budget_range = (
                Decimal(str(budget_min)) if budget_min else None,
                Decimal(str(budget_max)) if budget_max else None
            )
        
        freelancers, total = await freelancer_controller.get_available_freelancers(
            project_start_date=project_start_date,
            required_skills=required_skills,
            min_experience_years=min_exp,
            budget_range=budget_range,
            location=location,
            page=page,
            page_size=pageSize,
        )
        
        data = await freelancer_controller.freelancers_to_dict(freelancers, include_relations=True)
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/project-matching", summary="プロジェクトマッチング検索")
async def project_matching_search(
    matching_params: FreelancerProjectMatchingSchema,
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    """プロジェクト要件に基づくフリーランサーマッチング"""
    try:
        freelancers, total = await freelancer_controller.project_matching_search(
            matching_params.model_dump(exclude_none=True), page=page, page_size=pageSize
        )
        
        data = await freelancer_controller.freelancers_to_dict(freelancers, include_relations=True)
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/dashboard", summary="フリーランサーダッシュボード統計")
async def get_freelancer_dashboard(freelancer_id: int = Query(..., description="フリーランサーID")):
    """フリーランサーのダッシュボード統計情報を取得"""
    try:
        freelancer = await freelancer_controller.get_freelancer_by_id(freelancer_id, include_relations=True)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        dashboard_stats = await freelancer_controller.get_freelancer_dashboard_stats(freelancer)
        return Success(data=dashboard_stats)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/business-stats", summary="フリーランサー事業統計")
async def get_freelancer_business_stats(
    freelancer_id: int = Query(..., description="フリーランサーID"),
    stats_params: FreelancerBusinessStatsSchema = None,
):
    """フリーランサーの事業統計を取得"""
    try:
        freelancer = await freelancer_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        params = stats_params.model_dump(exclude_none=True) if stats_params else {}
        business_stats = await freelancer_controller.get_freelancer_business_stats(
            freelancer,
            year=params.get('year'),
            month_from=params.get('month_from', 1),
            month_to=params.get('month_to', 12)
        )
        
        return Success(data=business_stats)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/visa-expiring", summary="ビザ期限切れ警告")
async def get_visa_expiring_freelancers(days: Optional[int] = Query(90, description="警告日数", ge=1, le=365)):
    """ビザが期限切れになるフリーランサーを取得"""
    try:
        freelancers = await freelancer_controller.check_visa_expiring_soon(days=days)
        data = await freelancer_controller.freelancers_to_dict(freelancers, include_relations=False)
        return Success(data=data, total=len(freelancers))
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/top-rated", summary="高評価フリーランサー取得")
async def get_top_rated_freelancers(
    limit: Optional[int] = Query(10, description="取得件数", ge=1, le=50),
    min_evaluations: Optional[int] = Query(3, description="最低評価数", ge=1),
):
    """高評価フリーランサーを取得"""
    try:
        freelancers = await freelancer_controller.get_top_rated_freelancers(limit=limit, min_evaluations=min_evaluations)
        data = await freelancer_controller.freelancers_to_dict(freelancers, include_relations=True)
        return Success(data=data, total=len(freelancers))
    except Exception as e:
        return Fail(msg=str(e))