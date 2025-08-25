from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import CandidateStatus, CaseStatus, ChangeType


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

    # 統一Personnel使用（polymorphic reference）
    personnel = fields.ForeignKeyField("models.Personnel", null=True, related_name="case_candidates", description="候補人材")
    
    # 下記フィールドは後方互換性のため保留（新統一システムではpersonnelを使用）
    # bp_employee = fields.ForeignKeyField("models.BPEmployee", null=True, related_name="case_candidates", description="BP提供要員")
    # employee = fields.ForeignKeyField("models.Employee", null=True, related_name="case_candidates", description="自社社員")
    # freelancer = fields.ForeignKeyField("models.Freelancer", null=True, related_name="case_candidates", description="個人事業主")

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
        unique_together = [("case", "personnel")]

    @property
    def candidate_name(self) -> str:
        """候補者名を取得"""
        if self.personnel:
            return self.personnel.name
        return "不明"

    @property
    def candidate_type(self) -> str:
        """候補者タイプを取得"""
        if self.personnel:
            from app.models.enums import PersonType
            type_mapping = {
                PersonType.BP_EMPLOYEE: "BP社員",
                PersonType.EMPLOYEE: "自社社員",
                PersonType.FREELANCER: "フリーランス"
            }
            return type_mapping.get(self.personnel.person_type, "不明")
        return "不明"


class CaseHistory(BaseModel, TimestampMixin):
    """
    案件変更履歴
    """
    
    case = fields.ForeignKeyField("models.Case", related_name="history", description="案件")
    change_type = fields.CharEnumField(ChangeType, description="変更タイプ")
    
    # 変更者情報
    changed_by = fields.BigIntField(description="変更者ユーザーID")
    changed_by_name = fields.CharField(max_length=100, null=True, description="変更者名")
    
    # 変更内容
    field_name = fields.CharField(max_length=100, null=True, description="変更フィールド名")
    old_value = fields.TextField(null=True, description="変更前の値")
    new_value = fields.TextField(null=True, description="変更後の値")
    
    # 変更詳細（JSON形式で複数フィールドの変更を記録）
    change_details = fields.JSONField(null=True, description="変更詳細（JSON）")
    
    # 変更理由・コメント
    comment = fields.TextField(null=True, description="変更理由・コメント")
    
    # IP アドレス（監査用）
    ip_address = fields.CharField(max_length=45, null=True, description="変更者IPアドレス")
    
    class Meta:
        table = "ses_case_history"
        table_description = "案件変更履歴"
        ordering = ["-created_at"]
