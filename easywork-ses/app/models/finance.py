from datetime import datetime, date

from tortoise import fields
from tortoise.signals import post_save

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import (
    FinanceTransactionType,
    FinanceStatus,
    FinanceRecurrenceType,
    FinanceTaxType,
    FinanceApprovalStatus,
    FinanceCurrency,
    ApplicationStatus,
    ApplicationPriority,
    ApprovalLevel, FinancePaymentMethod,
)


class FinanceTransaction(BaseModel, TimestampMixin):
    """
    財務取引記録
    すべての収支記録の中心となるテーブル
    """

    # 基本情報
    transaction_number = fields.CharField(max_length=50, unique=True, description="取引番号")
    transaction_type = fields.CharEnumField(FinanceTransactionType, description="取引種別")

    # 取引詳細
    title = fields.CharField(max_length=200, description="取引タイトル")
    description = fields.TextField(null=True, description="取引詳細説明")

    # 金額情報
    amount = fields.FloatField(description="取引金額")
    currency = fields.CharEnumField(FinanceCurrency, default=FinanceCurrency.JPY, description="通貨")
    exchange_rate = fields.FloatField(default=1.0, description="為替レート")

    # カテゴリ・分類
    category = fields.CharField(default=None, max_length=20, description="取引カテゴリ")
    sub_category = fields.CharField(max_length=100, null=True, description="サブカテゴリ")

    # 税務情報
    tax_type = fields.CharEnumField(FinanceTaxType, default=FinanceTaxType.NONE, description="税務区分")
    tax_rate = fields.FloatField(default=0.0, description="税率")
    tax_amount = fields.FloatField(default=0.0, description="税額")
    tax_exclusive_amount = fields.FloatField(null=True, description="税抜金額")

    # 支払い情報
    payment_method = fields.CharField(max_length=20, description="支払方法")
    payment_date = fields.DateField(null=True, description="支払日")
    due_date = fields.DateField(null=True, description="支払期日")

    # 関連情報
    counterpart = fields.CharField(max_length=200, null=True, description="取引先")
    reference_number = fields.CharField(max_length=100, null=True, description="参照番号")

    # ビジネス関連
    case = fields.ForeignKeyField("models.Case", null=True, related_name="finance_transactions", description="関連案件")
    contract = fields.ForeignKeyField("models.Contract", null=True, related_name="finance_transactions", description="関連契約")
    personnel = fields.ForeignKeyField("models.Personnel", null=True, related_name="finance_transactions", description="関連人材")

    # 定期取引情報
    is_recurring = fields.BooleanField(default=False, description="定期取引フラグ")
    recurrence_rule = fields.ForeignKeyField("models.FinanceRecurrenceRule", null=True, related_name="transactions", description="定期取引ルール")
    parent_transaction = fields.ForeignKeyField("models.FinanceTransaction", null=True, related_name="recurring_transactions", description="親取引（定期取引の場合）")

    # ステータス
    status = fields.CharEnumField(FinanceStatus, default=FinanceStatus.PENDING, description="取引ステータス")
    approval_status = fields.CharEnumField(FinanceApprovalStatus, default=FinanceApprovalStatus.PENDING, description="承認ステータス")

    # 承認情報
    requested_by = fields.CharField(max_length=100, null=True, description="申請者")
    approved_by = fields.CharField(max_length=100, null=True, description="承認者")
    approved_at = fields.DatetimeField(null=True, description="承認日時")

    # 添付ファイル（S3）- JSON配列で複数ファイルを格納
    attachments = fields.JSONField(null=True, description="添付ファイル一覧")  # [{"name": "receipt.pdf", "s3_url": "s3://...", "size": 1024, "type": "receipt"}]

    # 備考・タグ
    notes = fields.TextField(null=True, description="備考")
    tags = fields.JSONField(null=True, description="タグ")  # ["経費", "交通費", "会議"]

    # 関連
    attachments_rel: fields.ReverseRelation["FinanceAttachment"]
    recurring_transactions: fields.ReverseRelation["FinanceTransaction"]

    class Meta:
        table = "finance_transaction"
        table_description = "財務取引記録"
        indexes = [
            ("transaction_type", "category"),
            ("payment_date",),
            ("status", "approval_status"),
            ("case_id",),
            ("contract_id",),
            ("created_at",),
        ]

    def __str__(self):
        return f"{self.transaction_number} - {self.title} (¥{self.amount:,.0f})"

    @property
    def is_income(self) -> bool:
        """収入取引かどうか"""
        return self.transaction_type == FinanceTransactionType.INCOME

    @property
    def is_expense(self) -> bool:
        """支出取引かどうか"""
        return self.transaction_type == FinanceTransactionType.EXPENSE

    @property
    def display_amount(self) -> str:
        """表示用金額（符号付き）"""
        sign = "+" if self.is_income else "-"
        return f"{sign}¥{self.amount:,.0f}"

    async def calculate_tax_amount(self) -> float:
        """税額を計算"""
        if self.tax_rate > 0:
            return self.amount * (self.tax_rate / 100)
        return 0.0

    async def approve(self, approved_by: str, notes: str = None):
        """取引を承認"""
        self.approval_status = FinanceApprovalStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        if notes:
            self.notes = f"{self.notes or ''}\n承認: {notes}".strip()
        await self.save()

    async def reject(self, rejected_by: str, reason: str):
        """取引を拒否"""
        self.approval_status = FinanceApprovalStatus.REJECTED
        self.approved_by = rejected_by
        self.approved_at = datetime.now()
        self.notes = f"{self.notes or ''}\n拒否理由: {reason}".strip()
        await self.save()


