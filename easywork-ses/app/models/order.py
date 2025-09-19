from datetime import datetime

from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import ApproveStatus, ContractItemType, OrderStatus


class Order(BaseModel, TimestampMixin):
    """
    注文書管理 - SES業務における月次注文書管理

    注文書は自社からBP会社に対して月度で発行する業務委託の注文書

    データの取得元：
    - BP会社: personnel.bp_employee_detail.bp_company
    - 要员名称: personnel.name
    - 案件名称: case.title
    - 契約詳細: contract (契約期間、工時、単価等)
    - 担当営業: case.company_sales_representative (自社営業)
    - 基本給: contract.calculation_items (BASIC_SALARY)
    """

    # 基本情報
    order_number = fields.CharField(max_length=50, unique=True, description="注文番号")
    year_month = fields.CharField(max_length=7, description="対象年月（YYYY-MM）")

    # 関連エンティティ（これらから必要な情報を全て取得）
    personnel = fields.ForeignKeyField("models.Personnel", related_name="orders", description="対象要員")
    case = fields.ForeignKeyField("models.Case", related_name="orders", description="案件")
    contract = fields.ForeignKeyField("models.Contract", related_name="orders", description="契約")

    # 文書管理
    order_document_url = fields.CharField(max_length=500, null=True, description="注文書PDF URL")
    order_request_url = fields.CharField(max_length=500, null=True, description="注文請書PDF URL")

    # ステータス管理
    status = fields.CharEnumField(OrderStatus, default=OrderStatus.DRAFT, description="ステータス")

    # 回収管理
    collected_date = fields.DatetimeField(null=True, description="回収日時")

    # 送信管理
    sent_date = fields.DatetimeField(null=True, description="送信日時")
    sent_by = fields.CharField(max_length=100, null=True, description="送信者")

    # 备考
    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "ses_order"
        table_description = "注文書管理"
        indexes = [
            ("personnel", "year_month"),
            ("status",),
            ("year_month",),
            ("order_number",),
        ]
        # 同一要員同一月不能重复注文书
        unique_together = (("personnel", "year_month"),)

    @property
    def is_sent(self) -> bool:
        """送信済みかどうか"""
        return self.status in [OrderStatus.SENT, OrderStatus.COLLECTED]

    @property
    def is_collected(self) -> bool:
        """回収済みかどうか"""
        return self.status == OrderStatus.COLLECTED

    def get_year_month_display(self) -> str:
        """年月表示用（2024年1月形式）"""
        if not self.year_month:
            return ""
        parts = self.year_month.split("-")
        if len(parts) == 2:
            return f"{parts[0]}年{int(parts[1])}月"
        return self.year_month

    async def mark_as_sent(self, sent_by: str = None):
        """送信済みマーク"""
        self.sent_date = datetime.now()
        self.sent_by = sent_by
        self.status = OrderStatus.SENT
        await self.save()

    async def mark_as_collected(self):
        """回収完了マーク"""
        self.collected_date = datetime.now()
        self.status = OrderStatus.COLLECTED
        await self.save()

    async def get_bp_company(self):
        """BP会社取得"""
        await self.fetch_related("personnel__bp_employee_detail__bp_company")
        personnel = self.personnel
        if personnel and hasattr(personnel, "bp_employee_detail") and personnel.bp_employee_detail:
            return await personnel.bp_employee_detail.bp_company
        return None

    async def get_sales_representative(self):
        """担当営業取得"""
        await self.fetch_related("case__company_sales_representative")
        case = self.case
        return case.company_sales_representative if case else None

    async def get_basic_salary(self) -> float:
        """基本給取得"""
        await self.fetch_related("contract__calculation_items")
        contract = self.contract
        if not contract:
            return 0.0

        basic_salary_item = await contract.calculation_items.filter(
            item_type=ContractItemType.BASIC_SALARY.value, is_active=True
        ).first()

        return float(basic_salary_item.amount) if basic_salary_item else 0.0

    async def get_full_details(self) -> dict:
        """
        注文書作成に必要な全ての詳細情報を取得
        """
        # 関連データを効率的に取得
        await self.fetch_related(
            "personnel__bp_employee_detail__bp_company",
            "case__company_sales_representative",
            "contract__calculation_items",
        )

        personnel = self.personnel
        case = self.case
        contract = self.contract
        bp_company = await self.get_bp_company()
        sales_rep = await self.get_sales_representative()
        basic_salary = await self.get_basic_salary()

        return {
            # 基本情報
            "order_number": self.order_number,
            "year_month": self.year_month,
            "year_month_display": self.get_year_month_display(),
            # 関連情報
            "bp_company_name": bp_company.name if bp_company else "",
            "bp_company_id": bp_company.id,
            "personnel_name": personnel.name if personnel else "",
            "case_title": case.title if case else "",
            "sales_representative_name": sales_rep.name if sales_rep else "",
            # 契約詳細
            "contract_details": {
                "contract_number": contract.contract_number if contract else "",
                "contract_start_date": contract.contract_start_date if contract else None,
                "contract_end_date": contract.contract_end_date if contract else None,
                "basic_salary": basic_salary,
                "standard_working_hours": contract.standard_working_hours if contract else 160.0,
                "min_working_hours": contract.min_working_hours if contract else None,
                "max_working_hours": contract.max_working_hours if contract else None,
            },
            # ステータス情報
            "status": self.status,
            "is_sent": self.is_sent,
            "is_collected": self.is_collected,
            "sent_date": self.sent_date,
            "collected_date": self.collected_date,
            # 文書情報
            "order_document_url": self.order_document_url,
            "order_request_url": self.order_request_url,
            # その他
            "remark": self.remark,
        }

    def __str__(self):
        return f"{self.order_number} ({self.year_month})"


