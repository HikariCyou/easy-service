from datetime import date, datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Query, Body, HTTPException

from app.controllers.attendance import attendance_controller
from app.controllers.import_person import import_person_controller
from app.core.ctx import CTX_USER_ID
from app.schemas import Success, Fail
from app.schemas.attendance import (
    DailyAttendanceSchema,
    CreateDailyAttendanceSchema,
    UpdateDailyAttendanceSchema,
    MonthlyAttendanceSchema,
    AttendanceApprovalSchema,
    BulkAttendanceCreateSchema,
    WeeklyMoodSchema,
    SetWeeklyMoodSchema,
    MoodHistoryResponse,
    TeamMoodSummarySchema,
    MonthlyAttendanceStatusSchema,
    SubmitMonthlyAttendanceSchema,
    ApproveMonthlyAttendanceSchema,
)

router = APIRouter()


@router.post("/daily", summary="日次出勤記録作成")
async def create_daily_attendance(data: CreateDailyAttendanceSchema):
    """
    日次出勤記録を作成
    
    - 契約IDと勤務日の組み合わせは一意
    - 出勤・退勤時刻から自動で実働時間を計算
    - 有給・病欠などの場合は標準時間を設定
    """
    try:
        attendance = await attendance_controller.create_daily_attendance(data)
        result = await attendance.to_dict()
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/daily/list", summary="日次出勤記録一覧取得")
async def get_daily_attendance_list(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    user_id: Optional[int] = Query(None, description="ユーザーID"),
    contract_id: Optional[int] = Query(None, description="契約ID"),
    start_date: Optional[date] = Query(None, description="検索開始日"),
    end_date: Optional[date] = Query(None, description="検索終了日"),
    attendance_type: Optional[str] = Query(None, description="出勤区分"),
    is_approved: Optional[bool] = Query(None, description="承認状態")
):
    """
    日次出勤記録の一覧を取得
    
    検索条件:
    - ユーザーID、契約ID
    - 日付範囲
    - 出勤区分（NORMAL/PAID_LEAVE/SICK_LEAVE等）
    - 承認状態
    """
    try:
        search_params = {}
        if user_id:
            search_params["user_id"] = user_id
        if contract_id:
            search_params["contract_id"] = contract_id
        if start_date:
            search_params["start_date"] = start_date
        if end_date:
            search_params["end_date"] = end_date
        if attendance_type:
            search_params["attendance_type"] = attendance_type
        if is_approved is not None:
            search_params["is_approved"] = is_approved

        result = await attendance_controller.get_daily_attendance_list(
            page=page,
            page_size=page_size,
            search_params=search_params
        )
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/daily/{attendance_id}", summary="日次出勤記録詳細取得")
async def get_daily_attendance(attendance_id: int):
    """
    指定IDの日次出勤記録詳細を取得
    """
    try:
        attendance = await attendance_controller.get_daily_attendance(attendance_id)
        if not attendance:
            return Fail(msg="出勤記録が見つかりません")
        return Success(data=attendance)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/daily/{attendance_id}", summary="日次出勤記録更新")
async def update_daily_attendance(attendance_id: int, data: UpdateDailyAttendanceSchema):
    """
    日次出勤記録を更新
    
    注意: 承認済みの記録は更新できません
    """
    try:
        attendance = await attendance_controller.update_daily_attendance(attendance_id, data)
        result = await attendance.to_dict()
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/daily/{attendance_id}", summary="日次出勤記録削除")
async def delete_daily_attendance(attendance_id: int):
    """
    日次出勤記録を削除
    
    注意: 承認済みの記録は削除できません
    """
    try:
        success = await attendance_controller.delete_daily_attendance(attendance_id)
        if success:
            return Success(data={"deleted": True})
        else:
            return Fail(msg="出勤記録が見つかりません")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/daily/bulk", summary="一括出勤記録作成")
