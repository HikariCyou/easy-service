from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import DecimalProcessingType


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
    
    # 出勤計算関連
    attendance_calc_type = fields.IntField(default=15, null=True, description="出勤計算区分（分単位）")
    decimal_processing_type = fields.CharEnumField(
        DecimalProcessingType, default=DecimalProcessingType.ROUND, null=True, description="小数処理区分"
    )
    
    remark = fields.TextField(null=True, description="備考")

    cases: fields.ReverseRelation["Case"]
    contacts: fields.ReverseRelation["ClientContact"]

    class Meta:
        table = "ses_client_company"
        table_description = "SES案件の取り先会社"


class ClientContact(BaseModel, TimestampMixin):
    """
    取り先会社営業担当者
    取り先会社との商談・営業活動を行う担当者管理
    """

    client_company = fields.ForeignKeyField("models.ClientCompany", related_name="contacts", description="所属会社")
    
    # 基本情報
    name = fields.CharField(max_length=100, description="担当者名")
    name_kana = fields.CharField(max_length=100, null=True, description="担当者名（フリーカナ）")
    gender = fields.IntField(null=True, default=0, description="性別 (0:不明, 1:男, 2:女)")
    
    # 連絡先情報
    phone = fields.CharField(max_length=50, null=True, description="電話番号")
    email = fields.CharField(max_length=100, description="メールアドレス")
    
    # ステータス
    is_primary = fields.BooleanField(default=False, description="主担当者かどうか")
    is_active = fields.BooleanField(default=True, description="有効フラグ")
    
    # 備考
    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "ses_client_contact"
        table_description = "顧客会社担当者（営業担当者）"
        indexes = [
            ("client_company", "is_active"),
            ("email",),
            ("is_primary",),
        ]

    def __str__(self):
        return f"{self.name} ({self.client_company.company_name})"
