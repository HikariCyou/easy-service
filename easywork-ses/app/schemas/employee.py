from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateEmployeeSchema(BaseModel):
    """创建员工schema"""

    # HR系統関連（必須）
    user_id: int = Field(..., description="関連したユーザーID", example=1)
    code: Optional[str] = Field(None, description="社員番号", example="EMP001")
    joining_time: Optional[date] = Field(None, description="入社時間", example="2023-04-01")
    
    # 基本情報
    name: Optional[str] = Field(None, description="氏名", example="山田太郎")
    free_kana_name: Optional[str] = Field(None, description="氏名（フリーカナ）", example="ヤマダタロウ")
    age: Optional[int] = Field(None, description="年齢", example=30, ge=0, le=120)
    sex: Optional[int] = Field(0, description="性別", example=1)
    birthday: Optional[date] = Field(None, description="生年月日", example="1993-01-01")
    station: Optional[str] = Field(None, description="最寄り駅", example="新宿駅")
    marriage_status: Optional[str] = Field("single", description="婚姻ステータス", example="single")
    
    # 連絡先
    phone: Optional[str] = Field(None, description="電話番号", example="090-1234-5678")
    email: Optional[str] = Field(None, description="メール", example="yamada@example.com")
    emergency_contact_name: Optional[str] = Field(None, description="緊急連絡先氏名", example="山田花子")
    emergency_contact_phone: Optional[str] = Field(None, description="緊急連絡先電話", example="090-9876-5432")
    emergency_contact_relation: Optional[str] = Field(None, description="緊急連絡先続柄", example="配偶者")
    
    # 住所
    zip_code: Optional[str] = Field(None, description="郵便コード", example="160-0023")
    address: Optional[str] = Field(None, description="住所", example="東京都新宿区西新宿1-1-1")
    
    # 外国人対応
    nationality: Optional[str] = Field(None, description="国籍", example="日本")
    visa_status: Optional[str] = Field(None, description="在留資格", example="技術・人文知識・国際業務")
    visa_expire_date: Optional[date] = Field(None, description="在留期限", example="2025-12-31")
    japanese_level: Optional[str] = Field(None, description="日本語レベル", example="N1")
    
    # 職歴・スキル関連
    total_experience_years: Optional[Decimal] = Field(None, description="総経験年数", example=5.5)
    it_experience_years: Optional[Decimal] = Field(None, description="IT経験年数", example=3.0)
    education_level: Optional[str] = Field(None, description="最終学歴", example="大学卒業")
    major: Optional[str] = Field(None, description="専攻", example="情報工学")
    certifications: Optional[str] = Field(None, description="保有資格（改行区切り）", example="応用情報技術者\\nTOEIC 800点")

    # 社員固有情報
    position: Optional[str] = Field(None, description="役職", example="シニアエンジニア")
    employment_type: Optional[str] = Field(None, description="雇用形態", example="正社員")
    business_content: Optional[str] = Field(None, description="業務内容", example="Webアプリケーション開発")
    
    # 給与関連
    salary_payment_type: Optional[str] = Field(None, description="給与支給形態", example="monthly")
    salary: Optional[int] = Field(None, description="給与額", example=400000)
    standard_unit_price: Optional[Decimal] = Field(None, description="標準単価（月額）", example=800000)
    
    # 稼働状況
    employment_status: Optional[str] = Field("available", description="稼働ステータス", example="available")
    available_start_date: Optional[date] = Field(None, description="稼働可能開始日", example="2024-01-01")
    current_project_end_date: Optional[date] = Field(None, description="現在プロジェクト終了予定日", example="2024-12-31")
    
    # 希望条件
    preferred_location: Optional[str] = Field(None, description="希望勤務地", example="東京都内")
    remote_work_available: Optional[bool] = Field(False, description="リモート可能", example=True)
    overtime_available: Optional[bool] = Field(False, description="残業可能", example=True)
    
    # その他
    photo_url: Optional[str] = Field(None, description="写真URL", example="https://example.com/photo.jpg")
    resume_url: Optional[str] = Field(None, description="履歴書URL", example="https://example.com/resume.pdf")
    portfolio_url: Optional[str] = Field(None, description="ポートフォリオURL", example="https://example.com/portfolio")
    remark: Optional[str] = Field(None, description="備考", example="特記事項なし")
    is_active: Optional[bool] = Field(True, description="アクティブかどうか", example=True)
    
    # HR系統固有
    process_instance_id: Optional[str] = Field(None, description="プロセスインスタンスID", example="proc_123")