class FinanceRecurrenceRule(BaseModel, TimestampMixin):
    """
    定期取引ルール
    給与、家賃等の定期的な取引パターンを管理
    """

    rule_name = fields.CharField(max_length=100, description="ルール名")
    description = fields.TextField(null=True, description="ルール説明")

    # 基本取引情報テンプレート
    transaction_type = fields.CharEnumField(FinanceTransactionType, description="取引種別")
    title_template = fields.CharField(max_length=200, description="タイトルテンプレート")
    amount = fields.FloatField(description="金額")
    category = fields.CharField(max_length=100,null=True, description="カテゴリ")

    # 定期実行設定
    recurrence_type = fields.CharEnumField(FinanceRecurrenceType, description="定期種別")
    interval_value = fields.IntField(default=1, description="間隔値")  # 毎週、隔週等
    execution_day = fields.IntField(null=True, description="実行日")  # 毎月25日等
    execution_weekday = fields.IntField(null=True, description="実行曜日")  # 0=月曜日

    # 期間設定
    start_date = fields.DateField(description="開始日")
    end_date = fields.DateField(null=True, description="終了日")
    max_occurrences = fields.IntField(null=True, description="最大実行回数")

    # 管理情報
    is_active = fields.BooleanField(default=True, description="有効フラグ")
    last_executed = fields.DateField(null=True, description="最終実行日")
    execution_count = fields.IntField(default=0, description="実行回数")

    # 関連
    transactions: fields.ReverseRelation["FinanceTransaction"]

    class Meta:
        table = "finance_recurrence_rule"
        table_description = "定期取引ルール"
        indexes = [
            ("is_active", "start_date"),
            ("recurrence_type",),
        ]

    def __str__(self):
        return f"{self.rule_name} - {self.recurrence_type}"

    async def should_execute_today(self) -> bool:
        """今日実行すべきかチェック"""
        from datetime import date
        today = date.today()

        if not self.is_active:
            return False

        if today < self.start_date:
            return False

        if self.end_date and today > self.end_date:
            return False

        if self.max_occurrences and self.execution_count >= self.max_occurrences:
            return False

        # 具体的な日付計算ロジックは実装時に詳細化
        return True

    async def create_transaction(self) -> "FinanceTransaction":
        """定期取引を作成"""
        from datetime import date

        transaction = await FinanceTransaction.create(
            transaction_number=f"REC-{self.id}-{date.today().strftime('%Y%m%d')}",
            transaction_type=self.transaction_type,
            title=self.title_template.format(date=date.today()),
            amount=self.amount,
            category=self.category,
            recurrence_rule=self,
            is_recurring=True,
            status=FinanceStatus.PENDING,
        )

        # 実行記録更新
        self.last_executed = date.today()
        self.execution_count += 1
        await self.save()

        return transaction


