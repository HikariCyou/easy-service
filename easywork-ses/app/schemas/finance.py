from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    FinanceApprovalStatus,
    FinanceCurrency,
    FinanceRecurrenceType,
    FinanceStatus,
    FinanceTaxType,
    FinanceTransactionType,
    ApplicationStatus,
    ApplicationPriority,
    ApprovalLevel,
)


class FinanceTransactionBase(BaseModel):
    """財務取引基本スキーマ"""

    transaction_type: FinanceTransactionType = Field(..., description="取引種別")
    title: str = Field(..., max_length=200, description="取引タイトル")
    description: Optional[str] = Field(None, description="取引詳細説明")
    amount: float = Field(..., gt=0, description="取引金額")
    currency: FinanceCurrency = Field(default=FinanceCurrency.JPY, description="通貨")
    category: str = Field(..., description="取引カテゴリ")
    sub_category: Optional[str] = Field(None, max_length=100, description="サブカテゴリ")
    payment_method: str = Field(..., description="支払方法")
    payment_date: Optional[date] = Field(None, description="支払日")
    due_date: Optional[date] = Field(None, description="支払期日")
    counterpart: Optional[str] = Field(None, max_length=200, description="取引先")
    reference_number: Optional[str] = Field(None, max_length=100, description="参照番号")
    notes: Optional[str] = Field(None, description="備考")


class FinanceTransactionCreate(FinanceTransactionBase):
    """財務取引作成スキーマ"""

    # 税務情報
    tax_type: FinanceTaxType = Field(default=FinanceTaxType.NONE, description="税務区分")
    tax_rate: float = Field(default=0.0, ge=0, le=100, description="税率")

    # 関連ID
    case_id: Optional[int] = Field(None, description="関連案件ID")
    contract_id: Optional[int] = Field(None, description="関連契約ID")
    personnel_id: Optional[int] = Field(None, description="関連人材ID")

    # 添付ファイル情報
    attachments: Optional[List[str]] = Field(None, description="添付ファイル一覧")
    tags: Optional[List[str]] = Field(None, description="タグ")


class FinanceTransactionUpdate(BaseModel):
    """財務取引更新スキーマ"""

    title: Optional[str] = Field(None, max_length=200, description="取引タイトル")
    description: Optional[str] = Field(None, description="取引詳細説明")
    amount: Optional[float] = Field(None, gt=0, description="取引金額")
    category: Optional[str] = Field(None, description="取引カテゴリ")
    sub_category: Optional[str] = Field(None, max_length=100, description="サブカテゴリ")
    payment_method: Optional[str] = Field(None, description="支払方法")
    payment_date: Optional[date] = Field(None, description="支払日")
    due_date: Optional[date] = Field(None, description="支払期日")
    counterpart: Optional[str] = Field(None, max_length=200, description="取引先")
    reference_number: Optional[str] = Field(None, max_length=100, description="参照番号")
    notes: Optional[str] = Field(None, description="備考")
    tax_rate: Optional[float] = Field(None, ge=0, le=100, description="税率")
    tags: Optional[List[str]] = Field(None, description="タグ")


