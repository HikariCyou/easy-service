from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Query

from app.controllers.person_evaluation import person_evaluation_controller
from app.models.enums import PersonType
from app.schemas import Fail, Success
from app.schemas.person_evaluation import (
    CreatePersonEvaluationSchema,
    PersonEvaluationDetailSchema,
    PersonEvaluationListResponse,
    PersonEvaluationListSchema,
    PersonEvaluationSearchSchema,
    PersonEvaluationStatsSchema,
    PersonEvaluationSummarySchema,
    PersonTopRatedSchema,
    UpdatePersonEvaluationSchema,
)

router = APIRouter()


@router.post("/create", summary="人材評価作成")
async def create_evaluation(
    evaluation_data: CreatePersonEvaluationSchema,
):
    """人材評価を作成する"""
    try:
        evaluation = await person_evaluation_controller.create_evaluation(evaluation_data=evaluation_data)
        evaluation_dict = await person_evaluation_controller.evaluation_to_dict(evaluation, include_relations=True)
        return Success(data=evaluation_dict, msg="評価作成が完了しました")
    except ValueError as e:
        return Fail(code=400, msg=str(e))
    except Exception as e:
        return Fail(code=500, msg=f"評価作成中にエラーが発生しました: {str(e)}")


@router.get("/list", summary="要員評価一覧取得")
async def list_evaluations(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(10, ge=1, le=100, description="ページサイズ"),
    person_type: Optional[PersonType] = Query(None, description="人材タイプ"),
    person_id: Optional[int] = Query(None, description="要員ID"),
    case_id: Optional[int] = Query(None, description="案件ID"),
    contract_id: Optional[int] = Query(None, description="契約ID"),
):
    """人材評価一覧を取得する"""
    try:
        search_params = {
            "person_type": person_type,
            "person_id": person_id,
            "case_id": case_id,
            "contract_id": contract_id,
        }
        # None値を削除
        search_params = {k: v for k, v in search_params.items() if v is not None}

        evaluations, total = await person_evaluation_controller.list_evaluations(
            page=page, page_size=page_size, search_params=search_params
        )

        evaluations_dict = await person_evaluation_controller.evaluations_to_dict(evaluations, include_relations=True)

        return Success(
            data=evaluations_dict,
            total=total,
            msg="評価一覧取得が完了しました",
        )
    except Exception as e:
        return Fail(code=500, msg=f"評価一覧取得中にエラーが発生しました: {str(e)}")


@router.get("/{evaluation_id}", summary="人材評価詳細取得")
async def get_evaluation(
    evaluation_id: int,
):
    """指定IDの人材評価詳細を取得する"""
    try:
        evaluation = await person_evaluation_controller.get_evaluation_by_id(evaluation_id, include_relations=True)
        if not evaluation:
            return Fail(code=404, msg="指定された評価が見つかりません")

        evaluation_dict = await person_evaluation_controller.evaluation_to_dict(evaluation, include_relations=True)
        return Success(data=evaluation_dict, msg="評価詳細取得が完了しました")
    except Exception as e:
        return Fail(code=500, msg=f"評価詳細取得中にエラーが発生しました: {str(e)}")


@router.put("/{evaluation_id}", summary="人材評価更新")
async def update_evaluation(
    evaluation_id: int,
    evaluation_data: UpdatePersonEvaluationSchema,
):
    """指定IDの人材評価を更新する"""
    try:
        # 空の値を除外
        update_data = {k: v for k, v in evaluation_data.dict().items() if v is not None}
        if not update_data:
            return Fail(code=400, msg="更新するデータがありません")

        evaluation = await person_evaluation_controller.update_evaluation(evaluation_id, update_data)
        if not evaluation:
            return Fail(code=404, msg="指定された評価が見つかりません")

        evaluation_dict = await person_evaluation_controller.evaluation_to_dict(evaluation, include_relations=True)
        return Success(data=evaluation_dict, msg="評価更新が完了しました")
    except ValueError as e:
        return Fail(code=400, msg=str(e))
    except Exception as e:
        return Fail(code=500, msg=f"評価更新中にエラーが発生しました: {str(e)}")


@router.delete("/{evaluation_id}", summary="人材評価削除")
async def delete_evaluation(
    evaluation_id: int,
):
    """指定IDの人材評価を削除する"""
    try:
        success = await person_evaluation_controller.delete_evaluation(evaluation_id)
        if not success:
            return Fail(code=404, msg="指定された評価が見つかりません")

        return Success(data={"id": evaluation_id}, msg="評価削除が完了しました")
    except Exception as e:
        return Fail(code=500, msg=f"評価削除中にエラーが発生しました: {str(e)}")


@router.get("/person/{person_type}/{person_id}", summary="特定人材の評価一覧")
async def get_person_evaluations(
    person_type: PersonType,
    person_id: int,
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(10, ge=1, le=100, description="ページサイズ"),
):
    """特定人材の評価一覧を取得する"""
    try:
        evaluations, total = await person_evaluation_controller.get_person_evaluations(
            person_type, person_id, page, page_size
        )

        evaluations_dict = await person_evaluation_controller.evaluations_to_dict(evaluations, include_relations=True)

        return Success(
            data={
                "evaluations": evaluations_dict,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
            },
            msg="人材評価一覧取得が完了しました",
        )
    except Exception as e:
        return Fail(code=500, msg=f"人材評価一覧取得中にエラーが発生しました: {str(e)}")


