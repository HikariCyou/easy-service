from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

from tortoise.expressions import Q
# Tortoise ORM doesn't support aggregate functions like Django

from app.models.personnel import Personnel
from app.models.bp import BPCompany
from app.models.client import ClientCompany
from app.models.case import Case, CaseCandidate
from app.models.contract import Contract
from app.models.evaluation import PersonEvaluation
from app.models.enums import (
    PersonType, EmploymentStatus, CaseStatus, ContractStatus,
    BPCompanyStatus, CandidateStatus
)


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
        active_contracts = await Contract.filter(
            status=ContractStatus.ACTIVE,
            contract_end_date__gte=today
        ).count()
        
        # 签约率计算
        total_candidates = await CaseCandidate.all().count()
        contract_rate = (total_contracts / total_candidates * 100) if total_candidates > 0 else 0
        
        return {
            "personnel_overview": {
                "total": total_personnel,
                "employees": employees,
                "freelancers": freelancers,
                "bp_personnel": bp_personnel
            },
            "company_overview": {
                "bp_companies": total_bp_companies,
                "client_companies": total_client_companies
            },
            "case_overview": {
                "total": total_cases,
                "open": open_cases,
                "in_progress": in_progress_cases,
                "completed": completed_cases
            },
            "contract_overview": {
                "total": total_contracts,
                "active": active_contracts,
                "contract_rate": round(contract_rate, 2)
            }
        }

    async def get_personnel_distribution(self) -> Dict[str, Any]:
        """
        获取人员分布统计（按类型、状态、国籍等）
        """
        # 按类型分布
        type_distribution = []
        for person_type in PersonType:
            count = await Personnel.filter(person_type=person_type, is_active=True).count()
            type_distribution.append({
                "name": PersonType.get_label(person_type.value) ,
                "value": count
            })
        
        # 按工作状态分布
        status_distribution = []
        for status in EmploymentStatus:
            count = await Personnel.filter(employment_status=status, is_active=True).count()
            status_distribution.append({
                "name": status.value,
                "value": count
            })
        
        # 按国籍分布
        nationality_stats = await Personnel.filter(is_active=True).values_list('nationality', flat=True)
        nationality_count = {}
        for nationality in nationality_stats:
            if nationality:
                nationality_count[nationality] = nationality_count.get(nationality, 0) + 1
        
        nationality_distribution = [
            {"name": k, "value": v} for k, v in sorted(nationality_count.items(), key=lambda x: x[1], reverse=True)
        ]
        
        # 按经验年数分布
        experience_ranges = [
            ("0-1年", 0, 1),
            ("1-3年", 1, 3),
            ("3-5年", 3, 5),
            ("5-10年", 5, 10),
            ("10年以上", 10, 100)
        ]
        
        experience_distribution = []
        for label, min_exp, max_exp in experience_ranges:
            if max_exp == 100:  # 10年以上
                count = await Personnel.filter(
                    it_experience_years__gte=min_exp, is_active=True
                ).count()
            else:
                count = await Personnel.filter(
                    it_experience_years__gte=min_exp,
                    it_experience_years__lt=max_exp,
                    is_active=True
                ).count()
            experience_distribution.append({
                "name": label,
                "value": count
            })
        
        return {
            "type_distribution": type_distribution,
            "status_distribution": status_distribution,
            "nationality_distribution": nationality_distribution[:10],  # 前10位
            "experience_distribution": experience_distribution
        }

    async def get_revenue_analysis(self) -> Dict[str, Any]:
        """
        获取收益分析（单价分布、月收入统计等）
        """
        today = date.today()
        current_month = today.replace(day=1)
        
        # 有效契约的月收入统计
        active_contracts = await Contract.filter(
            status=ContractStatus.ACTIVE,
            contract_start_date__lte=today,
            contract_end_date__gte=today
        ).prefetch_related('personnel')
        
        total_monthly_revenue = sum(float(contract.unit_price) for contract in active_contracts)
        
        # 按人员类型分组的收入
        revenue_by_type = {
            PersonType.get_label(PersonType.EMPLOYEE): 0,
            PersonType.get_label(PersonType.FREELANCER): 0,
            PersonType.get_label(PersonType.BP_EMPLOYEE): 0
        }
        
        for contract in active_contracts:
            if contract.personnel:
                person_type = contract.personnel.person_type.value
                revenue_by_type[ PersonType.get_label(person_type) ] += float(contract.unit_price)
        
        # 单价分布
        unit_price_ranges = [
            ("30万以下", 0, 300000),
            ("30-50万", 300000, 500000),
            ("50-70万", 500000, 700000),
            ("70-100万", 700000, 1000000),
            ("100万以上", 1000000, 10000000)
        ]
        
        unit_price_distribution = []
        for label, min_price, max_price in unit_price_ranges:
            if max_price == 10000000:  # 100万以上
                count = await Contract.filter(
                    unit_price__gte=min_price,
                    status=ContractStatus.ACTIVE
                ).count()
            else:
                count = await Contract.filter(
                    unit_price__gte=min_price,
                    unit_price__lt=max_price,
                    status=ContractStatus.ACTIVE
                ).count()
            unit_price_distribution.append({
                "name": label,
                "value": count
            })
        
        # 平均单价 - 手动计算
        active_contracts_with_price = await Contract.filter(
            status=ContractStatus.ACTIVE,
            unit_price__isnull=False
        ).values_list('unit_price', flat=True)
        
        avg_unit_price = 0
        if active_contracts_with_price:
            avg_unit_price = sum(float(price) for price in active_contracts_with_price) / len(active_contracts_with_price)
        
        return {
            "total_monthly_revenue": total_monthly_revenue,
            "revenue_by_type": revenue_by_type,
            "unit_price_distribution": unit_price_distribution,
            "average_unit_price": avg_unit_price,
            "active_contracts_count": len(active_contracts)
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
            case_status_distribution.append({
                "name": status.value,
                "value": count
            })
        
        # 月度案件趋势（最近12个月）
        monthly_case_trend = []
        for i in range(12):
            month_start = (today.replace(day=1) - timedelta(days=30*i)).replace(day=1)
            if i == 0:
                month_end = today
            else:
                month_end = month_start.replace(day=28) + timedelta(days=4)
                month_end = month_end - timedelta(days=month_end.day)
            
            case_count = await Case.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()
            
            monthly_case_trend.append({
                "month": month_start.strftime("%Y-%m"),
                "count": case_count
            })
        
        monthly_case_trend.reverse()
        
        # 按客户分组的案件数
        client_case_stats = await Case.filter().prefetch_related('client_company').all()
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
            "total_cases": total_cases
        }

    async def get_bp_company_analysis(self) -> Dict[str, Any]:
        """
        获取BP企业分析统计
        """
        # BP企业状态分布
        bp_status_distribution = []
        for status in BPCompanyStatus:
            count = await BPCompany.filter(status=status).count()
            bp_status_distribution.append({
                "name": status.value,
                "value": count
            })
        
        # BP企业人员数排行
        bp_companies = await BPCompany.filter(status=BPCompanyStatus.ACTIVE).prefetch_related('personnel_details').all()
        bp_personnel_count = []
        
        for bp_company in bp_companies:
            personnel_count = await Personnel.filter(
                bp_employee_detail__bp_company=bp_company,
                is_active=True
            ).count()
            bp_personnel_count.append({
                "company_name": bp_company.name,
                "personnel_count": personnel_count
            })
        
        # 按人员数排序，取前10
        bp_personnel_count.sort(key=lambda x: x['personnel_count'], reverse=True)
        top_bp_companies = bp_personnel_count[:10]
        
        # BP企业评价分布
        bp_ratings = await BPCompany.filter(status=BPCompanyStatus.ACTIVE).values_list('rating', flat=True)
        rating_distribution = {}
        for rating in bp_ratings:
            if rating is not None:
                rating_distribution[f"{rating}星"] = rating_distribution.get(f"{rating}星", 0) + 1
        
        rating_dist_list = [{"name": k, "value": v} for k, v in sorted(rating_distribution.items())]
        
        return {
            "status_distribution": bp_status_distribution,
            "top_companies_by_personnel": top_bp_companies,
            "rating_distribution": rating_dist_list,
            "total_bp_companies": len(bp_companies)
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取业绩指标统计
        """
        today = date.today()
        current_month = today.replace(day=1)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        
        # 当月签约数
        current_month_contracts = await Contract.filter(
            created_at__gte=current_month,
            created_at__lte=today
        ).count()
        
        # 上月签约数
        last_month_contracts = await Contract.filter(
            created_at__gte=last_month,
            created_at__lt=current_month
        ).count()
        
        # 签约增长率
        contract_growth_rate = 0
        if last_month_contracts > 0:
            contract_growth_rate = ((current_month_contracts - last_month_contracts) / last_month_contracts) * 100
        
        # 当月新增案件
        current_month_cases = await Case.filter(
            created_at__gte=current_month,
            created_at__lte=today
        ).count()
        
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
            status=ContractStatus.ACTIVE,
            contract_end_date__gte=today
        ).values_list('personnel_id', flat=True)
        personnel_with_contracts = len(set(personnel_ids_with_contracts))
        
        utilization_rate = (personnel_with_contracts / total_active_personnel * 100) if total_active_personnel > 0 else 0
        
        # 客户满意度（基于评价）
        recent_evaluations = await PersonEvaluation.filter(
            evaluation_date__gte=today - timedelta(days=90)
        ).all()
        
        satisfaction_scores = [eval.overall_rating for eval in recent_evaluations if eval.overall_rating]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
        
        return {
            "current_month_contracts": current_month_contracts,
            "contract_growth_rate": round(contract_growth_rate, 2),
            "current_month_cases": current_month_cases,
            "avg_case_processing_days": round(avg_processing_time, 1),
            "personnel_utilization_rate": round(utilization_rate, 2),
            "avg_customer_satisfaction": round(avg_satisfaction, 2),
            "total_evaluations": len(satisfaction_scores)
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
            visa_expire_date__lte=warning_date_90,
            visa_expire_date__gte=today,
            is_active=True
        ).count()
        
        # 合同即将到期
        contracts_expiring_soon = await Contract.filter(
            contract_end_date__lte=warning_date_30,
            contract_end_date__gte=today,
            status=ContractStatus.ACTIVE
        ).count()
        
        # 长期无分配的人员
        available_personnel = await Personnel.filter(
            employment_status=EmploymentStatus.AVAILABLE,
            is_active=True
        ).count()
        
        long_term_available = await Personnel.filter(
            employment_status=EmploymentStatus.AVAILABLE,
            available_start_date__lte=today - timedelta(days=30),
            is_active=True
        ).count()
        
        # 评价较低的人员
        low_rated_person_ids = await PersonEvaluation.filter(
            overall_rating__lte=2,
            evaluation_date__gte=today - timedelta(days=180)
        ).values_list('person_id', flat=True)
        low_rated_personnel = len(set(low_rated_person_ids))
        
        # 空闲的BP企业（无活跃人员）
        idle_bp_companies = 0
        bp_companies = await BPCompany.filter(status=BPCompanyStatus.ACTIVE).all()
        for bp_company in bp_companies:
            active_personnel = await Personnel.filter(
                bp_employee_detail__bp_company=bp_company,
                employment_status=EmploymentStatus.WORKING,
                is_active=True
            ).count()
            if active_personnel == 0:
                idle_bp_companies += 1
        
        return {
            "visa_expiring_soon": visa_expiring_soon,
            "contracts_expiring_soon": contracts_expiring_soon,
            "available_personnel": available_personnel,
            "long_term_available": long_term_available,
            "low_rated_personnel": low_rated_personnel,
            "idle_bp_companies": idle_bp_companies
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
            "last_updated": datetime.now().isoformat()
        }


# 全局实例
dashboard_controller = DashboardController()