class FinanceTransactionResponse(FinanceTransactionBase):
    """財務取引レスポンススキーマ"""

    id: int = Field(..., description="取引ID")
    transaction_number: str = Field(..., description="取引番号")
    exchange_rate: float = Field(..., description="為替レート")
    tax_type: FinanceTaxType = Field(..., description="税務区分")
    tax_rate: float = Field(..., description="税率")
    tax_amount: float = Field(..., description="税額")
    tax_exclusive_amount: Optional[float] = Field(None, description="税抜金額")
    is_recurring: bool = Field(..., description="定期取引フラグ")
    status: FinanceStatus = Field(..., description="取引ステータス")
    approval_status: FinanceApprovalStatus = Field(..., description="承認ステータス")
    requested_by: Optional[str] = Field(None, description="申請者")
    approved_by: Optional[str] = Field(None, description="承認者")
    approved_at: Optional[datetime] = Field(None, description="承認日時")
    attachments: Optional[List[dict]] = Field(None, description="添付ファイル一覧")
    tags: Optional[List[str]] = Field(None, description="タグ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        from_attributes = True


class FinanceTransactionApproval(BaseModel):
    """財務取引承認スキーマ"""

    action: str = Field(..., description="承認アクション", pattern="^(approve|reject)$")
    notes: Optional[str] = Field(None, description="承認・拒否理由")


class FinanceTransactionListQuery(BaseModel):
    """財務取引一覧クエリスキーマ"""

    transaction_type: Optional[FinanceTransactionType] = Field(None, description="取引種別")
    category: Optional[str] = Field(None, description="カテゴリ")
    status: Optional[FinanceStatus] = Field(None, description="ステータス")
    approval_status: Optional[FinanceApprovalStatus] = Field(None, description="承認ステータス")
    payment_date_from: Optional[date] = Field(None, description="支払日From")
    payment_date_to: Optional[date] = Field(None, description="支払日To")
    amount_min: Optional[float] = Field(None, ge=0, description="金額下限")
    amount_max: Optional[float] = Field(None, ge=0, description="金額上限")
    counterpart: Optional[str] = Field(None, description="取引先")
    case_id: Optional[int] = Field(None, description="案件ID")
    contract_id: Optional[int] = Field(None, description="契約ID")
    personnel_id: Optional[int] = Field(None, description="人材ID")
    search_keyword: Optional[str] = Field(None, description="検索キーワード")
    page: int = Field(default=1, ge=1, description="ページ番号")
    page_size: int = Field(default=20, ge=1, le=100, description="ページサイズ")


class FinanceRecurrenceRuleBase(BaseModel):
    """定期取引ルール基本スキーマ"""

    rule_name: str = Field(..., max_length=100, description="ルール名")
    description: Optional[str] = Field(None, description="ルール説明")
    transaction_type: FinanceTransactionType = Field(..., description="取引種別")
    title_template: str = Field(..., max_length=200, description="タイトルテンプレート")
    amount: float = Field(..., gt=0, description="金額")
    category: str = Field(..., description="カテゴリ")
    recurrence_type: FinanceRecurrenceType = Field(..., description="定期種別")
    interval_value: int = Field(default=1, ge=1, description="間隔値")
    execution_day: Optional[int] = Field(None, ge=1, le=31, description="実行日")
    execution_weekday: Optional[int] = Field(None, ge=0, le=6, description="実行曜日")
    start_date: date = Field(..., description="開始日")
    end_date: Optional[date] = Field(None, description="終了日")
    max_occurrences: Optional[int] = Field(None, ge=1, description="最大実行回数")


class FinanceRecurrenceRuleCreate(FinanceRecurrenceRuleBase):
    """定期取引ルール作成スキーマ"""
    pass


class FinanceRecurrenceRuleUpdate(BaseModel):
    """定期取引ルール更新スキーマ"""

    rule_name: Optional[str] = Field(None, max_length=100, description="ルール名")
    description: Optional[str] = Field(None, description="ルール説明")
    title_template: Optional[str] = Field(None, max_length=200, description="タイトルテンプレート")
    amount: Optional[float] = Field(None, gt=0, description="金額")
    category: Optional[str] = Field(None, description="カテゴリ")
    interval_value: Optional[int] = Field(None, ge=1, description="間隔値")
    execution_day: Optional[int] = Field(None, ge=1, le=31, description="実行日")
    execution_weekday: Optional[int] = Field(None, ge=0, le=6, description="実行曜日")
    end_date: Optional[date] = Field(None, description="終了日")
    max_occurrences: Optional[int] = Field(None, ge=1, description="最大実行回数")
    is_active: Optional[bool] = Field(None, description="有効フラグ")


class FinanceRecurrenceRuleResponse(FinanceRecurrenceRuleBase):
    """定期取引ルールレスポンススキーマ"""

    id: int = Field(..., description="ルールID")
    is_active: bool = Field(..., description="有効フラグ")
    last_executed: Optional[date] = Field(None, description="最終実行日")
    execution_count: int = Field(..., description="実行回数")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        from_attributes = True


class FinanceBudgetBase(BaseModel):
    """予算基本スキーマ"""

    budget_name: str = Field(..., max_length=100, description="予算名")
    category: str = Field(..., description="予算カテゴリ")
    period_start: date = Field(..., description="期間開始日")
    period_end: date = Field(..., description="期間終了日")
    budget_amount: float = Field(..., gt=0, description="予算金額")
    warning_threshold: float = Field(default=80.0, ge=0, le=100, description="警告閾値（%）")
    alert_threshold: float = Field(default=95.0, ge=0, le=100, description="アラート閾値（%）")
    description: Optional[str] = Field(None, description="予算説明")


class FinanceBudgetCreate(FinanceBudgetBase):
    """予算作成スキーマ"""
    pass


class FinanceBudgetUpdate(BaseModel):
    """予算更新スキーマ"""

    budget_name: Optional[str] = Field(None, max_length=100, description="予算名")
    budget_amount: Optional[float] = Field(None, gt=0, description="予算金額")
    warning_threshold: Optional[float] = Field(None, ge=0, le=100, description="警告閾値（%）")
    alert_threshold: Optional[float] = Field(None, ge=0, le=100, description="アラート閾値（%）")
    description: Optional[str] = Field(None, description="予算説明")
    is_active: Optional[bool] = Field(None, description="有効フラグ")


class FinanceBudgetResponse(FinanceBudgetBase):
    """予算レスポンススキーマ"""

    id: int = Field(..., description="予算ID")
    spent_amount: float = Field(..., description="使用済み金額")
    remaining_amount: float = Field(..., description="残予算")
    usage_percentage: float = Field(..., description="使用率（%）")
    is_over_warning: bool = Field(..., description="警告閾値超過フラグ")
    is_over_alert: bool = Field(..., description="アラート閾値超過フラグ")
    is_active: bool = Field(..., description="有効フラグ")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        from_attributes = True


class FinanceAttachmentResponse(BaseModel):
    """添付ファイルレスポンススキーマ"""

    id: int = Field(..., description="添付ファイルID")
    transaction_id: int = Field(..., description="取引ID")
    file_name: str = Field(..., description="ファイル名")
    original_name: str = Field(..., description="元ファイル名")
    file_size: int = Field(..., description="ファイルサイズ（bytes）")
    file_type: str = Field(..., description="ファイルタイプ")
    attachment_type: str = Field(..., description="添付種別")
    s3_url: str = Field(..., description="S3 URL")
    description: Optional[str] = Field(None, description="ファイル説明")
    is_processed: bool = Field(..., description="処理済みフラグ")
    uploaded_by: Optional[str] = Field(None, description="アップロード者")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        from_attributes = True


class FinanceReportResponse(BaseModel):
    """財務レポートレスポンススキーマ"""

    id: int = Field(..., description="レポートID")
    report_name: str = Field(..., description="レポート名")
    report_type: str = Field(..., description="レポート種別")
    period_start: date = Field(..., description="対象期間開始日")
    period_end: date = Field(..., description="対象期間終了日")
    total_income: float = Field(..., description="総収入")
    total_expense: float = Field(..., description="総支出")
    net_profit: float = Field(..., description="純利益")
    profit_margin: float = Field(..., description="利益率（%）")
    personnel_cost: float = Field(..., description="人件費")
    operational_cost: float = Field(..., description="運営費")
    project_cost: float = Field(..., description="プロジェクト費用")
    category_breakdown: Optional[dict] = Field(None, description="カテゴリ別内訳")
    monthly_trend: Optional[dict] = Field(None, description="月次推移データ")
    report_file_url: Optional[str] = Field(None, description="レポートファイルURL")
    generated_by: Optional[str] = Field(None, description="生成者")
    is_auto_generated: bool = Field(..., description="自動生成フラグ")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        from_attributes = True


class FinanceAnalyticsQuery(BaseModel):
    """財務分析クエリスキーマ"""

    period_start: date = Field(..., description="分析期間開始日")
    period_end: date = Field(..., description="分析期間終了日")
    categories: Optional[List[str]] = Field(None, description="分析対象カテゴリ")
    group_by: str = Field(default="month", description="グループ化基準", pattern="^(day|week|month|quarter|year)$")
    include_projections: bool = Field(default=False, description="予測データを含むか")


class FinanceReportGenerateRequest(BaseModel):
    """財務レポート生成リクエストスキーマ"""

    period_start: date = Field(..., description="レポート期間開始日")
    period_end: date = Field(..., description="レポート期間終了日")
    report_name: Optional[str] = Field(None, max_length=100, description="レポート名（自動生成されない場合）")
    report_type: str = Field(default="custom", pattern="^(monthly|quarterly|yearly|custom)$", description="レポート種別")
    include_details: bool = Field(default=True, description="詳細データを含めるか")
    include_charts: bool = Field(default=True, description="チャートデータを含めるか")
    transaction_type: Optional[FinanceTransactionType] = Field(None, description="対象取引種別（指定なしは全て）")
    categories: Optional[List[str]] = Field(None, description="対象カテゴリ（指定なしは全て）")


class FinanceAnalyticsResponse(BaseModel):
    """財務分析レスポンススキーマ"""

    period_start: date = Field(..., description="分析期間開始日")
    period_end: date = Field(..., description="分析期間終了日")
    summary: dict = Field(..., description="サマリー情報")
    trend_data: List[dict] = Field(..., description="推移データ")
    category_breakdown: dict = Field(..., description="カテゴリ別内訳")
    top_expenses: List[dict] = Field(..., description="主要支出項目")
    budget_analysis: dict = Field(..., description="予算分析")
    generated_at: datetime = Field(..., description="生成日時")


# ==================== 費用申請管理スキーマ ====================

class ExpenseApplicationBase(BaseModel):
    """費用申請基本スキーマ"""

    application_type: str = Field(..., description="申請種別")
    description: str = Field(..., description="申請内容詳細")
    amount: float = Field(..., gt=0, description="申請金額")
    expense_date_from: date = Field(..., description="費用発生日（開始）")
    expense_date_to: Optional[date] = Field(None, description="費用発生日（終了）")
    purpose: Optional[str] = Field(None, max_length=200, description="目的")
    currency: FinanceCurrency = Field(default=FinanceCurrency.JPY, description="通貨")


class ExpenseApplicationCreate(ExpenseApplicationBase):
    """費用申請作成スキーマ"""

    # 添付ファイル・備考
    attachments: Optional[List[str]] = Field(None, description="添付ファイル一覧")
    applicant_notes: Optional[str] = Field(None, description="申請者備考")


class ExpenseApplicationUpdate(BaseModel):
    """費用申請更新スキーマ"""

    title: Optional[str] = Field(None, max_length=200, description="申請タイトル")
    description: Optional[str] = Field(None, description="申請内容詳細")
    amount: Optional[float] = Field(None, gt=0, description="申請金額")
    expense_date_from: Optional[date] = Field(None, description="費用発生日（開始）")
    expense_date_to: Optional[date] = Field(None, description="費用発生日（終了）")
    purpose: Optional[str] = Field(None, max_length=200, description="目的")
    destination: Optional[str] = Field(None, max_length=200, description="出張先・訪問先")
    priority: Optional[ApplicationPriority] = Field(None, description="優先度")
    attachments: Optional[List[dict]] = Field(None, description="添付ファイル一覧")
    applicant_notes: Optional[str] = Field(None, description="申請者備考")
    estimated_payment_date: Optional[date] = Field(None, description="予定支払日")


class ExpenseApplicationResponse(ExpenseApplicationBase):
    """費用申請レスポンススキーマ"""

    id: int = Field(..., description="申請ID")
    application_number: str = Field(..., description="申請番号")
    applicant_id: int = Field(..., description="申請者ID")
    applicant_name: str = Field(..., description="申請者名")
    department: Optional[str] = Field(None, description="部署")

    # ステータス情報
    status: ApplicationStatus = Field(..., description="申請ステータス")
    application_date: Optional[date] = Field(None, description="申請日")
    submitted_at: Optional[datetime] = Field(None, description="提出日時")

    # 承認情報
    approval_level: Optional[ApprovalLevel] = Field(None, description="必要承認レベル")
    current_approver: Optional[str] = Field(None, description="現在の承認者")
    approved_by: Optional[str] = Field(None, description="承認者")
    approved_at: Optional[datetime] = Field(None, description="承認日時")
    rejection_reason: Optional[str] = Field(None, description="却下理由")

    # 財務連携
    finance_transaction_id: Optional[int] = Field(None, description="関連財務取引ID")
    estimated_payment_date: Optional[date] = Field(None, description="予定支払日")
    actual_payment_date: Optional[date] = Field(None, description="実際支払日")

    # 関連ID
    case_id: Optional[int] = Field(None, description="関連案件ID")
    contract_id: Optional[int] = Field(None, description="関連契約ID")
    personnel_id: Optional[int] = Field(None, description="関連人材ID")

    # その他
    attachments: Optional[List[dict]] = Field(None, description="添付ファイル一覧")
    internal_notes: Optional[str] = Field(None, description="内部メモ")
    applicant_notes: Optional[str] = Field(None, description="申請者備考")

    # プロパティ情報
    is_approved: bool = Field(..., description="承認済みフラグ")
    is_paid: bool = Field(..., description="支払済みフラグ")
    can_be_cancelled: bool = Field(..., description="キャンセル可能フラグ")

    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")

    class Config:
        from_attributes = True


class ExpenseApplicationListQuery(BaseModel):
    """費用申請一覧クエリスキーマ"""

    application_type: Optional[str] = Field(None, description="申請種別")
    status: Optional[ApplicationStatus] = Field(None, description="ステータス")
    applicant_id: Optional[int] = Field(None, description="申請者ID")
    priority: Optional[ApplicationPriority] = Field(None, description="優先度")
    application_date_from: Optional[date] = Field(None, description="申請日From")
    application_date_to: Optional[date] = Field(None, description="申請日To")
    expense_date_from: Optional[date] = Field(None, description="費用発生日From")
    expense_date_to: Optional[date] = Field(None, description="費用発生日To")
    amount_min: Optional[float] = Field(None, ge=0, description="金額下限")
    amount_max: Optional[float] = Field(None, ge=0, description="金額上限")
    search_keyword: Optional[str] = Field(None, description="検索キーワード")
    page: int = Field(default=1, ge=1, description="ページ番号")
    page_size: int = Field(default=20, ge=1, le=100, description="ページサイズ")


class ExpenseApplicationApproval(BaseModel):
    """費用申請承認スキーマ"""

    action: str = Field(..., description="承認アクション", pattern="^(approve|reject|cancel)$")
    notes: Optional[str] = Field(None, description="承認・拒否理由")


class ExpenseApplicationSubmit(BaseModel):
    """費用申請提出スキーマ"""

    notes: Optional[str] = Field(None, description="提出時の備考")


class ExpenseApplicationPayment(BaseModel):
    """費用申請支払完了スキーマ"""

    payment_date: Optional[date] = Field(None, description="支払日")
    notes: Optional[str] = Field(None, description="支払備考")


class ExpenseApprovalHistoryResponse(BaseModel):
    """費用申請承認履歴レスポンススキーマ"""

    id: int = Field(..., description="履歴ID")
    application_id: int = Field(..., description="申請ID")
    action: str = Field(..., description="アクション")
    actor: str = Field(..., description="実行者")
    action_date: datetime = Field(..., description="実行日時")
    notes: Optional[str] = Field(None, description="備考・理由")
    previous_status: Optional[str] = Field(None, description="変更前ステータス")
    new_status: Optional[str] = Field(None, description="変更後ステータス")
    created_at: datetime = Field(..., description="作成日時")

    class Config:
        from_attributes = True


class ExpenseApplicationStats(BaseModel):
    """費用申請統計スキーマ"""

    total_applications: int = Field(..., description="総申請件数")
    pending_applications: int = Field(..., description="承認待ち件数")
    approved_applications: int = Field(..., description="承認済み件数")
    rejected_applications: int = Field(..., description="却下件数")
    total_amount: float = Field(..., description="総申請金額")
    approved_amount: float = Field(..., description="承認済み金額")
    paid_amount: float = Field(..., description="支払済み金額")
    by_type: dict = Field(..., description="種別別統計")
    by_status: dict = Field(..., description="ステータス別統計")
    monthly_trend: List[dict] = Field(..., description="月次推移")