@router.post("/person/{person_type}/{person_id}", summary="特定人材の評価作成")
async def create_person_evaluation(
    person_type: PersonType,
    person_id: int,
    evaluation_data: CreatePersonEvaluationSchema,
    evaluator_id: int = Query(..., description="評価者ID"),
):
    """特定人材の評価を作成する"""
    try:
        # リクエストのperson_typeとperson_idを上書き
        evaluation_dict = evaluation_data.dict()
        evaluation_dict["person_type"] = person_type
        evaluation_dict["person_id"] = person_id

        evaluation = await person_evaluation_controller.create_person_evaluation(
            person_type, person_id, evaluation_dict, evaluator_id
        )

        evaluation_result = await person_evaluation_controller.evaluation_to_dict(evaluation, include_relations=True)
        return Success(data=evaluation_result, msg="人材評価作成が完了しました")
    except ValueError as e:
        return Fail(code=400, msg=str(e))
    except Exception as e:
        return Fail(code=500, msg=f"人材評価作成中にエラーが発生しました: {str(e)}")


@router.get("/person/{person_type}/{person_id}/summary", summary="特定人材の評価サマリー")
async def get_person_evaluation_summary(
    person_type: PersonType,
    person_id: int,
):
    """特定人材の評価サマリーを取得する"""
    try:
        summary = await person_evaluation_controller.get_person_evaluation_summary(person_type, person_id)
        return Success(data=summary, msg="評価サマリー取得が完了しました")
    except Exception as e:
        return Fail(code=500, msg=f"評価サマリー取得中にエラーが発生しました: {str(e)}")


@router.get("/stats/top-rated", summary="高評価人材一覧")
async def get_top_rated_persons(
    person_type: Optional[PersonType] = Query(None, description="人材タイプ"),
    limit: int = Query(10, ge=1, le=100, description="取得件数"),
    min_evaluations: int = Query(3, ge=1, description="最小評価数"),
):
    """高評価人材一覧を取得する"""
    try:
        top_persons = await person_evaluation_controller.get_top_rated_persons(person_type, limit, min_evaluations)
        return Success(data=top_persons, msg="高評価人材一覧取得が完了しました")
    except Exception as e:
        return Fail(code=500, msg=f"高評価人材取得中にエラーが発生しました: {str(e)}")


@router.get("/stats/period", summary="期間別評価統計")
async def get_evaluation_stats_by_period(
    start_date: date = Query(..., description="開始日"),
    end_date: date = Query(..., description="終了日"),
    person_type: Optional[PersonType] = Query(None, description="人材タイプ"),
):
    """期間別評価統計を取得する"""
    try:
        if start_date > end_date:
            return Fail(code=400, msg="開始日は終了日より前である必要があります")

        stats = await person_evaluation_controller.get_evaluation_stats_by_period(start_date, end_date, person_type)
        return Success(data=stats, msg="期間別評価統計取得が完了しました")
    except Exception as e:
        return Fail(code=500, msg=f"期間別評価統計取得中にエラーが発生しました: {str(e)}")


@router.get("/dashboard/overview", summary="評価ダッシュボード概要")
async def get_evaluation_dashboard():
    """評価ダッシュボード概要を取得する"""
    try:
        from datetime import datetime, timedelta

        # 最近30日の統計
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        recent_stats = await person_evaluation_controller.get_evaluation_stats_by_period(start_date, end_date)

        # 高評価人材トップ5
        top_persons = await person_evaluation_controller.get_top_rated_persons(limit=5, min_evaluations=1)

        dashboard_data = {
            "recent_stats": recent_stats,
            "top_persons": top_persons,
            "period": f"{start_date} ~ {end_date}",
        }

        return Success(data=dashboard_data, msg="ダッシュボード概要取得が完了しました")
    except Exception as e:
        return Fail(code=500, msg=f"ダッシュボード概要取得中にエラーが発生しました: {str(e)}")


# 人材タイプ別の便利なエンドポイント
@router.get("/bp-employee/{bp_employee_id}/evaluations", summary="BP社員の評価一覧")
async def get_bp_employee_evaluations(
    bp_employee_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """BP社員の評価一覧を取得する"""
    return await get_person_evaluations(PersonType.BP_EMPLOYEE, bp_employee_id, page, page_size)


@router.get("/freelancer/{freelancer_id}/evaluations", summary="フリーランスの評価一覧")
async def get_freelancer_evaluations(
    freelancer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """フリーランスの評価一覧を取得する"""
    return await get_person_evaluations(PersonType.FREELANCER, freelancer_id, page, page_size)


@router.get("/employee/{employee_id}/evaluations", summary="自社社員の評価一覧")
async def get_employee_evaluations(
    employee_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """自社社員の評価一覧を取得する"""
    return await get_person_evaluations(PersonType.EMPLOYEE, employee_id, page, page_size)
