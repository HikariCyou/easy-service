from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import DecimalProcessingType, SESContractForm


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
    invoice_number = fields.CharField(max_length=50, null=True, description="インボイス番号")
    
    # 出勤計算関連
    attendance_calc_type = fields.IntField(default=15, null=True, description="出勤計算区分（分単位）")
    decimal_processing_type = fields.CharEnumField(
        DecimalProcessingType, default=DecimalProcessingType.ROUND, null=True, description="小数処理区分"
    )
    
    remark = fields.TextField(null=True, description="備考")

    cases: fields.ReverseRelation["Case"]
    contacts: fields.ReverseRelation["ClientContact"]
    sales_representatives: fields.ReverseRelation["ClientContact"]
    bank_accounts: fields.ReverseRelation["ClientBankAccount"]
    contracts: fields.ReverseRelation["ClientCompanyContract"]

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



class ClientCompanyContract(BaseModel, TimestampMixin):
    """
    顧客会社との基本契約管理
    顧客会社と自社との間の基本業務提携契約
    """
    
    # 契約先顧客会社
    client_company = fields.ForeignKeyField("models.ClientCompany", related_name="contracts", description="契約先顧客会社")
    
    # 契約基本情報
    contract_number = fields.CharField(max_length=50, unique=True, description="契約書番号")
    contract_name = fields.CharField(max_length=200, description="契約名称")
    contract_form = fields.CharEnumField(SESContractForm, description="SES契約形態")
    
    # 契約期間
    contract_start_date = fields.DateField(description="契約開始日")
    contract_end_date = fields.DateField(null=True, description="契約終了日")
    
    # 契約ステータス
    status = fields.CharField(max_length=20, default="active", description="契約ステータス")
    
    # 契約書類管理
    contract_documents = fields.JSONField(default=list, description="契約書類ファイル情報")
    
    # 備考
    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "ses_client_company_contract"
        table_description = "顧客会社基本契約"
        indexes = [
            ("client_company", "status"),
            ("contract_start_date",),
            ("contract_end_date",),
        ]

    def __str__(self):
        return f"{self.contract_name} ({self.client_company.company_name})"

    async def add_contract_document(self, file_name: str, file_path: str, file_size: int = None, upload_date: str = None):
        """契約書類を追加"""
        from datetime import datetime
        
        if upload_date is None:
            upload_date = datetime.now().isoformat()
            
        document = {
            "file_name": file_name,
            "file_path": file_path,
            "file_size": file_size,
            "upload_date": upload_date
        }
        
        if self.contract_documents is None:
            self.contract_documents = []
        
        self.contract_documents.append(document)
        await self.save()
        
    def get_contract_documents(self):
        """契約書類一覧を取得"""
        return self.contract_documents or []
