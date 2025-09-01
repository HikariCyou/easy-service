from datetime import date, time, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class DailyAttendanceSchema(BaseModel):
    """日次出勤記録Schema"""
    
    id: int = Field(..., description="出勤記録ID")
    user_id: Optional[int] = Field(None, description="システムユーザーID") 
    contract_id: int = Field(..., description="契約ID")
    work_date: date = Field(..., description="勤務日")
    
    # 出退勤時刻
    start_time: Optional[time] = Field(None, description="出勤時刻")
    end_time: Optional[time] = Field(None, description="退勤時刻")
    
    # 休憩時間（詳細）
    lunch_break_minutes: int = Field(60, description="昼休憩時間（分）")
    evening_break_minutes: int = Field(0, description="夜休憩時間（分）")
    other_break_minutes: int = Field(0, description="その他休憩時間（分）")
    
    # 日付関連情報（計算値）
    weekday: Optional[int] = Field(None, description="曜日（0=月曜日）")
    weekday_name: Optional[str] = Field(None, description="曜日名")
    is_weekend: Optional[bool] = Field(None, description="週末フラグ")
    
    # 実働時間
    actual_working_hours: Optional[Decimal] = Field(None, description="実働時間")
    
    # 出勤区分
    attendance_type: str = Field(..., description="出勤区分")
    
    # 承認状況
    approved_status: str = Field("PENDING", description="承認ステータス")
    is_approved: Optional[bool] = Field(None, description="承認済みフラグ（計算値）")
    approved_at: Optional[datetime] = Field(None, description="承認日時")
    approved_by: Optional[int] = Field(None, description="承認者ID")
    
    # 備考
    remark: Optional[str] = Field(None, description="備考")
    
    # 関連データ
    contract: Optional[Dict[str, Any]] = Field(None, description="契約情報")
    
    # タイムスタンプ
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class CreateDailyAttendanceSchema(BaseModel):
    """日次出勤記録作成Schema"""
    user_id: Optional[int] = Field(None, description="システムユーザーID")
    work_date: date = Field(..., description="勤務日")
    start_time: Optional[time] = Field(None, description="出勤時刻")
    end_time: Optional[time] = Field(None, description="退勤時刻")
    lunch_break_minutes: int = Field(60, description="昼休憩時間（分）")
    evening_break_minutes: int = Field(0, description="夜休憩時間（分）")
    other_break_minutes: int = Field(0, description="その他休憩時間（分）")
    attendance_type: str = Field("NORMAL", description="出勤区分")
    remark: Optional[str] = Field(None, description="備考")


class UpdateDailyAttendanceSchema(BaseModel):
    """日次出勤記録更新Schema"""
    
    start_time: Optional[time] = Field(None, description="出勤時刻")
    end_time: Optional[time] = Field(None, description="退勤時刻")
    lunch_break_minutes: Optional[int] = Field(None, description="昼休憩時間（分）")
    evening_break_minutes: Optional[int] = Field(None, description="夜休憩時間（分）")
    other_break_minutes: Optional[int] = Field(None, description="その他休憩時間（分）")
    attendance_type: Optional[str] = Field(None, description="出勤区分")
    remark: Optional[str] = Field(None, description="備考")


class MonthlyAttendanceSchema(BaseModel):
    """月次出勤集計Schema"""
    
    id: int = Field(..., description="月次集計ID")
    user_id: Optional[int] = Field(None, description="システムユーザーID")
    contract_id: int = Field(..., description="契約ID")
    year_month: str = Field(..., description="対象年月（YYYY-MM）")
    
    # 集計結果
    total_working_hours: Decimal = Field(..., description="総実働時間")
    working_days: int = Field(..., description="出勤日数")
    paid_leave_days: int = Field(0, description="有給取得日数")
    absence_days: int = Field(0, description="欠勤日数")
    late_count: int = Field(0, description="遅刻回数")
    early_leave_count: int = Field(0, description="早退回数")
    
    # 計算結果
    base_payment: Decimal = Field(..., description="基本給")
    overtime_payment: Decimal = Field(0, description="超過時間手当")
    shortage_deduction: Decimal = Field(0, description="不足時間控除")
    total_payment: Decimal = Field(..., description="支払総額")
    overtime_hours: Decimal = Field(0, description="超過時間")
    shortage_hours: Decimal = Field(0, description="不足時間")
    
    # ステータス管理
    is_calculated: bool = Field(False, description="計算済みフラグ")
    is_confirmed: bool = Field(False, description="確定フラグ")
    confirmed_at: Optional[datetime] = Field(None, description="確定日時")
    confirmed_by: Optional[int] = Field(None, description="確定者ID")
    
    remark: Optional[str] = Field(None, description="備考")
    calculation_details: Optional[Dict[str, Any]] = Field(None, description="計算詳細")
    
    # 関連データ
    contract: Optional[Dict[str, Any]] = Field(None, description="契約情報")
    
    # タイムスタンプ
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class AttendanceSummarySchema(BaseModel):
    """出勤サマリーSchema"""
    
    contract_id: int = Field(..., description="契約ID")
    year_month: str = Field(..., description="対象年月")
    personnel_name: str = Field(..., description="要員名")
    contract_number: str = Field(..., description="契約番号")
    
    # 勤怠サマリー
    total_working_days: int = Field(..., description="総出勤日数")
    total_working_hours: Decimal = Field(..., description="総実働時間")
    average_daily_hours: Optional[Decimal] = Field(None, description="平均日次勤務時間")
    
    # 詳細内訳
    normal_days: int = Field(0, description="通常出勤日数")
    paid_leave_days: int = Field(0, description="有給取得日数")
    absence_days: int = Field(0, description="欠勤日数")
    late_count: int = Field(0, description="遅刻回数")
    early_leave_count: int = Field(0, description="早退回数")
    
    # 支払情報
    calculated_payment: Optional[Decimal] = Field(None, description="計算済み支払額")
    payment_status: str = Field("pending", description="支払ステータス")


