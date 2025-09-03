import math
from datetime import datetime, timedelta, date

from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.contract import Contract
from app.models.enums import AttendanceType, ApproveStatus, DecimalProcessingType, WeeklyMoodStatus


class DailyAttendance(BaseModel, TimestampMixin):
    """
    日次出勤記録
    """
    user_id = fields.BigIntField(default=None , null=True, description="user_id")

    contract = fields.ForeignKeyField("models.Contract", related_name="daily_attendances", description="対象契約" , null=True)
    work_date = fields.DateField(description="勤務日")

    # 出退勤時刻
    start_time = fields.TimeField(null=True, description="出勤時刻")
    end_time = fields.TimeField(null=True, description="退勤時刻")

    # 休憩時間（詳細）
    lunch_break_minutes = fields.IntField(default=60, description="昼休憩時間（分）")
    evening_break_minutes = fields.IntField(default=0, description="夜休憩時間（分）")
    other_break_minutes = fields.IntField(default=0, description="その他休憩時間（分）")

    # 実働時間は計算プロパティとして定義（下記参照）

    # 出勤区分
    attendance_type = fields.CharEnumField(AttendanceType, default=AttendanceType.NORMAL, description="出勤区分")

    # 日次考勤记录不需要审批状态，审批在月次层面进行
    # approved_status 已移至 MonthlyAttendance
    # approved_at = fields.DatetimeField(null=True, description="承認日時")
    # approved_by = fields.BigIntField(null=True, description="承認者ID")

    # 備考
    remark = fields.TextField(null=True, description="備考（遅刻・早退理由等）")

    class Meta:
        table = "ses_daily_attendance"
        table_description = "日次出勤記録"
        unique_together = [("contract", "work_date")]

    @property
    def total_break_minutes(self) -> int:
        """総休憩時間を計算"""
        return self.lunch_break_minutes + self.evening_break_minutes + self.other_break_minutes
    
    @property
    def weekday(self) -> int:
        """曜日を取得 (0=月曜日, 6=日曜日)"""
        return self.work_date.weekday()
    
    @property
    def is_weekend(self) -> bool:
        """週末かどうか判定"""
        return self.weekday >= 5  # 土曜日(5), 日曜日(6)
    
    @property
    def weekday_name_jp(self) -> str:
        """曜日名（日本語）"""
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        return weekdays[self.weekday]
    
    def calculate_working_hours_sync(self) -> float:
        """実働時間を同期計算（基本計算のみ）"""
        if not self.start_time or not self.end_time:
            return float("0.0")

        # 時刻を分に変換（time または timedelta 対応）
        if hasattr(self.start_time, 'hour'):  # time オブジェクト
            start_minutes = self.start_time.hour * 60 + self.start_time.minute
        else:  # timedelta オブジェクト
            start_minutes = int(self.start_time.total_seconds() / 60)
            
        if hasattr(self.end_time, 'hour'):  # time オブジェクト
            end_minutes = self.end_time.hour * 60 + self.end_time.minute
        else:  # timedelta オブジェクト
            end_minutes = int(self.end_time.total_seconds() / 60)

        # 跨日対応
        if end_minutes < start_minutes:
            end_minutes += 24 * 60

        # 実働時間計算（休憩時間を除く）
        total_minutes = end_minutes - start_minutes - self.total_break_minutes
        hours = round(total_minutes / 60, 1)  # デフォルト1小数点で四捨五入

        return max(float(hours), float("0.0"))
    
    @property
    def actual_working_hours(self) -> float:
        """実働時間を計算（同期版）"""
        return self.calculate_working_hours_sync()
    
    @property
    def overtime_hours(self) -> float:
        """加班时间（基于合同free_overtime_hours计算）"""
        if not hasattr(self, '_contract_cached') or not self._contract_cached:
            return 0.0
        
        # 获取合同的免费加班时间
        free_overtime = getattr(self._contract_cached, 'free_overtime_hours', 0.0) or 0.0
        actual_hours = self.actual_working_hours
        
        # 只有超过免费加班时间的部分才算真正的加班
        if actual_hours > free_overtime:
            return round(actual_hours - free_overtime, 1)
        return 0.0
    
    async def get_overtime_hours(self) -> float:
        """异步获取加班时间（确保合同数据已加载）"""
        if not self.contract:
            return 0.0
        
        # 缓存合同信息以供同步属性使用
        self._contract_cached = self.contract
        
        free_overtime = getattr(self.contract, 'free_overtime_hours', 0.0) or 0.0
        actual_hours = await self.calculate_working_hours()
        
        # 只有超过免费加班时间的部分才算真正的加班
        if actual_hours > free_overtime:
            return round(actual_hours - free_overtime, 1)
        return 0.0
    
    async def calculate_working_hours(self) -> float:
        """実働時間を計算（客户的小数処理設定を適用）"""
        if not self.start_time or not self.end_time:
            return float("0.0")

        # 時刻を分に変換（time または timedelta 対応）
        if hasattr(self.start_time, 'hour'):  # time オブジェクト
            start_minutes = self.start_time.hour * 60 + self.start_time.minute
        else:  # timedelta オブジェクト
            start_minutes = int(self.start_time.total_seconds() / 60)
            
        if hasattr(self.end_time, 'hour'):  # time オブジェクト
            end_minutes = self.end_time.hour * 60 + self.end_time.minute
        else:  # timedelta オブジェクト
            end_minutes = int(self.end_time.total_seconds() / 60)

        # 跨日対応
        if end_minutes < start_minutes:
            end_minutes += 24 * 60

        # 実働時間計算（休憩時間を除く）
        total_minutes = end_minutes - start_minutes - self.total_break_minutes
        raw_hours = total_minutes / 60

        # 客户設定に基づく小数処理
        try:
            contract = await Contract.get(id=self.contract.id).prefetch_related('case__client_company')
            client = contract.case.client_company
            calc_type = client.attendance_calc_type or 15  # デフォルト15分単位
            decimal_type = client.decimal_processing_type or DecimalProcessingType.ROUND
            
            # 計算単位での丸め処理
            calc_hours = calc_type / 60  # 分を時間に変換
            units = raw_hours / calc_hours
            
            if decimal_type == DecimalProcessingType.ROUND:
                processed_units = round(units)
            elif decimal_type == DecimalProcessingType.FLOOR:
                processed_units = math.floor(units)
            elif decimal_type == DecimalProcessingType.CEIL:
                processed_units = math.ceil(units)
            else:
                processed_units = round(units)
                
            hours = processed_units * calc_hours
        except:
            # エラー時はデフォルト処理
            hours = round(raw_hours, 1)

        return max(float(hours), float("0.0"))

    async def save(self, *args, **kwargs):
        """保存処理（実働時間は @property で自動計算される）"""
        await super().save(*args, **kwargs)