class UpdateEmployeeSchema(BaseModel):
    """更新員工schema"""

    # 基本情報
    name: Optional[str] = Field(None, description="氏名", example="山田太郎")
    free_kana_name: Optional[str] = Field(None, description="氏名（フリーカナ）", example="ヤマダタロウ")
    age: Optional[int] = Field(None, description="年齢", example=30, ge=0, le=120)
    sex: Optional[int] = Field(None, description="性別", example=1)
    birthday: Optional[date] = Field(None, description="生年月日", example="1993-01-01")
    station: Optional[str] = Field(None, description="最寄り駅", example="新宿駅")
    marriage_status: Optional[str] = Field(None, description="婚姻ステータス", example="single")
    
    # 連絡先
    phone: Optional[str] = Field(None, description="電話番号", example="090-1234-5678")
    email: Optional[str] = Field(None, description="メール", example="yamada@example.com")
    emergency_contact_name: Optional[str] = Field(None, description="緊急連絡先氏名", example="山田花子")
    emergency_contact_phone: Optional[str] = Field(None, description="緊急連絡先電話", example="090-9876-5432")
    emergency_contact_relation: Optional[str] = Field(None, description="緊急連絡先続柄", example="配偶者")
    
    # 住所
    zip_code: Optional[str] = Field(None, description="郵便コード", example="160-0023")
    address: Optional[str] = Field(None, description="住所", example="東京都新宿区西新宿1-1-1")
    
    # 外国人対応
    nationality: Optional[str] = Field(None, description="国籍", example="日本")
    visa_status: Optional[str] = Field(None, description="在留資格", example="技術・人文知識・国際業務")
    visa_expire_date: Optional[date] = Field(None, description="在留期限", example="2025-12-31")
    japanese_level: Optional[str] = Field(None, description="日本語レベル", example="N1")
    
    # 職歴・スキル関連
    total_experience_years: Optional[Decimal] = Field(None, description="総経験年数", example=5.5)
    it_experience_years: Optional[Decimal] = Field(None, description="IT経験年数", example=3.0)
    education_level: Optional[str] = Field(None, description="最終学歴", example="大学卒業")
    major: Optional[str] = Field(None, description="専攻", example="情報工学")
    certifications: Optional[str] = Field(None, description="保有資格（改行区切り）", example="応用情報技術者\\nTOEIC 800点")

    # 社員固有情報
    code: Optional[str] = Field(None, description="社員番号", example="EMP001")
    joining_time: Optional[date] = Field(None, description="入社時間", example="2023-04-01")
    position: Optional[str] = Field(None, description="役職", example="シニアエンジニア")
    employment_type: Optional[str] = Field(None, description="雇用形態", example="正社員")
    business_content: Optional[str] = Field(None, description="業務内容", example="Webアプリケーション開発")
    
    # 給与関連
    salary_payment_type: Optional[str] = Field(None, description="給与支給形態", example="monthly")
    salary: Optional[int] = Field(None, description="給与額", example=400000)
    standard_unit_price: Optional[Decimal] = Field(None, description="標準単価（月額）", example=800000)
    
    # 稼働状況
    employment_status: Optional[str] = Field(None, description="稼働ステータス", example="available")
    available_start_date: Optional[date] = Field(None, description="稼働可能開始日", example="2024-01-01")
    current_project_end_date: Optional[date] = Field(None, description="現在プロジェクト終了予定日", example="2024-12-31")
    
    # 希望条件
    preferred_location: Optional[str] = Field(None, description="希望勤務地", example="東京都内")
    remote_work_available: Optional[bool] = Field(None, description="リモート可能", example=True)
    overtime_available: Optional[bool] = Field(None, description="残業可能", example=True)
    
    # その他
    photo_url: Optional[str] = Field(None, description="写真URL", example="https://example.com/photo.jpg")
    resume_url: Optional[str] = Field(None, description="履歴書URL", example="https://example.com/resume.pdf")
    portfolio_url: Optional[str] = Field(None, description="ポートフォリオURL", example="https://example.com/portfolio")
    remark: Optional[str] = Field(None, description="備考", example="特記事項なし")
    is_active: Optional[bool] = Field(None, description="アクティブかどうか", example=True)
    
    # HR系統固有
    process_instance_id: Optional[str] = Field(None, description="プロセスインスタンスID", example="proc_123")


