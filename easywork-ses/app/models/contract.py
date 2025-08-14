from datetime import datetime
from decimal import Decimal

from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import ContractStatus, ContractType


class Contract(BaseModel, TimestampMixin):
    """
    SES契約管理（個別契約）
    """

    # 契約基本情報
    contract_number = fields.CharField(max_length=50, unique=True, description="契約番号")
    contract_type = fields.CharEnumField(ContractType, description="契約種別（BP/自社/フリーランス）")

    # 関連
    case = fields.ForeignKeyField("models.Case", related_name="contracts", description="案件")
    bp_employee = fields.ForeignKeyField("models.BPEmployee", null=True, related_name="contracts", description="BP社員")
    employee = fields.ForeignKeyField("models.Employee", null=True, related_name="contracts", description="自社社員")
    freelancer = fields.ForeignKeyField(
        "models.Freelancer", null=True, related_name="contracts", description="フリーランス"
    )

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
    overtime_rate = fields.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("1.25"), description="超過時間単価倍率"
    )
    shortage_rate = fields.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("1.00"), description="不足時間単価倍率"
    )

    # 超過・不足時間の計算基準
    min_guaranteed_hours = fields.DecimalField(
        max_digits=5, decimal_places=1, null=True, description="最低保証時間（この時間までは満額支払い）"
    )
    free_overtime_hours = fields.DecimalField(
        max_digits=5, decimal_places=1, default=Decimal("0.0"), description="無償残業時間（この時間までは追加料金なし）"
    )

    # ステータス
    status = fields.CharEnumField(ContractStatus, default=ContractStatus.ACTIVE, description="契約ステータス")

    # 備考
    remark = fields.TextField(null=True, description="特記事項")

    # 関連
    attendances: fields.ReverseRelation["Attendance"]

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
        if self.bp_employee:
            return self.bp_employee.name
        elif self.employee:
            return self.employee.name
        elif self.freelancer:
            return self.freelancer.name
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
