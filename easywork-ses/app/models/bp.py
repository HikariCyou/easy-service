from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import (BPCompanyStatus,
                              DecimalProcessingType,
                              EmploymentStatus, MarriageStatus)


class BPCompany(BaseModel, TimestampMixin):
    """
    SESのBP会社管理
    """

    name = fields.CharField(max_length=255, description="会社名")
    free_kana_name = fields.CharField(max_length=255, null=True, description="会社名（フリカナ）")
    representative = fields.CharField(max_length=100, null=True, description="代表者名")
    code = fields.CharField(max_length=50, null=True, description="会社コード", unique=True)
    tax_number = fields.CharField(max_length=50, null=True, description="法人番号 / 税番号")
    # 郵便コード
    zip_code = fields.CharField(max_length=10, null=True, description="郵便コード")
    address = fields.CharField(max_length=255, null=True, description="住所")
    phone = fields.CharField(max_length=50, null=True, description="電話番号", unique=True)
    email = fields.CharField(max_length=100, null=True, description="メール")
    website = fields.CharField(max_length=255, null=True, description="Webサイト")

    # 資本金
    capital = fields.CharField(max_length=50, null=True, description="資本金")
    # 設立月日
    established_date = fields.DateField(null=True, description="設立月日")

    status = fields.CharEnumField(
        BPCompanyStatus,
        null=True,
        default=BPCompanyStatus.ACTIVE,
        description="ステータス（active/inactive/blacklist）",
    )

    contract_start_date = fields.DateField(null=True, description="契約開始日")
    contract_end_date = fields.DateField(null=True, description="契約終了日")

    attendance_calc_type = fields.IntField(default=15, null=True, description="出勤計算区分")
    decimal_processing_type = fields.CharEnumField(
        DecimalProcessingType, default=DecimalProcessingType.ROUND, null=True, description="小数処理区分"
    )

    rating = fields.IntField(default=0, description="社内評価（1-5）")
    remark = fields.TextField(null=True, description="備考")
    employees: fields.ReverseRelation["BPEmployee"]

    class Meta:
        table = "ses_bp_company"
        table_description = "SESのBP会社管理"


