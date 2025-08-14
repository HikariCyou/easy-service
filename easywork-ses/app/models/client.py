from tortoise import fields

from app.models.base import BaseModel, TimestampMixin


class ClientCompany(BaseModel, TimestampMixin):
    """
    SES案件の取り先会社（顧客）
    """

    company_name = fields.CharField(max_length=255, description="取り先会社名")
    company_name_kana = fields.CharField(max_length=255, null=True, description="取り先会社名（フリーカナ）")
    # 代表者
    representative = fields.CharField(max_length=255, null=True, description="代表者名")
    # 資本金
    capital = fields.CharField(max_length=50, null=True, description="資本金")
    # 設立月日
    established_date = fields.DateField(null=True, description="設立月日")

    zip_code = fields.DateField(null=True, description="郵便番号")
    # 住所
    address = fields.CharField(max_length=255, null=True, description="住所")
    # 電話番号
    phone = fields.CharField(max_length=50, null=True, description="電話番号")
    email = fields.CharField(max_length=100, null=True, description="メール")
    website = fields.CharField(max_length=255, null=True, description="Webサイト")
    remark = fields.TextField(null=True, description="備考")

    cases: fields.ReverseRelation["Case"]
    contacts: fields.ReverseRelation["ClientContact"]

    class Meta:
        table = "ses_client_company"
        table_description = "SES案件の取り先会社"


class ClientContact(BaseModel, TimestampMixin):
    """
    顧客会社の担当者情報
    """

    client_company = fields.ForeignKeyField("models.ClientCompany", related_name="contacts", description="所属会社")
    name = fields.CharField(max_length=100, description="担当者名")
    name_kana = fields.CharField(max_length=100, null=True, description="担当者名（フリーカナ）")
    department = fields.CharField(max_length=100, null=True, description="部署")
    position = fields.CharField(max_length=100, null=True, description="役職")
    phone = fields.CharField(max_length=50, null=True, description="電話番号")
    email = fields.CharField(max_length=100, null=True, description="メール")
    is_primary = fields.BooleanField(default=False, description="主担当者かどうか")
    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "ses_client_contact"
        table_description = "顧客会社担当者"
