from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class AddClientCompanySchema(BaseModel):
    company_name: Optional[str] = Field(None, description="取り先会社名", examples="株式会社テスト")
    company_name_kana: Optional[str] = Field(
        None, description="取り先会社名（フリーカナ）", examples="カブシキガイシャテスト"
    )
    representative: Optional[str] = Field(None, description="代表者名", examples="テスト代表者")
    capital: Optional[str] = Field(None, description="資本金", examples="10000000")
    established_date: Optional[date] = Field(None, description="設立月日", examples="2020-01-01")
    zip_code: Optional[str] = Field(None, description="郵便番号", examples="1000001")
    address: Optional[str] = Field(None, description="住所", examples="東京都千代田区")
    phone: Optional[str] = Field(None, description="電話番号", examples="03-1234-5678")
    email: Optional[str] = Field(None, description="メール", examples="test@example.com")
    website: Optional[str] = Field(None, description="Webサイト", examples="https://example.com")
    remark: Optional[str] = Field(None, description="備考", examples="備考")


class UpdateClientCompanySchema(BaseModel):
    id: Optional[int] = Field(None, description="顧客会社ID")
    company_name: Optional[str] = Field(None, description="取り先会社名", examples="株式会社テスト")
    company_name_kana: Optional[str] = Field(
        None, description="取り先会社名（フリーカナ）", examples="カブシキガイシャテスト"
    )
    representative: Optional[str] = Field(None, description="代表者名", examples="テスト代表者")
    capital: Optional[str] = Field(None, description="資本金", examples="10000000")
    established_date: Optional[str] = Field(None, description="設立月日", examples="2020-01-01")
    zip_code: Optional[str] = Field(None, description="郵便番号", examples="1000001")
    address: Optional[str] = Field(None, description="住所", examples="東京都千代田区")
    phone: Optional[str] = Field(None, description="電話番号", examples="03-1234-5678")
    email: Optional[str] = Field(None, description="メール", examples="test@example.com")
    website: Optional[str] = Field(None, description="Webサイト", examples="https://example.com")
    remark: Optional[str] = Field(None, description="備考", examples="備考")
