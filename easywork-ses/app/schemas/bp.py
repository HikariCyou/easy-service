from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AddBPCompanySchema(BaseModel):
    name: Optional[str] = Field(None, description="協力会社名")
    free_kana_name: Optional[str] = Field(None, description="協力会社名（フリーカナ）")
    representative: Optional[str] = Field(None, description="代表者名")
    code: Optional[str] = Field(None, description="会社コード")
    invoice_number: Optional[str] = Field(None, description="インボイス番号")
    zip_code: Optional[str] = Field(None, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, description="電話番号")
    email: Optional[str] = Field(None, description="メール")
    website: Optional[str] = Field(None, description="Webサイト")
    status: Optional[str] = Field(None, description="ステータス（active/inactive/blacklist）")
    contract_start_date: Optional[date] = Field(None, description="契約開始日")
    contract_end_date: Optional[date] = Field(None, description="契約終了日")
    payment_site: Optional[str] = Field(None, description="支払いサイト")
    payment_day: Optional[str] = Field(None, description="支払い日")
    attendance_calc_type: Optional[int] = Field(None, description="出勤計算区分")
    decimal_processing_type: Optional[str] = Field(None, description="端数の処理区分")
    decimal_processing_position: Optional[str] = Field(None, description="端数の処理位置")
    capital: Optional[str] = Field(None, description="資本金")
    established_date: Optional[date] = Field(None, description="設立月日")
    rating: Optional[int] = Field(None, description="社内評価（1-5）")
    remark: Optional[str] = Field(None, description="備考")


class UpdateBPCompanySchema(BaseModel):
    id: Optional[int] = Field(None, description="顧客会社ID")
    name: Optional[str] = Field(None, description="協力会社名")
    free_kana_name: Optional[str] = Field(None, description="協力会社名（フリーカナ）")
    representative: Optional[str] = Field(None, description="代表者名")
    code: Optional[str] = Field(None, description="会社コード")
    invoice_number: Optional[str] = Field(None, description="インボイス番号")
    zip_code: Optional[str] = Field(None, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, description="電話番号")
    email: Optional[str] = Field(None, description="メール")
    website: Optional[str] = Field(None, description="Webサイト")
    status: Optional[str] = Field(None, description="ステータス（active/inactive/blacklist）")
    contract_start_date: Optional[date] = Field(None, description="契約開始日")
    contract_end_date: Optional[date] = Field(None, description="契約終了日")
    payment_site: Optional[str] = Field(None, description="支払いサイト")
    payment_day: Optional[str] = Field(None, description="支払い日")
    capital: Optional[str] = Field(None, description="資本金")
    established_date: Optional[date] = Field(None, description="設立月日")
    attendance_calc_type: Optional[int] = Field(None, description="出勤計算区分")
    decimal_processing_type: Optional[str] = Field(None, description="端数の処理区分")
    decimal_processing_position: Optional[str] = Field(None, description="端数の処理位置")
    rating: Optional[int] = Field(None, description="社内評価（1-5）")
    remark: Optional[str] = Field(None, description="備考")


class ActiveBpEmployeeSchema(BaseModel):
    bp_company_id: Optional[int] = Field(None, description="顧客会社ID")


class AddBPEmployeeSchema(BaseModel):
    bp_company_id: Optional[int] = Field(None, description="顧客会社ID")
    user_id: Optional[int] = Field(None, description="ユーザーID")
    name: Optional[str] = Field(None, description="要員")
    code: Optional[str] = Field(None, description="要員コード")
    free_kana_name: Optional[str] = Field(None, description="要員名（フリーカナ）")
    birthday: Optional[date] = Field(None, description="生年月日")
    station: Optional[str] = Field(None, description="最寄駅")
    marriage_status: Optional[str] = Field(None, description="婚姻状況")
    zip_code: Optional[str] = Field(None, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, description="電話番号")
    email: Optional[str] = Field(None, description="メール")
    emergency_contact_name: Optional[str] = Field(None, description="緊急連絡先")
    emergency_contact_phone: Optional[str] = Field(None, description="緊急連絡先電話番号")
    emergency_contact_relation: Optional[str] = Field(None, description="緊急連絡先関係")

    nationality: Optional[str] = Field(None, description="国籍")
    visa_status: Optional[str] = Field(None, description="在留資格")
    visa_expire_date: Optional[date] = Field(None, description="在留期間満了日")
    japanese_level: Optional[str] = Field(None, description="日本語レベル")
    # 職歴・スキル関連
    total_experience_years: Optional[int] = Field(None, description="合計経験年数")
    it_experience_years: Optional[int] = Field(None, description="IT経験年数")
    education_level: Optional[str] = Field(None, description="学歴")
    major: Optional[str] = Field(None, description="専攻")
    certifications: Optional[str] = Field(None, description="資格")

    # 単価と稼働状況関連
    standard_unit_price: Optional[int] = Field(None, description="標準単価")
    min_unit_price: Optional[int] = Field(None, description="最低単価")
    max_unit_price: Optional[int] = Field(None, description="最高単価")
    employment_status: Optional[str] = Field(None, description="稼働ステータス")
    available_start_date: Optional[date] = Field(None, description="稼働開始日")
    current_project_end_date: Optional[date] = Field(None, description="現在プロジェクト終了日")

    # 希望条件
    preferred_location: Optional[str] = Field(None, description="希望勤務地")
    preferred_project_type: Optional[str] = Field(None, description="希望プロジェクト種別")
    ng_client_companies: Optional[str] = Field(None, description="NGクライアント会社")

    # その他
    photo_url: Optional[str] = Field(None, description="写真URL")
    resume_url: Optional[str] = Field(None, description="履歴書URL")
    portfolio_url: Optional[str] = Field(None, description="ポートフォリオURL")
    remark: Optional[str] = Field(None, description="備考")


