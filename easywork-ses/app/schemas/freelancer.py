from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateFreelancerSchema(BaseModel):
    """フリーランサー作成schema"""

    user_id: Optional[int] = Field(None, description="ユーザーID")
    # 基本情報
    name: str = Field(..., description="氏名", example="田中太郎")
    code: Optional[str] = Field(None, description="フリーランサーコード", example="FL001")
    free_kana_name: Optional[str] = Field(None, description="氏名（フリーカナ）", example="タナカタロウ")
    age: Optional[int] = Field(None, description="年齢", example=35, ge=0, le=120)
    sex: Optional[int] = Field(0, description="性別", example=1)
    birthday: Optional[date] = Field(None, description="生年月日", example="1988-05-15")
    station: Optional[str] = Field(None, description="最寄り駅", example="渋谷駅")
    marriage_status: Optional[str] = Field("single", description="婚姻ステータス", example="single")

    # 事業者情報
    business_name: Optional[str] = Field(None, description="屋号", example="田中ITコンサルティング")
    tax_number: Optional[str] = Field(None, description="インボイス番号", example="T1234567890123")
    business_start_date: Optional[date] = Field(None, description="開業日", example="2020-04-01")

    # 連絡先
    phone: Optional[str] = Field(None, description="電話番号", example="090-1234-5678")
    email: Optional[str] = Field(None, description="メール", example="tanaka@example.com")
    emergency_contact_name: Optional[str] = Field(None, description="緊急連絡先氏名", example="田中花子")
    emergency_contact_phone: Optional[str] = Field(None, description="緊急連絡先電話", example="090-9876-5432")
    emergency_contact_relation: Optional[str] = Field(None, description="緊急連絡先続柄", example="配偶者")

    # 住所
    zip_code: Optional[str] = Field(None, description="郵便コード", example="150-0002")
    address: Optional[str] = Field(None, description="住所", example="東京都渋谷区渋谷1-1-1")
    work_address: Optional[str] = Field(None, description="作業場所住所", example="東京都渋谷区渋谷2-2-2")

    # 外国人対応
    nationality: Optional[str] = Field(None, description="国籍", example="日本")
    visa_status: Optional[str] = Field(None, description="在留資格")
    visa_expire_date: Optional[date] = Field(None, description="在留期限", example="2025-12-31")
    japanese_level: Optional[str] = Field(None, description="日本語レベル")

    # 職歴・スキル関連
    total_experience_years: Optional[Decimal] = Field(None, description="総経験年数", example=10.0)
    it_experience_years: Optional[Decimal] = Field(None, description="IT経験年数", example=8.0)
    freelance_experience_years: Optional[Decimal] = Field(None, description="フリーランス経験年数", example=3.0)
    education_level: Optional[str] = Field(None, description="最終学歴", example="大学卒業")
    major: Optional[str] = Field(None, description="専攻", example="情報工学")
    certifications: Optional[str] = Field(None, description="保有資格（改行区切り）", example="ITストラテジスト\\nPMP")

    # 単価・契約関連
    standard_unit_price: Optional[Decimal] = Field(None, description="標準単価（月額）", example=900000)
    min_unit_price: Optional[Decimal] = Field(None, description="最低受注単価", example=700000)
    max_unit_price: Optional[Decimal] = Field(None, description="最高受注単価", example=1200000)
    hourly_rate: Optional[Decimal] = Field(None, description="時間単価", example=5000)

    # 稼働状況
    employment_status: Optional[str] = Field(None, description="稼働ステータス", example="available")
    is_active: Optional[bool] = Field(True, description="稼働可能かどうか", example=True)
    available_start_date: Optional[date] = Field(None, description="稼働可能開始日", example="2024-02-01")
    current_project_end_date: Optional[date] = Field(None, description="現在プロジェクト終了予定日", example="2024-12-31")

    # 希望条件
    preferred_location: Optional[str] = Field(None, description="希望勤務地", example="東京都内")
    preferred_project_type: Optional[str] = Field(None, description="希望プロジェクト種別", example="Webアプリケーション開発")
    preferred_work_style: Optional[str] = Field(None, description="希望勤務形態（常駐/リモート等）", example="リモート")
    ng_client_companies: Optional[str] = Field(None, description="NG取引先（改行区切り）", example="A社\\nB社")

    # その他
    photo_url: Optional[str] = Field(None, description="写真URL", example="https://example.com/photo.jpg")
    resume_url: Optional[str] = Field(None, description="履歴書URL", example="https://example.com/resume.pdf")
    portfolio_url: Optional[str] = Field(None, description="ポートフォリオURL", example="https://example.com/portfolio")
    website_url: Optional[str] = Field(None, description="個人サイトURL", example="https://tanaka-it.com")
    remark: Optional[str] = Field(None, description="備考", example="特記事項なし")