async def bulk_create_attendances(data: BulkAttendanceCreateSchema):
    """
    複数の出勤記録を一括作成
    
    個別のエラーがあっても処理は継続し、成功した分のみ作成
    """
    try:
        attendances = await attendance_controller.bulk_create_attendances(data.attendances)
        result = [await att.to_dict() for att in attendances]
        return Success(data=result, total=len(result))
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/approval", summary="出勤記録承認")
async def approve_attendances(data: AttendanceApprovalSchema):
    """
    出勤記録を承認
    
    複数の記録を一括で承認可能
    承認済みの記録は承認者と承認日時を記録
    """
    try:
        approved_attendances = await attendance_controller.approve_attendances(
            data.attendance_ids, data.approved_by
        )
        result = [await att.to_dict() for att in approved_attendances]
        return Success(data=result, total=len(result))
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/monthly/list", summary="月次出勤集計一覧取得")
async def get_monthly_attendance_list(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    user_id: Optional[int] = Query(None, description="ユーザーID"),
    contract_id: Optional[int] = Query(None, description="契約ID"),
    year_month: Optional[str] = Query(None, description="対象年月（YYYY-MM）"),
    is_calculated: Optional[bool] = Query(None, description="計算済み状態"),
    is_confirmed: Optional[bool] = Query(None, description="確定状態")
):
    """
    月次出勤集計の一覧を取得
    """
    try:
        search_params = {}
        if user_id:
            search_params["user_id"] = user_id
        if contract_id:
            search_params["contract_id"] = contract_id
        if year_month:
            search_params["year_month"] = year_month
        if is_calculated is not None:
            search_params["is_calculated"] = is_calculated
        if is_confirmed is not None:
            search_params["is_confirmed"] = is_confirmed

        result = await attendance_controller.get_monthly_attendance_list(
            page=page,
            page_size=page_size,
            search_params=search_params
        )
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/monthly/calculate", summary="月次出勤集計計算")
async def calculate_monthly_attendance(
    contract_id: int = Body(..., description="契約ID"),
    year_month: str = Body(..., description="対象年月（YYYY-MM）")
):
    """
    指定契約・年月の月次出勤集計を計算
    
    日次出勤記録から自動集計し、支払額も計算
    """
    try:
        monthly = await attendance_controller.calculate_monthly_attendance(contract_id, year_month)
        result = await monthly.to_dict()
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/monthly/{monthly_id}/confirm", summary="月次出勤集計確定")
async def confirm_monthly_attendance(
    monthly_id: int,
    confirmed_by: int = Body(..., description="確定者ID")
):
    """
    月次出勤集計を確定
    
    確定後は変更不可となり、支払処理に使用可能
    """
    try:
        monthly = await attendance_controller.confirm_monthly_attendance(monthly_id, confirmed_by)
        result = await monthly.to_dict()
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/calendar", summary="出勤カレンダー取得")
async def get_attendance_calendar(
    contract_id: int = Query(..., description="契約ID"),
    year_month: str = Query(..., description="対象年月（YYYY-MM）")
):
    """
    指定契約・年月の出勤カレンダーを取得
    
    月間の全日程と出勤状況を日別に表示
    営業日判定、実績サマリーも含む
    """
    try:
        calendar_data = await attendance_controller.get_attendance_calendar(contract_id, year_month)
        return Success(data=calendar_data)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/stats", summary="出勤統計取得")
async def get_attendance_stats(
    user_id: Optional[int] = Query(None, description="ユーザーID"),
    contract_id: Optional[int] = Query(None, description="契約ID"),
    start_date: Optional[date] = Query(None, description="統計開始日"),
    end_date: Optional[date] = Query(None, description="統計終了日")
):
    """
    出勤統計を取得
    
    含まれる統計:
    - 出勤タイプ別集計
    - 承認状況
    - 勤務時間統計
    - 支払統計
    """
    try:
        search_params = {}
        if user_id:
            search_params["user_id"] = user_id
        if contract_id:
            search_params["contract_id"] = contract_id
        if start_date:
            search_params["start_date"] = start_date
        if end_date:
            search_params["end_date"] = end_date

        stats = await attendance_controller.get_attendance_stats(search_params)
        return Success(data=stats)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/export", summary="出勤データエクスポート")
