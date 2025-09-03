from datetime import datetime
from decimal import Decimal

from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import ContractStatus, ContractType, ContractChangeType, ContractChangeReason


class Contract(BaseModel, TimestampMixin):
    """
    SES契約管理（個別契約）
    """

    # 契約基本情報
    contract_number = fields.CharField(max_length=50, unique=True, description="契約番号")
    contract_type = fields.CharEnumField(ContractType, description="契約種別（BP/自社/フリーランス）")

    # 関連
    case = fields.ForeignKeyField("models.Case", related_name="contracts", description="案件")
    # 統一Personnel使用（polymorphic reference）
    personnel = fields.ForeignKeyField("models.Personnel", null=True, related_name="contracts", description="契約人材")
    
    # 下記フィールドは後方互換性のため保留（新統一システムではpersonnelを使用）
    # bp_employee = fields.ForeignKeyField("models.BPEmployee", null=True, related_name="contracts", description="BP社員")
    # employee = fields.ForeignKeyField("models.Employee", null=True, related_name="contracts", description="自社社員")
    # freelancer = fields.ForeignKeyField("models.Freelancer", null=True, related_name="contracts", description="フリーランス")

    # 契約期間
    contract_start_date = fields.DateField(description="契約開始日")
    contract_end_date = fields.DateField(description="契約終了日")

    # 単価・条件
    unit_price = fields.DecimalField(max_digits=10, decimal_places=0, description="基本単価（月額）")

    # 出勤時間管理（重要な部分）
    standard_working_hours = fields.DecimalField(
        max_digits=5, decimal_places=1, default=Decimal("160.0"), description="標準稼働時間/月"
    )
    min_working_hours = fields.DecimalField(
        max_digits=5, decimal_places=1, null=True, description="最低稼働時間/月（下限）"
    )
    max_working_hours = fields.DecimalField(
        max_digits=5, decimal_places=1, null=True, description="最高稼働時間/月（上限）"
    )

    # 超過・不足時の処理
    overtime_rate = fields.FloatField(null=True,default=float("1.00"), description="超過時間単価倍率"
    )
    shortage_rate = fields.FloatField(null=True, default=float("1.00"), description="不足時間単価倍率"
    )

    # 超過・不足時間の計算基準
    min_guaranteed_hours = fields.FloatField(
        null=True, description="最低保証時間（この時間までは満額支払い）"
    )
    free_overtime_hours = fields.FloatField(default=float("0.0"), description="無償残業時間（この時間までは追加料金なし）"
    )

    # ステータス
    status = fields.CharEnumField(ContractStatus, default=ContractStatus.ACTIVE, description="契約ステータス")

    # 備考
    remark = fields.TextField(null=True, description="特記事項")

    # 関連
    attendances: fields.ReverseRelation["Attendance"]
    change_histories: fields.ReverseRelation["ContractChangeHistory"]
    amendments: fields.ReverseRelation["ContractAmendment"]

    class Meta:
        table = "ses_contract"
        table_description = "SES個別契約管理"

    @property
    def is_active(self) -> bool:
        """契約が有効かどうかを取得"""
        active = True
        if self.status != ContractStatus.ACTIVE.value:
            active = False
        # 契約期間が過去かどうかを確認
        if self.contract_end_date and datetime.now().date() > self.contract_end_date:
            active = False

        return active

    @property
    def contractor_name(self) -> str:
        """契約者名を取得"""
        if self.personnel:
            return self.personnel.name
        return "不明"

    def calculate_monthly_payment(self, actual_hours: Decimal) -> dict:
        """月額支払い金額を計算"""
        result = {
            "base_payment": self.unit_price,
            "overtime_payment": Decimal("0"),
            "shortage_deduction": Decimal("0"),
            "total_payment": self.unit_price,
            "actual_hours": actual_hours,
            "details": [],
        }

        # 最低保証時間がある場合の処理
        if self.min_guaranteed_hours and actual_hours < self.min_guaranteed_hours:
            # 最低保証時間までは満額支払い
            guaranteed_payment = self.unit_price
            result["details"].append(f"最低保証時間適用: {self.min_guaranteed_hours}h")
        else:
            guaranteed_payment = self.unit_price

        # 上限を超えた場合の超過料金計算
        if self.max_working_hours and actual_hours > self.max_working_hours:
            # 無償残業時間を考慮
            billable_overtime = actual_hours - self.max_working_hours - self.free_overtime_hours
            if billable_overtime > 0:
                hourly_rate = self.unit_price / self.standard_working_hours
                overtime_payment = hourly_rate * billable_overtime * self.overtime_rate
                result["overtime_payment"] = overtime_payment
                result["details"].append(f"超過時間: {billable_overtime}h × {self.overtime_rate}")

        # 下限を下回った場合の減額計算
        if self.min_working_hours and actual_hours < self.min_working_hours:
            if not (self.min_guaranteed_hours and actual_hours >= self.min_guaranteed_hours):
                shortage_hours = self.min_working_hours - actual_hours
                hourly_rate = self.unit_price / self.standard_working_hours
                shortage_deduction = hourly_rate * shortage_hours * (Decimal("1.00") - self.shortage_rate)
                result["shortage_deduction"] = shortage_deduction
                result["details"].append(f"不足時間: {shortage_hours}h × {1.00 - self.shortage_rate}")

        result["total_payment"] = guaranteed_payment + result["overtime_payment"] - result["shortage_deduction"]
        return result

    async def record_change(self, change_type: ContractChangeType, change_reason: ContractChangeReason = None, 
                           before_values: dict = None, after_values: dict = None, 
                           description: str = None, effective_date = None, 
                           requested_by: str = None, approved_by: str = None):
        """
        契約変更履歴を記録
        """
        # 避免循环导入，直接使用类
        
        change_history = await ContractChangeHistory.create(
            contract=self,
            change_type=change_type,
            change_reason=change_reason,
            before_values=before_values,
            after_values=after_values,
            change_description=description,
            effective_date=effective_date,
            requested_by=requested_by,
            approved_by=approved_by
        )
        return change_history

    async def get_recent_changes(self, limit: int = 10):
        """
        最近の変更履歴を取得
        """
        return await self.change_histories.all().order_by("-created_at").limit(limit)

    async def terminate_early(self, reason: ContractChangeReason, termination_date, 
                             requested_by: str = None, description: str = None):
        """
        早期解約処理
        """
        before_values = {
            "status": self.status,
            "contract_end_date": str(self.contract_end_date)
        }
        
        # ステータスと終了日を更新
        self.status = ContractStatus.TERMINATED
        self.contract_end_date = termination_date
        await self.save()
        
        after_values = {
            "status": self.status,
            "contract_end_date": str(self.contract_end_date)
        }
        
        # 変更履歴を記録
        await self.record_change(
            change_type=ContractChangeType.EARLY_TERMINATION,
            change_reason=reason,
            before_values=before_values,
            after_values=after_values,
            description=description or f"契約を{termination_date}に早期終了",
            effective_date=termination_date,
            requested_by=requested_by
        )

    async def update_conditions(self, new_unit_price: Decimal = None, 
                               new_working_hours: Decimal = None,
                               reason: ContractChangeReason = ContractChangeReason.CLIENT_REQUEST,
                               effective_date = None, requested_by: str = None):
        """
        契約条件変更処理
        """
        before_values = {}
        after_values = {}
        changes = []
        
        if new_unit_price is not None:
            before_values["unit_price"] = str(self.unit_price)
            self.unit_price = new_unit_price
            after_values["unit_price"] = str(self.unit_price)
            changes.append(f"単価: {before_values['unit_price']}円 → {after_values['unit_price']}円")
            
        if new_working_hours is not None:
            before_values["standard_working_hours"] = str(self.standard_working_hours)
            self.standard_working_hours = new_working_hours
            after_values["standard_working_hours"] = str(self.standard_working_hours)
            changes.append(f"標準稼働時間: {before_values['standard_working_hours']}h → {after_values['standard_working_hours']}h")
        
        if changes:
            await self.save()
            
            # 変更履歴を記録
            await self.record_change(
                change_type=ContractChangeType.CONDITION_CHANGE,
                change_reason=reason,
                before_values=before_values,
                after_values=after_values,
                description="契約条件変更: " + ", ".join(changes),
                effective_date=effective_date,
                requested_by=requested_by
            )


