from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import (PersonType, EmploymentStatus, MarriageStatus, 
                              ResidenceStatus, JapaneseLevel, EmployeeType, 
                              SalaryPaymentType, DecimalProcessingType, 
                              HeadOfHouseholdRelationship, DocumentType)


class Personnel(BaseModel, TimestampMixin):
    """
    統一要員基礎表 - 所有人員的共同信息
    包含：BP員工、自社員工、自由職業者
    """
    
    # === 系統關聯 ===
    user_id = fields.BigIntField(null=True, index=True, description="関連システムアカウントID (ログイン・勤怠用)")
    person_type = fields.CharEnumField(PersonType, default=PersonType.EMPLOYEE, description="人員類型")
    code = fields.CharField(max_length=50, null=True, unique=True, description="要員番号")
    
    # === 基本情報 ===
    name = fields.CharField(max_length=100, description="氏名")
    free_kana_name = fields.CharField(max_length=100, null=True, description="氏名（カタカナ）")
    age = fields.IntField(null=True, description="年齢")
    sex = fields.IntField(null=True, default=0, description="性別 (0:男, 1:女)")
    birthday = fields.DateField(null=True, description="生年月日")
    station = fields.CharField(max_length=255, null=True, description="最寄駅")
    marriage_status = fields.CharEnumField(
        MarriageStatus, null=True, default=MarriageStatus.SINGLE, description="婚姻状況"
    )
    
    # === 連絡先 ===
    phone = fields.CharField(max_length=50, null=True, description="电话号码")
    email = fields.CharField(max_length=100, null=True, description="邮箱")
    emergency_contact_name = fields.CharField(max_length=100, null=True, description="紧急联系人姓名")
    emergency_contact_phone = fields.CharField(max_length=50, null=True, description="紧急联系人电话")
    emergency_contact_relation = fields.CharField(max_length=50, null=True, description="紧急联系人关系")
    
    # === 地址信息 ===
    zip_code = fields.CharField(max_length=10, null=True, description="邮政编码")
    address = fields.CharField(max_length=255, null=True, description="住址")
    work_address = fields.CharField(max_length=255, null=True, description="工作地址")
    
    # === 外国人对应 ===
    nationality = fields.CharField(max_length=50, null=True, description="国籍")
    visa_status = fields.CharEnumField(ResidenceStatus, null=True, description="在留資格")
    visa_expire_date = fields.DateField(null=True, description="在留期限")
    japanese_level = fields.CharEnumField(JapaneseLevel, null=True, description="日语水平")
    
    # === 技能・经验 ===
    total_experience_years = fields.FloatField(null=True, description="总经验年数")
    it_experience_years = fields.FloatField(null=True, description="IT经验年数")
    education_level = fields.CharField(max_length=100, null=True, description="最终学历")
    major = fields.CharField(max_length=100, null=True, description="专业")
    certifications = fields.TextField(null=True, description="持有资格（换行分割）")
    
    # === 单价・稼働 ===
    standard_unit_price = fields.FloatField(null=True, description="标准单价（月额）")
    min_unit_price = fields.FloatField(null=True, description="最低承接单价")
    max_unit_price = fields.FloatField(null=True, description="最高承接单价")
    hourly_rate = fields.FloatField(null=True, description="时间单价")
    
    # === 稼働状况 ===
    employment_status = fields.CharEnumField(
        EmploymentStatus, default=EmploymentStatus.AVAILABLE, description="稼働状態"
    )
    is_active = fields.BooleanField(default=True, description="是否有效")
    available_start_date = fields.DateField(null=True, description="可稼働开始日")
    current_project_end_date = fields.DateField(null=True, description="当前项目结束预定日")
    
    # === 希望条件 ===
    preferred_location = fields.CharField(max_length=255, null=True, description="希望工作地")
    remote_work_available = fields.BooleanField(default=False, description="远程工作可能")
    overtime_available = fields.BooleanField(default=False, description="加班可能")
    
    # === 其他 ===
    photo_url = fields.CharField(max_length=500, null=True, description="照片URL")
    resume_url = fields.CharField(max_length=500, null=True, description="简历URL")
    portfolio_url = fields.CharField(max_length=500, null=True, description="作品集URL")
    website_url = fields.CharField(max_length=500, null=True, description="个人网站URL")
    remark = fields.TextField(null=True, description="备注")

    process_instance_id = fields.CharField(max_length=255, null=True, description="工作流实例ID")
    
    # === 关联 ===
    # 特化信息（根据person_type）
    employee_detail: fields.ReverseRelation["EmployeeDetail"]
    
    # HR关联
    employee_addresses: fields.ReverseRelation["EmployeeAddress"]
    resident_addresses: fields.ReverseRelation["EmployeeResidentAddress"]
    emergency_contacts: fields.ReverseRelation["EmployeeEmergencyContact"]
    bank_accounts: fields.ReverseRelation["EmployeeBankAccount"]
    residence_statuses: fields.ReverseRelation["EmployeeResidenceStatus"]
    passports: fields.ReverseRelation["EmployeePassport"]
    social_insurance: fields.ReverseRelation["EmployeeSocialInsurance"]
    employment_insurance: fields.ReverseRelation["EmployeeEmploymentInsurance"]
    salaries: fields.ReverseRelation["EmployeeSalaryRecord"]
    documents: fields.ReverseRelation["EmployeeDocument"]
    histories: fields.ReverseRelation["EmployeeHistory"]

    class Meta:
        table = "ses_personnel"
        table_description = "要員管理"
        indexes = [
            ("user_id",),
            ("person_type",),
            ("employment_status",),
            ("nationality", "visa_status"),
            ("available_start_date",),
            ("standard_unit_price",),
            ("is_active", "person_type"),
        ]

    @property
    def current_age(self) -> int:
        if not self.birthday:
            return self.age or 0

        from datetime import date
        today = date.today()
        return today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))

    def is_visa_expiring_soon(self, days: int = 90) -> bool:
        if not self.visa_expire_date:
            return False

        from datetime import date, timedelta
        return self.visa_expire_date <= date.today() + timedelta(days=days)

    async def get_detail(self):
        if self.person_type == PersonType.EMPLOYEE:
            return await self.employee_detail.first()
        # 如果需要支持其他类型，可以在这里添加
        return None