class FinanceAttachment(BaseModel, TimestampMixin):
    """
    財務添付ファイル管理
    レシート、請求書、契約書等のファイル管理
    """

    transaction_id = fields.BigIntField(description="関連取引ID")

    # ファイル情報
    file_name = fields.CharField(max_length=255, description="ファイル名")
    original_name = fields.CharField(max_length=255, description="元ファイル名")
    file_size = fields.BigIntField(description="ファイルサイズ（bytes）")
    file_type = fields.CharField(max_length=50, description="ファイルタイプ")
    mime_type = fields.CharField(max_length=100, description="MIMEタイプ")

    # S3情報
    s3_bucket = fields.CharField(max_length=100, description="S3バケット名")
    s3_key = fields.CharField(max_length=500, description="S3キー")
    s3_url = fields.CharField(max_length=1000, description="S3 URL")

    # 分類情報
    attachment_type = fields.CharField(max_length=50, description="添付種別")  # receipt, invoice, contract等
    description = fields.TextField(null=True, description="ファイル説明")

    # OCR・AI分析結果
    ocr_text = fields.TextField(null=True, description="OCR抽出テキスト")
    ai_analysis = fields.JSONField(null=True, description="AI分析結果")  # 金額、日付、取引先等の抽出データ

    # 管理情報
    is_processed = fields.BooleanField(default=False, description="処理済みフラグ")
    uploaded_by = fields.CharField(max_length=100, null=True, description="アップロード者")

    class Meta:
        table = "finance_attachment"
        table_description = "財務添付ファイル"
        indexes = [
            ("transaction_id",),
            ("attachment_type",),
            ("created_at",),
        ]

    def __str__(self):
        return f"{self.original_name} ({self.file_size:,} bytes)"

    @property
    def file_size_mb(self) -> float:
        """ファイルサイズ（MB）"""
        return self.file_size / (1024 * 1024)

    async def get_signed_url(self, expires_in: int = 3600) -> str:
        """署名付きURLを生成"""
        # S3クライアントを使用してpre-signed URLを生成
        # 実装は実際のS3設定に依存
        return f"{self.s3_url}?expires_in={expires_in}"


class FinanceBudget(BaseModel, TimestampMixin):
    """
    予算管理
    カテゴリ別、期間別の予算設定と実績管理
    """

    budget_name = fields.CharField(max_length=100, description="予算名")
    category = fields.CharField(max_length=100, description="予算カテゴリ")

    # 期間設定
    period_start = fields.DateField(description="期間開始日")
    period_end = fields.DateField(description="期間終了日")

    # 予算金額
    budget_amount = fields.FloatField(description="予算金額")
    spent_amount = fields.FloatField(default=0.0, description="使用済み金額")
    remaining_amount = fields.FloatField(default=0.0, description="残予算")

    # アラート設定
    warning_threshold = fields.FloatField(default=80.0, description="警告閾値（%）")
    alert_threshold = fields.FloatField(default=95.0, description="アラート閾値（%）")

    # 管理情報
    is_active = fields.BooleanField(default=True, description="有効フラグ")
    description = fields.TextField(null=True, description="予算説明")

    class Meta:
        table = "finance_budget"
        table_description = "予算管理"
        indexes = [
            ("category", "period_start"),
            ("is_active",),
        ]

    def __str__(self):
        return f"{self.budget_name} - ¥{self.budget_amount:,.0f}"

    @property
    def usage_percentage(self) -> float:
        """使用率（%）"""
        if self.budget_amount > 0:
            return (self.spent_amount / self.budget_amount) * 100
        return 0.0

    @property
    def is_over_warning(self) -> bool:
        """警告閾値を超えているか"""
        return self.usage_percentage >= self.warning_threshold

    @property
    def is_over_alert(self) -> bool:
        """アラート閾値を超えているか"""
        return self.usage_percentage >= self.alert_threshold

    async def update_spent_amount(self):
        """使用済み金額を再計算"""
        transactions = await FinanceTransaction.filter(
            category=self.category,
            transaction_type=FinanceTransactionType.EXPENSE,
            payment_date__gte=self.period_start,
            payment_date__lte=self.period_end,
            status=FinanceStatus.COMPLETED
        ).all()

        total_spent = sum(t.amount for t in transactions)
        self.spent_amount = total_spent
        self.remaining_amount = self.budget_amount - total_spent
        await self.save()