class AttendanceApprovalSchema(BaseModel):
    """出勤承認Schema"""
    
    attendance_ids: List[int] = Field(..., description="承認対象の出勤記録ID一覧")
    approved_by: int = Field(..., description="承認者ID")
    approval_comment: Optional[str] = Field(None, description="承認コメント")


class AttendanceSearchSchema(BaseModel):
    """出勤検索Schema"""
    
    user_id: Optional[int] = Field(None, description="ユーザーID")
    contract_id: Optional[int] = Field(None, description="契約ID")
    personnel_id: Optional[int] = Field(None, description="要員ID")
    start_date: Optional[date] = Field(None, description="検索開始日")
    end_date: Optional[date] = Field(None, description="検索終了日")
    year_month: Optional[str] = Field(None, description="対象年月")
    attendance_type: Optional[str] = Field(None, description="出勤区分")
    is_approved: Optional[bool] = Field(None, description="承認状態")
    is_calculated: Optional[bool] = Field(None, description="計算状態")


class AttendanceStatsSchema(BaseModel):
    """出勤統計Schema"""
    
    period: str = Field(..., description="統計期間")
    total_records: int = Field(..., description="総記録数")
    approved_records: int = Field(..., description="承認済み記録数") 
    pending_approval: int = Field(..., description="承認待ち記録数")
    
    # 出勤タイプ別統計
    normal_attendance: int = Field(0, description="通常出勤数")
    paid_leave: int = Field(0, description="有給取得数")
    sick_leave: int = Field(0, description="病欠数")
    absence: int = Field(0, description="欠勤数")
    late_arrivals: int = Field(0, description="遅刻数")
    early_departures: int = Field(0, description="早退数")
    
    # 時間統計
    total_working_hours: Decimal = Field(0, description="総実働時間")
    average_daily_hours: Optional[Decimal] = Field(None, description="平均日次勤務時間")
    
    # 月次支払統計
    total_payments: Decimal = Field(0, description="総支払額")
    confirmed_payments: Decimal = Field(0, description="確定済み支払額")
    pending_payments: Decimal = Field(0, description="未確定支払額")


class BulkAttendanceCreateSchema(BaseModel):
    """一括出勤記録作成Schema"""
    
    attendances: List[CreateDailyAttendanceSchema] = Field(..., description="出勤記録一覧")


class AttendanceCalendarSchema(BaseModel):
    """出勤カレンダーSchema"""
    
    year_month: str = Field(..., description="対象年月")
    contract_id: int = Field(..., description="契約ID") 
    calendar_data: List[Dict[str, Any]] = Field(..., description="カレンダーデータ")
    
    # サマリー
    working_days: int = Field(..., description="出勤予定日数")
    actual_working_days: int = Field(..., description="実出勤日数")
    remaining_days: int = Field(..., description="残り出勤日数")
    total_hours: Decimal = Field(..., description="累計勤務時間")
    target_hours: Decimal = Field(..., description="目標勤務時間")