class MonthlyAttendance(BaseModel, TimestampMixin):
    """
    月次出勤記録提交管理（仅用于正式提交流程）
    
    设计理念：
    1. 平时考勤数据都存在DailyAttendance中，界面显示时实时计算
    2. MonthlyAttendance仅在以下场景使用：
       - 员工正式提交当月考勤（需要审批流程时）
       - 需要保存历史快照（防止后续日次数据修改影响已审批记录）
       - 合规性要求（某些公司需要月度考勤正式提交记录）
    3. 大部分查询和统计直接从DailyAttendance计算，性能更好且数据实时
    """
    # 核心字段
    user_id = fields.BigIntField(description="システムユーザーID")
    year_month = fields.CharField(max_length=7, description="対象年月（YYYY-MM）")
    
    # 提交审批流程管理（这是MonthlyAttendance存在的主要价值）
    status = fields.CharEnumField(
        ApproveStatus, default=ApproveStatus.DRAFT, description="审批状态"
    )
    submitted_at = fields.DatetimeField(null=True, description="提交日時")
    approved_at = fields.DatetimeField(null=True, description="承認日時")
    approved_by = fields.BigIntField(null=True, description="承認者ID")
    
    # 提交时的数据快照（关键功能：保证审批后数据不变）
    snapshot_data = fields.JSONField(null=True, description="提交時のデータ快照")
    
    # 审批相关备注
    submit_remark = fields.TextField(null=True, description="提交時の備考")
    approve_remark = fields.TextField(null=True, description="承認時の備考")

    class Meta:
        table = "ses_monthly_attendance"
        table_description = "月次出勤提交記録"
        unique_together = [("user_id", "year_month")]

    async def get_daily_records(self):
        """获取当月的日次记录"""
        year_month_str = str(self.year_month)
        year, month = map(int, year_month_str.split("-"))
        from calendar import monthrange
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])

        records = await DailyAttendance.filter(
            user_id=self.user_id,
            work_date__gte=start_date,
            work_date__lte=end_date
        ).prefetch_related('contract').all()
        
        # 为每条记录缓存合同信息，支持overtime_hours计算
        for record in records:
            if hasattr(record, 'contract'):
                record._contract_cached = record.contract
        
        return records

    @property
    async def total_working_hours(self) -> float:
        """総実働時间（计算属性）"""
        daily_records = await self.get_daily_records()
        total = 0.0
        for record in daily_records:
            hours = record.actual_working_hours
            if hours is not None:
                total += float(hours)
        return round(total, 2)

    @property
    async def working_days(self) -> int:
        """出勤日数（计算属性）"""
        daily_records = await self.get_daily_records()
        return len([r for r in daily_records if r.attendance_type == AttendanceType.NORMAL])

    @property
    async def paid_leave_days(self) -> int:
        """有給休暇日数（计算属性）"""
        daily_records = await self.get_daily_records()
        return len([r for r in daily_records if r.attendance_type == AttendanceType.PAID_LEAVE])

    @property 
    async def absence_days(self) -> int:
        """欠勤日数（计算属性）"""
        daily_records = await self.get_daily_records()
        return len([r for r in daily_records if r.attendance_type == AttendanceType.ABSENCE])

    @property
    async def overtime_hours(self) -> float:
        """残業時間（计算属性）"""
        total_hours = await self.total_working_hours
        # 使用标准月工作时间 160小时（20天 * 8小时）
        standard_hours = 160.0
        return max(0.0, total_hours - standard_hours)

    async def calculate_and_save_snapshot(self):
        """计算统计数据并保存快照（提交时调用）"""
        daily_records = await self.get_daily_records()
        
        # 安全的时间汇总，处理None值和类型转换
        total_working_hours = 0.0
        for record in daily_records:
            hours = record.actual_working_hours
            if hours is not None:
                total_working_hours += float(hours)
        
        snapshot = {
            "total_working_hours": round(total_working_hours, 2),
            "working_days": len([r for r in daily_records if r.attendance_type == AttendanceType.NORMAL]),
            "paid_leave_days": len([r for r in daily_records if r.attendance_type == AttendanceType.PAID_LEAVE]),
            "absence_days": len([r for r in daily_records if r.attendance_type == AttendanceType.ABSENCE]),
            "calculated_at": datetime.now().isoformat()
        }
        
        self.snapshot_data = snapshot
        await self.save()
        return snapshot

    async def submit(self, submit_remark: str = None):
        """提交月度考勤审批"""
        if self.status in [ApproveStatus.PENDING, ApproveStatus.APPROVED]:
            raise ValueError("已提交或已批准的记录无法重复提交")
        
        # 计算并保存快照（这是MonthlyAttendance的核心价值）
        await self.calculate_and_save_snapshot()
        
        self.status = ApproveStatus.PENDING
        self.submitted_at = datetime.now()
        self.submit_remark = submit_remark
        await self.save()

    async def withdraw(self):
        """撤回提交（恢复到可编辑状态）"""
        if self.status != ApproveStatus.PENDING:
            raise ValueError("只有等待审批状态的记录才能撤回")
        
        self.status = ApproveStatus.WITHDRAWN
        self.snapshot_data = None  # 清除快照，重新基于实时数据
        await self.save()

    async def approve(self, approved_by: int, approve_remark: str = None):
        """管理者批准月度考勤"""
        if self.status != ApproveStatus.PENDING:
            raise ValueError("只有等待审批状态的记录才能批准")
        
        self.status = ApproveStatus.APPROVED
        self.approved_at = datetime.now()
        self.approved_by = approved_by
        self.approve_remark = approve_remark
        await self.save()
    
    async def reject(self, approved_by: int, approve_remark: str = None):
        """管理者拒绝月度考勤"""
        if self.status != ApproveStatus.PENDING:
            raise ValueError("只有等待审批状态的记录才能拒绝")
        
        self.status = ApproveStatus.REJECTED
        self.approved_at = datetime.now()
        self.approved_by = approved_by
        self.approve_remark = approve_remark
        # 保留快照，以便查看被拒绝时的数据状态
        await self.save()
    
    @property 
    def can_edit_daily_records(self) -> bool:
        """判断是否可以编辑日次记录"""
        return self.status in [
            ApproveStatus.DRAFT, 
            ApproveStatus.WITHDRAWN,
            ApproveStatus.REJECTED
        ]
    
    def get_display_data(self):
        """获取用于显示的数据（优先使用快照）"""
        if self.snapshot_data and self.status == ApproveStatus.APPROVED:
            return self.snapshot_data
        # 对于未审批的记录，返回None，让调用方实时计算
        return None
    
    @classmethod
    async def get_or_create_for_submission(cls, user_id: int, year_month: str):
        """获取或创建月度提交记录（仅在需要提交审批时使用）"""
        record, created = await cls.get_or_create(
            user_id=user_id,
            year_month=year_month,
            defaults={
                "status": ApproveStatus.DRAFT
            }
        )
        return record, created


