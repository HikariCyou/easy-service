from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Body, Query

from app.controllers.employee_evaluation import employee_evaluation_controller
from app.controllers.personnel_unified import personnel_controller
from app.schemas import Fail, Success
from app.schemas.employee_evaluation import (
    CreateEmployeeEvaluationSchema,
    EmployeeEvaluationDetailSchema,
    EmployeeEvaluationListSchema,
    EmployeeEvaluationSearchSchema,
    EmployeeEvaluationSummarySchema,
    UpdateEmployeeEvaluationSchema,
)

router = APIRouter()


# ===== 評価基本管理 =====
@router.get("/list", summary="社員評価一覧取得")
async def get_evaluation_list(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(10, ge=1, le=100, description="ページサイズ"),
    employee_id: Optional[int] = Query(None, description="社員IDで絞り込み"),
    case_id: Optional[int] = Query(None, description="案件IDで絞り込み"),
    contract_id: Optional[int] = Query(None, description="契約IDで絞り込み"),
    evaluator_id: Optional[int] = Query(None, description="評価者IDで絞り込み"),
    min_overall_rating: Optional[int] = Query(None, description="最低総合評価", ge=1, le=5),
    max_overall_rating: Optional[int] = Query(None, description="最高総合評価", ge=1, le=5),
    recommendation: Optional[bool] = Query(None, description="推薦可能かどうか"),
    evaluation_date_from: Optional[date] = Query(None, description="評価日開始"),
    evaluation_date_to: Optional[date] = Query(None, description="評価日終了"),
):
    """
    社員評価一覧を取得

    対応する絞り込み条件：
    - 社員ID、案件ID、契約ID、評価者ID
    - 総合評価の範囲
    - 推薦可能かどうか
    - 評価日の期間
    """
    try:
        search_params = {}
        if employee_id:
            search_params["employee_id"] = employee_id
        if case_id:
            search_params["case_id"] = case_id
        if contract_id:
            search_params["contract_id"] = contract_id
        if evaluator_id:
            search_params["evaluator_id"] = evaluator_id
        if min_overall_rating:
            search_params["min_overall_rating"] = min_overall_rating
        if max_overall_rating:
            search_params["max_overall_rating"] = max_overall_rating
        if recommendation is not None:
            search_params["recommendation"] = recommendation
        if evaluation_date_from:
            search_params["evaluation_date_from"] = evaluation_date_from
        if evaluation_date_to:
            search_params["evaluation_date_to"] = evaluation_date_to

        evaluations, total = await employee_evaluation_controller.list_evaluations(
            page=page, page_size=page_size, search_params=search_params
        )

        data = await employee_evaluation_controller.evaluations_to_dict(evaluations, include_relations=True)
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/search", summary="社員評価高度検索")
async def search_evaluations(
    search_params: EmployeeEvaluationSearchSchema = Body(..., description="検索条件"),
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(10, ge=1, le=100, description="ページサイズ"),
):
    """社員評価の高度検索"""
    try:
        evaluations, total = await employee_evaluation_controller.list_evaluations(
            page=page, page_size=page_size, search_params=search_params.dict(exclude_none=True)
        )

        data = await employee_evaluation_controller.evaluations_to_dict(evaluations, include_relations=True)
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="IDで社員評価取得")
async def get_evaluation(
    id: int = Query(..., description="評価ID"),
    include_relations: bool = Query(True, description="関連情報を含むかどうか"),
):
    """IDで社員評価を取得"""
    try:
        evaluation = await employee_evaluation_controller.get_evaluation_by_id(id, include_relations=include_relations)
        if evaluation:
            data = await employee_evaluation_controller.evaluation_to_dict(
                evaluation, include_relations=include_relations
            )
            return Success(data=data)
        else:
            return Fail(msg="評価が見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/create", summary="社員評価作成")
