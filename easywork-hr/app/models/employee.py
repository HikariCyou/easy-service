from pygments.lexer import default
from tortoise import fields
from app.models.base import BaseModel, TimestampMixin
from app.models.enums import EmployeeType, SalaryPaymentType, HeadOfHouseholdRelationship, DocumentType, ResidenceStatus


class Employee(BaseModel, TimestampMixin):
    user_id = fields.BigIntField(index=True, description="関連したユーザーID")
    code = fields.CharField(max_length=50, null=True, unique=True, description="社員番号")
    joining_time = fields.DateField(null=True,description="入社時間")

    position = fields.CharField(max_length=255, null=True, description="役職")
    # 雇用形態
    employment_type = fields.CharField(max_length=255,null=True, default=EmployeeType.CONTRACT.value,  description="雇用形態")
    # 業務内容
    business_content = fields.CharField(max_length=255, null=True, description="業務内容")
    # 給与支給形態
    salary_payment_type = fields.CharEnumField(SalaryPaymentType, default=SalaryPaymentType.MONTHLY, null=True, description="給与支給形態")
    # 給与額
    salary = fields.IntField(default=0, null=True, description="給与額")

    # activeかどうか
    is_active = fields.BooleanField(default=False, null=True, description="アクティブかどうか")

    process_instance_id = fields.CharField(max_length=255, null=True, description="プロセスインスタンスID")
    class Meta:
        table = "hr_employee"


class EmployeeAddress(BaseModel, TimestampMixin):
    employee = fields.ForeignKeyField("models.Employee", related_name="employee_addresses", description="関連した社員")
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
    employee = fields.ForeignKeyField("models.Employee", related_name="resident_addresses", description="関連した社員")
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
    employee = fields.ForeignKeyField("models.Employee", related_name="emergency_contacts", description="関連した社員")
    name = fields.CharField(max_length=255, description="緊急連絡先の氏名")
    name_kana = fields.CharField(max_length=255, null=True, description="緊急連絡先の氏名（ヨミガナ）")
    relationship = fields.CharField(max_length=100, description="続柄")
    phone_number = fields.CharField(max_length=15, description="電話番号")
    email = fields.CharField(max_length=255, null=True, description="メールアドレス")

    class Meta:
        table = "hr_employee_emergency_contact"



# 口座情報
class EmployeeBankAccount(BaseModel, TimestampMixin):
    employee = fields.ForeignKeyField("models.Employee", related_name="bank_accounts", description="関連した社員")
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
    employee = fields.ForeignKeyField("models.Employee", related_name="residence_statuses", description="関連した社員")
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
    employee = fields.ForeignKeyField("models.Employee", related_name="passports", description="関連した社員")
    passport_number = fields.CharField(max_length=50, description="パスポート番号")
    expiration_date = fields.DateField(description="パスポートの有効期限")
    country_of_issue = fields.CharField(max_length=100, description="発行国")
    passport_images = fields.JSONField(null=True, description="パスポートの画像URLリスト")

    class Meta:
        table = "hr_employee_passport"


# 社会保険
class EmployeeSocialInsurance(BaseModel, TimestampMixin):
    employee = fields.ForeignKeyField("models.Employee", related_name="social_insurance", description="社員")
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
    employee = fields.ForeignKeyField("models.Employee", related_name="employment_insurance", description="社員")
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
    employee = fields.ForeignKeyField("models.Employee", related_name="salaries", description="関連した社員")
    basic_salary = fields.DecimalField(max_digits=12, decimal_places=2, description="基本給")

    class Meta:
        table = "hr_employee_salary_record"


class EmployeeDocument(BaseModel, TimestampMixin):
    employee = fields.ForeignKeyField("models.Employee", related_name="documents")
    file_url = fields.CharField(max_length=255, description="書類のファイルURL")
    document_type = fields.CharEnumField(DocumentType, default=DocumentType.OTHER,null=True, description="書類の種類")

    class Meta:
        table = "hr_employee_document"



class EmployeeHistory(BaseModel, TimestampMixin):
    employee = fields.ForeignKeyField("models.Employee", related_name="histories")
    model_name = fields.CharField(max_length=100)  # 例えば "EmployeeBankAccount"
    data = fields.JSONField()
    version = fields.IntField()
    changed_by = fields.BigIntField(null=True)

    class Meta:
        table = "hr_employee_history"