class UpdateFreelancerSchema(BaseModel):
    """フリーランサー更新schema"""

    user_id: Optional[int] = Field(None, description="ユーザーID")

    # 基本情報
    name: Optional[str] = Field(None, description="氏名", example="田中太郎")
    code: Optional[str] = Field(None, description="フリーランサーコード", example="FL001")
    free_kana_name: Optional[str] = Field(None, description="氏名（フリーカナ）", example="タナカタロウ")
    age: Optional[int] = Field(None, description="年齢", example=35, ge=0, le=120)
    sex: Optional[int] = Field(None, description="性別", example=1)
    birthday: Optional[date] = Field(None, description="生年月日", example="1988-05-15")
    station: Optional[str] = Field(None, description="最寄り駅", example="渋谷駅")
    marriage_status: Optional[str] = Field(None, description="婚姻ステータス", example="single")

    # 事業者情報
    business_name: Optional[str] = Field(None, description="屋号", example="田中ITコンサルティング")
    tax_number: Optional[str] = Field(None, description="インボイス番号", example="T1234567890123")
    business_start_date: Optional[date] = Field(None, description="開業日", example="2020-04-01")

    # 連絡先
    phone: Optional[str] = Field(None, description="電話番号", example="090-1234-5678")
    email: Optional[str] = Field(None, description="メール", example="tanaka@example.com")
    emergency_contact_name: Optional[str] = Field(None, description="緊急連絡先氏名", example="田中花子")
    emergency_contact_phone: Optional[str] = Field(None, description="緊急連絡先電話", example="090-9876-5432")
    emergency_contact_relation: Optional[str] = Field(None, description="緊急連絡先続柄", example="配偶者")

    # 住所
    zip_code: Optional[str] = Field(None, description="郵便コード", example="150-0002")
    address: Optional[str] = Field(None, description="住所", example="東京都渋谷区渋谷1-1-1")
    work_address: Optional[str] = Field(None, description="作業場所住所", example="東京都渋谷区渋谷2-2-2")

    # 外国人対応
    nationality: Optional[str] = Field(None, description="国籍", example="日本")
    visa_status: Optional[str] = Field(None, description="在留資格")
    visa_expire_date: Optional[date] = Field(None, description="在留期限", example="2025-12-31")
    japanese_level: Optional[str] = Field(None, description="日本語レベル")

    # 職歴・スキル関連
    total_experience_years: Optional[Decimal] = Field(None, description="総経験年数", example=10.0)
    it_experience_years: Optional[Decimal] = Field(None, description="IT経験年数", example=8.0)
    freelance_experience_years: Optional[Decimal] = Field(None, description="フリーランス経験年数", example=3.0)
    education_level: Optional[str] = Field(None, description="最終学歴", example="大学卒業")
    major: Optional[str] = Field(None, description="専攻", example="情報工学")
    certifications: Optional[str] = Field(None, description="保有資格（改行区切り）", example="ITストラテジスト\\nPMP")

    # 単価・契約関連
    standard_unit_price: Optional[Decimal] = Field(None, description="標準単価（月額）", example=900000)
    min_unit_price: Optional[Decimal] = Field(None, description="最低受注単価", example=700000)
    max_unit_price: Optional[Decimal] = Field(None, description="最高受注単価", example=1200000)
    hourly_rate: Optional[Decimal] = Field(None, description="時間単価", example=5000)

    # 稼働状況
    employment_status: Optional[str] = Field(None, description="稼働ステータス", example="available")
    is_active: Optional[bool] = Field(None, description="稼働可能かどうか", example=True)
    available_start_date: Optional[date] = Field(None, description="稼働可能開始日", example="2024-02-01")
    current_project_end_date: Optional[date] = Field(None, description="現在プロジェクト終了予定日", example="2024-12-31")

    # 希望条件
    preferred_location: Optional[str] = Field(None, description="希望勤務地", example="東京都内")
    preferred_project_type: Optional[str] = Field(None, description="希望プロジェクト種別", example="Webアプリケーション開発")
    preferred_work_style: Optional[str] = Field(None, description="希望勤務形態（常駐/リモート等）", example="リモート")
    ng_client_companies: Optional[str] = Field(None, description="NG取引先（改行区切り）", example="A社\\nB社")

    # その他
    photo_url: Optional[str] = Field(None, description="写真URL", example="https://example.com/photo.jpg")
    resume_url: Optional[str] = Field(None, description="履歴書URL", example="https://example.com/resume.pdf")
    portfolio_url: Optional[str] = Field(None, description="ポートフォリオURL", example="https://example.com/portfolio")
    website_url: Optional[str] = Field(None, description="個人サイトURL", example="https://tanaka-it.com")
    remark: Optional[str] = Field(None, description="備考", example="特記事項なし")


