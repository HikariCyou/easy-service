from typing import Optional

from pydantic import BaseModel, Field


class BankSchema(BaseModel):
    id: int = Field(..., description="銀行ID")
    code: str = Field(..., description="銀行コード")
    name: str = Field(..., description="銀行名")
    name_kana: Optional[str] = Field(None, description="銀行名カナ")


class BankBranchSchema(BaseModel):
    id: int = Field(..., description="支店ID")
    code: str = Field(..., description="支店コード")
    name: str = Field(..., description="支店名")
    name_kana: Optional[str] = Field(None, description="支店名カナ")
    bank_code: Optional[str] = Field(None, description="銀行コード")
    bank_name: Optional[str] = Field(None, description="銀行名")


class AddBankAccountSchema(BaseModel):
    bp_company_id: int = Field(..., description="BP会社ID")
    bank_id: int = Field(..., description="銀行ID")
    branch_id: int = Field(..., description="支店ID")
    account_type: str = Field("普通", description="口座種別（普通/当座）")
    account_number: str = Field(..., description="口座番号")
    account_holder: str = Field(..., description="口座名義")
    account_holder_kana: Optional[str] = Field(None, description="口座名義カナ")
    is_default: bool = Field(False, description="デフォルト口座")
    copy_url: Optional[list[str]] = Field(None, description="口座写しURLリスト")
    remark: Optional[str] = Field(None, description="備考")


class UpdateBankAccountSchema(BaseModel):
    id: int = Field(..., description="口座ID")
    bp_company_id: Optional[int] = Field(None, description="BP会社ID")
    bank_id: Optional[int] = Field(None, description="銀行ID")
    branch_id: Optional[int] = Field(None, description="支店ID")
    account_type: Optional[str] = Field(None, description="口座種別（普通/当座）")
    account_number: Optional[str] = Field(None, description="口座番号")
    account_holder: Optional[str] = Field(None, description="口座名義")
    account_holder_kana: Optional[str] = Field(None, description="口座名義カナ")
    is_default: Optional[bool] = Field(None, description="デフォルト口座")
    is_active: Optional[bool] = Field(None, description="有効フラグ")
    copy_url: Optional[list[str]] = Field(None, description="口座写しURLリスト")
    remark: Optional[str] = Field(None, description="備考")


class BankAccountResponseSchema(BaseModel):
    id: int = Field(..., description="口座ID")
    bp_company_id: int = Field(..., description="BP会社ID")
    bp_company_name: Optional[str] = Field(None, description="BP会社名")
    bank_id: int = Field(..., description="銀行ID")
    bank_code: str = Field(..., description="銀行コード")
    bank_name: str = Field(..., description="銀行名")
    branch_id: int = Field(..., description="支店ID")
    branch_code: str = Field(..., description="支店コード")
    branch_name: str = Field(..., description="支店名")
    account_type: str = Field(..., description="口座種別")
    account_number: str = Field(..., description="口座番号")
    account_holder: str = Field(..., description="口座名義")
    account_holder_kana: Optional[str] = Field(None, description="口座名義カナ")
    is_default: bool = Field(..., description="デフォルト口座")
    is_active: bool = Field(..., description="有効フラグ")
    remark: Optional[str] = Field(None, description="備考")


class BankSyncResultSchema(BaseModel):
    banks: int = Field(..., description="同期した銀行数")
    branches: Optional[int] = Field(None, description="同期した支店数")