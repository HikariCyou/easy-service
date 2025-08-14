from decimal import Decimal

from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.contract import Contract
from app.models.enums import AttendanceType


class DailyAttendance(BaseModel, TimestampMixin):
    """
    日次出勤記録
    """

    contract = fields.ForeignKeyField("models.Contract", related_name="daily_attendances", description="対象契約")
    work_date = fields.DateField(description="勤務日")

    # 出退勤時刻
    start_time = fields.TimeField(null=True, description="出勤時刻")
    end_time = fields.TimeField(null=True, description="退勤時刻")

    # 休憩時間
    break_minutes = fields.IntField(default=60, description="休憩時間（分）")

    # 実働時間
    actual_working_hours = fields.DecimalField(max_digits=4, decimal_places=1, null=True, description="実働時間")

    # 出勤区分
    attendance_type = fields.CharEnumField(AttendanceType, default=AttendanceType.NORMAL, description="出勤区分")

    # 承認状況
    is_approved = fields.BooleanField(default=False, description="承認済みフラグ")
    approved_at = fields.DatetimeField(null=True, description="承認日時")
    approved_by = fields.BigIntField(null=True, description="承認者ID")

    # 備考
    remark = fields.TextField(null=True, description="備考（遅刻・早退理由等）")

    class Meta:
        table = "ses_daily_attendance"
        table_description = "日次出勤記録"
        unique_together = [("contract", "work_date")]

    def calculate_working_hours(self) -> Decimal:
        """実働時間を計算"""
        if not self.start_time or not self.end_time:
            return Decimal("0.0")

        # 時刻を分に変換
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute

        # 跨日対応
        if end_minutes < start_minutes:
            end_minutes += 24 * 60

        # 実働時間計算（休憩時間を除く）
        total_minutes = end_minutes - start_minutes - self.break_minutes
        hours = Decimal(str(total_minutes / 60)).quantize(Decimal("0.1"))

        return max(hours, Decimal("0.0"))

    async def save(self, *args, **kwargs):
        """保存時に実働時間を自動計算"""
        if self.start_time and self.end_time and self.attendance_type == "NORMAL":
            self.actual_working_hours = self.calculate_working_hours()
        elif self.attendance_type in ["PAID_LEAVE", "SICK_LEAVE"]:
            # 有給・病気休暇の場合は標準時間を設定
            contract = await Contract.get(id=self.contract_id)
            daily_standard = contract.standard_working_hours / Decimal("22")  # 月22日想定
            self.actual_working_hours = daily_standard.quantize(Decimal("0.1"))
        else:
            self.actual_working_hours = Decimal("0.0")

        await super().save(*args, **kwargs)


class MonthlyAttendance(BaseModel, TimestampMixin):
    """
    月次出勤集計
    """

    contract = fields.ForeignKeyField("models.Contract", related_name="monthly_attendances", description="対象契約")
    year_month = fields.CharField(max_length=7, description="対象年月（YYYY-MM）")

    # 集計結果
    total_working_hours = fields.DecimalField(max_digits=6, decimal_places=1, description="総実働時間")
    working_days = fields.IntField(description="出勤日数")
    paid_leave_days = fields.IntField(default=0, description="有給取得日数")
    absence_days = fields.IntField(default=0, description="欠勤日数")
    late_count = fields.IntField(default=0, description="遅刻回数")
    early_leave_count = fields.IntField(default=0, description="早退回数")

    # 計算結果
    base_payment = fields.DecimalField(max_digits=10, decimal_places=0, description="基本給")
    overtime_payment = fields.DecimalField(
        max_digits=10, decimal_places=0, default=Decimal("0"), description="超過時間手当"
    )
    shortage_deduction = fields.DecimalField(
        max_digits=10, decimal_places=0, default=Decimal("0"), description="不足時間控除"
    )
    total_payment = fields.DecimalField(max_digits=10, decimal_places=0, description="支払総額")

    # 詳細計算情報
    overtime_hours = fields.DecimalField(max_digits=5, decimal_places=1, default=Decimal("0.0"), description="超過時間")
    shortage_hours = fields.DecimalField(max_digits=5, decimal_places=1, default=Decimal("0.0"), description="不足時間")
    calculation_details = fields.JSONField(null=True, description="計算詳細（JSON）")

    # ステータス管理
    is_calculated = fields.BooleanField(default=False, description="計算済みフラグ")
    is_confirmed = fields.BooleanField(default=False, description="確定フラグ")
    confirmed_at = fields.DatetimeField(null=True, description="確定日時")
    confirmed_by = fields.BigIntField(null=True, description="確定者ID")

    remark = fields.TextField(null=True, description="備考")

    class Meta:
        table = "ses_monthly_attendance"
        table_description = "月次出勤集計"
        unique_together = [("contract", "year_month")]

    async def calculate_from_daily_records(self):
        """日次記録から月次集計を計算"""

        # 対象年月の解析
        year, month = map(int, self.year_month.split("-"))

        # 該当月の日次記録を取得
        daily_records = await DailyAttendance.filter(
            contract=self.contract, work_date__year=year, work_date__month=month, is_approved=True
        ).all()

        # 集計計算
        self.total_working_hours = sum(record.actual_working_hours or Decimal("0.0") for record in daily_records)

        self.working_days = len([r for r in daily_records if r.attendance_type == "NORMAL"])
        self.paid_leave_days = len([r for r in daily_records if r.attendance_type == "PAID_LEAVE"])
        self.absence_days = len([r for r in daily_records if r.attendance_type == "ABSENCE"])
        self.late_count = len([r for r in daily_records if r.attendance_type == "LATE"])
        self.early_leave_count = len([r for r in daily_records if r.attendance_type == "EARLY_LEAVE"])

        # 支払額計算
        contract = await Contract.get(id=self.contract_id)
        payment_info = contract.calculate_monthly_payment(self.total_working_hours)

        self.base_payment = payment_info["base_payment"]
        self.overtime_payment = payment_info["overtime_payment"]
        self.shortage_deduction = payment_info["shortage_deduction"]
        self.total_payment = payment_info["total_payment"]
        self.overtime_hours = payment_info.get("overtime_hours", Decimal("0.0"))
        self.shortage_hours = payment_info.get("shortage_hours", Decimal("0.0"))
        self.calculation_details = payment_info

        self.is_calculated = True
        await self.save()
