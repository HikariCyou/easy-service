from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import (EmploymentStatus, JapaneseLevel, MarriageStatus,
                              VisaStatus, ResidenceStatus)


class Freelancer(BaseModel, TimestampMixin):
    """
    個人事業主（フリーランス）
    """

    # 基本情報
    name = fields.CharField(max_length=100, description="氏名")
    code = fields.CharField(max_length=50, null=True, description="フリーランサーコード")
    free_kana_name = fields.CharField(max_length=100, null=True, description="氏名（フリーカナ）")
    age = fields.IntField(null=True, description="年齢")
    sex = fields.IntField(null=True, default=0, description="性別")
    birthday = fields.DateField(null=True, description="生年月日")
    station = fields.CharField(max_length=255, null=True, description="最寄り駅")
    marriage_status = fields.CharEnumField(
        MarriageStatus, null=True, default=MarriageStatus.SINGLE, description="婚姻ステータス"
    )

    # 事業者情報
    business_name = fields.CharField(max_length=255, null=True, description="屋号")
    tax_number = fields.CharField(max_length=50, null=True, description="インボイス番号")
    business_start_date = fields.DateField(null=True, description="開業日")

    # 連絡先
    phone = fields.CharField(max_length=50, null=True, description="電話番号")
    email = fields.CharField(max_length=100, null=True, description="メール")
    emergency_contact_name = fields.CharField(max_length=100, null=True, description="緊急連絡先氏名")
    emergency_contact_phone = fields.CharField(max_length=50, null=True, description="緊急連絡先電話")
    emergency_contact_relation = fields.CharField(max_length=50, null=True, description="緊急連絡先続柄")

    # 住所
    zip_code = fields.CharField(max_length=10, null=True, description="郵便コード")
    address = fields.CharField(max_length=255, null=True, description="住所")
    work_address = fields.CharField(max_length=255, null=True, description="作業場所住所")

    # 外国人対応
    nationality = fields.CharField(max_length=50, null=True, description="国籍")
    visa_status = fields.CharEnumField(ResidenceStatus, null=True, description="在留資格")
    visa_expire_date = fields.DateField(null=True, description="在留期限")
    japanese_level = fields.CharEnumField(JapaneseLevel, null=True, description="日本語レベル")

    # 職歴・スキル関連
    total_experience_years = fields.DecimalField(max_digits=4, decimal_places=1, null=True, description="総経験年数")
    it_experience_years = fields.DecimalField(max_digits=4, decimal_places=1, null=True, description="IT経験年数")
    freelance_experience_years = fields.DecimalField(
        max_digits=4, decimal_places=1, null=True, description="フリーランス経験年数"
    )
    education_level = fields.CharField(max_length=100, null=True, description="最終学歴")
    major = fields.CharField(max_length=100, null=True, description="専攻")
    certifications = fields.TextField(null=True, description="保有資格（改行区切り）")

    # 単価・契約関連
    standard_unit_price = fields.DecimalField(
        max_digits=10, decimal_places=0, null=True, description="標準単価（月額）"
    )
    min_unit_price = fields.DecimalField(max_digits=10, decimal_places=0, null=True, description="最低受注単価")
    max_unit_price = fields.DecimalField(max_digits=10, decimal_places=0, null=True, description="最高受注単価")
    hourly_rate = fields.DecimalField(max_digits=10, decimal_places=0, null=True, description="時間単価")

    # 稼働状況
    employment_status = fields.CharEnumField(
        EmploymentStatus, default=EmploymentStatus.AVAILABLE, description="稼働ステータス"
    )
    is_active = fields.BooleanField(default=True, description="稼働可能かどうか")
    available_start_date = fields.DateField(null=True, description="稼働可能開始日")
    current_project_end_date = fields.DateField(null=True, description="現在プロジェクト終了予定日")

    # 希望条件
    preferred_location = fields.CharField(max_length=255, null=True, description="希望勤務地")
    preferred_project_type = fields.TextField(null=True, description="希望プロジェクト種別")
    preferred_work_style = fields.CharField(max_length=100, null=True, description="希望勤務形態（常駐/リモート等）")
    ng_client_companies = fields.TextField(null=True, description="NG取引先（改行区切り）")


    # その他
    photo_url = fields.CharField(max_length=500, null=True, description="写真URL")
    resume_url = fields.CharField(max_length=500, null=True, description="履歴書URL")
    portfolio_url = fields.CharField(max_length=500, null=True, description="ポートフォリオURL")
    website_url = fields.CharField(max_length=500, null=True, description="個人サイトURL")
    remark = fields.TextField(null=True, description="備考")

    # 関連
    case_candidates: fields.ReverseRelation["CaseCandidate"]
    skills: fields.ReverseRelation["FreelancerSkill"]
    contracts: fields.ReverseRelation["Contract"]
    evaluations: fields.ReverseRelation["FreelancerEvaluation"]

    class Meta:
        table = "ses_freelancer"
        table_description = "個人事業主"
        indexes = [
            ("employment_status",),
            ("nationality", "visa_status"),
            ("available_start_date",),
            ("standard_unit_price",),
        ]

    @property
    def current_age(self) -> int:
        """現在年齢を計算"""
        if not self.birthday:
            return self.age or 0

        from datetime import date

        today = date.today()
        return today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))

    def is_visa_expiring_soon(self, days: int = 90) -> bool:
        """ビザ期限が近いかチェック"""
        if not self.visa_expire_date:
            return False

        from datetime import date, timedelta

        return self.visa_expire_date <= date.today() + timedelta(days=days)

    @property
    def business_years(self) -> float:
        """開業からの年数を計算"""
        if not self.business_start_date:
            return 0.0

        from datetime import date

        today = date.today()
        days = (today - self.business_start_date).days
        return round(days / 365.25, 1)


