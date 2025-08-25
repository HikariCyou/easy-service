from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import PersonType


class PersonEvaluation(BaseModel, TimestampMixin):
    """
    統一人材評価記録（プロジェクト終了時の評価）
    Personnel統一モデルに対応
    """

    # 評価対象の指定（polymorphic reference）
    person_type = fields.CharEnumField(PersonType, description="人材タイプ（bp_employee/freelancer/employee）")
    person_id = fields.BigIntField(description="対象人材ID")
    
    # 案件・契約情報
    case = fields.ForeignKeyField(
        "models.Case", related_name="person_evaluations", null=True, description="評価対象案件"
    )
    contract = fields.ForeignKeyField(
        "models.Contract", related_name="person_evaluations", null=True, description="評価対象契約"
    )

    # 共通評価項目
    technical_skill = fields.IntField(description="技術力 (1-5)")
    communication = fields.IntField(description="コミュニケーション力 (1-5)")
    reliability = fields.IntField(description="信頼性 (1-5)")
    proactiveness = fields.IntField(description="積極性 (1-5)")
    independence = fields.IntField(null=True, description="自立性 (1-5) ※フリーランス・自社員工のみ")
    delivery_quality = fields.IntField(null=True, description="成果物品質 (1-5) ※フリーランス・自社員工のみ")
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
        table = "ses_person_evaluation"
        table_description = "統一人材評価記録"
        indexes = [
            ("person_type", "person_id"),
            ("case_id",),
            ("contract_id",),
            ("evaluation_date",),
            ("overall_rating",),
        ]

    @property
    def person_name(self) -> str:
        """評価対象の名前を取得（表示用）"""
        return f"{self.person_type.upper()}-{self.person_id}"

    def has_extended_fields(self) -> bool:
        """拡張フィールド（independence、delivery_quality）を持つかどうか"""
        return self.person_type in [PersonType.FREELANCER, PersonType.EMPLOYEE]

    async def get_person_object(self):
        """評価対象の実際のオブジェクトを取得"""
        from app.models.personnel import Personnel
        return await Personnel.get_or_none(id=self.person_id, person_type=self.person_type)

    async def get_person_name(self) -> str:
        """評価対象の実際の名前を取得"""
        person = await self.get_person_object()
        return person.name if person else f"Unknown-{self.person_id}"