async def export_attendance_data(
    format: str = Query("excel", description="エクスポート形式", pattern="^(excel|csv)$"),
    user_id: Optional[int] = Query(None, description="ユーザーID"),
    contract_id: Optional[int] = Query(None, description="契約ID"),
    start_date: Optional[date] = Query(None, description="開始日"),
    end_date: Optional[date] = Query(None, description="終了日"),
    include_summary: bool = Query(True, description="サマリー情報を含む")
):
    """
    出勤データをエクスポート
    
    対応形式: Excel、CSV
    日次記録と月次集計の両方をエクスポート可能
    
    注意: このエンドポイントは予約済み
    実装時は指定形式のファイルを生成し、ダウンロードURLを返す
    """
    try:
        # エクスポート機能の予約エンドポイント
        export_params = {
            "format": format,
            "filters": {
                "user_id": user_id,
                "contract_id": contract_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "include_summary": include_summary
        }
        
        return Success(data={
            "export_params": export_params,
            "download_url": None,
            "note": "出勤データエクスポート機能は今後のバージョンで提供予定です"
        })
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/user", summary="ユーザー勤怠情報取得")
async def get_user_attendance_data(
    year_month: str = Query(..., description="対象年月（YYYY-MM）", pattern="^\\d{4}-\\d{2}$")
):
    """
    現在ログインユーザーの月次勤怠情報を取得（勤怠録入画面用）
    
    Args:
        year_month: 対象年月（YYYY-MM形式）
    
    機能:
    - 現在ログインユーザーの勤怠データを取得
    - 指定月の全日程の勤怠記録とカレンダー表示
    - 契約情報、案件情報も含めた包括的な情報提供
    - 出勤率、承認状況などのサマリー情報
    
    返却データ:
    - 要員基本情報
    - 現在の契約・案件情報  
    - 月内の勤怠記録
    - カレンダー形式の日別データ（編集可能状態含む）
    - 統計サマリー（総勤務時間、出勤率等）
    """
    try:
        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(msg="ユーザー情報が取得できません")
        
        # YYYY-MM形式から年月の最初の日を作成
        year, month = map(int, year_month.split('-'))
        target_date = date(year, month, 1)
        
        data = await attendance_controller.get_user_attendance_data(
            user_id=user_id,
            period_type="month",
            target_date=target_date
        )
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get_attendance_by_uid" , summary="ユーザーIDで出勤記録取得")
async def get_attendance_by_uid(
    id: int = Query(..., description="ユーザーID"),
    year_month: str = Query(..., description="対象年月（YYYY-MM）", pattern="^\\d{4}-\\d{2}$")
):
    try:
        year, month = map(int, year_month.split('-'))
        target_date = date(year, month, 1)

        personal = await import_person_controller.get_staff(person_id=id)

        data = await attendance_controller.get_user_attendance_data(
            user_id=personal.user_id,
            period_type="month",
            target_date=target_date
        )
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))

@router.get("/dashboard", summary="出勤管理ダッシュボード")
async def get_attendance_dashboard(
    user_id: Optional[int] = Query(None, description="ユーザーID"),
    contract_id: Optional[int] = Query(None, description="契約ID")
):
    """
    出勤管理ダッシュボード用データを取得
    
    含まれる情報:
    - 当月出勤統計
    - 承認待ち件数
    - 月次集計状況
    - 最近の出勤記録
    """
    try:
        # 当月の統計
        today = datetime.now(timezone.utc).date()
        current_month_stats = await attendance_controller.get_attendance_stats({
            "user_id": user_id,
            "contract_id": contract_id,
            "start_date": today.replace(day=1),
            "end_date": today
        })
        
        # 承認待ち件数
        pending_approvals = await attendance_controller.get_daily_attendance_list(
            page=1, 
            page_size=1,
            search_params={"user_id": user_id, "contract_id": contract_id, "is_approved": False}
        )
        
        dashboard_data = {
            "current_month_stats": current_month_stats,
            "pending_approvals_count": pending_approvals["total"],
            "quick_actions": {
                "today_attendance_recorded": False,  # 実装時に当日記録チェック
                "monthly_calculation_needed": False,  # 実装時に月次計算要否チェック
            }
        }
        
        return Success(data=dashboard_data)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/staff/list", summary="要員リスト取得（考勤データ付き）")