class BPEmployee(BaseModel, TimestampMixin):
    bp_company = fields.ForeignKeyField("models.BPCompany", related_name="employees", description="所属BP会社")

    # 基本情報
    name = fields.CharField(max_length=100, description="氏名")
    code = fields.CharField(max_length=50, null=True, description="協力社員コード", unique=True)
    free_kana_name = fields.CharField(max_length=100, null=True, description="氏名（フリーカナ）")
    age = fields.IntField(null=True, description="年齢")
    sex = fields.IntField(null=True, default=0, description="性別")
    birthday = fields.DateField(null=True, description="生年月日")
    station = fields.CharField(max_length=255, null=True, description="最寄り駅")
    marriage_status = fields.CharEnumField(
        MarriageStatus, null=True, default=MarriageStatus.SINGLE, description="婚姻ステータス"
    )

    # 連絡先
    phone = fields.CharField(max_length=50, null=True, description="電話番号")
    email = fields.CharField(max_length=100, null=True, description="メール")
    emergency_contact_name = fields.CharField(max_length=100, null=True, description="緊急連絡先氏名")
    emergency_contact_phone = fields.CharField(max_length=50, null=True, description="緊急連絡先電話")
    emergency_contact_relation = fields.CharField(max_length=50, null=True, description="緊急連絡先続柄")

    zip_code = fields.CharField(max_length=10, null=True, description="郵便コード")
    address = fields.CharField(max_length=255, null=True, description="住所")

    # 外国人対応
    nationality = fields.CharField(max_length=50, null=True, description="国籍")
    visa_status = fields.CharField(max_length=255, null=True, description="在留資格")
    visa_expire_date = fields.DateField(null=True, description="在留期限")
    japanese_level = fields.CharField(max_length=25, null=True, description="日本語レベル")

    # 職歴・スキル関連
    total_experience_years = fields.DecimalField(max_digits=4, decimal_places=1, null=True, description="総経験年数")
    it_experience_years = fields.DecimalField(max_digits=4, decimal_places=1, null=True, description="IT経験年数")
    education_level = fields.CharField(max_length=100, null=True, description="最終学歴")
    major = fields.CharField(max_length=100, null=True, description="専攻")
    certifications = fields.TextField(null=True, description="保有資格（改行区切り）")

    # 単価
    standard_unit_price = fields.DecimalField(
        max_digits=10, decimal_places=0, null=True, description="標準単価（月額）"
    )
    min_unit_price = fields.DecimalField(max_digits=10, decimal_places=0, null=True, description="最低受注単価")
    max_unit_price = fields.DecimalField(max_digits=10, decimal_places=0, null=True, description="最高受注単価")

    # 稼働状況
    employment_status = fields.CharEnumField(
        EmploymentStatus, default=EmploymentStatus.AVAILABLE, description="稼働ステータス"
    )
    available_start_date = fields.DateField(null=True, description="稼働可能開始日")
    current_project_end_date = fields.DateField(null=True, description="現在プロジェクト終了予定日")

    # 希望条件
    preferred_location = fields.CharField(max_length=255, null=True, description="希望勤務地")
    remote_work_available = fields.BooleanField(default=False, description="リモート可能")
    overtime_available = fields.BooleanField(default=False, description="残業可能")
    interview_available = fields.BooleanField(default=False, description="面談可能")

    # その他
    photo_url = fields.CharField(max_length=500, null=True, description="写真URL")
    resume_url = fields.CharField(max_length=500, null=True, description="履歴書URL")
    portfolio_url = fields.CharField(max_length=500, null=True, description="ポートフォリオURL")
    remark = fields.TextField(null=True, description="備考")
    is_active = fields.BooleanField(default=True, description="ユーザー有効フラグ")

    # 関連
    case_candidates: fields.ReverseRelation["CaseCandidate"]
    skills: fields.ReverseRelation["BPEmployeeSkill"]
    contracts: fields.ReverseRelation["Contract"]
    evaluations: fields.ReverseRelation["BPEmployeeEvaluation"]

    class Meta:
        table = "ses_bp_employee"
        table_description = "BP提供の要員情報"
        indexes = [
            ("bp_company", "employment_status"),
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


class BPEmployeeSkill(BaseModel, TimestampMixin):
    """
    BP员工与技能的关联表
    """

    bp_employee = fields.ForeignKeyField("models.BPEmployee", related_name="skills", description="BP员工")
    skill = fields.ForeignKeyField("models.Skill", related_name="bp_employees", description="技能")
    proficiency = fields.IntField(default=1, description="熟练度 (1-5)")
    years_of_experience = fields.DecimalField(max_digits=4, decimal_places=1, null=True, description="经验年限")
    last_used_date = fields.DateField(null=True, description="最終使用日")
    is_primary_skill = fields.BooleanField(default=False, description="主要スキルかどうか")
    remark = fields.TextField(null=True, description="備考（使用したプロジェクト等）")

    class Meta:
        table = "ses_bp_employee_skill"
        table_description = "BP员工与技能关联"
        unique_together = (("bp_employee", "skill"),)


class BPEmployeeEvaluation(BaseModel, TimestampMixin):
    """
    BP員工評価記録（プロジェクト終了時の評価）
    """

    bp_employee = fields.ForeignKeyField("models.BPEmployee", related_name="evaluations", description="対象BP員工")
    case = fields.ForeignKeyField("models.Case", related_name="bp_evaluations", null=True, description="評価対象案件")
    contract = fields.ForeignKeyField(
        "models.Contract", related_name="evaluations", null=True, description="評価対象契約"
    )

    # 評価項目
    technical_skill = fields.IntField(description="技術力 (1-5)")
    communication = fields.IntField(description="コミュニケーション力 (1-5)")
    reliability = fields.IntField(description="信頼性 (1-5)")
    proactiveness = fields.IntField(description="積極性 (1-5)")
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
        table = "ses_bp_employee_evaluation"
        table_description = "BP員工評価記録"