class UpdateBPEmployeeSchema(AddBPEmployeeSchema):
    id: Optional[int] = Field(None, description="顧客会社ID")


class AddBPSalesRepresentativeSchema(BaseModel):
    bp_company_id: int = Field(..., description="所属BP会社ID")
    name: str = Field(..., description="氏名")
    name_kana: Optional[str] = Field(None, description="氏名（フリーカナ）")
    gender: Optional[int] = Field(0, description="性別 (0:不明, 1:男, 2:女)")
    email: str = Field(..., description="メールアドレス")
    phone: Optional[str] = Field(None, description="電話番号")
    is_primary: bool = Field(False, description="主担当者かどうか")
    remark: Optional[str] = Field(None, description="備考")


class UpdateBPSalesRepresentativeSchema(BaseModel):
    id: int = Field(..., description="営業担当者ID")
    bp_company_id: Optional[int] = Field(None, description="所属BP会社ID")
    name: Optional[str] = Field(None, description="氏名")
    name_kana: Optional[str] = Field(None, description="氏名（フリーカナ）")
    gender: Optional[int] = Field(None, description="性別 (0:不明, 1:男, 2:女)")
    email: Optional[str] = Field(None, description="メールアドレス")
    phone: Optional[str] = Field(None, description="電話番号")
    is_primary: Optional[bool] = Field(None, description="主担当者かどうか")
    is_active: Optional[bool] = Field(None, description="有効フラグ")
    remark: Optional[str] = Field(None, description="備考")


class AddBPOrderEmailConfigSchema(BaseModel):
    bp_company_id: int = Field(..., description="対象BP会社ID")
    config_name: str = Field(..., description="設定名称")
    is_default: bool = Field(False, description="デフォルト設定かどうか")
    sender_sales_rep_id: int = Field(..., description="送信者（BP営業担当者ID）")
    cc_sales_rep_ids: Optional[list[int]] = Field(None, description="CC営業担当者IDs")
    remark: Optional[str] = Field(None, description="備考")


class UpdateBPOrderEmailConfigSchema(BaseModel):
    id: int = Field(..., description="設定ID")
    bp_company_id: Optional[int] = Field(None, description="対象BP会社ID")
    config_name: Optional[str] = Field(None, description="設定名称")
    is_default: Optional[bool] = Field(None, description="デフォルト設定かどうか")
    is_active: Optional[bool] = Field(None, description="有効フラグ")
    sender_sales_rep_id: Optional[int] = Field(None, description="送信者（BP営業担当者ID）")
    cc_sales_rep_ids: Optional[list[int]] = Field(None, description="CC営業担当者IDs")
    remark: Optional[str] = Field(None, description="備考")


class AddBPPaymentEmailConfigSchema(BaseModel):
    bp_company_id: int = Field(..., description="対象BP会社ID")
    config_name: str = Field(..., description="設定名称")
    is_default: bool = Field(False, description="デフォルト設定かどうか")
    sender_sales_rep_id: int = Field(..., description="送信者（BP営業担当者ID）")
    cc_sales_rep_ids: Optional[list[int]] = Field(None, description="CC営業担当者IDs")
    remark: Optional[str] = Field(None, description="備考")


class UpdateBPPaymentEmailConfigSchema(BaseModel):
    id: int = Field(..., description="設定ID")
    bp_company_id: Optional[int] = Field(None, description="対象BP会社ID")
    config_name: Optional[str] = Field(None, description="設定名称")
    is_default: Optional[bool] = Field(None, description="デフォルト設定かどうか")
    is_active: Optional[bool] = Field(None, description="有効フラグ")
    sender_sales_rep_id: Optional[int] = Field(None, description="送信者（BP営業担当者ID）")
    cc_sales_rep_ids: Optional[list[int]] = Field(None, description="CC営業担当者IDs")
    remark: Optional[str] = Field(None, description="備考")


# ==================== BP会社契約関連のSchema ====================


class AddBPCompanyContractSchema(BaseModel):
    bp_company_id: int = Field(..., description="契約先BP会社ID")
    contract_number: str = Field(..., description="契約書番号")
    contract_name: str = Field(..., description="契約名称")
    contract_form: str = Field(..., description="SES契約形態")
    contract_start_date: date = Field(..., description="契約開始日")
    contract_end_date: date = Field(..., description="契約終了日")
    status: Optional[str] = Field("有効", description="契約ステータス")
    contract_documents: Optional[List[str]] = Field([], description="契約書類ファイル情報")
    remark: Optional[str] = Field(None, description="備考")


class UpdateBPCompanyContractSchema(BaseModel):
    id: int = Field(..., description="契約ID")
    bp_company_id: Optional[int] = Field(None, description="契約先BP会社ID")
    contract_number: Optional[str] = Field(None, description="契約書番号")
    contract_name: Optional[str] = Field(None, description="契約名称")
    contract_form: Optional[str] = Field(None, description="SES契約形態")
    contract_start_date: Optional[date] = Field(None, description="契約開始日")
    contract_end_date: Optional[date] = Field(None, description="契約終了日")
    status: Optional[str] = Field(None, description="契約ステータス")
    contract_documents: Optional[List[str]] = Field(None, description="契約書類ファイル情報")
    remark: Optional[str] = Field(None, description="備考")