class EmployeeSearchSchema(BaseModel):
    """員工検索schema"""
    
    name: Optional[str] = Field(None, description="氏名で検索", example="山田")
    code: Optional[str] = Field(None, description="社員番号で検索", example="EMP")
    employment_status: Optional[str] = Field(None, description="稼働ステータスで検索", example="available")
    nationality: Optional[str] = Field(None, description="国籍で検索", example="日本")
    skill_name: Optional[str] = Field(None, description="スキル名で検索", example="Java")
    available_from: Optional[date] = Field(None, description="稼働可能日から検索", example="2024-01-01")
    available_to: Optional[date] = Field(None, description="稼働可能日まで検索", example="2024-12-31")
    min_experience_years: Optional[Decimal] = Field(None, description="最低経験年数", example=2.0)


class CreateEmployeeSkillSchema(BaseModel):
    """員工技能作成schema"""

    skill_name: str = Field(..., description="スキル名称", example="Java")
    category: Optional[str] = Field(None, description="スキル分類", example="プログラミング言語")
    proficiency: Optional[int] = Field(1, description="熟練度 (1-5)", example=3, ge=1, le=5)
    years_of_experience: Optional[Decimal] = Field(None, description="経験年数", example=2.5)
    last_used_date: Optional[date] = Field(None, description="最終使用日", example="2023-12-01")
    is_primary_skill: Optional[bool] = Field(False, description="主要スキルかどうか", example=False)
    remark: Optional[str] = Field(None, description="備考", example="プロジェクトXで使用")


class UpdateEmployeeSkillSchema(BaseModel):
    """員工技能更新schema"""

    skill_name: Optional[str] = Field(None, description="スキル名称", example="Java")
    category: Optional[str] = Field(None, description="スキル分類", example="プログラミング言語")
    proficiency: Optional[int] = Field(None, description="熟練度 (1-5)", example=3, ge=1, le=5)
    years_of_experience: Optional[Decimal] = Field(None, description="経験年数", example=2.5)
    last_used_date: Optional[date] = Field(None, description="最終使用日", example="2023-12-01")
    is_primary_skill: Optional[bool] = Field(None, description="主要スキルかどうか", example=False)
    remark: Optional[str] = Field(None, description="備考", example="プロジェクトXで使用")


class BatchUpdateEmployeeSkillsSchema(BaseModel):
    """員工技能批量更新schema"""

    skills: List[dict] = Field(
        ...,
        description="スキルリスト",
        example=[
            {
                "skill_name": "Java",
                "category": "プログラミング言語",
                "proficiency": 4,
                "years_of_experience": 3.0,
                "is_primary_skill": True,
            },
            {
                "skill_name": "Python",
                "category": "プログラミング言語",
                "proficiency": 3,
                "years_of_experience": 1.5,
                "is_primary_skill": False,
            },
        ],
    )


class CreateEmployeeEvaluationSchema(BaseModel):
    """員工評価作成schema"""
    
    case_id: Optional[int] = Field(None, description="評価対象案件ID", example=1)
    contract_id: Optional[int] = Field(None, description="評価対象契約ID", example=1)
    technical_skill: int = Field(..., description="技術力 (1-5)", example=4, ge=1, le=5)
    communication: int = Field(..., description="コミュニケーション力 (1-5)", example=4, ge=1, le=5)
    reliability: int = Field(..., description="信頼性 (1-5)", example=5, ge=1, le=5)
    proactiveness: int = Field(..., description="積極性 (1-5)", example=3, ge=1, le=5)
    independence: int = Field(..., description="自立性 (1-5)", example=4, ge=1, le=5)
    delivery_quality: int = Field(..., description="成果物品質 (1-5)", example=4, ge=1, le=5)
    overall_rating: int = Field(..., description="総合評価 (1-5)", example=4, ge=1, le=5)
    good_points: Optional[str] = Field(None, description="良い点", example="技術力が高く、期限内に高品質な成果物を提供した")
    improvement_points: Optional[str] = Field(None, description="改善点", example="コミュニケーションをもう少し積極的に取ってほしい")
    recommendation: bool = Field(..., description="次回推薦可能か", example=True)
    evaluation_date: date = Field(..., description="評価日", example="2024-01-15")
    remark: Optional[str] = Field(None, description="備考", example="特記事項なし")