class FreelancerSearchSchema(BaseModel):
    """フリーランサー検索schema"""

    name: Optional[str] = Field(None, description="氏名で検索", example="田中")
    code: Optional[str] = Field(None, description="フリーランサーコードで検索", example="FL")
    employment_status: Optional[str] = Field(None, description="稼働ステータスで検索", example="available")
    nationality: Optional[str] = Field(None, description="国籍で検索", example="日本")
    skill_name: Optional[str] = Field(None, description="スキル名で検索", example="Python")
    available_from: Optional[date] = Field(None, description="稼働可能日から検索", example="2024-01-01")
    available_to: Optional[date] = Field(None, description="稼働可能日まで検索", example="2024-12-31")
    min_experience_years: Optional[Decimal] = Field(None, description="最低経験年数", example=3.0)
    min_unit_price: Optional[Decimal] = Field(None, description="最低単価", example=500000)
    max_unit_price: Optional[Decimal] = Field(None, description="最高単価", example=1000000)
    preferred_location: Optional[str] = Field(None, description="希望勤務地で検索", example="東京")
    business_name: Optional[str] = Field(None, description="屋号で検索", example="コンサル")


class CreateFreelancerSkillSchema(BaseModel):
    """フリーランサー技能作成schema"""

    freelancer_id: int = Field(..., description="フリーランサーID", example=1)
    skill_name: str = Field(..., description="スキル名称", example="Python")
    category: Optional[str] = Field(None, description="スキル分類", example="プログラミング言語")
    proficiency: Optional[int] = Field(1, description="熟練度 (1-5)", example=4, ge=1, le=5)
    years_of_experience: Optional[float] = Field(None, description="経験年数", example=3.5)
    last_used_date: Optional[date] = Field(None, description="最終使用日", example="2024-01-15")
    is_primary_skill: Optional[bool] = Field(False, description="主要スキルかどうか", example=True)
    remark: Optional[str] = Field(None, description="備考", example="Webアプリケーション開発で使用")


