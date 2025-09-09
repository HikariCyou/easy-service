from datetime import date
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.enums import SESContractForm


class ContractDocumentSchema(BaseModel):
    file_name: str = Field(..., description="ファイル名")
    file_path: str = Field(..., description="ファイルパス")
    file_size: Optional[int] = Field(None, description="ファイルサイズ")
    upload_date: Optional[str] = Field(None, description="アップロード日時")


class AddClientCompanySchema(BaseModel):
    company_name: str = Field(..., description="取り先会社名")
    company_name_kana: Optional[str] = Field(None, description="取り先会社名（フリーカナ）")
    representative: Optional[str] = Field(None, description="代表者名")
    capital: Optional[str] = Field(None, description="資本金")
    established_date: Optional[date] = Field(None, description="設立月日")
    zip_code: Optional[str] = Field(None, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, description="電話番号")
    email: Optional[str] = Field(None, description="メール")
    website: Optional[str] = Field(None, description="Webサイト")
    attendance_calc_type: Optional[int] = Field(15, description="出勤計算区分（分単位）")
    decimal_processing_type: Optional[str] = Field("round", description="小数処理区分")
    remark: Optional[str] = Field(None, description="備考")


class UpdateClientCompanySchema(BaseModel):
    id: int = Field(..., description="取り先会社ID")
    company_name: Optional[str] = Field(None, description="取り先会社名")
    company_name_kana: Optional[str] = Field(None, description="取り先会社名（フリーカナ）")
    representative: Optional[str] = Field(None, description="代表者名")
    capital: Optional[str] = Field(None, description="資本金")
    established_date: Optional[date] = Field(None, description="設立月日")
    zip_code: Optional[str] = Field(None, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, description="電話番号")
    email: Optional[str] = Field(None, description="メール")
    website: Optional[str] = Field(None, description="Webサイト")
    attendance_calc_type: Optional[int] = Field(None, description="出勤計算区分（分単位）")
    decimal_processing_type: Optional[str] = Field(None, description="小数処理区分")
    remark: Optional[str] = Field(None, description="備考")




# === 銀行口座関連 ===

class AddClientBankAccountSchema(BaseModel):
    client_company_id: int = Field(..., description="所属顧客会社ID")
    bank_id: int = Field(..., description="銀行ID")
    branch_id: int = Field(..., description="支店ID")
    account_type: Optional[str] = Field("普通", description="口座種別（普通/当座）")
    account_number: str = Field(..., description="口座番号")
    account_holder: str = Field(..., description="口座名義")
    account_holder_kana: Optional[str] = Field(None, description="口座名義カナ")
    is_default: bool = Field(False, description="デフォルト口座")
    copy_url: Optional[List[str]] = Field(None, description="口座写しURL")
    remark: Optional[str] = Field(None, description="備考")


class UpdateClientBankAccountSchema(BaseModel):
    id: int = Field(..., description="口座ID")
    client_company_id: Optional[int] = Field(None, description="所属顧客会社ID")
    bank_id: Optional[int] = Field(None, description="銀行ID")
    branch_id: Optional[int] = Field(None, description="支店ID")
    account_type: Optional[str] = Field(None, description="口座種別（普通/当座）")
    account_number: Optional[str] = Field(None, description="口座番号")
    account_holder: Optional[str] = Field(None, description="口座名義")
    account_holder_kana: Optional[str] = Field(None, description="口座名義カナ")
    is_default: Optional[bool] = Field(None, description="デフォルト口座")
    is_active: Optional[bool] = Field(None, description="有効フラグ")
    copy_url: Optional[List[str]] = Field(None, description="口座写しURL")
    remark: Optional[str] = Field(None, description="備考")


# === 契約関連 ===

class AddClientCompanyContractSchema(BaseModel):
    client_company_id: int = Field(..., description="契約先顧客会社ID")
    contract_number: str = Field(..., description="契約書番号")
    contract_name: str = Field(..., description="契約名称")
    contract_form: SESContractForm = Field(..., description="SES契約形態")
    contract_start_date: date = Field(..., description="契約開始日")
    contract_end_date: Optional[date] = Field(None, description="契約終了日")
    status: Optional[str] = Field("active", description="契約ステータス")
    contract_documents: Optional[List[ContractDocumentSchema]] = Field([], description="契約書類ファイル情報")
    remark: Optional[str] = Field(None, description="備考")


class UpdateClientCompanyContractSchema(BaseModel):
    id: int = Field(..., description="契約ID")
    client_company_id: Optional[int] = Field(None, description="契約先顧客会社ID")
    contract_number: Optional[str] = Field(None, description="契約書番号")
    contract_name: Optional[str] = Field(None, description="契約名称")
    contract_form: Optional[SESContractForm] = Field(None, description="SES契約形態")
    contract_start_date: Optional[date] = Field(None, description="契約開始日")
    contract_end_date: Optional[date] = Field(None, description="契約終了日")
    status: Optional[str] = Field(None, description="契約ステータス")
    contract_documents: Optional[List[ContractDocumentSchema]] = Field(None, description="契約書類ファイル情報")
    remark: Optional[str] = Field(None, description="備考")