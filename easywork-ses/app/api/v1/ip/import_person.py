from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, Body

from app.controllers.import_person import import_person_controller
from app.schemas import Success, Fail
from app.schemas.import_person import (
    ImportPersonListSchema,
    ImportPersonDetailSchema,
    ImportPersonHistorySchema,
    ImportPersonCurrentAssignmentSchema,
    ImportPersonStatsSchema,
    ImportPersonSearchSchema,
    UpdatePersonStatusSchema
)

router = APIRouter()


@router.get("/list", summary="要員リスト取得")
async def get_staff_list(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(10, ge=1, le=100, description="ページサイズ"),
    keyword: Optional[str] = Query(None, description="氏名検索やコード検索"),
    person_type: Optional[str] = Query(None, description="要員タイプフィルター", regex="^(bp_employee|freelancer|employee)$"),
    employment_status: Optional[str] = Query(None, description="就業ステータスフィルター"),
    is_active: Optional[bool] = Query(None, description="アクティブステータスフィルター"),
    skill_name: Optional[str] = Query(None, description="スキル名検索"),
    min_experience_years: Optional[float] = Query(None, description="最低経験年数"),
    max_experience_years: Optional[float] = Query(None, description="最高経験年数"),
    min_unit_price: Optional[float] = Query(None, description="最低単価"),
    max_unit_price: Optional[float] = Query(None, description="最高単価"),
    nationality: Optional[str] = Query(None, description="国籍フィルター"),
    preferred_location: Optional[str] = Query(None, description="希望勤務地"),
    visa_expiring_within_days: Optional[int] = Query(None, description="ビザN日以内期限切れ"),
    has_active_case: Optional[bool] = Query(None, description="アクティブ案件あり"),
    case_id: Optional[int] = Query(None, description="特定案件IDフィルター"),
    include_inactive: bool = Query(False, description="非アクティブ要員を含む")
):
    """
    すべての要員リストを取得（作業ステータス付き）
    
    対応するフィルター条件：
    - 基本情報：氏名、コード、要員タイプ、就業ステータス
    - スキルフィルター：スキル名、経験年数
    - 単価フィルター：最低/最高単価
    - 地理フィルター：国籍、希望勤務地
    - ビザフィルター：期限切れ間近のビザ
    - 案件フィルター：アクティブ案件の有無、特定案件
    """
    try:
        search_params = {}
        if keyword:
            search_params["keyword"] = keyword
        if person_type:
            search_params["person_type"] = person_type
        if employment_status:
            search_params["employment_status"] = employment_status
        if is_active is not None:
            search_params["is_active"] = is_active
        if skill_name:
            search_params["skill_name"] = skill_name
        if min_experience_years is not None:
            search_params["min_experience_years"] = min_experience_years
        if max_experience_years is not None:
            search_params["max_experience_years"] = max_experience_years
        if min_unit_price is not None:
            search_params["min_unit_price"] = min_unit_price
        if max_unit_price is not None:
            search_params["max_unit_price"] = max_unit_price
        if nationality:
            search_params["nationality"] = nationality
        if preferred_location:
            search_params["preferred_location"] = preferred_location
        if visa_expiring_within_days is not None:
            search_params["visa_expiring_within_days"] = visa_expiring_within_days
        if has_active_case is not None:
            search_params["has_active_case"] = has_active_case
        if case_id is not None:
            search_params["case_id"] = case_id

        result = await import_person_controller.get_staff_list(
            page=page,
            page_size=page_size,
            search_params=search_params,
            include_inactive=include_inactive
        )
        
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", response_model=ImportPersonDetailSchema, summary="要員詳細取得")
async def get_staff_detail(
    id: int = Query(..., description="要員ID"),
    person_type: Optional[str] = Query(None, description="要員タイプ", regex="^(bp_employee|freelancer|employee)$")
):
    """
    要員詳細を取得（履歴付き）
    
    person_typeを指定することでクエリ性能を最適化できます。
    指定しない場合、システムが自動的に対応する要員タイプを検索します。
    """
    try:
        detail = await import_person_controller.get_staff_detail(
            person_id=id,
            person_type=person_type
        )
        
        if not detail:
            return Fail(msg="要員が見つかりません")
        
        return Success(data=detail.dict())
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/history", response_model=List[ImportPersonHistorySchema], summary="要員作業履歴取得")
async def get_staff_history(
    id: int = Query(..., description="要員ID"),
    person_type: Optional[str] = Query(None, description="要員タイプ", regex="^(bp_employee|freelancer|employee)$"),
    page: Optional[int] = Query(1, description="ページ番号"),
    pageSize: Optional[int] = Query(10, description="ページサイズ")
):
    """
    要員の作業履歴を取得
    
    含まれる内容：
    - 過去の契約記録
    - 案件参加状況
    - プロジェクト評価（該当する場合）
    - 顧客情報
    """
    try:
        history , total = await import_person_controller.get_staff_history(
            person_id=id,
            person_type=person_type,
            page = page,
            page_size= pageSize
        )
        
        return Success(data=[item.dict() for item in history] , total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/current-assignments", response_model=ImportPersonCurrentAssignmentSchema, summary="要員現在のアサイン情報取得")
async def get_staff_current_assignments(
    id: int = Query(..., description="要員ID"),
    person_type: Optional[str] = Query(None, description="要員タイプ", regex="^(bp_employee|freelancer|employee)$")
):
    """
    要員の現在の案件と契約情報を取得
    
    含まれる内容：
    - 現在アクティブな案件
    - 現在有効な契約
    - 期限切れ間近の契約（30日以内）
    - 作業ステータス判定
    """
    try:
        assignments = await import_person_controller.get_staff_current_assignments(
            person_id=id,
            person_type=person_type
        )
        
        if not assignments:
            return Fail(msg="要員が見つかりません")
        
        return Success(data=assignments.dict())
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/update-status", summary="要員ステータス更新")
async def update_staff_status(
    data: UpdatePersonStatusSchema = Body(..., description="ステータス更新データ")
):
    """
    要員の作業ステータスを更新
    
    更新可能なステータス：
    - 就業ステータス (employment_status)
    - アクティブ状態 (is_active)
    - 稼働可能開始日 (available_start_date)
    """
    try:
        success = await import_person_controller.update_staff_status(
            person_id=data.person_id,
            person_type=data.person_type,
            status_data=data.dict(exclude={'person_id', 'person_type'}, exclude_none=True)
        )
        
        if not success:
            return Fail(msg="要員が見つからないか更新に失敗しました")
        
        return Success(data={"success": True})
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/stats", response_model=ImportPersonStatsSchema, summary="要員統計情報取得")
async def get_staff_stats():
    """
    要員統計情報を取得
    
    含まれる内容：
    - 総数統計：タイプ別、ステータス別、国籍別分類
    - ビザ期限切れ警告
    - 経験レベル分布
    - 作業ステータス分布
    """
    try:
        stats = await import_person_controller.get_staff_stats()
        
        return Success(data=stats.dict())
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/search", response_model=ImportPersonListSchema, summary="要員高度検索")
async def search_staff(
    search_schema: ImportPersonSearchSchema = Body(..., description="検索条件"),
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(10, ge=1, le=100, description="ページサイズ")
):
    """
    要員の高度検索
    
    複雑な検索条件の組み合わせをサポート。
    /listエンドポイントの拡張版で、より柔軟な検索機能を提供。
    """
    try:
        result = await import_person_controller.get_staff_list(
            page=page,
            page_size=page_size,
            search_params=search_schema.dict(exclude_none=True),
            include_inactive=False
        )
        
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/export", summary="要員データエクスポート")
async def export_staff_data(
    format: str = Query("excel", description="エクスポート形式", regex="^(excel|csv|pdf)$"),
    person_type: Optional[str] = Query(None, description="要員タイプフィルター"),
    employment_status: Optional[str] = Query(None, description="就業ステータスフィルター"),
    include_skills: bool = Query(False, description="スキル情報を含む"),
    include_history: bool = Query(False, description="履歴情報を含む")
):
    """
    要員データをエクスポート
    
    対応形式：Excel、CSV、PDF
    含める情報範囲を選択可能
    
    注意：このエンドポイントは予約済みです。具体的な実装はエクスポート要件に応じて開発が必要です。
    """
    try:
        # エクスポート機能の予約エンドポイント
        # 実際の実装時はformat パラメータに応じて対応形式のファイルを生成
        return Success(data={
            "format": format,
            "download_url": None,
            "note": "エクスポート機能は今後のバージョンで提供予定です"
        })
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/dashboard", summary="要員管理ダッシュボードデータ取得")
async def get_staff_dashboard():
    """
    要員管理ダッシュボードデータを取得
    
    統計情報、警告情報、トレンドデータなどを統合し、
    管理画面向けのワンストップデータサポートを提供。
    """
    try:
        # 基本統計を取得
        stats = await import_person_controller.get_staff_stats()
        
        # ダッシュボードに必要な追加データをここに追加可能
        # 例：月次トレンド、トップスキル、警告リストなど
        dashboard_data = {
            "stats": stats.dict(),
            "alerts": {
                "visa_expiring_count": stats.visa_expiring_soon,
                "new_staff_this_month": 0,  # 実装が必要
                "contracts_expiring_soon": 0,  # 実装が必要
            },
            "trends": {
                "monthly_staff_growth": [],  # 実装が必要
                "skill_demand_ranking": [],  # 実装が必要
                "average_unit_price_trend": []  # 実装が必要
            }
        }
        
        return Success(data=dashboard_data)
    except Exception as e:
        return Fail(msg=str(e))