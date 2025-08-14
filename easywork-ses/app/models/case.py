from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import CandidateStatus, CaseStatus


class Case(BaseModel, TimestampMixin):
    """
    SES案件情報
    """

    title = fields.CharField(max_length=255, description="案件タイトル")
    client_company = fields.ForeignKeyField("models.ClientCompany", related_name="cases", description="取り先会社")
    location = fields.CharField(max_length=255, null=True, description="勤務地")
    # もっと最寄り駅
    station = fields.CharField(max_length=255, null=True, description="最寄り駅")

    # 期間
    start_date = fields.DateField(null=True, description="開始日")
    end_date = fields.DateField(null=True, description="終了日")

    # 条件
    required_skills = fields.TextField(null=True, description="必要スキル")
    preferred_skills = fields.TextField(null=True, description="歓迎スキル")
    unit_price = fields.DecimalField(max_digits=10, decimal_places=0, null=True, description="単価（月額）")
    required_members = fields.IntField(default=1, description="必要人数")

    # 管理
    status = fields.CharEnumField(CaseStatus, default=CaseStatus.OPEN, description="ステータス")
    manager = fields.BigIntField(null=True, description="案件マネージャーID")
    description = fields.TextField(null=True, description="詳細・備考")

    candidates: fields.ReverseRelation["CaseCandidate"]

    class Meta:
        table = "ses_case"
        table_description = "SES案件情報"


class CaseCandidate(BaseModel, TimestampMixin):
    """
    案件候補者（BP社員 / 自社社員 / フリーランス）をまとめて管理
    """

    case = fields.ForeignKeyField("models.Case", related_name="candidates", description="案件")

    # 三つの候補者タイプ（いずれか一つのみ設定）
    bp_employee = fields.ForeignKeyField(
        "models.BPEmployee", null=True, related_name="case_candidates", description="BP提供要員"
    )
    employee = fields.ForeignKeyField(
        "models.Employee", null=True, related_name="case_candidates", description="自社社員"
    )
    freelancer = fields.ForeignKeyField(
        "models.Freelancer", null=True, related_name="case_candidates", description="個人事業主"
    )

    # プロセス管理
    recommend_date = fields.DateField(null=True, description="推薦日")
    interview_date = fields.DatetimeField(null=True, description="面談日時")
    decision_date = fields.DateField(null=True, description="決定日")
    status = fields.CharEnumField(CandidateStatus, default=CandidateStatus.PENDING, description="状態")

    # 条件
    proposed_unit_price = fields.DecimalField(max_digits=10, decimal_places=0, null=True, description="提案単価")
    contract_start_date = fields.DateField(null=True, description="契約開始日")
    contract_end_date = fields.DateField(null=True, description="契約終了日")

    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "ses_case_candidate"
        table_description = "案件候補者（BP社員/自社社員/フリーランス）"
        # 一つの案件に対して同じ人は一度しか候補になれない制約
        unique_together = [("case", "bp_employee"), ("case", "employee"), ("case", "freelancer")]

    @property
    def candidate_name(self) -> str:
        """候補者名を取得"""
        if self.bp_employee:
            return self.bp_employee.name
        elif self.employee:
            return self.employee.name
        elif self.freelancer:
            return self.freelancer.name
        return "不明"

    @property
    def candidate_type(self) -> str:
        """候補者タイプを取得"""
        if self.bp_employee:
            return "BP社員"
        elif self.employee:
            return "自社社員"
        elif self.freelancer:
            return "フリーランス"
        return "不明"
