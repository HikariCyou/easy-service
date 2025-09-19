from datetime import datetime

from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import RequestStatus


class Request(BaseModel, TimestampMixin):
    """
    請求書管理 - SES業務における月次請求書管理

    請求書は自社からClient(顧客)に対して月度で発行する業務委託の請求書
    CP会社（Client）から受け取った注文書に基づいて請求書を作成する

    データの取得元：
    - Client会社: case.client_company
    - 案件名称: case.title
    - 契約詳細: contract (契約期間、工時、単価等)
    - 担当営業: case.company_sales_representative (自社営業)
    - 基本給: contract.calculation_items (BASIC_SALARY)
    """

    # 基本情報
    request_number = fields.CharField(max_length=50, unique=True, description="請求番号")
    year_month = fields.CharField(max_length=7, description="対象年月（YYYY-MM）")

    # 関連エンティティ（請求書はClient会社単位で作成）
    client_company = fields.ForeignKeyField("models.ClientCompany", related_name="requests", description="Client会社")

    # 請求金額情報
    request_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="請求金額（税込）")
    calculation_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="精算金額")
    tax_excluded_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="税抜き金額")
    tax_rate = fields.DecimalField(max_digits=5, decimal_places=2, default=10.0, description="税率（%）")

    # 文書管理
    request_document_url = fields.CharField(max_length=500, null=True, description="請求書PDF URL")
    order_document_url = fields.CharField(max_length=500, null=True, description="注文書PDF URL（Client提供）")

    # ステータス管理
    status = fields.CharEnumField(RequestStatus, default=RequestStatus.DRAFT, description="ステータス")

    # 送信管理
    sent_date = fields.DatetimeField(null=True, description="送信日時")
    sent_by = fields.CharField(max_length=100, null=True, description="送信者")

    # 支払い管理
    payment_due_date = fields.DateField(null=True, description="支払期限")
    payment_received_date = fields.DatetimeField(null=True, description="入金確認日時")
    payment_amount = fields.DecimalField(max_digits=12, decimal_places=2, null=True, description="入金金額")

    # 备考
    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "ses_request"
        table_description = "請求書管理"
        indexes = [
            ("client_company_id", "year_month"),
            ("status",),
            ("year_month",),
            ("request_number",),
            ("payment_due_date",),
        ]
        # 同一Client会社同一月不能重复請求書
        unique_together = (("client_company_id", "year_month"),)

    @property
    def is_sent(self) -> bool:
        """送信済みかどうか"""
        return self.status in [RequestStatus.SENT, RequestStatus.PAID]

    @property
    def is_paid(self) -> bool:
        """支払済みかどうか"""
        return self.status == RequestStatus.PAID

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
        self.status = RequestStatus.SENT
        await self.save()

    async def mark_as_paid(self, payment_amount: float = None):
        """支払完了マーク"""
        self.payment_received_date = datetime.now()
        if payment_amount:
            self.payment_amount = payment_amount
        self.status = RequestStatus.PAID
        await self.save()

    async def get_client_company(self):
        """Client会社取得"""
        await self.fetch_related("client_company")
        return self.client_company

    async def get_sales_representative(self):
        """担当営業取得"""
        # 取得第一个明细项目的案件担当営業
        items = await self.items.all().limit(1).prefetch_related("case__company_sales_representative")
        if items:
            case = items[0].case
            return case.company_sales_representative if case else None
        return None

    async def get_basic_salary(self) -> float:
        """基本給取得（所有明细项目的合计）"""
        items = await self.items.all()
        total_amount = sum(float(item.item_amount) for item in items)
        return total_amount

    async def get_full_details(self) -> dict:
        """
        請求書作成に必要な全ての詳細情報を取得（新しい多要員対応版）
        """
        # 関連データを効率的に取得
        await self.fetch_related("client_company")
        client_company = self.client_company
        sales_rep = await self.get_sales_representative()
        basic_salary = await self.get_basic_salary()

        # 明細項目取得
        items = await self.items.all().prefetch_related("personnel", "case", "contract")

        # 明細項目情報を構築
        item_details = []
        case_titles = []
        personnel_names = []

        for item in items:
            if item.case and item.case.title:
                case_titles.append(item.case.title)
            if item.personnel and item.personnel.name:
                personnel_names.append(item.personnel.name)

            item_details.append({
                "id": item.id,
                "personnel_name": item.personnel.name if item.personnel else "",
                "case_title": item.case.title if item.case else "",
                "item_amount": float(item.item_amount) * 10000,
                "work_hours": float(item.work_hours),
                "unit_price": float(item.unit_price) * 10000,
                "item_remark": item.item_remark or "",
                # 合約情報追加
                "contract_id": item.contract.id if item.contract else None,
                "contract_number": item.contract.contract_number if item.contract else "",
                "contract_start_date": item.contract.contract_start_date if item.contract else None,
                "contract_end_date": item.contract.contract_end_date if item.contract else None,
                "standard_working_hours": float(item.contract.standard_working_hours) if item.contract and item.contract.standard_working_hours else 160.0,
            })

        return {
            # 基本情報
            "request_number": self.request_number,
            "year_month": self.year_month,
            "year_month_display": self.get_year_month_display(),
            # 関連情報
            "client_company_name": client_company.company_name if client_company else "",
            "client_company_id": client_company.id if client_company else None,
            "case_title": ", ".join(case_titles) if case_titles else "",  # 複数案件の場合は結合
            "case_id": None,  # 複数案件なので特定のIDは返さない
            "sales_representative_name": sales_rep.name if sales_rep else "",
            "personnel_name": ", ".join(personnel_names) if personnel_names else "",  # 複数要員の場合は結合
            # 金額詳細（万元转为元显示）
            "request_amount": float(self.request_amount) * 10000,
            "calculation_amount": float(self.calculation_amount) * 10000,
            "tax_excluded_amount": float(self.tax_excluded_amount) * 10000,
            "tax_rate": float(self.tax_rate),
            "basic_salary": basic_salary * 10000,
            # 明細項目
            "items": item_details,
            # ステータス情報
            "status": self.status,
            "is_sent": self.is_sent,
            "is_paid": self.is_paid,
            "sent_date": self.sent_date,
            "payment_due_date": self.payment_due_date,
            "payment_received_date": self.payment_received_date,
            "payment_amount": float(self.payment_amount) if self.payment_amount else None,
            # 文書情報
            "request_document_url": self.request_document_url,
            "order_document_url": self.order_document_url,
            # その他
            "remark": self.remark,
        }

    def __str__(self):
        return f"{self.request_number} ({self.year_month})"


class RequestItem(BaseModel, TimestampMixin):
    """
    請求書明細項目 - 請求書内の各要員の明細

    一つの請求書に複数の要員明細が含まれる
    """

    # 関連エンティティ
    request = fields.ForeignKeyField("models.Request", related_name="items", description="請求書")
    personnel = fields.ForeignKeyField("models.Personnel", related_name="request_items", description="対象要員")
    case = fields.ForeignKeyField("models.Case", related_name="request_items", description="案件")
    contract = fields.ForeignKeyField("models.Contract", related_name="request_items", description="契約")

    # 明細金額情報
    item_amount = fields.DecimalField(max_digits=12, decimal_places=2, description="明細金額（税抜）")
    work_hours = fields.DecimalField(max_digits=6, decimal_places=1, default=160.0, description="作業時間")
    unit_price = fields.DecimalField(max_digits=10, decimal_places=2, description="単価")

    # 明細備考
    item_remark = fields.CharField(max_length=500, null=True, description="明細備考")

    class Meta:
        table = "request_items"
        unique_together = (("request_id", "personnel_id", "case_id"),)

    def __str__(self):
        return f"RequestItem-{self.request.request_number if self.request else 'Unknown'}-{self.personnel.name if self.personnel else 'Unknown'}"
