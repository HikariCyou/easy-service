from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from tortoise.expressions import Q

from app.models.bp import BPCompany
from app.models.case import Case, CaseCandidate
from app.models.client import ClientCompany
from app.models.contract import Contract
from app.models.enums import (
    ApproveStatus,
    AttendanceType,
    BPCompanyStatus,
    CandidateStatus,
    CaseStatus,
    ContractStatus,
    EmploymentStatus,
    PersonType,
    WeeklyMoodStatus,
)
from app.models.evaluation import PersonEvaluation
from app.models.personnel import Personnel

# Tortoise ORM doesn't support aggregate functions like Django



class DashboardController:
    """
    SES业务dashboard统计控制器
    为前端ECharts等图表组件提供全面的业务统计数据
    """

    def __init__(self):
        pass

    async def get_overview_stats(self) -> Dict[str, Any]:
        """
        获取总览统计数据
        """
        today = date.today()

        # 人员统计
        total_personnel = await Personnel.filter(is_active=True).count()
        employees = await Personnel.filter(person_type=PersonType.EMPLOYEE, is_active=True).count()
        freelancers = await Personnel.filter(person_type=PersonType.FREELANCER, is_active=True).count()
        bp_personnel = await Personnel.filter(person_type=PersonType.BP_EMPLOYEE, is_active=True).count()

        # BP企业统计
        total_bp_companies = await BPCompany.filter(status=BPCompanyStatus.ACTIVE).count()

        # 客户企业统计
        total_client_companies = await ClientCompany.all().count()

        # 案件统计
        total_cases = await Case.all().count()
        open_cases = await Case.filter(status=CaseStatus.OPEN).count()
        in_progress_cases = await Case.filter(status=CaseStatus.IN_PROGRESS).count()
        completed_cases = await Case.filter(status=CaseStatus.CLOSED).count()

        # 契约统计
        total_contracts = await Contract.all().count()
        active_contracts = await Contract.filter(status=ContractStatus.ACTIVE, contract_end_date__gte=today).count()

        # 签约率计算
        total_candidates = await CaseCandidate.all().count()
        contract_rate = (total_contracts / total_candidates * 100) if total_candidates > 0 else 0

        return {
            "personnel_overview": {
                "total": total_personnel,
                "employees": employees,
                "freelancers": freelancers,
                "bp_personnel": bp_personnel,
            },
            "company_overview": {"bp_companies": total_bp_companies, "client_companies": total_client_companies},
            "case_overview": {
                "total": total_cases,
                "open": open_cases,
                "in_progress": in_progress_cases,
                "completed": completed_cases,
            },
            "contract_overview": {
                "total": total_contracts,
                "active": active_contracts,
                "contract_rate": round(contract_rate, 2),
            },
        }

    async def get_personnel_distribution(self) -> Dict[str, Any]:
        """
        获取人员分布统计（按类型、状态、国籍等）
        """
        # 按类型分布
        type_distribution = []
        for person_type in PersonType:
            count = await Personnel.filter(person_type=person_type, is_active=True).count()
            type_distribution.append({"name": PersonType.get_label(person_type.value), "value": count})

        # 按工作状态分布
        status_distribution = []
        for status in EmploymentStatus:
            count = await Personnel.filter(employment_status=status, is_active=True).count()
            status_distribution.append({"name": status.value, "value": count})

        # 按国籍分布
        nationality_stats = await Personnel.filter(is_active=True).values_list("nationality", flat=True)
        nationality_count = {}
        for nationality in nationality_stats:
            if nationality:
                nationality_count[nationality] = nationality_count.get(nationality, 0) + 1

        nationality_distribution = [
            {"name": k, "value": v} for k, v in sorted(nationality_count.items(), key=lambda x: x[1], reverse=True)
        ]

        # 按经验年数分布
        experience_ranges = [("0-1年", 0, 1), ("1-3年", 1, 3), ("3-5年", 3, 5), ("5-10年", 5, 10), ("10年以上", 10, 100)]

        experience_distribution = []
        for label, min_exp, max_exp in experience_ranges:
            if max_exp == 100:  # 10年以上
                count = await Personnel.filter(it_experience_years__gte=min_exp, is_active=True).count()
            else:
                count = await Personnel.filter(
                    it_experience_years__gte=min_exp, it_experience_years__lt=max_exp, is_active=True
                ).count()
            experience_distribution.append({"name": label, "value": count})

        return {
            "type_distribution": type_distribution,
            "status_distribution": status_distribution,
            "nationality_distribution": nationality_distribution[:10],  # 前10位
            "experience_distribution": experience_distribution,
        }

    async def get_revenue_analysis(self) -> Dict[str, Any]:
        """
        获取收益分析（基于精算项目的月收入统计等）
        """
        from app.models.enums import ContractItemType, PaymentUnit

        today = date.today()
        current_month = today.replace(day=1)

        # 有效契约的月收入统计
        active_contracts = await Contract.filter(
            status=ContractStatus.ACTIVE, contract_start_date__lte=today, contract_end_date__gte=today
        ).prefetch_related("personnel", "calculation_items")

        # 计算总月收入和按类型分组的收入
        total_monthly_revenue = 0
        revenue_by_type = {
            PersonType.get_label(PersonType.EMPLOYEE): 0,
            PersonType.get_label(PersonType.FREELANCER): 0,
            PersonType.get_label(PersonType.BP_EMPLOYEE): 0,
        }

        contract_revenues = []  # 存储每个合约的月收入用于分布分析

        for contract in active_contracts:
            # 计算合约月收入（基于基本给项目）
            basic_salary_item = await contract.calculation_items.filter(
                item_type=ContractItemType.BASIC_SALARY, is_active=True
            ).first()

            monthly_revenue = 0
            if basic_salary_item:
                # 计算月收入
                if basic_salary_item.payment_unit == PaymentUnit.TEN_THOUSAND_YEN_PER_MONTH:
                    monthly_revenue = basic_salary_item.amount * 10000
                elif basic_salary_item.payment_unit == PaymentUnit.YEN_PER_MONTH:
                    monthly_revenue = basic_salary_item.amount
                else:
                    # 对于其他单位，使用标准工时换算
                    monthly_revenue = basic_salary_item.calculate_monthly_amount(contract.standard_working_hours, 0)

            total_monthly_revenue += monthly_revenue
            contract_revenues.append(monthly_revenue)

            # 按人员类型分组
            if contract.personnel:
                person_type = contract.personnel.person_type.value
                revenue_by_type[PersonType.get_label(person_type)] += monthly_revenue

        # 收入分布（基于月收入）
        revenue_ranges = [
            ("30万以下", 0, 300000),
            ("30-50万", 300000, 500000),
            ("50-70万", 500000, 700000),
            ("70-100万", 700000, 1000000),
            ("100万以上", 1000000, 10000000),
        ]

        revenue_distribution = []
        for label, min_revenue, max_revenue in revenue_ranges:
            count = 0
            for revenue in contract_revenues:
                if max_revenue == 10000000:  # 100万以上
                    if revenue >= min_revenue:
                        count += 1
                else:
                    if min_revenue <= revenue < max_revenue:
                        count += 1

            revenue_distribution.append({"name": label, "value": count})

        # 平均月收入
        avg_monthly_revenue = 0
        if contract_revenues:
            avg_monthly_revenue = sum(contract_revenues) / len(contract_revenues)

        return {
            "total_monthly_revenue": total_monthly_revenue,
            "revenue_by_type": revenue_by_type,
            "revenue_distribution": revenue_distribution,
            "average_monthly_revenue": avg_monthly_revenue,
            "active_contracts_count": len(active_contracts),
        }

    async def get_case_analysis(self) -> Dict[str, Any]:
        """
        获取案件分析统计
        """
        today = date.today()

        # 案件状态分布
        case_status_distribution = []
        for status in CaseStatus:
            count = await Case.filter(status=status).count()
            case_status_distribution.append({"name": status.value, "value": count})

        # 月度案件趋势（最近12个月）
        monthly_case_trend = []
        for i in range(12):
            month_start = (today.replace(day=1) - timedelta(days=30 * i)).replace(day=1)
            if i == 0:
                month_end = today
            else:
                month_end = month_start.replace(day=28) + timedelta(days=4)
                month_end = month_end - timedelta(days=month_end.day)

            # 转换为datetime对象
            month_start_dt = datetime.combine(month_start, datetime.min.time())
            month_end_dt = datetime.combine(month_end, datetime.min.time())

            case_count = await Case.filter(created_at__gte=month_start_dt, created_at__lte=month_end_dt).count()

            monthly_case_trend.append({"month": month_start.strftime("%Y-%m"), "count": case_count})

        monthly_case_trend.reverse()

        # 按客户分组的案件数
        client_case_stats = await Case.filter().prefetch_related("client_company").all()
        client_case_count = {}
        for case in client_case_stats:
            if case.client_company:
                company_name = case.client_company.company_name
                client_case_count[company_name] = client_case_count.get(company_name, 0) + 1

        top_clients = sorted(client_case_count.items(), key=lambda x: x[1], reverse=True)[:10]

        # 案件成功率（完成案件 / 总案件）
        total_cases = await Case.all().count()
        completed_cases = await Case.filter(status=CaseStatus.CLOSED).count()
        success_rate = (completed_cases / total_cases * 100) if total_cases > 0 else 0

        return {
            "status_distribution": case_status_distribution,
            "monthly_trend": monthly_case_trend,
            "top_clients": [{"name": name, "value": count} for name, count in top_clients],
            "success_rate": round(success_rate, 2),
            "total_cases": total_cases,
        }

    async def get_bp_company_analysis(self) -> Dict[str, Any]:
        """
        获取BP企业分析统计
        """
        # BP企业状态分布
        bp_status_distribution = []
        for status in BPCompanyStatus:
            count = await BPCompany.filter(status=status).count()
            bp_status_distribution.append({"name": status.value, "value": count})

        # BP企业人员数排行
        bp_companies = await BPCompany.filter(status=BPCompanyStatus.ACTIVE).prefetch_related("personnel_details").all()
        bp_personnel_count = []

        for bp_company in bp_companies:
            personnel_count = await Personnel.filter(bp_employee_detail__bp_company=bp_company, is_active=True).count()
            bp_personnel_count.append({"company_name": bp_company.name, "personnel_count": personnel_count})

        # 按人员数排序，取前10
        bp_personnel_count.sort(key=lambda x: x["personnel_count"], reverse=True)
        top_bp_companies = bp_personnel_count[:10]

        # BP企业评价分布
        bp_ratings = await BPCompany.filter(status=BPCompanyStatus.ACTIVE).values_list("rating", flat=True)
        rating_distribution = {}
        for rating in bp_ratings:
            if rating is not None:
                rating_distribution[f"{rating}星"] = rating_distribution.get(f"{rating}星", 0) + 1

        rating_dist_list = [{"name": k, "value": v} for k, v in sorted(rating_distribution.items())]

        return {
            "status_distribution": bp_status_distribution,
            "top_companies_by_personnel": top_bp_companies,
            "rating_distribution": rating_dist_list,
            "total_bp_companies": len(bp_companies),
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取业绩指标统计
        """
        today = date.today()
        current_month = today.replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)

        # 转换为datetime对象以便与created_at字段比较
        today_dt = datetime.combine(today, datetime.min.time())
        current_month_dt = datetime.combine(current_month, datetime.min.time())
        last_month_dt = datetime.combine(last_month, datetime.min.time())

        # 当月签约数
        current_month_contracts = await Contract.filter(created_at__gte=current_month_dt, created_at__lte=today_dt).count()

        # 上月签约数
        last_month_contracts = await Contract.filter(created_at__gte=last_month_dt, created_at__lt=current_month_dt).count()

        # 签约增长率
        contract_growth_rate = 0
        if last_month_contracts > 0:
            contract_growth_rate = ((current_month_contracts - last_month_contracts) / last_month_contracts) * 100

        # 当月新增案件
        current_month_cases = await Case.filter(created_at__gte=current_month_dt, created_at__lte=today_dt).count()

        # 平均案件处理时间（从创建到完成）
        completed_cases = await Case.filter(status=CaseStatus.CLOSED).all()
        processing_times = []
        for case in completed_cases:
            if case.created_at and case.updated_at:
                processing_time = (case.updated_at.date() - case.created_at.date()).days
                processing_times.append(processing_time)

        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0

        # 人员利用率（有活跃合同的人员 / 总人员）
        total_active_personnel = await Personnel.filter(is_active=True).count()
        # 获取有活跃合同的人员ID列表，然后计算唯一数量
        personnel_ids_with_contracts = await Contract.filter(
            status=ContractStatus.ACTIVE, contract_end_date__gte=today
        ).values_list("personnel_id", flat=True)
        personnel_with_contracts = len(set(personnel_ids_with_contracts))

        utilization_rate = (
            (personnel_with_contracts / total_active_personnel * 100) if total_active_personnel > 0 else 0
        )

        # 客户满意度（基于评价）
        ninety_days_ago = today - timedelta(days=90)
        ninety_days_ago_dt = datetime.combine(ninety_days_ago, datetime.min.time())
        recent_evaluations = await PersonEvaluation.filter(evaluation_date__gte=ninety_days_ago_dt).all()

        satisfaction_scores = [eval.overall_rating for eval in recent_evaluations if eval.overall_rating]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0

        return {
            "current_month_contracts": current_month_contracts,
            "contract_growth_rate": round(contract_growth_rate, 2),
            "current_month_cases": current_month_cases,
            "avg_case_processing_days": round(avg_processing_time, 1),
            "personnel_utilization_rate": round(utilization_rate, 2),
            "avg_customer_satisfaction": round(avg_satisfaction, 2),
            "total_evaluations": len(satisfaction_scores),
        }

    async def get_warning_alerts(self) -> Dict[str, Any]:
        """
        获取预警提醒统计
        """
        today = date.today()
        warning_date_30 = today + timedelta(days=30)
        warning_date_90 = today + timedelta(days=90)

        # 签证即将到期的人员
        visa_expiring_soon = await Personnel.filter(
            visa_expire_date__lte=warning_date_90, visa_expire_date__gte=today, is_active=True
        ).count()

        # 合同即将到期
        contracts_expiring_soon = await Contract.filter(
            contract_end_date__lte=warning_date_30, contract_end_date__gte=today, status=ContractStatus.ACTIVE
        ).count()

        # 长期无分配的人员
        available_personnel = await Personnel.filter(
            employment_status=EmploymentStatus.AVAILABLE, is_active=True
        ).count()

        long_term_available = await Personnel.filter(
            employment_status=EmploymentStatus.AVAILABLE,
            available_start_date__lte=today - timedelta(days=30),
            is_active=True,
        ).count()

        # 评价较低的人员
        low_rated_person_ids = await PersonEvaluation.filter(
            overall_rating__lte=2, evaluation_date__gte=today - timedelta(days=180)
        ).values_list("person_id", flat=True)
        low_rated_personnel = len(set(low_rated_person_ids))

        # 空闲的BP企业（无活跃人员）
        idle_bp_companies = 0
        bp_companies = await BPCompany.filter(status=BPCompanyStatus.ACTIVE).all()
        for bp_company in bp_companies:
            active_personnel = await Personnel.filter(
                bp_employee_detail__bp_company=bp_company, employment_status=EmploymentStatus.WORKING, is_active=True
            ).count()
            if active_personnel == 0:
                idle_bp_companies += 1

        return {
            "visa_expiring_soon": visa_expiring_soon,
            "contracts_expiring_soon": contracts_expiring_soon,
            "available_personnel": available_personnel,
            "long_term_available": long_term_available,
            "low_rated_personnel": low_rated_personnel,
            "idle_bp_companies": idle_bp_companies,
        }

    async def get_comprehensive_dashboard(self) -> Dict[str, Any]:
        """
        获取综合dashboard数据（整合所有统计）
        """
        # 并行获取所有统计数据
        overview = await self.get_overview_stats()
        personnel_dist = await self.get_personnel_distribution()
        revenue = await self.get_revenue_analysis()
        case_analysis = await self.get_case_analysis()
        bp_analysis = await self.get_bp_company_analysis()
        performance = await self.get_performance_metrics()
        warnings = await self.get_warning_alerts()

        return {
            "overview": overview,
            "personnel_distribution": personnel_dist,
            "revenue_analysis": revenue,
            "case_analysis": case_analysis,
            "bp_company_analysis": bp_analysis,
            "performance_metrics": performance,
            "warning_alerts": warnings,
            "last_updated": datetime.now().isoformat(),
        }

    # =======================================
    # 考勤Dashboard专用方法
    # =======================================

    async def get_attendance_overview(
        self, year_month: Optional[str] = None, department: Optional[str] = None, person_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取考勤概览统计
        """
        try:
            from calendar import monthrange

            from app.models.attendance import DailyAttendance, MonthlyAttendance
            from app.models.enums import AttendanceType

            # 确定目标月份
            if year_month:
                year, month = map(int, year_month.split("-"))
                target_date = date(year, month, 1)
            else:
                today = date.today()
                target_date = date(today.year, today.month, 1)

            # 计算月份范围
            last_day = monthrange(target_date.year, target_date.month)[1]
            month_start = target_date
            month_end = date(target_date.year, target_date.month, last_day)

            # 获取有效人员
            personnel_query = Personnel.filter(is_active=True)
            if person_type:
                personnel_query = personnel_query.filter(person_type=person_type)

            total_personnel = await personnel_query.count()
            working_personnel = await personnel_query.filter(employment_status=EmploymentStatus.WORKING).count()

            # 获取当月考勤记录
            attendance_query = DailyAttendance.filter(work_date__gte=month_start, work_date__lte=month_end)

            total_records = await attendance_query.count()
            # 日次考勤记录不再有审批状态，审批在月次层面
            # approved_records = await attendance_query.filter(is_approved=True).count()
            approved_records = 0  # 暂时设为0，实际应从MonthlyAttendance中计算

            # 计算各种出勤类型统计
            normal_attendance = await attendance_query.filter(attendance_type=AttendanceType.NORMAL).count()

            paid_leave = await attendance_query.filter(attendance_type=AttendanceType.PAID_LEAVE).count()

            # 计算总工作时长和加班时长（需要预加载合同信息）
            attendance_records = await attendance_query.prefetch_related("contract").all()
            total_working_hours = 0
            total_overtime_hours = 0

            for record in attendance_records:
                total_working_hours += record.actual_working_hours or 0
                # 预缓存合同信息以供overtime_hours属性使用
                record._contract_cached = record.contract
                total_overtime_hours += record.overtime_hours or 0

            # 计算提交完成率
            monthly_submissions = await MonthlyAttendance.filter(
                year_month=year_month or f"{target_date.year}-{target_date.month:02d}"
            ).count()

            submitted_count = await MonthlyAttendance.filter(
                year_month=year_month or f"{target_date.year}-{target_date.month:02d}",
                status__in=[ApproveStatus.PENDING, ApproveStatus.APPROVED],
            ).count()

            submission_rate = (submitted_count / monthly_submissions * 100) if monthly_submissions > 0 else 0
            approval_rate = (approved_records / total_records * 100) if total_records > 0 else 0
            attendance_rate = (normal_attendance / total_records * 100) if total_records > 0 else 0

            return {
                "period": f"{target_date.year}-{target_date.month:02d}",
                "personnel_summary": {
                    "total_personnel": total_personnel,
                    "working_personnel": working_personnel,
                    "available_rate": round((working_personnel / total_personnel * 100), 1)
                    if total_personnel > 0
                    else 0,
                },
                "attendance_summary": {
                    "total_records": total_records,
                    "attendance_rate": round(attendance_rate, 1),
                    "approval_rate": round(approval_rate, 1),
                    "submission_rate": round(submission_rate, 1),
                },
                "time_summary": {
                    "total_working_hours": round(total_working_hours, 1),
                    "total_overtime_hours": round(total_overtime_hours, 1),
                    "average_daily_hours": round((total_working_hours / max(total_records, 1)), 1),
                    "overtime_rate": round((total_overtime_hours / max(total_working_hours, 1) * 100), 1)
                    if total_working_hours > 0
                    else 0,
                },
                "leave_summary": {
                    "paid_leave_days": paid_leave,
                    "leave_usage_rate": round((paid_leave / max(total_records, 1) * 100), 1),
                },
            }
        except Exception as e:
            raise Exception(f"考勤概览统计获取失败: {str(e)}")

    async def get_attendance_trend(
        self,
        period_type: str = "month",
        periods: int = 6,
        metric: str = "attendance_rate",
        department: Optional[str] = None,
        person_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取考勤趋势分析数据
        """
        try:
            from calendar import monthrange

            from app.models.attendance import DailyAttendance
            from app.models.enums import AttendanceType

            today = date.today()
            trend_data = []

            for i in range(periods):
                if period_type == "month":
                    # 月统计
                    target_month = today.replace(day=1) - timedelta(days=32 * i)
                    target_month = target_month.replace(day=1)

                    # 计算该月的最后一天
                    last_day = monthrange(target_month.year, target_month.month)[1]
                    month_end = date(target_month.year, target_month.month, last_day)

                    period_label = f"{target_month.year}-{target_month.month:02d}"

                elif period_type == "week":
                    # 周统计
                    target_week_start = today - timedelta(weeks=i, days=today.weekday())
                    target_week_end = target_week_start + timedelta(days=6)

                    target_month = target_week_start
                    month_end = target_week_end
                    period_label = f"第{target_week_start.isocalendar()[1]}周"

                elif period_type == "quarter":
                    # 季度统计
                    quarter_months = [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)]
                    current_quarter = (today.month - 1) // 3
                    target_quarter = (current_quarter - i) % 4
                    year_offset = (current_quarter - i) // 4

                    target_year = today.year + year_offset
                    quarter_start_month = quarter_months[target_quarter][0]
                    quarter_end_month = quarter_months[target_quarter][2]

                    target_month = date(target_year, quarter_start_month, 1)
                    month_end = date(target_year, quarter_end_month, monthrange(target_year, quarter_end_month)[1])
                    period_label = f"{target_year}Q{target_quarter + 1}"

                # 获取该时期的考勤数据（预加载合同）
                attendance_records = (
                    await DailyAttendance.filter(work_date__gte=target_month, work_date__lte=month_end)
                    .prefetch_related("contract")
                    .all()
                )

                # 为加班时间计算预缓存合同信息
                for record in attendance_records:
                    record._contract_cached = record.contract

                if metric == "attendance_rate":
                    normal_count = len([r for r in attendance_records if r.attendance_type == AttendanceType.NORMAL])
                    total_count = len(attendance_records)
                    value = (normal_count / max(total_count, 1)) * 100

                elif metric == "working_hours":
                    value = sum(r.actual_working_hours or 0 for r in attendance_records)

                elif metric == "overtime_hours":
                    value = sum(r.overtime_hours or 0 for r in attendance_records)

                elif metric == "leave_days":
                    value = len([r for r in attendance_records if r.attendance_type != AttendanceType.NORMAL])

                trend_data.append({"period": period_label, "value": round(value, 1), "date": target_month.isoformat()})

            # 按日期排序（最新的在最后）
            trend_data.reverse()

            return {
                "period_type": period_type,
                "metric": metric,
                "periods": periods,
                "trend_data": trend_data,
                "chart_config": {
                    "x_axis": [item["period"] for item in trend_data],
                    "y_axis": [item["value"] for item in trend_data],
                    "unit": "%" if metric == "attendance_rate" else ("小时" if "hours" in metric else "天"),
                },
            }
        except Exception as e:
            raise Exception(f"考勤趋势分析失败: {str(e)}")

    async def get_attendance_distribution(
        self, analysis_type: str = "department", year_month: Optional[str] = None, metric: str = "attendance_rate"
    ) -> Dict[str, Any]:
        """
        获取考勤数据分布分析
        """
        try:
            from calendar import monthrange
            from collections import defaultdict

            from app.models.attendance import DailyAttendance
            from app.models.enums import AttendanceType

            # 确定分析月份
            if year_month:
                year, month = map(int, year_month.split("-"))
                target_date = date(year, month, 1)
            else:
                today = date.today()
                target_date = date(today.year, today.month, 1)

            last_day = monthrange(target_date.year, target_date.month)[1]
            month_end = date(target_date.year, target_date.month, last_day)

            # 获取考勤记录（预加载合同和人员）
            attendance_records = (
                await DailyAttendance.filter(work_date__gte=target_date, work_date__lte=month_end)
                .prefetch_related("contract__personnel")
                .all()
            )

            # 为加班时间计算预缓存合同信息
            for record in attendance_records:
                record._contract_cached = record.contract

            # 按分析维度分组
            distribution_data = defaultdict(list)

            for record in attendance_records:
                personnel = record.contract.personnel if hasattr(record, "contract") and record.contract else None
                if not personnel:
                    continue

                if analysis_type == "person_type":
                    key = personnel.person_type.value if personnel.person_type else "unknown"
                elif analysis_type == "nationality":
                    key = personnel.nationality or "unknown"
                elif analysis_type == "age_group":
                    if personnel.birthday:
                        age = (date.today() - personnel.birthday).days // 365
                        if age < 25:
                            key = "25歳以下"
                        elif age < 35:
                            key = "25-35歳"
                        elif age < 45:
                            key = "35-45歳"
                        else:
                            key = "45歳以上"
                    else:
                        key = "年齢不明"
                else:  # department
                    key = "部门未分类"  # 根据实际需求设置

                distribution_data[key].append(record)

            # 计算各分组的指标
            result_data = []
            for group_name, records in distribution_data.items():
                if metric == "attendance_rate":
                    normal_count = len([r for r in records if r.attendance_type == AttendanceType.NORMAL])
                    value = (normal_count / max(len(records), 1)) * 100
                elif metric == "working_hours":
                    value = sum(r.actual_working_hours or 0 for r in records) / max(len(records), 1)
                elif metric == "overtime_rate":
                    total_hours = sum(r.actual_working_hours or 0 for r in records)
                    overtime_hours = sum(r.overtime_hours or 0 for r in records)
                    value = (overtime_hours / max(total_hours, 1)) * 100
                elif metric == "leave_rate":
                    leave_count = len([r for r in records if r.attendance_type != AttendanceType.NORMAL])
                    value = (leave_count / max(len(records), 1)) * 100

                result_data.append({"name": group_name, "value": round(value, 1), "count": len(records)})

            # 按值排序
            result_data.sort(key=lambda x: x["value"], reverse=True)

            return {
                "analysis_type": analysis_type,
                "metric": metric,
                "period": f"{target_date.year}-{target_date.month:02d}",
                "distribution_data": result_data,
                "chart_config": {
                    "pie_data": [{"name": item["name"], "value": item["value"]} for item in result_data],
                    "bar_data": {
                        "x_axis": [item["name"] for item in result_data],
                        "y_axis": [item["value"] for item in result_data],
                    },
                },
            }
        except Exception as e:
            raise Exception(f"考勤数据分布分析失败: {str(e)}")

    async def get_attendance_ranking(
        self,
        rank_type: str = "attendance_rate",
        year_month: Optional[str] = None,
        top_n: int = 10,
        department: Optional[str] = None,
        person_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取考勤排行榜
        """
        try:
            from calendar import monthrange
            from collections import defaultdict

            from app.models.attendance import DailyAttendance
            from app.models.enums import AttendanceType

            # 确定排名月份
            if year_month:
                year, month = map(int, year_month.split("-"))
                target_date = date(year, month, 1)
            else:
                today = date.today()
                target_date = date(today.year, today.month, 1)

            last_day = monthrange(target_date.year, target_date.month)[1]
            month_end = date(target_date.year, target_date.month, last_day)

            # 获取考勤记录（按人员分组，预加载合同和人员）
            attendance_records = (
                await DailyAttendance.filter(work_date__gte=target_date, work_date__lte=month_end)
                .prefetch_related("contract__personnel")
                .all()
            )

            # 为加班时间计算预缓存合同信息
            for record in attendance_records:
                record._contract_cached = record.contract

            # 按人员分组计算指标
            personnel_stats = defaultdict(list)
            for record in attendance_records:
                if hasattr(record, "contract") and record.contract and record.contract.personnel:
                    personnel = record.contract.personnel
                    personnel_stats[personnel.id].append(record)

            ranking_data = []
            for personnel_id, records in personnel_stats.items():
                if not records:
                    continue

                personnel = records[0].contract.personnel

                # 应用筛选条件
                if person_type and personnel.person_type.value != person_type:
                    continue

                # 计算排名指标
                if rank_type == "attendance_rate":
                    normal_count = len([r for r in records if r.attendance_type == AttendanceType.NORMAL])
                    score = (normal_count / max(len(records), 1)) * 100

                elif rank_type == "working_hours":
                    score = sum(r.actual_working_hours or 0 for r in records)

                elif rank_type == "overtime_hours":
                    score = sum(r.overtime_hours or 0 for r in records)

                elif rank_type == "efficiency_score":
                    # 工作效率评分（示例计算）
                    total_hours = sum(r.actual_working_hours or 0 for r in records)
                    overtime_hours = sum(r.overtime_hours or 0 for r in records)
                    score = total_hours / max((total_hours + overtime_hours), 1) * 100

                ranking_data.append(
                    {
                        "personnel_id": personnel.id,
                        "name": personnel.name,
                        "person_type": personnel.person_type.value if personnel.person_type else "",
                        "company": getattr(personnel, "company_name", ""),
                        "score": round(score, 1),
                        "record_count": len(records),
                    }
                )

            # 排序（加班时长是反向排序）
            reverse_sort = rank_type != "overtime_hours"
            ranking_data.sort(key=lambda x: x["score"], reverse=reverse_sort)

            # 取前N名
            ranking_data = ranking_data[:top_n]

            return {
                "rank_type": rank_type,
                "period": f"{target_date.year}-{target_date.month:02d}",
                "top_n": top_n,
                "ranking_data": ranking_data,
                "chart_config": {
                    "names": [item["name"] for item in ranking_data],
                    "scores": [item["score"] for item in ranking_data],
                    "unit": "%" if rank_type in ["attendance_rate", "efficiency_score"] else "小时",
                },
            }
        except Exception as e:
            raise Exception(f"考勤排行榜获取失败: {str(e)}")

    async def get_attendance_calendar_heatmap(
        self, year: int, metric: str = "attendance_count", user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取考勤热力图数据
        """
        try:
            from collections import defaultdict

            from app.models.attendance import DailyAttendance
            from app.models.enums import AttendanceType

            # 获取全年考勤记录
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)

            query = DailyAttendance.filter(work_date__gte=year_start, work_date__lte=year_end).prefetch_related(
                "contract"
            )

            if user_id:
                query = query.filter(contract__personnel__user_id=user_id)

            attendance_records = await query.all()

            # 为加班时间计算预缓存合同信息
            for record in attendance_records:
                record._contract_cached = record.contract

            # 按日期分组统计
            daily_stats = defaultdict(list)
            for record in attendance_records:
                daily_stats[record.work_date].append(record)

            # 生成热力图数据
            heatmap_data = []
            current_date = year_start

            while current_date <= year_end:
                records = daily_stats.get(current_date, [])

                if metric == "attendance_count":
                    value = len(records)
                elif metric == "working_hours":
                    value = sum(r.actual_working_hours or 0 for r in records)
                elif metric == "overtime_hours":
                    value = sum(r.overtime_hours or 0 for r in records)
                elif metric == "leave_count":
                    value = len([r for r in records if r.attendance_type != AttendanceType.NORMAL])

                heatmap_data.append([current_date.isoformat(), round(value, 1)])
                current_date += timedelta(days=1)

            return {
                "year": year,
                "metric": metric,
                "user_id": user_id,
                "heatmap_data": heatmap_data,
                "chart_config": {
                    "calendar": {"range": year, "cellSize": ["auto", 13]},
                    "visualMap": {
                        "min": 0,
                        "max": max([item[1] for item in heatmap_data]) if heatmap_data else 10,
                        "type": "piecewise",
                        "orient": "horizontal",
                        "left": "center",
                    },
                },
            }
        except Exception as e:
            raise Exception(f"考勤热力图数据获取失败: {str(e)}")

    async def get_mood_analysis(
        self,
        user_id: int,
        analysis_period: str = "month",
        periods: int = 12,
        analysis_type: str = "trend",
        team_view: bool = False,
    ) -> Dict[str, Any]:
        """
        获取心情数据分析
        """
        try:
            from collections import defaultdict

            from app.models.attendance import DailyAttendance, WeeklyMood

            if team_view:
                # 团队视图 - 需要管理员权限
                mood_records = (
                    await WeeklyMood.filter(created_at__gte=datetime.now() - timedelta(weeks=periods * 4))
                    .prefetch_related("user")
                    .all()
                )
            else:
                # 个人视图
                mood_records = await WeeklyMood.filter(
                    user_id=user_id, created_at__gte=datetime.now() - timedelta(weeks=periods * 4)
                ).all()

            if analysis_type == "trend":
                # 心情趋势分析
                mood_trend = defaultdict(list)
                for record in mood_records:
                    week_key = f"{record.year}-W{record.week_number:02d}"
                    mood_trend[week_key].append(record.mood_score)

                trend_data = []
                for week, scores in sorted(mood_trend.items()):
                    avg_score = sum(scores) / len(scores) if scores else 0
                    trend_data.append({"period": week, "score": round(avg_score, 1), "count": len(scores)})

                return {
                    "analysis_type": "trend",
                    "trend_data": trend_data,
                    "chart_config": {
                        "x_axis": [item["period"] for item in trend_data],
                        "y_axis": [item["score"] for item in trend_data],
                    },
                }

            elif analysis_type == "distribution":
                # 心情状态分布
                mood_distribution = defaultdict(int)
                for record in mood_records:
                    mood_distribution[record.mood_status.value] += 1

                distribution_data = [{"name": status, "value": count} for status, count in mood_distribution.items()]

                return {
                    "analysis_type": "distribution",
                    "distribution_data": distribution_data,
                    "total_records": len(mood_records),
                }

            elif analysis_type == "correlation":
                # 心情与考勤相关性分析（示例）
                correlation_data = []
                for record in mood_records:
                    # 获取同期考勤数据进行关联分析
                    week_start = datetime.strptime(f"{record.year}-W{record.week_number:02d}-1", "%Y-W%W-%w").date()
                    week_end = week_start + timedelta(days=6)

                    attendance_count = await DailyAttendance.filter(
                        contract__personnel__user_id=record.user_id, work_date__gte=week_start, work_date__lte=week_end
                    ).count()

                    correlation_data.append(
                        {
                            "mood_score": record.mood_score,
                            "attendance_days": attendance_count,
                            "week": f"{record.year}-W{record.week_number:02d}",
                        }
                    )

                return {"analysis_type": "correlation", "correlation_data": correlation_data}

        except Exception as e:
            raise Exception(f"心情数据分析失败: {str(e)}")

    async def get_attendance_alerts(
        self, alert_level: Optional[str] = None, alert_type: Optional[str] = None, date_range: int = 7
    ) -> Dict[str, Any]:
        """
        获取考勤预警信息
        """
        try:
            from collections import defaultdict

            from app.models.attendance import DailyAttendance, WeeklyMood
            from app.models.enums import AttendanceType, WeeklyMoodStatus

            alerts = []
            end_date = date.today()
            start_date = end_date - timedelta(days=date_range)

            # 考勤异常预警
            if not alert_type or alert_type == "attendance":
                # 连续缺勤预警
                absent_records = (
                    await DailyAttendance.filter(
                        work_date__gte=start_date,
                        work_date__lte=end_date,
                        attendance_type__in=[AttendanceType.ABSENCE, AttendanceType.SICK_LEAVE],  # 使用正确的枚举值
                    )
                    .prefetch_related("contract__personnel")
                    .all()
                )

                personnel_absents = defaultdict(int)
                for record in absent_records:
                    if hasattr(record, "contract") and record.contract and record.contract.personnel:
                        personnel_absents[record.contract.personnel.id] += 1

                for personnel_id, absent_days in personnel_absents.items():
                    if absent_days >= 3:  # 连续缺勤3天以上
                        personnel = await Personnel.get(id=personnel_id)
                        alerts.append(
                            {
                                "type": "attendance",
                                "level": "high" if absent_days >= 5 else "medium",
                                "title": f"{personnel.name} 连续缺勤预警",
                                "description": f"最近{date_range}天内缺勤{absent_days}天",
                                "personnel_id": personnel_id,
                                "data": {"absent_days": absent_days},
                            }
                        )

            # 加班过度预警
            if not alert_type or alert_type == "overtime":
                # 获取所有记录，然后在程序中筛选加班时长大于0的
                potential_overtime_records = (
                    await DailyAttendance.filter(work_date__gte=start_date, work_date__lte=end_date)
                    .prefetch_related("contract__personnel")
                    .all()
                )

                # 预缓存合同信息并筛选有加班的记录
                overtime_records = []
                for record in potential_overtime_records:
                    record._contract_cached = record.contract
                    if record.overtime_hours > 0:
                        overtime_records.append(record)

                personnel_overtime = defaultdict(float)
                for record in overtime_records:
                    if hasattr(record, "contract") and record.contract and record.contract.personnel:
                        personnel_overtime[record.contract.personnel.id] += record.overtime_hours or 0

                for personnel_id, total_overtime in personnel_overtime.items():
                    if total_overtime > 40:  # 周加班超过40小时
                        personnel = await Personnel.get(id=personnel_id)
                        alerts.append(
                            {
                                "type": "overtime",
                                "level": "critical" if total_overtime > 60 else "high",
                                "title": f"{personnel.name} 加班过度预警",
                                "description": f"最近{date_range}天加班{total_overtime:.1f}小时",
                                "personnel_id": personnel_id,
                                "data": {"overtime_hours": total_overtime},
                            }
                        )

            # 心情状态预警
            if not alert_type or alert_type == "mood":
                recent_moods = await WeeklyMood.filter(
                    created_at__gte=datetime.now() - timedelta(days=date_range)
                ).all()

                for mood in recent_moods:
                    if mood.mood_status in [WeeklyMoodStatus.STRESSED, WeeklyMoodStatus.DIFFICULT]:
                        personnel = await Personnel.filter(user_id=mood.user_id).first()
                        if personnel:
                            alerts.append(
                                {
                                    "type": "mood",
                                    "level": "medium" if mood.mood_status == WeeklyMoodStatus.STRESSED else "high",
                                    "title": f"{personnel.name} 心情状态预警",
                                    "description": f"心情状态: {mood.mood_emoji} {mood.comment or ''}",
                                    "personnel_id": personnel.id,
                                    "data": {"mood_status": mood.mood_status.value},
                                }
                            )

            # 按预警级别筛选
            if alert_level:
                alerts = [alert for alert in alerts if alert["level"] == alert_level]

            # 按级别和时间排序
            level_priority = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            alerts.sort(key=lambda x: level_priority.get(x["level"], 4))

            return {
                "total_alerts": len(alerts),
                "alert_summary": {
                    "critical": len([a for a in alerts if a["level"] == "critical"]),
                    "high": len([a for a in alerts if a["level"] == "high"]),
                    "medium": len([a for a in alerts if a["level"] == "medium"]),
                    "low": len([a for a in alerts if a["level"] == "low"]),
                },
                "alerts": alerts,
                "date_range": date_range,
            }
        except Exception as e:
            raise Exception(f"考勤预警信息获取失败: {str(e)}")


# 全局实例
dashboard_controller = DashboardController()