# 为了兼容性，保留Employee别名
Employee = Personnel


class EmployeeDetail(BaseModel, TimestampMixin):
    """自社员工特化信息"""
    
    personnel = fields.OneToOneField(
        "models.Personnel", related_name="employee_detail", description="关联要员"
    )
    
    # === HR系统关联 ===
    joining_time = fields.DateField(null=True, description="入社时间")
    
    # === 职位信息 ===
    position = fields.CharField(max_length=255, null=True, description="职位")
    employment_type = fields.CharField(
        max_length=255, null=True, default=EmployeeType.CONTRACT.value, description="雇用形态"
    )
    business_content = fields.CharField(max_length=255, null=True, description="业务内容")
    
    # === 给与关联 ===
    salary_payment_type = fields.CharEnumField(
        SalaryPaymentType, default=SalaryPaymentType.MONTHLY, null=True, description="给与支给形态"
    )
    salary = fields.IntField(default=0, null=True, description="给与额")


    class Meta:
        table = "ses_employee_detail"
        table_description = "自社员工详细信息"


class EmployeeAddress(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="employee_addresses", description="関連した人員")
    is_overseas = fields.BooleanField(default=False, null=True, description="海外住所かどうか")
    postal_code = fields.CharField(max_length=10, description="郵便番号")
    prefecture = fields.CharField(max_length=100, description="住所（都道府県）")
    city = fields.CharField(max_length=100, description="住所（市区町村）")
    street_address = fields.CharField(max_length=255, description="住所（丁目・番地）")
    building_name = fields.CharField(max_length=255, null=True, description="住所（建物名・部屋番号）")
    #住所（ヨミガナ）
    address_kana = fields.CharField(max_length=255, null=True, description="住所（ヨミガナ）")
    # 世帯主の氏名
    head_of_household_name = fields.CharField(max_length=255, null=True, description="世帯主の氏名")
    # 世帯主の続柄
    head_of_household_relationship = fields.CharEnumField(HeadOfHouseholdRelationship,default=HeadOfHouseholdRelationship.HEAD, null=True, description="世帯主の続柄")

    class Meta:
        table = "hr_employee_address"


# 住民票住所
class EmployeeResidentAddress(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="resident_addresses", description="関連した人員")
    postal_code = fields.CharField(max_length=10, description="郵便番号")
    prefecture = fields.CharField(max_length=100, description="住所（都道府県）")
    city = fields.CharField(max_length=100, description="住所（市区町村）")
    street_address = fields.CharField(max_length=255, description="住所（丁目・番地）")
    building_name = fields.CharField(max_length=255, null=True, description="住所（建物名・部屋番号）")
    # 住所（ヨミガナ）
    address_kana = fields.CharField(max_length=255, null=True, description="住所（ヨミガナ）")

    # 世帯主の氏名
    head_of_household_name = fields.CharField(max_length=255, null=True, description="世帯主の氏名")
    # 世帯主の続柄
    head_of_household_relationship = fields.CharEnumField(HeadOfHouseholdRelationship,default=HeadOfHouseholdRelationship.HEAD, null=True, description="世帯主の続柄")

    class Meta:
        table = "hr_employee_resident_address"

# 緊急連絡先
class EmployeeEmergencyContact(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="emergency_contacts", description="関連した人員")
    name = fields.CharField(max_length=255, description="緊急連絡先の氏名")
    name_kana = fields.CharField(max_length=255, null=True, description="緊急連絡先の氏名（ヨミガナ）")
    relationship = fields.CharField(max_length=100, description="続柄")
    phone_number = fields.CharField(max_length=15, description="電話番号")
    email = fields.CharField(max_length=255, null=True, description="メールアドレス")

    class Meta:
        table = "hr_employee_emergency_contact"