class ContractChangeHistory(BaseModel, TimestampMixin):
    """
    契約変更履歴
    契約の変更・更新・解約等の操作履歴を記録
    """
    
    # 関連する契約
    contract = fields.ForeignKeyField("models.Contract", related_name="change_histories", description="対象契約")
    
    # 変更情報
    change_type = fields.CharEnumField(ContractChangeType, description="変更種別")
    change_reason = fields.CharEnumField(ContractChangeReason, null=True, description="変更理由")
    
    # 変更前後の値（JSON形式で格納）
    before_values = fields.JSONField(null=True, description="変更前の値")
    after_values = fields.JSONField(null=True, description="変更後の値")
    
    # 変更詳細
    change_description = fields.TextField(null=True, description="変更内容の詳細説明")
    
    # 効力発生日
    effective_date = fields.DateField(null=True, description="変更効力発生日")
    
    # 申請・承認情報
    requested_by = fields.CharField(max_length=100, null=True, description="変更申請者")
    approved_by = fields.CharField(max_length=100, null=True, description="変更承認者")
    approval_date = fields.DatetimeField(null=True, description="承認日時")
    
    # 関連ファイル・文書
    attachment_files = fields.JSONField(null=True, description="添付ファイル情報")
    
    # 備考
    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "ses_contract_change_history"
        table_description = "契約変更履歴"
        indexes = [
            ("contract_id", "change_type"),
            ("effective_date",),
            ("created_at",),
        ]

    def __str__(self):
        return f"契約{self.contract.contract_number} - {self.change_type} ({self.created_at.strftime('%Y-%m-%d')})"