async def create_evaluation(
    data: CreateEmployeeEvaluationSchema = Body(..., description="評価作成データ"),
    evaluator_id: int = Query(..., description="評価者ID"),
):
    """社員評価を作成"""
    try:
        evaluation_data = data.dict(exclude_none=True)
        evaluation = await employee_evaluation_controller.create_evaluation(evaluation_data, evaluator_id)

        result = await employee_evaluation_controller.evaluation_to_dict(evaluation, include_relations=True)
        return Success(data=result, msg="評価が正常に作成されました")
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/update", summary="社員評価更新")
async def update_evaluation(
    id: int = Query(..., description="評価ID"),
    data: UpdateEmployeeEvaluationSchema = Body(..., description="評価更新データ"),
):
    """社員評価情報を更新"""
    try:
        evaluation_data = data.dict(exclude_none=True)
        evaluation = await employee_evaluation_controller.update_evaluation(id, evaluation_data)

        if evaluation:
            result = await employee_evaluation_controller.evaluation_to_dict(evaluation, include_relations=True)
            return Success(data=result, msg="評価情報が正常に更新されました")
        else:
            return Fail(msg="評価が見つかりません")
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/delete", summary="社員評価削除")
async def delete_evaluation(id: int = Query(..., description="評価ID")):
    """社員評価を削除"""
    try:
        success = await employee_evaluation_controller.delete_evaluation(id)
        if success:
            return Success(msg="評価が正常に削除されました")
        else:
            return Fail(msg="評価が見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


# ===== 特定社員の評価管理 =====
@router.get("/employee/{employee_id}/evaluations", summary="特定社員の評価一覧取得")
async def get_employee_evaluations(
    employee_id: int,
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(10, ge=1, le=100, description="ページサイズ"),
):
    """特定社員の評価一覧を取得"""
    try:
        employee = await personnel_controller.get_employee_by_id(employee_id)
        if not employee:
            return Fail(msg="社員が見つかりません")

        evaluations, total = await employee_evaluation_controller.get_employee_evaluations(
            employee, page=page, page_size=page_size
        )

        data = await employee_evaluation_controller.evaluations_to_dict(evaluations, include_relations=True)
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/employee/{employee_id}/evaluations/create", summary="特定社員の評価作成")
async def create_employee_evaluation(
    employee_id: int,
    data: CreateEmployeeEvaluationSchema = Body(..., description="評価作成データ"),
    evaluator_id: int = Query(..., description="評価者ID"),
):
    """特定社員の評価を作成"""
    try:
        employee = await personnel_controller.get_employee_by_id(employee_id)
        if not employee:
            return Fail(msg="社員が見つかりません")

        evaluation_data = data.dict(exclude_none=True)
        # employee_idをURLパラメータから設定（Bodyのデータを上書き）
        evaluation_data["employee_id"] = employee_id

        evaluation = await employee_evaluation_controller.create_employee_evaluation(
            employee, evaluation_data, evaluator_id
        )

        result = await employee_evaluation_controller.evaluation_to_dict(evaluation, include_relations=True)
        return Success(data=result, msg="評価が正常に作成されました")
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/employee/{employee_id}/evaluations/summary", summary="特定社員の評価サマリー取得")
async def get_employee_evaluation_summary(employee_id: int):
    """特定社員の評価サマリーを取得"""
    try:
        employee = await personnel_controller.get_employee_by_id(employee_id)
        if not employee:
            return Fail(msg="社員が見つかりません")

        summary = await employee_evaluation_controller.get_employee_evaluation_summary(employee)
        return Success(data=summary)
    except Exception as e:
        return Fail(msg=str(e))


# ===== 業務ロジック =====
@router.get("/top-rated", summary="高評価社員取得")
async def get_top_rated_employees(
    limit: int = Query(10, description="取得件数", ge=1, le=50),
    min_evaluations: int = Query(3, description="最低評価数", ge=1),
):
    """高評価社員を取得"""
    try:
        employees = await employee_evaluation_controller.get_top_rated_employees(
            limit=limit, min_evaluations=min_evaluations
        )

        # 社員データを辞書形式に変換
        employees_data = []
        for employee in employees:
            employee_dict = await employee.to_dict()
            # 評価サマリーも追加
            summary = await employee_evaluation_controller.get_employee_evaluation_summary(employee)
            employee_dict["evaluation_summary"] = summary
            employees_data.append(employee_dict)

        return Success(data=employees_data, total=len(employees_data))
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/stats/period", summary="期間別評価統計取得")
async def get_evaluation_stats_by_period(
    start_date: date = Query(..., description="開始日"),
    end_date: date = Query(..., description="終了日"),
):
    """期間別評価統計を取得"""
    try:
        if start_date > end_date:
            return Fail(msg="開始日は終了日より前である必要があります")

        stats = await employee_evaluation_controller.get_evaluation_stats_by_period(start_date, end_date)
        return Success(data=stats)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/dashboard", summary="評価ダッシュボードデータ取得")
async def get_evaluation_dashboard():
    """評価管理ダッシュボードデータを取得"""
    try:
        # 今月の評価統計
        from datetime import datetime

        today = datetime.now().date()
        start_of_month = today.replace(day=1)

        monthly_stats = await employee_evaluation_controller.get_evaluation_stats_by_period(start_of_month, today)

        # 高評価社員トップ5
        top_employees = await employee_evaluation_controller.get_top_rated_employees(limit=5, min_evaluations=2)
        top_employees_data = []
        for employee in top_employees:
            employee_dict = await employee.to_dict()
            summary = await employee_evaluation_controller.get_employee_evaluation_summary(employee)
            employee_dict["evaluation_summary"] = summary
            top_employees_data.append(employee_dict)

        dashboard_data = {
            "monthly_stats": monthly_stats,
            "top_employees": top_employees_data,
            "summary": {
                "total_evaluations_this_month": monthly_stats["total_evaluations"],
                "average_rating_this_month": monthly_stats["average_overall_rating"],
                "recommendation_rate_this_month": monthly_stats["recommendation_rate"],
            },
        }

        return Success(data=dashboard_data)
    except Exception as e:
        return Fail(msg=str(e))
