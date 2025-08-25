from typing import Optional
from fastapi import APIRouter, Query, Body

from app.controllers.dashboard import dashboard_controller
from app.schemas import Success, Fail
from app.schemas.dashboard import (
    ComprehensiveDashboardResponse,
    OverviewStatsResponse,
    PersonnelDistributionResponse,
    RevenueAnalysisResponse,
    CaseAnalysisResponse,
    BPCompanyAnalysisResponse,
    PerformanceMetricsResponse,
    WarningAlertsResponse,
    DashboardFilter
)

router = APIRouter()


@router.get("/comprehensive", summary="综合Dashboard数据获取")
async def get_comprehensive_dashboard():
    """
    获取综合Dashboard的所有统计数据
    
    包含内容：
    - 总览统计：人员、企业、案件、契约概况
    - 人员分布：按类型、状态、国籍、经验分布
    - 收益分析：月收入、单价分布、平均单价
    - 案件分析：状态分布、月度趋势、客户排行、成功率
    - BP企业分析：状态分布、人员排行、评价分布
    - 业绩指标：签约增长率、处理时间、利用率、满意度
    - 预警提醒：签证到期、契约到期、长期可用人员等
    
    适用于：主Dashboard页面的一次性数据加载
    """
    try:
        data = await dashboard_controller.get_comprehensive_dashboard()
        return Success(data=data)
    except Exception as e:
        return Fail(msg=f"获取综合Dashboard数据失败: {str(e)}")


@router.get("/overview", summary="总览统计")
async def get_overview_stats():
    """
    获取总览统计数据
    
    包含：
    - 人员总览：自社员工、自由职业者、BP人员数量
    - 企业总览：BP企业、客户企业数量
    - 案件总览：总数、开放、进行中、已完成案件数
    - 契约总览：总数、活跃契约数、签约率
    """
    try:
        data = await dashboard_controller.get_overview_stats()
        return Success(data=data)
    except Exception as e:
        return Fail(msg=f"获取总览统计失败: {str(e)}")


@router.get("/personnel-distribution", summary="人员分布统计")
async def get_personnel_distribution():
    """
    获取人员分布统计
    
    包含：
    - 按人员类型分布（饼图数据）
    - 按工作状态分布（饼图数据）
    - 按国籍分布（柱状图数据，前10位）
    - 按IT经验年数分布（柱状图数据）
    
    适用于：人员管理Dashboard的图表展示
    """
    try:
        data = await dashboard_controller.get_personnel_distribution()
        return Success(data=data)
    except Exception as e:
        return Fail(msg=f"获取人员分布统计失败: {str(e)}")


@router.get("/revenue-analysis", summary="收益分析")
async def get_revenue_analysis():
    """
    获取收益分析统计
    
    包含：
    - 当月总收入（活跃契约）
    - 按人员类型分组的收入
    - 单价分布（柱状图数据）
    - 平均单价
    - 活跃契约数量
    
    适用于：财务Dashboard的收益分析图表
    """
    try:
        data = await dashboard_controller.get_revenue_analysis()
        return Success(data=data)
    except Exception as e:
        return Fail(msg=f"获取收益分析失败: {str(e)}")


@router.get("/case-analysis", summary="案件分析")
async def get_case_analysis():
    """
    获取案件分析统计
    
    包含：
    - 案件状态分布（饼图数据）
    - 月度案件趋势（折线图数据，最近12个月）
    - 前10客户的案件数排行（柱状图数据）
    - 案件成功率
    - 总案件数
    
    适用于：案件管理Dashboard的分析图表
    """
    try:
        data = await dashboard_controller.get_case_analysis()
        return Success(data=data)
    except Exception as e:
        return Fail(msg=f"获取案件分析失败: {str(e)}")


@router.get("/bp-company-analysis", summary="BP企业分析")
async def get_bp_company_analysis():
    """
    获取BP企业分析统计
    
    包含：
    - BP企业状态分布（饼图数据）
    - 按人员数排行的前10 BP企业（柱状图数据）
    - BP企业评价分布（柱状图数据）
    - 总BP企业数
    
    适用于：BP企业管理Dashboard的分析图表
    """
    try:
        data = await dashboard_controller.get_bp_company_analysis()
        return Success(data=data)
    except Exception as e:
        return Fail(msg=f"获取BP企业分析失败: {str(e)}")


