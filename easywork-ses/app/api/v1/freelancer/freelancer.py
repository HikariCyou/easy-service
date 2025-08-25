from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import ValidationError

from app.controllers.personnel_unified import personnel_controller
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
        freelancer_data, total = await personnel_controller.list_freelancers(
            page=page, page_size=pageSize
        )
        return Success(data=freelancer_data, total=total)
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
        freelancer_data, total = await personnel_controller.list_freelancers(
            page=page, page_size=pageSize, search_params=search_params.model_dump(exclude_none=True)
        )
        return Success(data=freelancer_data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="IDでフリーランサー取得")
async def get_freelancer(
    id: int = Query(..., description="フリーランサーID"),
    include_relations: Optional[bool] = Query(True, description="関連情報を含むかどうか"),
):
    """IDでフリーランサーを取得"""
    try:
        freelancer_data = await personnel_controller.get_freelancer_by_id(id)
        if freelancer_data:
            return Success(data=freelancer_data)
        else:
            return Fail(msg="フリーランサーが見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/create", summary="フリーランサー作成")
async def create_freelancer(data: CreateFreelancerSchema):
    """フリーランサーを作成"""
    try:
        freelancer_data = data.model_dump(exclude_none=True)
        freelancer = await personnel_controller.create_freelancer(freelancer_data)
        result = await freelancer.to_dict()
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
        freelancer = await personnel_controller.update_freelancer(id, freelancer_data)
        if freelancer:
            result = await freelancer.to_dict()
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
        success = await personnel_controller.delete_freelancer(id)
        if success:
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
        freelancer = await personnel_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        skills, total = await personnel_controller.get_personnel_skills(freelancer_id, page=page, page_size=pageSize)
        
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
        freelancer = await personnel_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        skill_data = clean_dict( data.model_dump(exclude_none=True) ) if data else {}
        skill_relation = await personnel_controller.add_personnel_skill(freelancer_id, skill_data)
        
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
        skill_relation = await personnel_controller.update_personnel_skill(skill_id, skill_data)
        
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
        success = await personnel_controller.delete_personnel_skill(skill_id)
        if success:
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
        freelancer = await personnel_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        skills_data = data.skills if data else []
        
        # 統一Controllerには一括更新メソッドがないので、手動実装
        from tortoise.transactions import in_transaction
        from app.models.personnel import PersonnelSkill
        
        async with in_transaction():
            # 既存スキル削除
            await PersonnelSkill.filter(personnel_id=freelancer_id).delete()
            
            # 新しいスキル追加
            for skill_item in skills_data:
                try:
                    await personnel_controller.add_personnel_skill(freelancer_id, skill_item)
                except ValueError:
                    continue
        
        # 更新後のスキル一覧を取得
        skills, total = await personnel_controller.get_personnel_skills(freelancer_id)
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
        from app.models.evaluation import PersonEvaluation
        
        freelancer = await personnel_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        # 統一評価テーブルから取得
        query = PersonEvaluation.filter(personnel_id=freelancer_id).select_related("case", "contract")
        total = await query.count()
        evaluations = await query.order_by("-evaluation_date", "-created_at").limit(pageSize).offset((page - 1) * pageSize).all()
        
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
        from app.models.evaluation import PersonEvaluation
        from tortoise.transactions import in_transaction
        
        freelancer = await personnel_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        evaluation_data = data.model_dump(exclude_none=True) if data else {}
        evaluation_data['personnel_id'] = freelancer_id
        evaluation_data['evaluator_id'] = evaluator_id
        
        async with in_transaction():
            evaluation = await PersonEvaluation.create(**evaluation_data)
        
        result = await evaluation.to_dict()
        return Success(data=result, msg="評価が正常に作成されました")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/evaluations/summary", summary="フリーランサー評価サマリー取得")
