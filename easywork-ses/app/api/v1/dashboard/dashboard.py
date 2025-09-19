from typing import Optional

from fastapi import APIRouter, Body, Query

from app.controllers.dashboard import dashboard_controller
from app.schemas import Fail, Success
from app.schemas.dashboard import (
    BPCompanyAnalysisResponse,
    CaseAnalysisResponse,
    ComprehensiveDashboardResponse,
    DashboardFilter,
    OverviewStatsResponse,
    PerformanceMetricsResponse,
    PersonnelDistributionResponse,
    RevenueAnalysisResponse,
    WarningAlertsResponse,
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
                "series": [
                    {
                        "name": "数据分布",
                        "type": "pie",
                        "radius": "50%",
                        "data": [],  # 数据格式: [{"value": 335, "name": "直接访问"}]
                        "emphasis": {
                            "itemStyle": {"shadowBlur": 10, "shadowOffsetX": 0, "shadowColor": "rgba(0, 0, 0, 0.5)"}
                        },
                    }
                ],
            },
            "bar_chart": {
                "title": {"text": "数量统计"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": []},  # 类别数据
                "yAxis": {"type": "value"},
                "series": [{"data": [], "type": "bar"}],  # 数值数据
            },
            "line_chart": {
                "title": {"text": "趋势分析"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": []},  # 时间轴数据
                "yAxis": {"type": "value"},
                "series": [{"data": [], "type": "line", "smooth": True}],  # 趋势数据
            },
            "gauge_chart": {
                "title": {"text": "指标监控"},
                "series": [
                    {
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
                        "data": [{"value": 0, "name": "利用率"}],  # 指标数据
                    }
                ],
            },
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

        from app.models.case import Case
        from app.models.contract import Contract
        from app.models.enums import CaseStatus, ContractStatus, EmploymentStatus
        from app.models.personnel import Personnel

        today = date.today()

        # 实时关键指标
        data = {
            "active_personnel": await Personnel.filter(
                employment_status=EmploymentStatus.WORKING, is_active=True
            ).count(),
            "available_personnel": await Personnel.filter(
                employment_status=EmploymentStatus.AVAILABLE, is_active=True
            ).count(),
            "active_contracts": await Contract.filter(
                status=ContractStatus.ACTIVE, contract_end_date__gte=today
            ).count(),
            "open_cases": await Case.filter(status=CaseStatus.OPEN).count(),
            "timestamp": today.isoformat(),
        }

        return Success(data=data)
    except Exception as e:
        return Fail(msg=f"获取实时统计数据失败: {str(e)}")


# =======================================
# 考勤Dashboard专用接口
# =======================================


@router.get("/attendance/overview", summary="考勤概览统计")
async def get_attendance_overview(
    year_month: Optional[str] = Query(None, description="年月（YYYY-MM）、未指定时是当月", pattern="^\\d{4}-\\d{2}$"),
    department: Optional[str] = Query(None, description="部门筛选"),
    person_type: Optional[str] = Query(None, description="要员类型筛选"),
):
    """
    考勤概览统计 - 适用于dashboard首页卡片

    返回数据:
    - 总要员数、在职要员数
    - 本月出勤率、迟到率
    - 提交完成率、审批完成率
    - 有薪假期使用情况
    - 加班时长统计

    适用图表: 卡片数值显示、环形图
    """
    try:
        data = await dashboard_controller.get_attendance_overview(
            year_month=year_month, department=department, person_type=person_type
        )
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/attendance/trend", summary="考勤趋势分析")
async def get_attendance_trend(
    period_type: str = Query("month", description="统计周期", pattern="^(week|month|quarter)$"),
    periods: int = Query(6, ge=1, le=24, description="统计期数（1-24）"),
    metric: str = Query(
        "attendance_rate", description="统计指标", pattern="^(attendance_rate|working_hours|overtime_hours|leave_days)$"
    ),
    department: Optional[str] = Query(None, description="部门筛选"),
    person_type: Optional[str] = Query(None, description="要员类型筛选"),
):
    """
    考勤趋势分析 - 时间序列数据

    统计周期:
    - week: 周统计（最多24周）
    - month: 月统计（最多24月）
    - quarter: 季度统计（最多8季）

    统计指标:
    - attendance_rate: 出勤率趋势
    - working_hours: 工作时长趋势
    - overtime_hours: 加班时长趋势
    - leave_days: 请假天数趋势

    适用图表: 折线图、柱状图
    """
    try:
        trend = await dashboard_controller.get_attendance_trend(
            period_type=period_type, periods=periods, metric=metric, department=department, person_type=person_type
        )
        return Success(data=trend)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/attendance/distribution", summary="考勤数据分布分析")
async def get_attendance_distribution(
    analysis_type: str = Query(
        "department", description="分析维度", pattern="^(department|person_type|age_group|nationality)$"
    ),
    year_month: Optional[str] = Query(None, description="年月（YYYY-MM）", pattern="^\\d{4}-\\d{2}$"),
    metric: str = Query(
        "attendance_rate", description="分析指标", pattern="^(attendance_rate|working_hours|overtime_rate|leave_rate)$"
    ),
):
    """
    考勤数据分布分析 - 多维度对比

    分析维度:
    - department: 按部门分析
    - person_type: 按要员类型分析（BP/自社/フリー）
    - age_group: 按年龄段分析
    - nationality: 按国籍分析

    分析指标:
    - attendance_rate: 出勤率分布
    - working_hours: 工作时长分布
    - overtime_rate: 加班比率分布
    - leave_rate: 请假率分布

    适用图表: 饼图、环形图、柱状图
    """
    try:
        distribution = await dashboard_controller.get_attendance_distribution(
            analysis_type=analysis_type, year_month=year_month, metric=metric
        )
        return Success(data=distribution)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/attendance/ranking", summary="考勤排行榜")
async def get_attendance_ranking(
    rank_type: str = Query(
        "attendance_rate",
        description="排行类型",
        pattern="^(attendance_rate|working_hours|overtime_hours|efficiency_score)$",
    ),
    year_month: Optional[str] = Query(None, description="年月（YYYY-MM）", pattern="^\\d{4}-\\d{2}$"),
    top_n: int = Query(10, ge=5, le=50, description="排行榜人数（5-50）"),
    department: Optional[str] = Query(None, description="部门筛选"),
    person_type: Optional[str] = Query(None, description="要员类型筛选"),
):
    """
    考勤排行榜 - 个人/团队表现排名

    排行类型:
    - attendance_rate: 出勤率排名
    - working_hours: 工作时长排名
    - overtime_hours: 加班时长排名（反向）
    - efficiency_score: 工作效率评分排名

    适用图表: 横向柱状图、表格
    """
    try:
        ranking = await dashboard_controller.get_attendance_ranking(
            rank_type=rank_type, year_month=year_month, top_n=top_n, department=department, person_type=person_type
        )
        return Success(data=ranking)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/attendance/calendar-heatmap", summary="考勤热力图数据")
async def get_attendance_calendar_heatmap(
    year: int = Query(..., ge=2020, le=2030, description="年份"),
    metric: str = Query(
        "attendance_count", description="热力图指标", pattern="^(attendance_count|working_hours|overtime_hours|leave_count)$"
    ),
    user_id: Optional[int] = Query(None, description="指定用户ID（个人视图）"),
):
    """
    考勤热力图数据 - 全年考勤活跃度可视化

    热力图指标:
    - attendance_count: 每日出勤人数
    - working_hours: 每日总工作时长
    - overtime_hours: 每日总加班时长
    - leave_count: 每日请假人数

    返回格式: [[date, value], ...] 适合ECharts日历热力图
    适用图表: 日历热力图
    """
    try:
        heatmap = await dashboard_controller.get_attendance_calendar_heatmap(year=year, metric=metric, user_id=user_id)
        return Success(data=heatmap)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/mood/analysis", summary="心情数据分析")
async def get_mood_analysis(
    analysis_period: str = Query("month", description="分析周期", pattern="^(week|month|quarter)$"),
    periods: int = Query(12, ge=4, le=24, description="分析期数"),
    analysis_type: str = Query("trend", description="分析类型", pattern="^(trend|distribution|correlation)$"),
    team_view: bool = Query(False, description="团队视图（管理者权限）"),
):
    """
    心情数据分析 - 员工心理状态分析

    分析类型:
    - trend: 心情趋势分析（时间序列）
    - distribution: 心情状态分布（饼图数据）
    - correlation: 心情与考勤相关性分析

    适用图表:
    - trend: 折线图、面积图
    - distribution: 饼图、环形图
    - correlation: 散点图、热力图
    """
    try:
        from app.core.ctx import CTX_USER_ID

        user_id = CTX_USER_ID.get()
        if not user_id:
            return Fail(msg="用户信息获取失败")

        analysis = await dashboard_controller.get_mood_analysis(
            user_id=user_id,
            analysis_period=analysis_period,
            periods=periods,
            analysis_type=analysis_type,
            team_view=team_view,
        )
        return Success(data=analysis)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/alerts/attendance", summary="考勤预警信息")
async def get_attendance_alerts(
    alert_level: Optional[str] = Query(None, description="预警级别筛选", pattern="^(low|medium|high|critical)$"),
    alert_type: Optional[str] = Query(
        None, description="预警类型筛选", pattern="^(attendance|overtime|leave|mood|performance)$"
    ),
    date_range: int = Query(7, ge=1, le=30, description="预警时间范围（天数）"),
):
    """
    考勤预警信息汇总 - 需要关注的问题

    预警类型:
    - attendance: 考勤异常（连续迟到、缺勤）
    - overtime: 加班过度预警
    - leave: 请假异常预警
    - mood: 心情状态预警（连续低落）
    - performance: 绩效下滑预警

    适用显示: 告警列表、状态卡片
    """
    try:
        alerts = await dashboard_controller.get_attendance_alerts(
            alert_level=alert_level, alert_type=alert_type, date_range=date_range
        )
        return Success(data=alerts)
    except Exception as e:
        return Fail(msg=str(e))