class UpdateFreelancerSkillSchema(BaseModel):
    """フリーランサー技能更新schema"""

    skill_name: Optional[str] = Field(None, description="スキル名称", example="Python")
    category: Optional[str] = Field(None, description="スキル分類", example="プログラミング言語")
    proficiency: Optional[int] = Field(None, description="熟練度 (1-5)", example=4, ge=1, le=5)
    years_of_experience: Optional[Decimal] = Field(None, description="経験年数", example=3.5)
    last_used_date: Optional[date] = Field(None, description="最終使用日", example="2024-01-15")
    is_primary_skill: Optional[bool] = Field(None, description="主要スキルかどうか", example=True)
    remark: Optional[str] = Field(None, description="備考", example="Webアプリケーション開発で使用")


class BatchUpdateFreelancerSkillsSchema(BaseModel):
    """フリーランサー技能批量更新schema"""

    skills: List[dict] = Field(
        ...,
        description="スキルリスト",
        example=[
            {
                "skill_name": "Python",
                "category": "プログラミング言語",
                "proficiency": 5,
                "years_of_experience": 5.0,
                "is_primary_skill": True,
            },
            {
                "skill_name": "React",
                "category": "フロントエンド",
                "proficiency": 4,
                "years_of_experience": 2.5,
                "is_primary_skill": False,
            },
        ],
    )


class CreateFreelancerEvaluationSchema(BaseModel):
    """フリーランサー評価作成schema"""

    case_id: Optional[int] = Field(None, description="評価対象案件ID", example=1)
    contract_id: Optional[int] = Field(None, description="評価対象契約ID", example=1)
    technical_skill: int = Field(..., description="技術力 (1-5)", example=5, ge=1, le=5)
    communication: int = Field(..., description="コミュニケーション力 (1-5)", example=4, ge=1, le=5)
    reliability: int = Field(..., description="信頼性 (1-5)", example=5, ge=1, le=5)
    proactiveness: int = Field(..., description="積極性 (1-5)", example=4, ge=1, le=5)
    independence: int = Field(..., description="自立性 (1-5)", example=5, ge=1, le=5)
    delivery_quality: int = Field(..., description="成果物品質 (1-5)", example=5, ge=1, le=5)
    overall_rating: int = Field(..., description="総合評価 (1-5)", example=5, ge=1, le=5)
    good_points: Optional[str] = Field(None, description="良い点", example="高い技術力と迅速な対応で期待以上の成果を提供した")
    improvement_points: Optional[str] = Field(None, description="改善点", example="定期的な進捗報告があるとより良い")
    recommendation: bool = Field(..., description="次回推薦可能か", example=True)
    evaluation_date: date = Field(..., description="評価日", example="2024-01-31")
    remark: Optional[str] = Field(None, description="備考", example="優秀なフリーランサーです")


class FreelancerProjectMatchingSchema(BaseModel):
    """フリーランサー案件マッチング検索schema"""

    required_skills: List[str] = Field(..., description="必要スキルリスト", example=["Python", "React"])
    project_start_date: Optional[date] = Field(None, description="案件開始日", example="2024-03-01")
    project_end_date: Optional[date] = Field(None, description="案件終了日", example="2024-12-31")
    budget_min: Optional[Decimal] = Field(None, description="予算下限", example=600000)
    budget_max: Optional[Decimal] = Field(None, description="予算上限", example=1000000)
    location: Optional[str] = Field(None, description="勤務地", example="東京都")
    work_style: Optional[str] = Field(None, description="勤務形態", example="リモート")
    min_experience_years: Optional[Decimal] = Field(None, description="最低経験年数", example=3.0)
    exclude_ng_companies: Optional[List[str]] = Field(None, description="除外するNG企業リスト", example=["A社", "B社"])


class FreelancerBusinessStatsSchema(BaseModel):
    """フリーランサー事業統計schema"""

    year: Optional[int] = Field(None, description="統計年度", example=2024)
    month_from: Optional[int] = Field(None, description="開始月", example=1, ge=1, le=12)
    month_to: Optional[int] = Field(None, description="終了月", example=12, ge=1, le=12)
    include_tax_info: Optional[bool] = Field(False, description="税務情報を含むかどうか", example=True)