class OrderBatch(BaseModel, TimestampMixin):
    """
    注文書一括処理管理

    月度注文書的一括生成・送信管理
    - 全体一括
    - BP会社別一括
    - 営業担当別一括
    """

    # 基本情報
    batch_number = fields.CharField(max_length=50, unique=True, description="バッチ番号")
    year_month = fields.CharField(max_length=7, description="対象年月")
    batch_type = fields.CharField(max_length=50, description="バッチタイプ")  # "all", "by_bp_company", "by_sales_rep"

    # フィルター条件（タイプに応じて使用）
    filter_bp_company_id = fields.BigIntField(null=True, description="対象BP会社ID")
    filter_sales_rep_id = fields.BigIntField(null=True, description="担当営業ID")

    # 処理状況
    status = fields.CharEnumField(ApproveStatus, default=ApproveStatus.DRAFT, description="バッチステータス")
    total_orders = fields.IntField(default=0, description="総注文書数")
    sent_orders = fields.IntField(default=0, description="送信済み数")

    # 処理者情報
    created_by = fields.CharField(max_length=100, description="作成者")
    processed_date = fields.DatetimeField(null=True, description="処理日時")
    processed_by = fields.CharField(max_length=100, null=True, description="処理者")

    # 備考
    remark = fields.TextField(null=True, description="備考")

    # 関連注文書
    orders = fields.ManyToManyField("models.Order", related_name="batches", description="関連注文書")

    class Meta:
        table = "ses_order_batch"
        table_description = "注文書一括処理"
        indexes = [
            ("year_month", "batch_type"),
            ("status",),
            ("batch_number",),
        ]

    @property
    def completion_rate(self) -> float:
        """完了率"""
        if self.total_orders == 0:
            return 0.0
        return (self.sent_orders / self.total_orders) * 100

    async def update_counts(self):
        """件数更新"""
        orders = await self.orders.all()
        self.total_orders = len(orders)
        self.sent_orders = len([o for o in orders if o.is_sent])
        await self.save()

    async def mark_as_processed(self, processed_by: str):
        """処理完了マーク"""
        self.processed_date = datetime.now()
        self.processed_by = processed_by
        self.status = ApproveStatus.APPROVED
        await self.save()

    def __str__(self):
        return f"{self.batch_number} - {self.year_month} ({self.batch_type})"
