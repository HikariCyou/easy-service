from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChartDataPoint(BaseModel):
    """图表数据点"""

    name: str = Field(..., description="数据点名称")
    value: int = Field(..., description="数据点数值")


class OverviewStats(BaseModel):
    """总览统计"""

    personnel_overview: Dict[str, int] = Field(..., description="人员总览统计")
    company_overview: Dict[str, int] = Field(..., description="企业总览统计")
    case_overview: Dict[str, int] = Field(..., description="案件总览统计")
    contract_overview: Dict[str, Any] = Field(..., description="契约总览统计")


class PersonnelDistribution(BaseModel):
    """人员分布统计"""

    type_distribution: List[ChartDataPoint] = Field(..., description="按类型分布")
    status_distribution: List[ChartDataPoint] = Field(..., description="按状态分布")
    nationality_distribution: List[ChartDataPoint] = Field(..., description="按国籍分布")
    experience_distribution: List[ChartDataPoint] = Field(..., description="按经验分布")


class RevenueAnalysis(BaseModel):
    """收益分析"""

    total_monthly_revenue: float = Field(..., description="当月总收入")
    revenue_by_type: Dict[str, float] = Field(..., description="按人员类型分组收入")
    unit_price_distribution: List[ChartDataPoint] = Field(..., description="单价分布")
    average_unit_price: float = Field(..., description="平均单价")
    active_contracts_count: int = Field(..., description="活跃契约数")


class MonthlyTrendPoint(BaseModel):
    """月度趋势数据点"""

    month: str = Field(..., description="月份", example="2024-01")
    count: int = Field(..., description="数量")


class CaseAnalysis(BaseModel):
    """案件分析"""

    status_distribution: List[ChartDataPoint] = Field(..., description="案件状态分布")
    monthly_trend: List[MonthlyTrendPoint] = Field(..., description="月度案件趋势")
    top_clients: List[ChartDataPoint] = Field(..., description="前10客户案件数")
    success_rate: float = Field(..., description="案件成功率(%)")
    total_cases: int = Field(..., description="总案件数")


class BPCompanyRanking(BaseModel):
    """BP企业排行"""

    company_name: str = Field(..., description="企业名称")
    personnel_count: int = Field(..., description="人员数量")


class BPCompanyAnalysis(BaseModel):
    """BP企业分析"""

    status_distribution: List[ChartDataPoint] = Field(..., description="BP企业状态分布")
    top_companies_by_personnel: List[BPCompanyRanking] = Field(..., description="按人员数排行的前10 BP企业")
    rating_distribution: List[ChartDataPoint] = Field(..., description="BP企业评价分布")
    total_bp_companies: int = Field(..., description="总BP企业数")


class PerformanceMetrics(BaseModel):
    """业绩指标"""

    current_month_contracts: int = Field(..., description="当月签约数")
    contract_growth_rate: float = Field(..., description="签约增长率(%)")
    current_month_cases: int = Field(..., description="当月新增案件")
    avg_case_processing_days: float = Field(..., description="平均案件处理天数")
    personnel_utilization_rate: float = Field(..., description="人员利用率(%)")
    avg_customer_satisfaction: float = Field(..., description="平均客户满意度")
    total_evaluations: int = Field(..., description="评价总数")


class WarningAlerts(BaseModel):
    """预警提醒"""

    visa_expiring_soon: int = Field(..., description="签证即将到期人数")
    contracts_expiring_soon: int = Field(..., description="契约即将到期数")
    available_personnel: int = Field(..., description="可用人员数")
    long_term_available: int = Field(..., description="长期可用人员数")
    low_rated_personnel: int = Field(..., description="低评价人员数")
    idle_bp_companies: int = Field(..., description="空闲BP企业数")


class ComprehensiveDashboard(BaseModel):
    """综合dashboard数据"""

    overview: OverviewStats = Field(..., description="总览统计")
    personnel_distribution: PersonnelDistribution = Field(..., description="人员分布统计")
    revenue_analysis: RevenueAnalysis = Field(..., description="收益分析")
    case_analysis: CaseAnalysis = Field(..., description="案件分析")
    bp_company_analysis: BPCompanyAnalysis = Field(..., description="BP企业分析")
    performance_metrics: PerformanceMetrics = Field(..., description="业绩指标")
    warning_alerts: WarningAlerts = Field(..., description="预警提醒")
    last_updated: str = Field(..., description="最后更新时间")


class DashboardFilter(BaseModel):
    """Dashboard过滤条件"""

    date_range: Optional[str] = Field(None, description="日期范围", example="last_30_days")
    person_type: Optional[str] = Field(None, description="人员类型过滤")
    bp_company_id: Optional[int] = Field(None, description="BP企业ID过滤")
    case_status: Optional[str] = Field(None, description="案件状态过滤")
    include_inactive: bool = Field(False, description="是否包含非活跃数据")


# 单独的统计API响应schemas
class OverviewStatsResponse(BaseModel):
    """总览统计响应"""

    data: OverviewStats


class PersonnelDistributionResponse(BaseModel):
    """人员分布统计响应"""

    data: PersonnelDistribution


class RevenueAnalysisResponse(BaseModel):
    """收益分析响应"""

    data: RevenueAnalysis


class CaseAnalysisResponse(BaseModel):
    """案件分析响应"""

    data: CaseAnalysis


class BPCompanyAnalysisResponse(BaseModel):
    """BP企业分析响应"""

    data: BPCompanyAnalysis


class PerformanceMetricsResponse(BaseModel):
    """业绩指标响应"""

    data: PerformanceMetrics


class WarningAlertsResponse(BaseModel):
    """预警提醒响应"""

    data: WarningAlerts


class ComprehensiveDashboardResponse(BaseModel):
    """综合dashboard响应"""

    data: ComprehensiveDashboard