class FinanceReport(BaseModel, TimestampMixin):
    """
    財務レポート
    定期的な財務分析レポートの保存・管理
    """

    report_name = fields.CharField(max_length=100, description="レポート名")
    report_type = fields.CharField(max_length=50, description="レポート種別")  # monthly, quarterly, yearly, custom

    # 期間
    period_start = fields.DateField(description="対象期間開始日")
    period_end = fields.DateField(description="対象期間終了日")

    # 分析データ
    total_income = fields.FloatField(default=0.0, description="総収入")
    total_expense = fields.FloatField(default=0.0, description="総支出")
    net_profit = fields.FloatField(default=0.0, description="純利益")
    profit_margin = fields.FloatField(default=0.0, description="利益率（%）")

    # カテゴリ別分析（JSON）
    category_breakdown = fields.JSONField(null=True, description="カテゴリ別内訳")
    monthly_trend = fields.JSONField(null=True, description="月次推移データ")

    # コスト分析
    personnel_cost = fields.FloatField(default=0.0, description="人件費")
    operational_cost = fields.FloatField(default=0.0, description="運営費")
    project_cost = fields.FloatField(default=0.0, description="プロジェクト費用")

    # レポートファイル
    report_file_url = fields.CharField(max_length=1000, null=True, description="レポートファイルURL（PDF等）")

    # 生成情報
    generated_by = fields.CharField(max_length=100, null=True, description="生成者")
    is_auto_generated = fields.BooleanField(default=False, description="自動生成フラグ")

    class Meta:
        table = "finance_report"
        table_description = "財務レポート"
        indexes = [
            ("report_type", "period_start"),
            ("created_at",),
        ]

    def __str__(self):
        return f"{self.report_name} ({self.period_start} - {self.period_end})"

    async def calculate_metrics(self):
        """財務指標を計算"""
        # 期間内の取引データを取得して分析
        transactions = await FinanceTransaction.filter(
            payment_date__gte=self.period_start,
            payment_date__lte=self.period_end,
            status=FinanceStatus.COMPLETED
        ).all()

        income_transactions = [t for t in transactions if t.is_income]
        expense_transactions = [t for t in transactions if t.is_expense]

        self.total_income = sum(t.amount for t in income_transactions)
        self.total_expense = sum(t.amount for t in expense_transactions)
        self.net_profit = self.total_income - self.total_expense

        if self.total_income > 0:
            self.profit_margin = (self.net_profit / self.total_income) * 100

        await self.save()


