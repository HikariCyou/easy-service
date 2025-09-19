from tortoise import fields

from app.models.base import BaseModel, TimestampMixin


class Bank(BaseModel, TimestampMixin):
    """
    銀行情報
    """

    code = fields.CharField(max_length=10, unique=True, description="銀行コード")
    name = fields.CharField(max_length=100, description="銀行名")
    name_kana = fields.CharField(max_length=100, null=True, description="銀行名カナ")

    # 関連
    branches: fields.ReverseRelation["BankBranch"]

    class Meta:
        table = "bank"
        table_description = "銀行情報"


class BankBranch(BaseModel, TimestampMixin):
    """
    銀行支店情報
    """

    bank = fields.ForeignKeyField("models.Bank", related_name="branches", description="所属銀行")
    code = fields.CharField(max_length=10, description="支店コード")
    name = fields.CharField(max_length=100, description="支店名")
    name_kana = fields.CharField(max_length=100, null=True, description="支店名カナ")

    # 関連
    accounts: fields.ReverseRelation["BankAccount"]

    class Meta:
        table = "bank_branch"
        table_description = "銀行支店情報"
        unique_together = (("bank", "code"),)


class BankAccount(BaseModel, TimestampMixin):
    """
    銀行口座情報
    """

    # 銀行情報
    bank = fields.ForeignKeyField("models.Bank", related_name="accounts", description="銀行")
    branch = fields.ForeignKeyField("models.BankBranch", related_name="accounts", description="支店")

    # 口座情報
    account_type = fields.CharField(max_length=20, default="普通", description="口座種別（普通/当座）")
    account_number = fields.CharField(max_length=20, description="口座番号")
    account_holder = fields.CharField(max_length=100, description="口座名義")
    account_holder_kana = fields.CharField(max_length=100, null=True, description="口座名義カナ")

    # 関連情報
    bp_company = fields.ForeignKeyField("models.BPCompany", related_name="bank_accounts", description="所属BP会社")
    is_default = fields.BooleanField(default=False, description="デフォルト口座")
    is_active = fields.BooleanField(default=True, description="有効フラグ")

    # 写し
    copy_url = fields.JSONField(null=True, description="口座写しURL")

    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "bp_bank_account"
        table_description = "BP会社銀行口座情報"
        indexes = [
            ("bp_company", "is_default"),
            ("bank", "branch"),
        ]

    def __str__(self):
        return f"{self.bank.name} {self.branch.name} {self.account_number} ({self.bp_company.name})"


class ClientBankAccount(BaseModel, TimestampMixin):
    """
    顧客会社銀行口座情報
    """

    # 銀行情報
    bank = fields.ForeignKeyField("models.Bank", related_name="client_accounts", description="銀行")
    branch = fields.ForeignKeyField("models.BankBranch", related_name="client_accounts", description="支店")

    # 口座情報
    account_type = fields.CharField(max_length=20, default="普通", description="口座種別（普通/当座）")
    account_number = fields.CharField(max_length=20, description="口座番号")
    account_holder = fields.CharField(max_length=100, description="口座名義")
    account_holder_kana = fields.CharField(max_length=100, null=True, description="口座名義カナ")

    # 関連情報
    client_company = fields.ForeignKeyField("models.ClientCompany", related_name="bank_accounts", description="所属顧客会社")
    is_default = fields.BooleanField(default=False, description="デフォルト口座")
    is_active = fields.BooleanField(default=True, description="有効フラグ")

    # 写し
    copy_url = fields.JSONField(null=True, description="口座写しURL")

    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "client_bank_account"
        table_description = "顧客会社銀行口座情報"
        indexes = [
            ("client_company", "is_default"),
            ("bank", "branch"),
        ]

    def __str__(self):
        return f"{self.bank.name} {self.branch.name} {self.account_number} ({self.client_company.company_name})"