class ContractAmendment(BaseModel, TimestampMixin):
    """
    契約修正書（契約変更の正式文書）
    重要な契約変更時に作成される修正契約書の管理
    """
    
    # 元契約
    original_contract = fields.ForeignKeyField("models.Contract", related_name="amendments", description="元契約")
    
    # 修正書基本情報
    amendment_number = fields.CharField(max_length=50, unique=True, description="修正書番号")
    amendment_title = fields.CharField(max_length=200, description="修正書タイトル")
    
    # 修正内容
    amendment_type = fields.CharEnumField(ContractChangeType, description="修正種別")
    amendment_reason = fields.CharEnumField(ContractChangeReason, description="修正理由")
    amendment_details = fields.TextField(description="修正内容詳細")
    
    # 期間
    effective_start_date = fields.DateField(description="修正効力開始日")
    effective_end_date = fields.DateField(null=True, description="修正効力終了日")
    
    # 修正後の契約条件（主要項目のみ）
    new_unit_price = fields.DecimalField(max_digits=10, decimal_places=0, null=True, description="修正後単価")
    new_contract_end_date = fields.DateField(null=True, description="修正後契約終了日")
    new_working_hours = fields.DecimalField(max_digits=5, decimal_places=1, null=True, description="修正後標準稼働時間")
    
    # 承認・署名情報
    client_approved = fields.BooleanField(default=False, description="クライアント承認")
    client_approved_date = fields.DatetimeField(null=True, description="クライアント承認日")
    client_signature = fields.CharField(max_length=100, null=True, description="クライアント署名者")
    
    company_approved = fields.BooleanField(default=False, description="自社承認")
    company_approved_date = fields.DatetimeField(null=True, description="自社承認日") 
    company_signature = fields.CharField(max_length=100, null=True, description="自社署名者")
    
    personnel_acknowledged = fields.BooleanField(default=False, description="人材確認")
    personnel_acknowledged_date = fields.DatetimeField(null=True, description="人材確認日")
    
    # 文書管理
    document_path = fields.CharField(max_length=500, null=True, description="修正書ファイルパス")
    digital_signature = fields.TextField(null=True, description="デジタル署名")
    
    # ステータス
    status = fields.CharField(max_length=20, default="草案", description="修正書ステータス")  # 草案、承認待ち、承認済み、発効中、終了
    
    class Meta:
        table = "ses_contract_amendment"
        table_description = "契約修正書"
        indexes = [
            ("original_contract_id",),
            ("effective_start_date",),
            ("status",),
        ]

    @property
    def is_effective(self) -> bool:
        """修正書が有効かどうか"""
        from datetime import date
        today = date.today()
        
        if self.status != "発効中":
            return False
            
        if today < self.effective_start_date:
            return False
            
        if self.effective_end_date and today > self.effective_end_date:
            return False
            
        return True

    @property 
    def all_parties_approved(self) -> bool:
        """全当事者の承認が完了しているか"""
        return (self.client_approved and 
                self.company_approved and 
                self.personnel_acknowledged)

    def __str__(self):
        return f"{self.amendment_number} - {self.amendment_title}"
