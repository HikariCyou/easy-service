from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class AddBPCompanySchema(BaseModel):
    name: Optional[str] = Field(None, description="協力会社名", examples="株式会社テスト")
    free_kana_name: Optional[str] = Field(
        None, description="協力会社名（フリーカナ）", examples="カブシキガイシャテスト"
    )
    representative: Optional[str] = Field(None, description="代表者名", examples="テスト代表者")
    code: Optional[str] = Field(None, description="会社コード", examples="123456")
    tax_number: Optional[str] = Field(None, description="法人番号 / 税番号", examples="1234567890")
    zip_code: Optional[str] = Field(None, description="郵便番号", examples="1000001")
    address: Optional[str] = Field(None, description="住所", examples="東京都千代田区")
    phone: Optional[str] = Field(None, description="電話番号", examples="03-1234-5678")
    email: Optional[str] = Field(None, description="メール", examples="test@example.com")
    website: Optional[str] = Field(None, description="Webサイト", examples="https://example.com")
    status: Optional[str] = Field(None, description="ステータス（active/inactive/blacklist）", examples="active")
    contract_start_date: Optional[date] = Field(None, description="契約開始日", examples="2020-01-01")
    contract_end_date: Optional[date] = Field(None, description="契約終了日", examples="2020-12-31")
    attendance_calc_type: Optional[str | int] = Field(None, description="出勤計算区分", examples="monthly")
    decimal_processing_type: Optional[str] = Field(None, description="小数処理区分", examples="round")
    capital: Optional[str] = Field(None, description="資本金", examples="10000000")
    established_date: Optional[date] = Field(None, description="設立月日", examples="2020-01-01")
    rating: Optional[int] = Field(None, description="社内評価（1-5）", examples=5)
    remark: Optional[str] = Field(None, description="備考", examples="備考")


class UpdateBPCompanySchema(BaseModel):
    id: Optional[int] = Field(None, description="顧客会社ID")
    name: Optional[str] = Field(None, description="協力会社名", examples="株式会社テスト")
    free_kana_name: Optional[str] = Field(
        None, description="協力会社名（フリーカナ）", examples="カブシキガイシャテスト"
    )
    representative: Optional[str] = Field(None, description="代表者名", examples="テスト代表者")
    code: Optional[str] = Field(None, description="会社コード", examples="123456")
    tax_number: Optional[str] = Field(None, description="法人番号 / 税番号", examples="1234567890")
    zip_code: Optional[str] = Field(None, description="郵便番号", examples="1000001")
    address: Optional[str] = Field(None, description="住所", examples="東京都千代田区")
    phone: Optional[str] = Field(None, description="電話番号", examples="03-1234-5678")
    email: Optional[str] = Field(None, description="メール", examples="test@example.com")
    website: Optional[str] = Field(None, description="Webサイト", examples="https://example.com")
    status: Optional[str] = Field(None, description="ステータス（active/inactive/blacklist）", examples="active")
    contract_start_date: Optional[date] = Field(None, description="契約開始日", examples="2020-01-01")
    contract_end_date: Optional[date] = Field(None, description="契約終了日", examples="2020-12-31")
    capital: Optional[str] = Field(None, description="資本金", examples="10000000")
    established_date: Optional[date] = Field(None, description="設立月日", examples="2020-01-01")
    attendance_calc_type: Optional[str | int] = Field(None, description="出勤計算区分", examples="monthly")
    decimal_processing_type: Optional[str] = Field(None, description="小数処理区分", examples="round")
    rating: Optional[int] = Field(None, description="社内評価（1-5）", examples=5)
    remark: Optional[str] = Field(None, description="備考", examples="備考")


class ActiveBpEmployeeSchema(BaseModel):
    bp_company_id: Optional[int] = Field(None, description="顧客会社ID")


class AddBPEmployeeSchema(BaseModel):
    bp_company_id: Optional[int] = Field(None, description="顧客会社ID")
    name: Optional[str] = Field(None, description="要員", examples="要員A")
    code: Optional[str] = Field(None, description="要員コード", examples="123456")
    free_kana_name: Optional[str] = Field(None, description="要員名（フリーカナ）", examples="ヨウインA")
    birthday: Optional[date] = Field(None, description="生年月日", examples="1990-01-01")
    station: Optional[str] = Field(None, description="最寄駅", examples="東京駅")
    marriage_status: Optional[str] = Field(None, description="婚姻状況", examples="single")
    zip_code: Optional[str] = Field(None, description="郵便番号", examples="1000001")
    address: Optional[str] = Field(None, description="住所", examples="東京都千代田区")
    phone: Optional[str] = Field(None, description="電話番号", examples="03-1234-5678")
    email: Optional[str] = Field(None, description="メール", examples="test@example.com")
    emergency_contact_name: Optional[str] = Field(None, description="緊急連絡先", examples="緊急連絡先A")
    emergency_contact_phone: Optional[str] = Field(None, description="緊急連絡先電話番号", examples="03-1234-5678")
    emergency_contact_relation: Optional[str] = Field(None, description="緊急連絡先関係", examples="family")

    nationality: Optional[str] = Field(None, description="国籍", examples="日本")
    visa_status: Optional[str] = Field(None, description="在留資格", examples="在留資格A")
    visa_expire_date: Optional[date] = Field(None, description="在留期間満了日", examples="2020-12-31")
    japanese_level: Optional[str] = Field(None, description="日本語レベル", examples="N1")
    # 職歴・スキル関連
    total_experience_years: Optional[int] = Field(None, description="合計経験年数", examples=10)
    it_experience_years: Optional[int] = Field(None, description="IT経験年数", examples=5)
    education_level: Optional[str] = Field(None, description="学歴", examples="大学院")
    major: Optional[str] = Field(None, description="専攻", examples="情報科学")
    certifications: Optional[str] = Field(
        None, description="資格", examples="Oracle Certified Professional, Java SE 11 Developer"
    )

    # 単価と稼働状況関連
    standard_unit_price: Optional[int] = Field(None, description="標準単価", examples=100000)
    min_unit_price: Optional[int] = Field(None, description="最低単価", examples=90000)
    max_unit_price: Optional[int] = Field(None, description="最高単価", examples=110000)
    employment_status: Optional[str] = Field(None, description="稼働ステータス", examples="稼働可能")
    available_start_date: Optional[date] = Field(None, description="稼働開始日", examples="2020-01-01")
    current_project_end_date: Optional[date] = Field(None, description="現在プロジェクト終了日", examples="2020-12-31")

    # 希望条件
    preferred_location: Optional[str] = Field(None, description="希望勤務地", examples="東京")
    preferred_project_type: Optional[str] = Field(None, description="希望プロジェクト種別", examples="システム開発")
    ng_client_companies: Optional[str] = Field(None, description="NGクライアント会社", examples="NGクライアント会社A")

    # その他
    photo_url: Optional[str] = Field(None, description="写真URL", examples="https://example.com/photo.jpg")
    resume_url: Optional[str] = Field(None, description="履歴書URL", examples="https://example.com/resume.pdf")
    portfolio_url: Optional[str] = Field(
        None, description="ポートフォリオURL", examples="https://example.com/portfolio"
    )
    remark: Optional[str] = Field(None, description="備考", examples="備考")


class UpdateBPEmployeeSchema(AddBPEmployeeSchema):
    id: Optional[int] = Field(None, description="顧客会社ID")