async def get_freelancer_evaluation_summary(freelancer_id: int = Query(..., description="フリーランサーID")):
    """フリーランサー評価のサマリーを取得"""
    try:
        from app.models.evaluation import PersonEvaluation
        
        freelancer = await personnel_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        # 評価サマリー計算
        evaluations = await PersonEvaluation.filter(personnel_id=freelancer_id).all()
        
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
        from app.models.enums import PersonType
        
        freelancers, total = await personnel_controller.get_available_personnel(
            person_type=PersonType.FREELANCER,
            project_start_date=project_start_date,
            required_skills=required_skills,
            min_experience_years=min_experience_years,
            page=page,
            page_size=pageSize,
        )
        
        data = [await p.to_dict() for p in freelancers]
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
        # TODO: 統一Controllerにマッチングロジックを実装する必要があります
        # 現在は基本検索で代用
        from app.models.enums import PersonType
        
        params = matching_params.model_dump(exclude_none=True)
        freelancers, total = await personnel_controller.get_available_personnel(
            person_type=PersonType.FREELANCER,
            project_start_date=params.get('project_start_date'),
            required_skills=params.get('required_skills'),
            min_experience_years=params.get('min_experience_years'),
            page=page,
            page_size=pageSize,
        )
        
        data = [await p.to_dict() for p in freelancers]
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/dashboard", summary="フリーランサーダッシュボード統計")
async def get_freelancer_dashboard(freelancer_id: int = Query(..., description="フリーランサーID")):
    """フリーランサーのダッシュボード統計情報を取得"""
    try:
        from app.models.personnel import PersonnelSkill
        from app.models.evaluation import PersonEvaluation
        
        freelancer = await personnel_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        # スキル統計
        skills_count = await PersonnelSkill.filter(personnel_id=freelancer_id).count()
        primary_skills_count = await PersonnelSkill.filter(personnel_id=freelancer_id, is_primary_skill=True).count()
        
        # 評価統計 
        evaluations = await PersonEvaluation.filter(personnel_id=freelancer_id).all()
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
            evaluation_summary.update({
                "average_overall_rating": round(sum(e.overall_rating for e in evaluations) / total_evaluations, 2),
                "average_technical_skill": round(sum(e.technical_skill for e in evaluations) / total_evaluations, 2),
                "average_communication": round(sum(e.communication for e in evaluations) / total_evaluations, 2),
                "average_reliability": round(sum(e.reliability for e in evaluations) / total_evaluations, 2),
                "recommendation_rate": round(sum(1 for e in evaluations if e.recommendation) / total_evaluations * 100, 1),
            })
        
        # フリーランサー詳細情報取得
        detail = await freelancer.freelancer_detail.first()
        business_years = 0.0
        if detail and detail.business_start_date:
            from datetime import date
            today = date.today()
            days = (today - detail.business_start_date).days
            business_years = round(days / 365.25, 1)
        
        dashboard_stats = {
            "basic_info": {
                "name": freelancer.name,
                "code": freelancer.code,
                "current_age": freelancer.current_age,
                "employment_status": freelancer.employment_status,
                "is_visa_expiring": freelancer.is_visa_expiring_soon(),
                "business_years": business_years,
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


@router.post("/business-stats", summary="フリーランサー事業統計")
async def get_freelancer_business_stats(
    freelancer_id: int = Query(..., description="フリーランサーID"),
    stats_params: FreelancerBusinessStatsSchema = None,
):
    """フリーランサーの事業統計を取得"""
    try:
        freelancer = await personnel_controller.get_freelancer_by_id(freelancer_id)
        if not freelancer:
            return Fail(msg="フリーランサーが見つかりません")

        # TODO: 統一Controllerに事業統計メソッドを実装する必要があります
        # 現在は基本情報のみ返す
        params = stats_params.model_dump(exclude_none=True) if stats_params else {}
        
        business_stats = {
            "year": params.get('year'),
            "month_from": params.get('month_from', 1),
            "month_to": params.get('month_to', 12),
            "total_projects": 0,  # TODO: Contractモデル統一後に実装
            "total_revenue": 0.0,
            "average_project_value": 0.0,
            "top_skills": [],  # TODO: スキル統計実装
            "client_satisfaction": 0.0,
        }
        
        return Success(data=business_stats)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/visa-expiring", summary="ビザ期限切れ警告")
async def get_visa_expiring_freelancers(days: Optional[int] = Query(90, description="警告日数", ge=1, le=365)):
    """ビザが期限切れになるフリーランサーを取得"""
    try:
        freelancers = await personnel_controller.check_visa_expiring_soon(days=days)
        data = [await p.to_dict() for p in freelancers]
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
        # TODO: 統一Controllerに高評価ランキングメソッドを実装する必要があります
        # 現在は有効なフリーランサーを返す
        from app.models.enums import PersonType
        
        freelancers, total = await personnel_controller.get_available_personnel(
            person_type=PersonType.FREELANCER,
            page=1,
            page_size=limit,
        )
        
        data = [await p.to_dict() for p in freelancers]
        return Success(data=data, total=len(freelancers))
    except Exception as e:
        return Fail(msg=str(e))