class UserAttendanceDataSchema(BaseModel):
    """ユーザー勤怠データSchema"""
    
    user_id: int = Field(..., description="システムユーザーID")
    personnel: Dict[str, Any] = Field(..., description="要員基本情報")
    contracts: List[Dict[str, Any]] = Field(..., description="契約情報一覧")
    attendance_data: List[Dict[str, Any]] = Field(..., description="勤怠記録一覧")
    calendar_days: List[Dict[str, Any]] = Field(..., description="カレンダー形式日別データ")
    
    # 期間情報
    period_info: Dict[str, Any] = Field(..., description="期間情報")
    
    # サマリー
    summary: Dict[str, Any] = Field(..., description="統計サマリー")


class AttendanceDayInfo(BaseModel):
    """勤怠日別情報Schema"""
    
    date: str = Field(..., description="日付（YYYY-MM-DD）")
    weekday: int = Field(..., description="曜日（0=月曜日）")
    is_weekend: bool = Field(..., description="週末かどうか")
    attendance: Optional[Dict[str, Any]] = Field(None, description="出勤記録詳細")


class AttendanceSummaryInfo(BaseModel):
    """勤怠サマリー情報Schema"""
    
    total_working_hours: float = Field(..., description="総勤務時間")
    total_days: int = Field(..., description="総出勤日数")
    approved_days: int = Field(..., description="承認済み日数")
    pending_approval_days: int = Field(..., description="承認待ち日数")
    expected_working_days: int = Field(..., description="予定出勤日数（営業日）")
    attendance_rate: float = Field(..., description="出勤率（%）")


class StaffAttendanceSummarySchema(BaseModel):
    """要員考勤汇总Schema"""
    
    total_days: int = Field(..., description="出勤天数")
    total_hours: float = Field(..., description="実働时间")
    overtime_hours: float = Field(..., description="残業时间")
    paid_leave_days: int = Field(..., description="有給休暇天数")
    period: str = Field(..., description="対象期間")


class StaffCompanyInfoSchema(BaseModel):
    """要員所属会社情報Schema"""
    
    type: str = Field(..., description="会社タイプ（bp_company/employee/freelancer）")
    name: str = Field(..., description="会社名")


class StaffCaseInfoSchema(BaseModel):
    """要員案件情報Schema"""
    
    case_title: str = Field(..., description="案件タイトル")
    client_company: str = Field(..., description="取引先会社名")
    unit_price: float = Field(..., description="単価")
    contract_period: str = Field(..., description="契約期間")


class StaffWithAttendanceSchema(BaseModel):
    """要員情報（考勤データ付き）Schema"""
    
    # 要員基本情報
    id: int = Field(..., description="要員ID")
    user_id: Optional[int] = Field(None, description="システムユーザーID")
    name: str = Field(..., description="氏名")
    name_kana: Optional[str] = Field(None, description="氏名（フリーカナ）")
    personnel_code: Optional[str] = Field(None, description="要員コード")
    person_type: str = Field(..., description="要員タイプ（bp_employee/freelancer/employee）")
    employment_status: Optional[str] = Field(None, description="就業ステータス")
    is_active: bool = Field(True, description="アクティブ状態")
    nationality: Optional[str] = Field(None, description="国籍")
    
    # 関連情報
    company_info: Optional[StaffCompanyInfoSchema] = Field(None, description="所属会社情報")
    case_info: Optional[StaffCaseInfoSchema] = Field(None, description="案件情報")
    attendance_summary: StaffAttendanceSummarySchema = Field(..., description="考勤データ汇总")
    current_contract: Optional[Dict[str, Any]] = Field(None, description="現在の契約情報")


class StaffListResponse(BaseModel):
    """要員リスト返却Schema"""
    
    items: List[StaffWithAttendanceSchema] = Field(..., description="要員一覧")
    total: int = Field(..., description="総件数")
    page: int = Field(..., description="ページ番号")
    page_size: int = Field(..., description="ページサイズ")


# Weekly Mood Tracking Schemas
class WeeklyMoodSchema(BaseModel):
    """週間心情記録Schema"""
    
    id: int = Field(..., description="記録ID")
    user_id: int = Field(..., description="ユーザーID")
    year: int = Field(..., description="年")
    week_number: int = Field(..., description="週番号（1-53）")
    mood_status: str = Field(..., description="心情状態")
    comment: Optional[str] = Field(None, description="心情コメント")
    week_start_date: str = Field(..., description="週開始日（YYYY-MM-DD）")
    week_end_date: str = Field(..., description="週終了日（YYYY-MM-DD）")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class SetWeeklyMoodSchema(BaseModel):
    """週間心情設定Schema"""
    week_number: Optional[int] = Field(None, ge=1, le=53, description="週番号（1-53）")
    mood_status: str = Field(..., description="心情状態（excellent/good/normal/stressed/tired/difficult）")
    comment: Optional[str] = Field(None, max_length=500, description="心情コメント（500文字以内）")