class FreelancerSkill(BaseModel, TimestampMixin):
    """
    フリーランス技能関連表
    """

    freelancer = fields.ForeignKeyField("models.Freelancer", related_name="skills", description="フリーランス")
    skill = fields.ForeignKeyField("models.Skill", related_name="freelancers", description="技能")
    proficiency = fields.IntField(default=1, description="熟練度 (1-5)")
    years_of_experience = fields.DecimalField(max_digits=4, decimal_places=1, null=True, description="経験年数")
    last_used_date = fields.DateField(null=True, description="最終使用日")
    is_primary_skill = fields.BooleanField(default=False, description="主要スキルかどうか")
    remark = fields.TextField(null=True, description="備考（使用したプロジェクト等）")

    class Meta:
        table = "ses_freelancer_skill"
        table_description = "フリーランス技能関連"
        unique_together = (("freelancer", "skill"),)


class FreelancerEvaluation(BaseModel, TimestampMixin):
    """
    フリーランス評価記録（プロジェクト終了時の評価）
    """

    freelancer = fields.ForeignKeyField("models.Freelancer", related_name="evaluations", description="対象フリーランス")
    case = fields.ForeignKeyField(
        "models.Case", related_name="freelancer_evaluations", null=True, description="評価対象案件"
    )
    contract = fields.ForeignKeyField(
        "models.Contract", related_name="freelancer_evaluations", null=True, description="評価対象契約"
    )

    # 評価項目
    technical_skill = fields.IntField(description="技術力 (1-5)")
    communication = fields.IntField(description="コミュニケーション力 (1-5)")
    reliability = fields.IntField(description="信頼性 (1-5)")
    proactiveness = fields.IntField(description="積極性 (1-5)")
    independence = fields.IntField(description="自立性 (1-5)")  # フリーランス特有
    delivery_quality = fields.IntField(description="成果物品質 (1-5)")  # フリーランス特有
    overall_rating = fields.IntField(description="総合評価 (1-5)")

    # 詳細評価
    good_points = fields.TextField(null=True, description="良い点")
    improvement_points = fields.TextField(null=True, description="改善点")
    recommendation = fields.BooleanField(description="次回推薦可能か")

    # 評価者情報
    evaluator_id = fields.BigIntField(description="評価者ID")
    evaluation_date = fields.DateField(description="評価日")

    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "ses_freelancer_evaluation"
        table_description = "フリーランス評価記録"