# 口座情報
class EmployeeBankAccount(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="bank_accounts", description="関連した人員")
    bank_name = fields.CharField(max_length=255, description="銀行名")
    branch_name = fields.CharField(max_length=255, description="支店名")
    account_type = fields.CharField(max_length=50, description="口座種別（普通、当座など）")
    account_number = fields.CharField(max_length=20, description="口座番号")
    account_holder_name = fields.CharField(max_length=255, description="口座名義人名")
    bank_images = fields.JSONField(null=True, description="銀行口座の画像URLリスト")

    class Meta:
        table = "hr_employee_bank_account"


#　在留資格
class EmployeeResidenceStatus(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="residence_statuses", description="関連した人員")
    status = fields.CharEnumField(ResidenceStatus, default=ResidenceStatus.ENGINEERING_HUMANITIES_INTERNATIONAL, description="在留資格の種類")
    # 在留カード番号
    residence_card_number = fields.CharField(max_length=50, null=True, description="在留カード番号")
    # 在留資格の有効期限
    expiration_date = fields.DateField(null=True, description="在留資格の有効期限")
    # 資格外活動許可の有無
    permission_for_activities = fields.BooleanField(default=False, null=True, description="資格外活動許可の有無")
    # 在留カードの画像URLリスト
    card_images = fields.JSONField(null=True, description="在留カードの画像URLリスト")

    class Meta:
        table = "hr_employee_residence_status"

# パスポート旅券
class EmployeePassport(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="passports", description="関連した人員")
    passport_number = fields.CharField(max_length=50, description="パスポート番号")
    expiration_date = fields.DateField(description="パスポートの有効期限")
    country_of_issue = fields.CharField(max_length=100, description="発行国")
    passport_images = fields.JSONField(null=True, description="パスポートの画像URLリスト")

    class Meta:
        table = "hr_employee_passport"


# 社会保険
class EmployeeSocialInsurance(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="social_insurance", description="人員")
    pension_basic_number = fields.CharField(max_length=20, null=True, description="基礎年金番号")
    pension_number_reason = fields.CharField(max_length=100, null=True, description="基礎年金番号が不明な場合の理由")
    first_join_pension = fields.BooleanField(default=False, description="はじめて厚生年金に加入するか")
    pension_images = fields.JSONField(null=True, description="基礎年金番号を確認できる画像URLリスト")
    qualification_acquisition_date = fields.DateField(null=True, description="社会保険の資格取得年月日")
    health_insurance_number = fields.CharField(max_length=50, null=True, description="健康保険番号")
    health_insurance_qualification_date = fields.DateField(null=True, description="健康保険の資格取得年月日")
    health_insurance_number_reason = fields.CharField(max_length=50, null=True, description="健康保険番号が不明な場合の理由")
    health_insurance_images = fields.JSONField(null=True, description="健康保険番号を確認できる画像URLリスト")

    class Meta:
        table = "hr_employee_social_insurance"


# 雇用保険
class EmployeeEmploymentInsurance(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="employment_insurance", description="人員")
    employment_insurance_number = fields.CharField(max_length=50, null=True, description="雇用保険の被保険者番号")
    employment_number_reason = fields.CharField(max_length=100, null=True,
                                                description="雇用保険の被保険者番号がない場合の理由")
    employment_images = fields.JSONField(null=True, description="雇用保険の被保険者番号を確認できる画像URLリスト")
    employment_qualification_date = fields.DateField(null=True, description="雇用保険の資格取得年月日")

    # 資格取得区分
    qualification_type = fields.CharField(max_length=50, null=True, description="資格取得区分")
    # 被保険者となったことの原因
    insured_reason = fields.CharField(max_length=100, null=True, description="被保険者となったことの原因")

    class Meta:
        table = "hr_employee_employment_insurance"


# 給与改定記録
class EmployeeSalaryRecord(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="salaries", description="関連した人員")
    basic_salary = fields.DecimalField(max_digits=12, decimal_places=2, description="基本給")

    class Meta:
        table = "hr_employee_salary_record"


class EmployeeDocument(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="documents")
    file_url = fields.CharField(max_length=255, description="書類のファイルURL")
    document_type = fields.CharEnumField(DocumentType, default=DocumentType.OTHER,null=True, description="書類の種類")

    class Meta:
        table = "hr_employee_document"



class EmployeeHistory(BaseModel, TimestampMixin):
    personnel = fields.ForeignKeyField("models.Personnel", related_name="histories")
    model_name = fields.CharField(max_length=100)  # 例えば "EmployeeBankAccount"
    data = fields.JSONField()
    version = fields.IntField()
    changed_by = fields.BigIntField(null=True)

    class Meta:
        table = "hr_employee_history"