class ExpenseApplication(BaseModel, TimestampMixin):
    """
    費用申請管理
    従業員の交通費、出張費、その他経費申請を管理
    """

    # 申請基本情報
    application_number = fields.CharField(max_length=50, unique=True, description="申請番号")
    application_type = fields.CharField(max_length=100 , null=True, description="申請種別")

    # 申請者情報
    applicant_id = fields.BigIntField(description="申請者ID")
    applicant_name = fields.CharField(max_length=100, description="申請者名")
    department = fields.CharField(max_length=100, null=True, description="部署")

    # 金額・期間
    amount = fields.FloatField(description="申請金額")
    currency = fields.CharEnumField(FinanceCurrency, default=FinanceCurrency.JPY, description="通貨")
    expense_date_from = fields.DateField(description="費用発生日（開始）")
    expense_date_to = fields.DateField(null=True, description="費用発生日（終了）")

    # 申請内容
    title = fields.CharField(max_length=200, description="申請タイトル")
    description = fields.TextField(description="申請内容詳細")
    purpose = fields.CharField(max_length=200, null=True, description="目的")
    destination = fields.CharField(max_length=200, null=True, description="出張先・訪問先")

    # 業務関連
    case = fields.ForeignKeyField("models.Case", null=True, related_name="expense_applications", description="関連案件")
    contract = fields.ForeignKeyField("models.Contract", null=True, related_name="expense_applications", description="関連契約")
    personnel = fields.ForeignKeyField("models.Personnel", null=True, related_name="expense_applications", description="関連人材")

    # ステータス管理
    status = fields.CharEnumField(ApplicationStatus, default=ApplicationStatus.DRAFT, description="申請ステータス")
    priority = fields.CharEnumField(ApplicationPriority, default=ApplicationPriority.NORMAL, description="優先度")

    # 申請・提出情報
    application_date = fields.DateField(null=True, description="申請日")
    submitted_at = fields.DatetimeField(null=True, description="提出日時")

    # 承認情報
    approval_level = fields.CharEnumField(ApprovalLevel, null=True, description="必要承認レベル")
    current_approver = fields.CharField(max_length=100, null=True, description="現在の承認者")
    approved_by = fields.CharField(max_length=100, null=True, description="承認者")
    approved_at = fields.DatetimeField(null=True, description="承認日時")
    rejection_reason = fields.TextField(null=True, description="却下理由")

    # 財務連携
    finance_transaction_id = fields.BigIntField(null=True, description="関連財務取引ID")
    estimated_payment_date = fields.DateField(null=True, description="予定支払日")
    actual_payment_date = fields.DateField(null=True, description="実際支払日")

    # 添付ファイル・メモ
    attachments = fields.JSONField(null=True, description="添付ファイル一覧")  # レシート、領収書等
    internal_notes = fields.TextField(null=True, description="内部メモ")
    applicant_notes = fields.TextField(null=True, description="申請者備考")

    # 関連
    approval_history: fields.ReverseRelation["ExpenseApprovalHistory"]

    class Meta:
        table = "expense_application"
        table_description = "費用申請管理"
        indexes = [
            ("applicant_id", "application_date"),
            ("status", "created_at"),
            ("application_type", "status"),
            ("case_id",),
            ("finance_transaction_id",),
        ]

    def __str__(self):
        return f"{self.application_number} - {self.title} (¥{self.amount:,.0f})"

    @property
    def is_approved(self) -> bool:
        """承認済みかどうか"""
        return self.status == ApplicationStatus.APPROVED

    @property
    def is_paid(self) -> bool:
        """支払済みかどうか"""
        return self.status == ApplicationStatus.PAID

    @property
    def can_be_cancelled(self) -> bool:
        """キャンセル可能かどうか"""
        return self.status in [ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED]

    async def submit_application(self, submitted_by: str = None):
        """申請を提出"""
        if self.status != ApplicationStatus.DRAFT:
            raise ValueError("草稿状態の申請のみ提出可能です")

        self.status = ApplicationStatus.SUBMITTED
        self.application_date = datetime.now().date()
        self.submitted_at = datetime.now()
        await self.save()

        # 承認履歴を記録
        await ExpenseApprovalHistory.create(
            application=self,
            action="submit",
            actor=submitted_by or self.applicant_name,
            notes=f"申請を提出しました",
            action_date=datetime.now()
        )

    async def approve_application(self, approved_by: str, notes: str = None):
        """申請を承認"""
        if self.status not in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]:
            raise ValueError("申請中または審査中の申請のみ承認可能です")

        self.status = ApplicationStatus.APPROVED
        self.approved_by = approved_by
        self.approved_at = datetime.now()
        await self.save()

        # 承認履歴を記録
        await ExpenseApprovalHistory.create(
            application=self,
            action="approve",
            actor=approved_by,
            notes=notes or "申請が承認されました",
            action_date=datetime.now()
        )

        # 財務取引を自動生成
        await self.create_finance_transaction()

    async def reject_application(self, rejected_by: str, reason: str):
        """申請を却下"""
        if self.status not in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]:
            raise ValueError("申請中または審査中の申請のみ却下可能です")

        self.status = ApplicationStatus.REJECTED
        self.approved_by = rejected_by
        self.approved_at = datetime.now()
        self.rejection_reason = reason
        await self.save()

        # 承認履歴を記録
        await ExpenseApprovalHistory.create(
            application=self,
            action="reject",
            actor=rejected_by,
            notes=reason,
            action_date=datetime.now()
        )

    async def create_finance_transaction(self):
        """承認後に財務取引を作成"""
        if not self.is_approved:
            raise ValueError("承認済みの申請のみ財務取引を作成可能です")

        if self.finance_transaction_id:
            raise ValueError("財務取引は既に作成済みです")


        # 財務取引を作成
        finance_transaction = await FinanceTransaction.create(
            transaction_number=f"EXP-{self.application_number}",
            transaction_type=FinanceTransactionType.EXPENSE,
            title=f"{self.application_type} - {self.applicant_name}",
            description=f"費用申請: {self.description}",
            amount=self.amount,
            currency=self.currency,
            category=self.application_type,
            payment_method=FinancePaymentMethod.BANK_TRANSFER,
            due_date=self.estimated_payment_date,
            counterpart=self.applicant_name,
            reference_number=self.application_number,
            status=FinanceStatus.PENDING,
            approval_status=FinanceApprovalStatus.APPROVED,
            requested_by=self.applicant_name,
            approved_by=self.approved_by,
            approved_at=self.approved_at,
            attachments=self.attachments,
            notes=f"費用申請番号: {self.application_number}\n目的: {self.purpose or 'N/A'}",
            case_id=self.case_id,
            contract_id=self.contract_id,
            personnel_id=self.personnel_id,
        )

        # 関連付け
        self.finance_transaction_id = finance_transaction.id
        await self.save()

        return finance_transaction

    async def mark_as_paid(self, payment_date: date = None):
        """支払完了をマーク"""
        if not self.is_approved:
            raise ValueError("承認済みの申請のみ支払完了可能です")

        self.status = ApplicationStatus.PAID
        self.actual_payment_date = payment_date or date.today()
        await self.save()

        # 関連する財務取引も更新
        if self.finance_transaction_id:
            finance_transaction = await FinanceTransaction.get_or_none(id=self.finance_transaction_id)
            if finance_transaction:
                finance_transaction.status = FinanceStatus.COMPLETED
                finance_transaction.payment_date = self.actual_payment_date
                await finance_transaction.save()