async def get_staff_list_with_attendance(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(10, ge=1, le=100, description="ページサイズ"),
    year_month: Optional[str] = Query(None, description="考勤データ対象年月（YYYY-MM）、未指定時は当月", pattern="^\\d{4}-\\d{2}$"),
    keyword: Optional[str] = Query(None, description="氏名検索やコード検索"),
    person_type: Optional[str] = Query(None, description="要員タイプフィルター", pattern="^(bp_employee|freelancer|employee)$"),
    employment_status: Optional[str] = Query(None, description="就業ステータスフィルター"),
    is_active: Optional[bool] = Query(None, description="アクティブステータスフィルター"),
    nationality: Optional[str] = Query(None, description="国籍フィルター"),
    include_inactive: bool = Query(False, description="非アクティブ要員を含む")
):
    """
    要員リスト取得（考勤データ汇总付き）
    
    返却する情報:
    - 要員基本情報（氏名、コード、タイプ等）
    - 所属会社情報（BP社、自社、フリーランス）
    - 現在の案件・取引先情報
    - 指定月の考勤データ汇总（出勤天数、実働时间、残業时间、有給休暇等）
    
    検索条件:
    - year_month: 考勤データの対象年月（YYYY-MM）、未指定時は当月
    - keyword: 氏名、フリーカナ、要員コードでの検索
    - person_type: 要員タイプ（bp_employee/freelancer/employee）
    - employment_status: 就業ステータス
    - is_active: アクティブ状態
    - nationality: 国籍
    - include_inactive: 非アクティブ要員を含むかどうか
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
        if nationality:
            search_params["nationality"] = nationality
        if not include_inactive and is_active is None:
            search_params["is_active"] = True
        if year_month:
            search_params["year_month"] = year_month

        result = await attendance_controller.get_staff_list_with_attendance(
            page=page,
            page_size=page_size,
            search_params=search_params
        )
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=str(e))


# =======================================
# Weekly Mood Tracking API Endpoints
# =======================================

@router.post("/mood/weekly", summary="週間心情設定")
async def set_weekly_mood(data: SetWeeklyMoodSchema):
    """
    現在週の心情状態を設定
    
    機能:
    - 現在週の心情状態を記録
    - 既存の記録がある場合は更新
    - WeChat/Lark風の心情追跡機能
    
    心情状態:
    - excellent: 😄 優秀/非常好
    - good: 😊 良好  
    - normal: 😐 一般
    - stressed: 😰 有压力
    - tired: 😴 疲劳
    - difficult: 😞 困难/不好
    """
    try:
        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(msg="ユーザー情報が取得できません")
            
        mood = await attendance_controller.set_weekly_mood(
            user_id=user_id,
            mood_status=data.mood_status,
            comment=data.comment
        )
        return Success(data=mood)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/mood/current", summary="現在週心情取得")
async def get_current_week_mood():
    """
    現在週の心情記録を取得
    
    返却データ:
    - 現在週の心情状態（設定済みの場合）
    - 週期間情報
    - 設定日時
    """
    try:
        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(msg="ユーザー情報が取得できません")
            
        mood = await attendance_controller.get_current_week_mood(user_id=user_id)
        return Success(data=mood)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/mood/history", summary="心情履歴取得")
async def get_mood_history(
    year: Optional[int] = Query(None, description="対象年（未指定の場合は現在年）"),
    limit: int = Query(12, ge=1, le=52, description="取得週数（1-52、デフォルト12週）")
):
    """
    心情履歴を取得
    
    機能:
    - 指定年の心情履歴を時系列で取得
    - 未指定の場合は現在年の最近12週を取得
    - 週期間、心情状態、コメント等を含む
    
    Args:
        year: 対象年（未指定時は現在年）
        limit: 取得週数（デフォルト12週、最大52週）
    """
    try:
        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(msg="ユーザー情報が取得できません")
            
        history = await attendance_controller.get_mood_history(
            user_id=user_id,
            year=year,
            limit=limit
        )
        return Success(data=history)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/mood/monthly", summary="月次心情データ取得")
async def get_current_month_moods(
    year_month: Optional[str] = Query(None, description="対象年月（YYYY-MM）、未指定時は当月", pattern="^\\d{4}-\\d{2}$")
):
    """
    指定月の4週間心情データを取得
    
    機能:
    - 指定月に含まれる全ての週の心情データを取得
    - 各週の詳細情報（週期間、心情状態、記録日時等）
    - 月次統計（記録率、平均スコア、心情分布等）
    - 跨年・跨月週の適切な処理
    
    返却データ:
    - 月内の全週データ（通常4-5週）
    - 各週の心情記録状況
    - 月次心情統計サマリー
    - 記録完了率と分析
    
    Args:
        year_month: 対象年月（YYYY-MM形式、未指定時は当月）
        
    使用例:
    - /mood/monthly - 当月の心情データ
    - /mood/monthly?year_month=2024-07 - 2024年7月の心情データ
    """
    try:
        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(msg="ユーザー情報が取得できません")
            
        monthly_moods = await attendance_controller.get_current_month_moods(
            user_id=user_id,
            year_month=year_month
        )
        return Success(data=monthly_moods)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/mood/team-summary", summary="チーム心情サマリー取得（管理者用）")
async def get_team_mood_summary(
    week_count: int = Query(4, ge=1, le=12, description="対象週数（1-12、デフォルト4週）"),
    team_filter: Optional[str] = Query(None, description="チームフィルター（案件名等）")
):
    """
    チーム心情サマリーを取得（管理者機能）
    
    機能:
    - チームメンバーの心情状態分布を取得
    - 指定週数での心情推移を分析
    - 管理者が中心の状況把握用
    
    返却データ:
    - 心情分布（状態別人数）
    - 心情推移トレンド
    - 平均心情スコア
    - チーム人数統計
    
    Args:
        week_count: 分析対象週数（デフォルト4週）
        team_filter: チーム絞り込み条件
    """
    try:
        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(msg="ユーザー情報が取得できません")
            
        # 管理者権限チェック（将来的に実装）
        # if not await check_manager_permission(user_id):
        #     return Fail(msg="管理者権限が必要です")
            
        summary = await attendance_controller.get_team_mood_summary(
            manager_user_id=user_id,
            week_count=week_count,
            team_filter=team_filter
        )
        return Success(data=summary)
    except Exception as e:
        return Fail(msg=str(e))


# =======================================
# Monthly Attendance Submission Workflow API Endpoints  
# =======================================

@router.post("/monthly/submit", summary="月次考勤提交")
async def submit_monthly_attendance(data: SubmitMonthlyAttendanceSchema):
    """
    月次考勤を提交
    
    機能:
    - 指定月の日次考勤記録を集計して提交
    - 提交時に統計データの快照を作成
    - 提交後は日次記録の修正が制限される
    
    提交条件:
    - 対象月の日次記録が存在する
    - 未提交状態（draft/withdrawn）である
    - 必要な承認が完了している
    
    Args:
        data: 提交データ（対象年月、備考）
    """
    try:
        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(msg="ユーザー情報が取得できません")
            
        result = await attendance_controller.submit_monthly_attendance(
            user_id=user_id,
            year_month=data.year_month,
            remark=data.remark
        )
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/monthly/{monthly_id}/withdraw", summary="月次考勤提交撤回")  
async def withdraw_monthly_attendance(monthly_id: int):
    """
    月次考勤提交を撤回
    
    機能:
    - 提交済みの月次考勤を撤回して修正可能状態に戻す
    - 統計データ快照をクリア
    - 日次記録の修正が再び可能になる
    
    撤回条件:
    - submitted状态である
    - まだ承認されていない
    - 本人または権限のある管理者による操作
    
    Args:
        monthly_id: 月次考勤記録ID
    """
    try:
        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(msg="ユーザー情報が取得できません")
            
        result = await attendance_controller.withdraw_monthly_attendance(
            monthly_id=monthly_id,
            user_id=user_id
        )
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/monthly/approve", summary="月次考勤承認（管理者用）")
async def approve_monthly_attendance(data: ApproveMonthlyAttendanceSchema):
    """
    月次考勤を承認（管理者機能）
    
    機能:
    - 提交済みの月次考勤を承認
    - 承認後は修正不可の確定状态になる
    - 承認者情報と承認日時を記録
    
    承認条件:
    - submitted状态である
    - 管理者権限を持つ
    - 統計データが正常である
    
    Args:
        data: 承認データ（月次考勤ID、備考）
    """
    try:
        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(msg="ユーザー情報が取得できません")
            
        # 管理者権限チェック（将来的に実装）
        # if not await check_manager_permission(user_id):
        #     return Fail(msg="管理者権限が必要です")
            
        result = await attendance_controller.approve_monthly_attendance(
            monthly_id=data.monthly_attendance_id,
            approved_by=user_id,
            remark=data.remark
        )
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/monthly/status", summary="月次考勤状态取得")
async def get_monthly_attendance_status(
    year_month: str = Query(..., description="対象年月（YYYY-MM）", pattern="^\\d{4}-\\d{2}$"),
    user_id: Optional[int] = Query(None, description="ユーザーID（管理者用、未指定時は自分）")
):
    """
    月次考勤状态を取得
    
    機能:
    - 指定年月の月次考勤状态と統計データを取得
    - 提交状态、承認情報を含む
    - 計算済み統計データまたはリアルタイム計算データを返却
    
    返却データ:
    - 基本情報（年月、状态、提交・承認日時等）
    - 統計データ（出勤天数、実働时間、残業时间等）
    - 提交・承認履歴
    
    Args:
        year_month: 対象年月（YYYY-MM形式）
        user_id: 対象ユーザーID（管理者用、未指定時は自分のデータ）
    """
    try:
        current_user_id = CTX_USER_ID.get()
        if not current_user_id:
            return Fail(msg="ユーザー情報が取得できません")
            
        # ユーザーID未指定時は自分のデータを取得
        target_user_id = user_id if user_id else current_user_id
        
        # 他人のデータを参照する場合の権限チェック（将来的に実装）
        # if user_id and user_id != current_user_id:
        #     if not await check_manager_permission(current_user_id):
        #         return Fail(msg="他のユーザーのデータを参照する権限がありません")
            
        status = await attendance_controller.get_monthly_attendance_status(
            user_id=target_user_id,
            year_month=year_month
        )
        return Success(data=status)
    except Exception as e:
        return Fail(msg=str(e))