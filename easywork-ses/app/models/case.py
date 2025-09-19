from datetime import datetime

from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import (
    BusinessClassification,
    CandidateStatus,
    CaseStatus,
    ChangeType,
    ContractCompanyType,
)


class Case(BaseModel, TimestampMixin):
    """
    SES案件情報
    """

    title = fields.CharField(max_length=255, description="案件タイトル")
    client_company = fields.ForeignKeyField("models.ClientCompany", related_name="cases", description="取り先会社")

    # 営業担当
    client_sales_representative = fields.ForeignKeyField(
        "models.ClientContact", null=True, related_name="managed_cases", description="取引先担当営業"
    )
    company_sales_representative = fields.ForeignKeyField(
        "models.Personnel", null=True, related_name="sales_managed_cases", description="自社担当営業"
    )

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

    # 追加フィールド
    contract_company_type = fields.CharEnumField(ContractCompanyType, null=True, description="契約会社種別")
    business_classification = fields.CharEnumField(BusinessClassification, null=True, description="事業分類")
    department = fields.CharField(max_length=255, null=True, description="所属部署")

    candidates: fields.ReverseRelation["CaseCandidate"]
    contracts: fields.ReverseRelation["Contract"]

    class Meta:
        table = "ses_case"
        table_description = "SES案件情報"

    async def terminate_case(self, termination_date: datetime = None, reason: str = "案件終了", terminated_by: str = None):
        """
        案件終了処理：案件を終了し、関連する全契約も終了する
        """
        from tortoise.transactions import in_transaction

        from app.models.enums import (
            CaseStatus,
            ContractChangeReason,
            ContractChangeType,
            ContractStatus,
        )

        if termination_date is None:
            termination_date = datetime.now().date()

        async with in_transaction():
            # 1. 案件ステータスを終了に変更
            original_status = self.status
            self.status = CaseStatus.CLOSED
            self.end_date = termination_date
            await self.save()

            # 2. 関連する有効な契約を全て取得
            active_contracts = await self.contracts.filter(status=ContractStatus.ACTIVE).prefetch_related("personnel")

            if not active_contracts:
                return {"message": "案件を終了しましたが、有効な契約は見つかりませんでした", "terminated_contracts": 0}

            # 3. 各契約を終了処理
            terminated_contracts = []
            for contract in active_contracts:
                try:
                    # 契約終了処理
                    await contract.terminate_early(
                        reason=ContractChangeReason.PROJECT_CHANGE,
                        termination_date=termination_date,
                        requested_by=terminated_by or "システム自動（案件終了）",
                        description=f"案件終了による契約終了: {reason}",
                    )

                    terminated_contracts.append(
                        {
                            "contract_id": contract.id,
                            "contract_number": contract.contract_number,
                            "personnel_name": contract.personnel.name if contract.personnel else "不明",
                            "original_end_date": contract.contract_end_date.isoformat()
                            if contract.contract_end_date
                            else None,
                            "new_end_date": termination_date.isoformat(),
                        }
                    )

                except Exception as e:
                    # 個別契約の終了に失敗してもログを残して続行
                    print(f"契約ID {contract.id} の終了処理でエラー: {e}")
                    continue

            # 4. 案件変更履歴を記録
            try:
                from app.models.case import CaseHistory
                from app.models.enums import ChangeType

                await CaseHistory.create(
                    case=self,
                    change_type=ChangeType.STATUS_CHANGE,
                    old_value=original_status,
                    new_value=CaseStatus.CLOSED,
                    change_reason=reason,
                    changed_by=terminated_by or "システム",
                    description=f"案件終了処理により {len(terminated_contracts)} 件の契約も終了",
                )
            except Exception as e:
                # 履歴記録の失敗は処理を続行
                print(f"案件履歴記録でエラー: {e}")

            return {
                "message": f"案件を終了しました。{len(terminated_contracts)}件の契約も終了されました。",
                "case_id": self.id,
                "case_title": self.title,
                "termination_date": termination_date.isoformat(),
                "terminated_contracts": len(terminated_contracts),
                "contract_details": terminated_contracts,
            }


class CaseCandidate(BaseModel, TimestampMixin):
    """
    案件候補者（BP社員 / 自社社員 / フリーランス）をまとめて管理
    """

    case = fields.ForeignKeyField("models.Case", related_name="candidates", description="案件")

    # 統一Personnel使用（polymorphic reference）
    personnel = fields.ForeignKeyField(
        "models.Personnel", null=True, related_name="case_candidates", description="候補人材"
    )

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
                PersonType.FREELANCER: "フリーランス",
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
