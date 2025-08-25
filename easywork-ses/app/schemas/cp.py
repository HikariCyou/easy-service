from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import DecimalProcessingType


class AddClientCompanySchema(BaseModel):
    company_name: Optional[str] = Field(None, description="取り先会社名")
    company_name_kana: Optional[str] = Field(
        None, description="取り先会社名（フリーカナ）"
    )
    representative: Optional[str] = Field(None, description="代表者名")
    capital: Optional[str] = Field(None, description="資本金")
    established_date: Optional[date] = Field(None, description="設立月日")
    zip_code: Optional[str] = Field(None, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, description="電話番号")
    email: Optional[str] = Field(None, description="メール")
    website: Optional[str] = Field(None, description="Webサイト")
    
    # 出勤計算関連
    attendance_calc_type: Optional[int] = Field(15, description="出勤計算区分（分単位）")
    decimal_processing_type: Optional[DecimalProcessingType] = Field(
        DecimalProcessingType.ROUND, description="小数処理区分"
    )
    
    remark: Optional[str] = Field(None, description="備考")


class UpdateClientCompanySchema(BaseModel):
    id: Optional[int] = Field(None, description="顧客会社ID")
    company_name: Optional[str] = Field(None, description="取り先会社名")
    company_name_kana: Optional[str] = Field(
        None, description="取り先会社名（フリーカナ）"
    )
    representative: Optional[str] = Field(None, description="代表者名")
    capital: Optional[str] = Field(None, description="資本金")
    established_date: Optional[str] = Field(None, description="設立月日")
    zip_code: Optional[str] = Field(None, description="郵便番号")
    address: Optional[str] = Field(None, description="住所")
    phone: Optional[str] = Field(None, description="電話番号")
    email: Optional[str] = Field(None, description="メール")
    website: Optional[str] = Field(None, description="Webサイト")
    
    # 出勤計算関連
    attendance_calc_type: Optional[int] = Field(None, description="出勤計算区分（分単位）")
    decimal_processing_type: Optional[DecimalProcessingType] = Field(
        None, description="小数処理区分"
    )
    
    remark: Optional[str] = Field(None, description="備考")