class MoodHistorySchema(BaseModel):
    """心情履歴Schema"""
    
    year: int = Field(..., description="年")
    week_number: int = Field(..., description="週番号")
    mood_status: str = Field(..., description="心情状態")
    comment: Optional[str] = Field(None, description="コメント")
    week_period: str = Field(..., description="週期間（YYYY-MM-DD～YYYY-MM-DD）")
    created_at: datetime = Field(..., description="記録日時")


class MoodHistoryResponse(BaseModel):
    """心情履歴返却Schema"""
    
    items: List[MoodHistorySchema] = Field(..., description="心情履歴一覧")
    total: int = Field(..., description="総件数")
    current_year: int = Field(..., description="現在年")
    current_week: int = Field(..., description="現在週")


class TeamMoodSummarySchema(BaseModel):
    """チーム心情サマリーSchema"""
    
    period: str = Field(..., description="対象期間")
    team_size: int = Field(..., description="チーム人数")
    mood_distribution: Dict[str, int] = Field(..., description="心情分布（状態別人数）")
    mood_trends: List[Dict[str, Any]] = Field(..., description="心情推移データ")
    average_mood_score: float = Field(..., description="平均心情スコア（1-6）")


class WeekMoodDataSchema(BaseModel):
    """週間心情データSchema"""
    
    status: Optional[str] = Field(None, description="心情状態")
    emoji: str = Field(..., description="心情表情符号")
    score: Optional[int] = Field(None, description="心情スコア（1-6）")
    comment: Optional[str] = Field(None, description="コメント")
    recorded_at: Optional[datetime] = Field(None, description="記録日時")
    is_recorded: bool = Field(..., description="記録済みフラグ")


class MonthlyWeekInfoSchema(BaseModel):
    """月内週情報Schema"""
    
    year: int = Field(..., description="年")
    week_number: int = Field(..., description="週番号")
    week_key: str = Field(..., description="週キー（YYYY-WNN）")
    week_start: str = Field(..., description="週開始日（YYYY-MM-DD）")
    week_end: str = Field(..., description="週終了日（YYYY-MM-DD）")
    month_days_in_week: str = Field(..., description="該当月内の日期范囲")
    days_count_in_month: int = Field(..., description="該当月内の日数")
    mood_data: WeekMoodDataSchema = Field(..., description="心情データ")


class MonthlyMoodSummarySchema(BaseModel):
    """月次心情サマリーSchema"""
    
    completion_rate: str = Field(..., description="記録完成率（N/M形式）")
    most_common_mood: Optional[str] = Field(None, description="最多心情状態")


class MonthlyMoodsResponseSchema(BaseModel):
    """月次心情データ返却Schema"""
    
    year_month: str = Field(..., description="対象年月（YYYY-MM）")
    total_weeks: int = Field(..., description="総週数")
    recorded_weeks: int = Field(..., description="記録済み週数")
    unrecorded_weeks: int = Field(..., description="未記録週数")
    average_score: Optional[float] = Field(None, description="平均心情スコア")
    mood_distribution: Dict[str, int] = Field(..., description="心情分布")
    weeks_data: List[MonthlyWeekInfoSchema] = Field(..., description="週別データ")
    summary: MonthlyMoodSummarySchema = Field(..., description="サマリー情報")


# Monthly Attendance Submission Workflow Schemas
class MonthlyAttendanceStatusSchema(BaseModel):
    """月次考勤状态Schema"""
    
    id: int = Field(..., description="月次考勤ID")
    user_id: Optional[int] = Field(None, description="ユーザーID")
    contract_id: int = Field(..., description="契約ID")
    year_month: str = Field(..., description="対象年月（YYYY-MM）")
    submission_status: str = Field(..., description="提交状态")
    submitted_at: Optional[datetime] = Field(None, description="提交日時")
    approved_at: Optional[datetime] = Field(None, description="承認日時")
    approved_by: Optional[int] = Field(None, description="承認者ID")
    remark: Optional[str] = Field(None, description="備考")
    
    # 计算统计数据
    statistics: Optional[Dict[str, Any]] = Field(None, description="考勤統計データ")
    
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class SubmitMonthlyAttendanceSchema(BaseModel):
    """月次考勤提交Schema"""
    
    year_month: str = Field(..., description="対象年月（YYYY-MM）")
    remark: Optional[str] = Field(None, max_length=1000, description="提交備考（1000文字以内）")


class ApproveMonthlyAttendanceSchema(BaseModel):
    """月次考勤承認Schema"""
    
    monthly_attendance_id: int = Field(..., description="月次考勤ID")
    remark: Optional[str] = Field(None, max_length=1000, description="承認備考（1000文字以内）")