@router.get("/performance-metrics", summary="业绩指标")
async def get_performance_metrics():
    """
    获取业绩指标统计
    
    包含：
    - 当月签约数
    - 签约增长率（与上月对比）
    - 当月新增案件数
    - 平均案件处理天数
    - 人员利用率
    - 平均客户满意度
    - 评价总数
    
    适用于：管理层Dashboard的KPI监控
    """
    try:
        data = await dashboard_controller.get_performance_metrics()
        return Success(data=data)
    except Exception as e:
        return Fail(msg=f"获取业绩指标失败: {str(e)}")


@router.get("/warning-alerts", summary="预警提醒")
async def get_warning_alerts():
    """
    获取预警提醒统计
    
    包含：
    - 签证即将到期人数（90天内）
    - 契约即将到期数（30天内）
    - 当前可用人员数
    - 长期可用人员数（30天以上）
    - 低评价人员数（评分≤2）
    - 空闲BP企业数（无活跃人员）
    
    适用于：Dashboard的预警提醒组件
    """
    try:
        data = await dashboard_controller.get_warning_alerts()
        return Success(data=data)
    except Exception as e:
        return Fail(msg=f"获取预警提醒失败: {str(e)}")


@router.get("/echart-templates", summary="EChart模板配置")
async def get_echart_templates():
    """
    获取前端EChart图表的推荐配置模板
    
    为前端开发提供常用的EChart配置选项：
    - 饼图配置（人员类型分布、案件状态分布等）
    - 柱状图配置（收入分析、企业排行等）
    - 折线图配置（月度趋势等）
    - 仪表盘配置（利用率、满意度等）
    
    注意：这是静态配置模板，实际数据需要调用对应的统计API获取
    """
    try:
        templates = {
            "pie_chart": {
                "title": {"text": "分布统计", "left": "center"},
                "tooltip": {"trigger": "item"},
                "legend": {"orient": "vertical", "left": "left"},
                "series": [{
                    "name": "数据分布",
                    "type": "pie",
                    "radius": "50%",
                    "data": [],  # 数据格式: [{"value": 335, "name": "直接访问"}]
                    "emphasis": {
                        "itemStyle": {
                            "shadowBlur": 10,
                            "shadowOffsetX": 0,
                            "shadowColor": "rgba(0, 0, 0, 0.5)"
                        }
                    }
                }]
            },
            "bar_chart": {
                "title": {"text": "数量统计"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": []},  # 类别数据
                "yAxis": {"type": "value"},
                "series": [{
                    "data": [],  # 数值数据
                    "type": "bar"
                }]
            },
            "line_chart": {
                "title": {"text": "趋势分析"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": []},  # 时间轴数据
                "yAxis": {"type": "value"},
                "series": [{
                    "data": [],  # 趋势数据
                    "type": "line",
                    "smooth": True
                }]
            },
            "gauge_chart": {
                "title": {"text": "指标监控"},
                "series": [{
                    "type": "gauge",
                    "startAngle": 180,
                    "endAngle": 0,
                    "min": 0,
                    "max": 100,
                    "pointer": {"show": False},
                    "progress": {"show": True, "overlap": False, "roundCap": True, "clip": False},
                    "axisLine": {"lineStyle": {"width": 40}},
                    "splitLine": {"show": False},
                    "axisTick": {"show": False},
                    "axisLabel": {"show": False},
                    "data": [{"value": 0, "name": "利用率"}]  # 指标数据
                }]
            }
        }
        
        return Success(data=templates)
    except Exception as e:
        return Fail(msg=f"获取EChart模板失败: {str(e)}")


@router.get("/real-time-stats", summary="实时统计数据")
async def get_real_time_stats():
    """
    获取实时更新的关键统计数据
    
    提供轻量级的实时数据，适用于：
    - Dashboard首页的实时监控组件
    - 系统状态指示器
    - 快速概览数据
    
    数据更新频率建议：每30秒-1分钟
    """
    try:
        from datetime import date
        from app.models.personnel import Personnel
        from app.models.contract import Contract
        from app.models.case import Case
        from app.models.enums import EmploymentStatus, ContractStatus, CaseStatus
        
        today = date.today()
        
        # 实时关键指标
        data = {
            "active_personnel": await Personnel.filter(
                employment_status=EmploymentStatus.WORKING, 
                is_active=True
            ).count(),
            "available_personnel": await Personnel.filter(
                employment_status=EmploymentStatus.AVAILABLE, 
                is_active=True
            ).count(),
            "active_contracts": await Contract.filter(
                status=ContractStatus.ACTIVE,
                contract_end_date__gte=today
            ).count(),
            "open_cases": await Case.filter(status=CaseStatus.OPEN).count(),
            "timestamp": today.isoformat()
        }
        
        return Success(data=data)
    except Exception as e:
        return Fail(msg=f"获取实时统计数据失败: {str(e)}")