from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

from app.models import EmployeeType


class EmployeeSchema(BaseModel):
    user_id: Optional[int] = Field(None, description="関連したユーザーID", example=1)
    birthday: str = Field(default=None, description="生年月日", example="1990-01-01")
    code: Optional[str] = Field(None, max_length=20, description="社員番号", example="EMP001")
    joining_time: Optional[str] = Field(None, description="入社時間", example="2020-01-01")
    position: Optional[str] = Field(None, max_length=255, description="役職", example="Software Engineer")
    employment_type: Optional[EmployeeType] = Field(default=EmployeeType.CONTRACT.value, description="雇用形態", example="contract")
    business_content: Optional[str] = Field(None, max_length=255, description="業務内容", example="Software Development")
    salary_payment_type: Optional[str] = Field(None, max_length=50, description="給与支給形態", example="monthly")


class EmployeeUpdateSchema(BaseModel):
    id: Optional[int] = Field(None, description="従業員ID", example=1)
    user_id: Optional[int] = Field(None, description="関連したユーザーID", example=1)
    birthday: str = Field(default=None, description="生年月日", example="1990-01-01")
    code: Optional[str] = Field(None, max_length=20, description="社員番号", example="EMP001")
    joining_time: Optional[str] = Field(None, description="入社時間", example="2020-01-01")
    salary: Optional[int] = Field(default=None, description="給料", examples="100000")
    position: Optional[str] = Field(None, max_length=255, description="役職", example="Software Engineer")
    employment_type: Optional[EmployeeType] = Field(default=EmployeeType.CONTRACT.value, description="雇用形態", example="contract")
    business_content: Optional[str] = Field(None, max_length=255, description="業務内容", example="Software Development")
    salary_payment_type: Optional[str] = Field(None, max_length=50, description="給与支給形態", example="monthly")

class EmployeeAddressSchema(BaseModel):
    employee_id: Optional[int] = Field(None, description="関連した社員のID")
    is_overseas: Optional[bool] = Field(default=False, description="海外住所かどうか")
    postal_code: str = Field(..., max_length=10, description="郵便番号")
    prefecture: str = Field(..., max_length=100, description="住所（都道府県）")
    city: str = Field(..., max_length=100, description="住所（市区町村）")
    street_address: str = Field(..., max_length=255, description="住所（丁目・番地）")
    building_name: Optional[str] = Field(None, max_length=255, description="住所（建物名・部屋番号）")
    address_kana: Optional[str] = Field(None, max_length=255, description="住所（ヨミガナ）")
    head_of_household_name: Optional[str] = Field(None, max_length=255, description="世帯主の氏名")
    head_of_household_relationship: Optional[str] = Field(None, description="世帯主の続柄")

class EmployeeEmergencyContactSchema(BaseModel):
    employee_id: Optional[int] = Field(None, description="関連した社員のID")
    name: str = Field(..., max_length=255, description="緊急連絡先の氏名")
    name_kana: Optional[str] = Field(None, max_length=255, description="緊急連絡先の氏名（ヨミガナ）")
    relationship: str = Field(..., max_length=50, description="緊急連絡先との関係")
    phone_number: str = Field(..., max_length=20, description="緊急連絡先の電話番号")
    email: Optional[str] = Field(None, max_length=255, description="緊急連絡先のメールアドレス")


class EmployeeBankSchema(BaseModel):
    employee_id: Optional[int] = Field(None, description="関連した社員のID")
    bank_name: str = Field(..., max_length=255, description="銀行名")
    branch_name: str = Field(..., max_length=255, description="支店名")
    account_type: str = Field(..., max_length=50, description="口座種別")
    account_number: str = Field(..., max_length=20, description="口座番号")
    account_holder_name: str = Field(..., max_length=255, description="口座名義人の氏名")
    account_holder_kana: Optional[str] = Field(None, max_length=255, description="口座名義人の氏名（ヨミガナ）")
    bank_images: Optional[List[str]] = Field(None, description="銀行口座の画像URLリスト")

# パスポートや旅券
class EmployeePassportSchema(BaseModel):
    employee_id: Optional[int] = Field(None, description="関連した社員のID")
    passport_number: Optional[str] = Field(None, max_length=50, description="パスポート番号")
    expiration_date: Optional[date] = Field(None, description="パスポートの有効期限")
    country_of_issue: Optional[str] = Field(None, max_length=255, description="発行国")
    passport_images: Optional[List[str]] = Field(None, description="パスポートの画像URLリスト")

# 社会保険schema
class EmployeeSocialInsuranceSchema(BaseModel):
    employee_id: Optional[int] = Field(None, description="関連した社員のID")
    pension_basic_number: Optional[str] = Field(None, max_length=50, description="基礎年金番号")
    qualification_acquisition_date: Optional[date] = Field(None, description="社会保険の資格取得年月日")
    pension_number_reason: Optional[str] = Field(None, max_length=50, description="基礎年金番号が不明な場合の理由")
    first_join_pension: Optional[bool] = Field(default=False, description="はじめて厚生年金に加入するか")
    pension_images: Optional[List[str]] = Field(None, description="基礎年金番号を確認できる画像URLリスト")
    health_insurance_number: Optional[str] = Field(None, max_length=50, description="健康保険番号")
    health_insurance_qualification_date: Optional[date] = Field(None, description="健康保険の資格取得年月日")
    health_insurance_number_reason: Optional[str] = Field(None, max_length=50, description="健康保険番号が不明な場合の理由")
    health_insurance_images: Optional[List[str]] = Field(None, description="健康保険番号を確認できる画像URLリスト")

# 雇用保険
class EmployeeEmploymentInsuranceSchema(BaseModel):
    employee_id: Optional[int] = Field(None, description="関連した社員のID")
    employment_insurance_number : Optional[str] = Field(None, max_length=50, description="雇用保険の被保険者番号")
    employment_qualification_date: Optional[date] = Field(None, description="雇用保険の資格取得年月日")
    employment_number_reason: Optional[str] = Field(None, max_length=100, description="雇用保険の被保険者番号がない場合の理由")
    employment_images: Optional[List[str]] = Field(None, description="雇用保険の被保険者番号を確認できる画像URLリスト")
    qualification_type : Optional[str] = Field(None, max_length=50, description="資格取得の種類")
    insured_reason: Optional[str] = Field(None, max_length=50, description="被保険者となったことの原因")

# 在留カード
class EmployeeResidenceStatusSchema(BaseModel):
    employee_id: Optional[int] = Field(None, description="関連した社員のID")
    status: str = Field(..., description="在留資格の種類")
    residence_card_number: Optional[str] = Field(None, max_length=50, description="在留カード番号")
    expiration_date: Optional[date] = Field(None, description="在留資格の有効期限")
    permission_for_activities: Optional[bool] = Field(default=False, description="資格外活動許可の有無")
    card_images: Optional[List[str]] = Field(None, description="在留カードの画像URLリスト")