class ExpenseApprovalHistory(BaseModel, TimestampMixin):
    """
    費用申請承認履歴
    申請の承認プロセスを記録
    """

    application = fields.ForeignKeyField("models.ExpenseApplication", related_name="approval_history", description="対象申請")

    # アクション情報
    action = fields.CharField(max_length=50, description="アクション")  # submit, approve, reject, cancel等
    actor = fields.CharField(max_length=100, description="実行者")
    action_date = fields.DatetimeField(description="実行日時")

    # 詳細情報
    notes = fields.TextField(null=True, description="備考・理由")
    previous_status = fields.CharField(max_length=50, null=True, description="変更前ステータス")
    new_status = fields.CharField(max_length=50, null=True, description="変更後ステータス")

    # システム情報
    ip_address = fields.CharField(max_length=45, null=True, description="IPアドレス")
    user_agent = fields.TextField(null=True, description="ユーザーエージェント")

    class Meta:
        table = "expense_approval_history"
        table_description = "費用申請承認履歴"
        indexes = [
            ("application_id", "action_date"),
            ("actor", "action_date"),
        ]

    def __str__(self):
        return f"{self.application.application_number} - {self.action} by {self.actor}"


# Signal handlers
@post_save(FinanceTransaction)
async def transaction_post_save(sender, instance, created, using_db, update_fields):
    """取引保存後の処理"""
    if instance.status == FinanceStatus.COMPLETED and instance.approval_status == FinanceApprovalStatus.APPROVED:
        # 関連する予算の使用済み金額を更新
        if instance.payment_date and instance.is_expense:
            budgets = await FinanceBudget.filter(
                category=instance.category,
                period_start__lte=instance.payment_date,
                period_end__gte=instance.payment_date,
                is_active=True
            ).all()

            for budget in budgets:
                await budget.update_spent_amount()


@post_save(ExpenseApplication)
async def expense_application_post_save(sender, instance, created, using_db, update_fields):
    """費用申請保存後の処理"""
    # 申請番号の自動生成
    if created and not instance.application_number:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        instance.application_number = f"EXP-{timestamp}-{instance.id:04d}"
        await instance.save()