class WeeklyMood(BaseModel, TimestampMixin):
    """
    週間心情記録（按周存储工作心情状态）
    """
    user_id = fields.BigIntField(description="システムユーザーID")
    year = fields.IntField(description="年")
    week_number = fields.IntField(description="週番号（1-53）")
    
    # 心情状态
    mood_status = fields.CharEnumField(WeeklyMoodStatus, description="心情状態")
    
    # 可选的文字说明
    comment = fields.TextField(null=True, description="心情コメント")
    
    class Meta:
        table = "ses_weekly_mood"
        table_description = "週間心情記録"
        unique_together = [("user_id", "year", "week_number")]

    @property
    def week_start_date(self):
        """获取该周的开始日期（使用ISO周标准）"""
        from datetime import datetime, timedelta
        # 使用ISO周标准：周一为一周的开始
        jan_4 = datetime(self.year, 1, 4).date()  # ISO年的第一周包含1月4日
        jan_4_weekday = jan_4.weekday()  # 周一为0
        first_monday = jan_4 - timedelta(days=jan_4_weekday)
        target_week_start = first_monday + timedelta(weeks=self.week_number - 1)
        return target_week_start

    @property  
    def week_end_date(self):
        """获取该周的结束日期（周日）"""
        from datetime import timedelta
        return self.week_start_date + timedelta(days=6)
    
    @property
    def week_period_str(self):
        """获取周期间的字符串表示"""
        start = self.week_start_date
        end = self.week_end_date
        return f"{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}"
    
    @property
    def mood_emoji(self):
        """获取心情对应的表情符号"""
        emoji_map = {
            WeeklyMoodStatus.EXCELLENT: "😄",
            WeeklyMoodStatus.GOOD: "😊", 
            WeeklyMoodStatus.NORMAL: "😐",
            WeeklyMoodStatus.STRESSED: "😰",
            WeeklyMoodStatus.TIRED: "😴",
            WeeklyMoodStatus.DIFFICULT: "😞"
        }
        return emoji_map.get(self.mood_status, "😐")
    
    @property
    def mood_score(self):
        """获取心情对应的数值分数（1-6）"""
        score_map = {
            WeeklyMoodStatus.EXCELLENT: 6,
            WeeklyMoodStatus.GOOD: 5,
            WeeklyMoodStatus.NORMAL: 4,
            WeeklyMoodStatus.STRESSED: 3,
            WeeklyMoodStatus.TIRED: 2,
            WeeklyMoodStatus.DIFFICULT: 1
        }
        return score_map.get(self.mood_status, 4)

    @classmethod
    async def get_current_week_mood(cls, user_id: int):
        """获取当前周的心情记录"""
        from datetime import datetime
        today = datetime.now().date()
        year = today.year
        week_number = today.isocalendar()[1]
        
        return await cls.get_or_none(
            user_id=user_id,
            year=year, 
            week_number=week_number
        )

    @classmethod
    async def set_weekly_mood(cls, user_id: int, mood_status: WeeklyMoodStatus,week_number:int=None, comment: str = None):
        """设置当前周的心情"""
        from datetime import datetime
        today = datetime.now().date()
        year = today.year
        week_number = week_number if week_number else today.isocalendar()[1]
        
        mood, created = await cls.get_or_create(
            user_id=user_id,
            year=year,
            week_number=week_number,
            defaults={
                "mood_status": mood_status,
                "week_number": week_number,
                "comment": comment
            }
        )
        
        if not created:
            mood.mood_status = mood_status
            mood.comment = comment
            mood.week_number = week_number
            await mood.save()
        
        return mood
    
    @classmethod
    async def get_user_mood_history(cls, user_id: int, year: int = None, limit: int = 12):
        """获取用户心情历史记录"""
        from datetime import datetime
        
        if year is None:
            year = datetime.now().year
        
        moods = await cls.filter(
            user_id=user_id,
            year=year
        ).order_by('-year', '-week_number').limit(limit)
        
        return moods
    
    @classmethod
    async def get_team_mood_summary(cls, user_ids: list, weeks_back: int = 4):
        """获取团队心情汇总（最近几周）"""
        from datetime import datetime
        
        today = datetime.now().date()
        current_year = today.year
        current_week = today.isocalendar()[1]
        
        # 计算周范围
        start_week = max(1, current_week - weeks_back + 1)
        
        moods = await cls.filter(
            user_id__in=user_ids,
            year=current_year,
            week_number__gte=start_week,
            week_number__lte=current_week
        ).all()
        
        # 统计分析
        mood_distribution = {}
        total_score = 0
        total_count = len(moods)
        
        for mood in moods:
            status = mood.mood_status.value if hasattr(mood.mood_status, 'value') else str(mood.mood_status)
            mood_distribution[status] = mood_distribution.get(status, 0) + 1
            total_score += mood.mood_score
        
        average_score = total_score / total_count if total_count > 0 else 4.0
        
        # 周期趋势分析
        weekly_trends = {}
        for mood in moods:
            week_key = f"{mood.year}-W{mood.week_number:02d}"
            if week_key not in weekly_trends:
                weekly_trends[week_key] = []
            weekly_trends[week_key].append(mood.mood_score)
        
        trend_data = []
        for week_key in sorted(weekly_trends.keys()):
            scores = weekly_trends[week_key]
            avg_score = sum(scores) / len(scores)
            trend_data.append({
                "week": week_key,
                "average_score": round(avg_score, 1),
                "mood_count": len(scores)
            })
        
        return {
            "period": f"{current_year}-W{start_week:02d} ~ {current_year}-W{current_week:02d}",
            "team_size": len(user_ids),
            "active_responses": total_count,
            "mood_distribution": mood_distribution,
            "average_mood_score": round(average_score, 1),
            "mood_trends": trend_data
        }
    
    @classmethod
    async def get_mood_analytics(cls, user_id: int, year: int = None):
        """获取用户心情分析报告"""
        from datetime import datetime
        
        if year is None:
            year = datetime.now().year
            
        moods = await cls.filter(user_id=user_id, year=year).all()
        
        if not moods:
            return {
                "year": year,
                "total_records": 0,
                "mood_distribution": {},
                "average_score": 4.0,
                "trend_analysis": "暂无数据"
            }
        
        # 心情分布统计
        mood_distribution = {}
        total_score = 0
        
        for mood in moods:
            status = mood.mood_status.value if hasattr(mood.mood_status, 'value') else str(mood.mood_status)
            mood_distribution[status] = mood_distribution.get(status, 0) + 1
            total_score += mood.mood_score
        
        average_score = total_score / len(moods)
        
        # 简单的趋势分析
        recent_moods = sorted(moods, key=lambda x: x.week_number)[-4:]  # 最近4周
        recent_avg = sum(m.mood_score for m in recent_moods) / len(recent_moods) if recent_moods else 4.0
        
        if recent_avg > average_score + 0.5:
            trend_analysis = "最近心情有所改善"
        elif recent_avg < average_score - 0.5:
            trend_analysis = "最近心情有所下降"
        else:
            trend_analysis = "心情相对稳定"
        
        return {
            "year": year,
            "total_records": len(moods),
            "mood_distribution": mood_distribution,
            "average_score": round(average_score, 1),
            "recent_average": round(recent_avg, 1),
            "trend_analysis": trend_analysis,
            "most_common_mood": max(mood_distribution.items(), key=lambda x: x[1])[0] if mood_distribution else "normal"
        }


class MonthlyAttendanceLog(BaseModel, TimestampMixin):
    """月次考勤操作日志"""
    
    monthly_id = fields.IntField(description="月次考勤ID")
    operation = fields.CharField(max_length=20, description="操作类型")  # submit/approve/reject/withdraw
    operator_id = fields.IntField(description="操作者ID")
    from_status = fields.CharField(max_length=20, null=True, description="原状态")
    to_status = fields.CharField(max_length=20, description="新状态")  
    remark = fields.TextField(null=True, description="操作备注")
    operated_at = fields.DatetimeField(auto_now_add=True, description="操作时间")
    
    class Meta:
        table = "ses_monthly_attendance_log"
        table_description = "月次考勤操作日志"
