import json
from datetime import date, datetime, timedelta, time
from typing import Any, Dict, List, Optional

from tortoise.expressions import Q

from app.core.ctx import CTX_USER_ID, CTX_USER_INFO
from app.core.process_client import process_client
from app.core.user_client import user_client

# 工作流常量
EXPENSE_APPROVAL_PROCESS_KEY = "TOB_COMMUTING"
from app.models.finance import (
    FinanceTransaction,
    FinanceRecurrenceRule,
    FinanceBudget,
    FinanceReport,
    FinanceAttachment,
    ExpenseApplication,
    ExpenseApprovalHistory,
)
from app.models.enums import (
    FinanceTransactionType,
    FinanceStatus,
    FinanceApprovalStatus,
    ApplicationStatus,
)
from app.schemas.finance import (
    FinanceTransactionCreate,
    FinanceTransactionUpdate,
    FinanceTransactionListQuery,
    FinanceRecurrenceRuleCreate,
    FinanceRecurrenceRuleUpdate,
    FinanceBudgetCreate,
    FinanceBudgetUpdate,
    FinanceAnalyticsQuery,
    FinanceReportGenerateRequest,
    ExpenseApplicationCreate,
    ExpenseApplicationUpdate,
    ExpenseApplicationListQuery,
)
from app.utils.common import clean_dict


class FinanceController:
    def __init__(self):
        pass

    def _get_current_user_info(self):
        """現在のユーザー情報を取得"""
        user_id = CTX_USER_ID.get()
        user_info = CTX_USER_INFO.get()
        user_name = user_info.get("nickname") if user_info else None
        return user_id, user_name

    def _generate_transaction_number(self) -> str:
        """取引番号を生成"""
        now = datetime.now()
        return f"TXN-{now.strftime('%Y%m%d%H%M%S')}-{now.microsecond // 1000:03d}"

    # ==================== 財務取引管理 ====================

    async def create_transaction(self, data: FinanceTransactionCreate) -> Dict[str, Any]:
        """財務取引を作成"""
        user_id, user_name = self._get_current_user_info()

        transaction_data = data.dict(exclude_unset=True)
        transaction_data["transaction_number"] = self._generate_transaction_number()
        transaction_data["requested_by"] = user_name

        # 税額を計算
        if transaction_data.get("tax_rate", 0) > 0:
            tax_amount = transaction_data["amount"] * (transaction_data["tax_rate"] / 100)
            transaction_data["tax_amount"] = tax_amount
            transaction_data["tax_exclusive_amount"] = transaction_data["amount"] - tax_amount

        transaction = await FinanceTransaction.create(**transaction_data)

        return {
            "transaction": await transaction.to_dict(),
            "message": "財務取引が正常に作成されました"
        }

    async def get_transaction_list(self, query: FinanceTransactionListQuery) -> Dict[str, Any]:
        """財務取引一覧を取得"""
        filters = Q()

        # フィルタ条件構築
        if query.transaction_type:
            filters &= Q(transaction_type=query.transaction_type)
        if query.category:
            filters &= Q(category=query.category)
        if query.status:
            filters &= Q(status=query.status)
        if query.approval_status:
            filters &= Q(approval_status=query.approval_status)
        if query.payment_date_from:
            filters &= Q(payment_date__gte=query.payment_date_from)
        if query.payment_date_to:
            filters &= Q(payment_date__lte=query.payment_date_to)
        if query.amount_min is not None:
            filters &= Q(amount__gte=query.amount_min)
        if query.amount_max is not None:
            filters &= Q(amount__lte=query.amount_max)
        if query.counterpart:
            filters &= Q(counterpart__icontains=query.counterpart)
        if query.case_id:
            filters &= Q(case_id=query.case_id)
        if query.contract_id:
            filters &= Q(contract_id=query.contract_id)
        if query.personnel_id:
            filters &= Q(personnel_id=query.personnel_id)
        if query.search_keyword:
            filters &= Q(
                Q(title__icontains=query.search_keyword) |
                Q(description__icontains=query.search_keyword) |
                Q(counterpart__icontains=query.search_keyword)
            )

        # 総数取得
        total = await FinanceTransaction.filter(filters).count()

        # データ取得
        transactions = await FinanceTransaction.filter(filters).select_related(
            "case", "contract", "personnel", "recurrence_rule"
        ).order_by("-created_at").offset(
            (query.page - 1) * query.page_size
        ).limit(query.page_size).all()

        transaction_list = []
        for txn in transactions:
            txn_dict = await txn.to_dict()
            transaction_list.append(txn_dict)

        # 状态统计（見込み）
        base_filters = Q()
        # 复制原始过滤条件，但排除status过滤
        if query.transaction_type:
            base_filters &= Q(transaction_type=query.transaction_type)
        if query.category:
            base_filters &= Q(category=query.category)
        if query.approval_status:
            base_filters &= Q(approval_status=query.approval_status)
        if query.payment_date_from:
            base_filters &= Q(payment_date__gte=query.payment_date_from)
        if query.payment_date_to:
            base_filters &= Q(payment_date__lte=query.payment_date_to)
        if query.amount_min is not None:
            base_filters &= Q(amount__gte=query.amount_min)
        if query.amount_max is not None:
            base_filters &= Q(amount__lte=query.amount_max)
        if query.counterpart:
            base_filters &= Q(counterpart__icontains=query.counterpart)
        if query.case_id:
            base_filters &= Q(case_id=query.case_id)
        if query.contract_id:
            base_filters &= Q(contract_id=query.contract_id)
        if query.personnel_id:
            base_filters &= Q(personnel_id=query.personnel_id)
        if query.search_keyword:
            base_filters &= Q(
                Q(title__icontains=query.search_keyword) |
                Q(description__icontains=query.search_keyword) |
                Q(counterpart__icontains=query.search_keyword)
            )

        # 各状态统计
        # 保留中状态
        pending_count = await FinanceTransaction.filter(base_filters & Q(status=FinanceStatus.PENDING)).count()
        pending_transactions = await FinanceTransaction.filter(base_filters & Q(status=FinanceStatus.PENDING)).all()
        pending_amount = sum(txn.amount for txn in pending_transactions)

        # 処理中状态
        processing_count = await FinanceTransaction.filter(base_filters & Q(status=FinanceStatus.PROCESSING)).count()
        processing_transactions = await FinanceTransaction.filter(base_filters & Q(status=FinanceStatus.PROCESSING)).all()
        processing_amount = sum(txn.amount for txn in processing_transactions)

        # 完了状态
        completed_count = await FinanceTransaction.filter(base_filters & Q(status=FinanceStatus.COMPLETED)).count()
        completed_transactions = await FinanceTransaction.filter(base_filters & Q(status=FinanceStatus.COMPLETED)).all()
        completed_amount = sum(txn.amount for txn in completed_transactions)

        # キャンセル状态
        cancelled_count = await FinanceTransaction.filter(base_filters & Q(status=FinanceStatus.CANCELLED)).count()
        cancelled_transactions = await FinanceTransaction.filter(base_filters & Q(status=FinanceStatus.CANCELLED)).all()
        cancelled_amount = sum(txn.amount for txn in cancelled_transactions)

        # 承認待ち状态
        approval_pending_count = await FinanceTransaction.filter(base_filters & Q(approval_status=FinanceApprovalStatus.PENDING)).count()
        approval_pending_transactions = await FinanceTransaction.filter(base_filters & Q(approval_status=FinanceApprovalStatus.PENDING)).all()
        approval_pending_amount = sum(txn.amount for txn in approval_pending_transactions)

        # 承認済み状态
        approved_count = await FinanceTransaction.filter(base_filters & Q(approval_status=FinanceApprovalStatus.APPROVED)).count()
        approved_transactions = await FinanceTransaction.filter(base_filters & Q(approval_status=FinanceApprovalStatus.APPROVED)).all()
        approved_amount = sum(txn.amount for txn in approved_transactions)

        # 却下状态（单独统计，不计入見込み）
        rejected_count = await FinanceTransaction.filter(base_filters & Q(approval_status=FinanceApprovalStatus.REJECTED)).count()
        rejected_transactions = await FinanceTransaction.filter(base_filters & Q(approval_status=FinanceApprovalStatus.REJECTED)).all()
        rejected_amount = sum(txn.amount for txn in rejected_transactions)

        # 見込み总计（排除取消和拒绝的）
        pending_total_count = pending_count + processing_count + approval_pending_count + approved_count
        pending_total_amount = pending_amount + processing_amount + approval_pending_amount + approved_amount

        status_stats = {
            "pending": {
                "count": pending_count,
                "total_amount": pending_amount,
                "status_label": "保留中"
            },
            "processing": {
                "count": processing_count,
                "total_amount": processing_amount,
                "status_label": "処理中"
            },
            "completed": {
                "count": completed_count,
                "total_amount": completed_amount,
                "status_label": "完了"
            },
            "cancelled": {
                "count": cancelled_count,
                "total_amount": cancelled_amount,
                "status_label": "キャンセル"
            },
            "approval_pending": {
                "count": approval_pending_count,
                "total_amount": approval_pending_amount,
                "status_label": "承認待ち"
            },
            "approved": {
                "count": approved_count,
                "total_amount": approved_amount,
                "status_label": "承認済み"
            },
            "rejected": {
                "count": rejected_count,
                "total_amount": rejected_amount,
                "status_label": "却下"
            },
            "pending_total": {
                "count": pending_total_count,
                "total_amount": pending_total_amount,
                "description": "見込み総額（キャンセル・却下を除く）"
            }
        }

        return {
            "transactions": transaction_list,
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "total_pages": (total + query.page_size - 1) // query.page_size,
            "status_statistics": status_stats
        }

    async def get_transaction_detail(self, transaction_id: int) -> Dict[str, Any]:
        """財務取引詳細を取得"""
        transaction = await FinanceTransaction.filter(id=transaction_id).select_related(
            "case", "contract", "personnel", "recurrence_rule"
        ).first()

        if not transaction:
            raise ValueError("指定された取引が見つかりません")

        # 添付ファイル取得
        # attachments = await FinanceAttachment.filter(transaction_id=transaction_id).all()

        return {
            "transaction": await transaction.to_dict(),
            "case": await transaction.case.to_dict() if transaction.case else None,
            "contract": await transaction.contract.to_dict() if transaction.contract else None,
            "personnel": await transaction.personnel.to_dict() if transaction.personnel else None,
            # "attachments": [await att.to_dict() for att in attachments]
        }

    async def update_transaction(self, transaction_id: int, data: FinanceTransactionUpdate) -> Dict[str, Any]:
        """財務取引を更新"""
        transaction = await FinanceTransaction.get_or_none(id=transaction_id)
        if not transaction:
            raise ValueError("指定された取引が見つかりません")

        update_data = clean_dict(data.dict(exclude_unset=True))

        # 税額再計算
        if "tax_rate" in update_data or "amount" in update_data:
            amount = update_data.get("amount", transaction.amount)
            tax_rate = update_data.get("tax_rate", transaction.tax_rate)
            if tax_rate > 0:
                tax_amount = amount * (tax_rate / 100)
                update_data["tax_amount"] = tax_amount
                update_data["tax_exclusive_amount"] = amount - tax_amount

        await transaction.update_from_dict(update_data)
        await transaction.save()

        return {
            "transaction": await transaction.to_dict(),
            "message": "財務取引が正常に更新されました"
        }

    async def approve_transaction(self, transaction_id: int, action: str, notes: str = None) -> Dict[str, Any]:
        """財務取引を承認/拒否"""
        user_id, user_name = self._get_current_user_info()

        transaction = await FinanceTransaction.get_or_none(id=transaction_id)
        if not transaction:
            raise ValueError("指定された取引が見つかりません")

        if action == "approve":
            await transaction.approve(user_name, notes)
            message = "財務取引が承認されました"
        elif action == "reject":
            await transaction.reject(user_name, notes)
            message = "財務取引が拒否されました"
        else:
            raise ValueError("不正なアクション")

        return {
            "transaction": await transaction.to_dict(),
            "message": message
        }

    async def delete_transaction(self, transaction_id: int) -> Dict[str, Any]:
        """財務取引を削除"""
        transaction = await FinanceTransaction.get_or_none(id=transaction_id)
        if not transaction:
            raise ValueError("指定された取引が見つかりません")

        # 承認済みの取引は削除できない
        if transaction.approval_status == FinanceApprovalStatus.APPROVED:
            raise ValueError("承認済みの取引は削除できません")

        await transaction.delete()

        return {"message": "財務取引が正常に削除されました"}

    # ==================== 定期取引ルール管理 ====================

    async def create_recurrence_rule(self, data: FinanceRecurrenceRuleCreate) -> Dict[str, Any]:
        """定期取引ルールを作成"""
        rule_data = data.dict()
        rule = await FinanceRecurrenceRule.create(**rule_data)

        return {
            "rule": await rule.to_dict(),
            "message": "定期取引ルールが正常に作成されました"
        }

    async def get_recurrence_rule_list(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """定期取引ルール一覧を取得"""
        total = await FinanceRecurrenceRule.all().count()
        rules = await FinanceRecurrenceRule.all().order_by("-created_at").offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        rule_list = []
        for rule in rules:
            rule_dict = await rule.to_dict()
            rule_list.append(rule_dict)

        return {
            "rules": rule_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def update_recurrence_rule(self, rule_id: int, data: FinanceRecurrenceRuleUpdate) -> Dict[str, Any]:
        """定期取引ルールを更新"""
        rule = await FinanceRecurrenceRule.get_or_none(id=rule_id)
        if not rule:
            raise ValueError("指定された定期取引ルールが見つかりません")

        update_data = clean_dict(data.dict(exclude_unset=True))
        await rule.update_from_dict(update_data)
        await rule.save()

        return {
            "rule": await rule.to_dict(),
            "message": "定期取引ルールが正常に更新されました"
        }

    async def execute_recurrence_rules(self) -> Dict[str, Any]:
        """定期取引ルールを実行"""
        executed_count = 0
        created_transactions = []

        rules = await FinanceRecurrenceRule.filter(is_active=True).all()

        for rule in rules:
            if await rule.should_execute_today():
                transaction = await rule.create_transaction()
                created_transactions.append(await transaction.to_dict())
                executed_count += 1

        return {
            "executed_count": executed_count,
            "created_transactions": created_transactions,
            "message": f"{executed_count}件の定期取引が実行されました"
        }

    # ==================== 予算管理 ====================

    async def create_budget(self, data: FinanceBudgetCreate) -> Dict[str, Any]:
        """予算を作成"""
        budget_data = data.dict()
        budget_data["remaining_amount"] = budget_data["budget_amount"]

        budget = await FinanceBudget.create(**budget_data)

        return {
            "budget": await budget.to_dict(),
            "message": "予算が正常に作成されました"
        }

    async def get_budget_list(self, page: int = 1, page_size: int = 20, category: str = None) -> Dict[str, Any]:
        """予算一覧を取得"""
        filters = Q(is_active=True)
        if category:
            filters &= Q(category=category)

        total = await FinanceBudget.filter(filters).count()
        budgets = await FinanceBudget.filter(filters).order_by("-created_at").offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        budget_list = []
        for budget in budgets:
            await budget.update_spent_amount()  # 最新の使用額で更新
            budget_dict = await budget.to_dict()
            budget_dict["usage_percentage"] = budget.usage_percentage
            budget_dict["is_over_warning"] = budget.is_over_warning
            budget_dict["is_over_alert"] = budget.is_over_alert
            budget_list.append(budget_dict)

        return {
            "budgets": budget_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    async def update_budget(self, budget_id: int, data: FinanceBudgetUpdate) -> Dict[str, Any]:
        """予算を更新"""
        budget = await FinanceBudget.get_or_none(id=budget_id)
        if not budget:
            raise ValueError("指定された予算が見つかりません")

        update_data = clean_dict(data.dict(exclude_unset=True))

        # 予算金額が変更された場合、残予算も更新
        if "budget_amount" in update_data:
            update_data["remaining_amount"] = update_data["budget_amount"] - budget.spent_amount

        await budget.update_from_dict(update_data)
        await budget.save()

        return {
            "budget": await budget.to_dict(),
            "message": "予算が正常に更新されました"
        }

    # ==================== 財務分析 ====================

    async def get_financial_analytics(self, query: FinanceAnalyticsQuery) -> Dict[str, Any]:
        """財務分析データを取得"""
        filters = Q(
            payment_date__gte=query.period_start,
            payment_date__lte=query.period_end,
            status=FinanceStatus.COMPLETED
        )

        if query.categories:
            filters &= Q(category__in=query.categories)

        # 全取引データ取得
        transactions = await FinanceTransaction.filter(filters).all()

        # 基本統計
        total_income = sum(t.amount for t in transactions if t.is_income)
        total_expense = sum(t.amount for t in transactions if t.is_expense)
        net_profit = total_income - total_expense
        profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0

        # カテゴリ別集計
        category_breakdown = {}
        for txn in transactions:
            cat = txn.category
            if cat not in category_breakdown:
                category_breakdown[cat] = {"income": 0, "expense": 0, "count": 0}

            if txn.is_income:
                category_breakdown[cat]["income"] += txn.amount
            else:
                category_breakdown[cat]["expense"] += txn.amount
            category_breakdown[cat]["count"] += 1

        # 主要支出項目（TOP10）
        expense_items = [(cat, data["expense"]) for cat, data in category_breakdown.items() if data["expense"] > 0]
        top_expenses = sorted(expense_items, key=lambda x: x[1], reverse=True)[:10]
        top_expenses = [{"category": cat, "amount": amount} for cat, amount in top_expenses]

        # 月次推移データ（簡単な実装）
        trend_data = []
        current_date = query.period_start
        while current_date <= query.period_end:
            month_start = current_date.replace(day=1)
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)

            month_transactions = [t for t in transactions if month_start <= t.payment_date <= month_end]
            month_income = sum(t.amount for t in month_transactions if t.is_income)
            month_expense = sum(t.amount for t in month_transactions if t.is_expense)

            trend_data.append({
                "period": month_start.strftime("%Y-%m"),
                "income": month_income,
                "expense": month_expense,
                "profit": month_income - month_expense
            })

            current_date = month_end + timedelta(days=1)

        # 予算分析
        budgets = await FinanceBudget.filter(
            period_start__lte=query.period_end,
            period_end__gte=query.period_start,
            is_active=True
        ).all()

        budget_analysis = {
            "total_budget": sum(b.budget_amount for b in budgets),
            "total_spent": sum(b.spent_amount for b in budgets),
            "over_budget_count": len([b for b in budgets if b.is_over_alert]),
            "warning_count": len([b for b in budgets if b.is_over_warning])
        }

        return {
            "period_start": query.period_start,
            "period_end": query.period_end,
            "summary": {
                "total_income": total_income,
                "total_expense": total_expense,
                "net_profit": net_profit,
                "profit_margin": profit_margin,
                "transaction_count": len(transactions)
            },
            "trend_data": trend_data,
            "category_breakdown": category_breakdown,
            "top_expenses": top_expenses,
            "budget_analysis": budget_analysis,
            "generated_at": datetime.now()
        }

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """財務ダッシュボード用サマリーを取得"""
        today = date.today()
        this_month_start = today.replace(day=1)

        # 今月の取引統計
        month_transactions = await FinanceTransaction.filter(
            payment_date__gte=this_month_start,
            payment_date__lte=today,
            status=FinanceStatus.COMPLETED
        ).all()

        month_income = sum(t.amount for t in month_transactions if t.is_income)
        month_expense = sum(t.amount for t in month_transactions if t.is_expense)

        # 承認待ち件数
        pending_count = await FinanceTransaction.filter(
            approval_status=FinanceApprovalStatus.PENDING
        ).count()

        # 予算アラート
        alert_budgets = await FinanceBudget.filter(is_active=True).all()
        over_budget_count = 0
        for budget in alert_budgets:
            await budget.update_spent_amount()
            if budget.is_over_alert:
                over_budget_count += 1

        # 今日実行予定の定期取引
        recurring_rules = await FinanceRecurrenceRule.filter(is_active=True).all()
        executable_rules = []
        for rule in recurring_rules:
            if await rule.should_execute_today():
                executable_rules.append(await rule.to_dict())

        return {
            "month_income": month_income,
            "month_expense": month_expense,
            "month_profit": month_income - month_expense,
            "pending_approval_count": pending_count,
            "over_budget_count": over_budget_count,
            "executable_rules_count": len(executable_rules),
            "executable_rules": executable_rules
        }

    # ==================== レポート生成 ====================

    async def generate_monthly_report(self, year: int, month: int) -> Dict[str, Any]:
        """月次財務レポートを生成（内部でcustom_reportを呼び出し）"""
        # 期間設定
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(year, month + 1, 1) - timedelta(days=1)

        # カスタムレポート要求を作成
        from app.schemas.finance import FinanceReportGenerateRequest

        request = FinanceReportGenerateRequest(
            period_start=period_start,
            period_end=period_end,
            report_type="monthly",
            include_details=False,
            include_charts=True
        )

        # カスタムレポート機能を使用
        return await self.generate_custom_report(request)

    async def generate_custom_report(self, request: FinanceReportGenerateRequest) -> Dict[str, Any]:
        """財務分析レポートを生成"""
        # 根据report_type决定实际查询的时间范围
        if request.report_type == "monthly":
            # 月次：查询整年数据
            year = request.period_start.year
            actual_start = date(year, 1, 1)
            actual_end = date(year, 12, 31)
        elif request.report_type == "quarterly":
            # 四半期：查询整年数据
            year = request.period_start.year
            actual_start = date(year, 1, 1)
            actual_end = date(year, 12, 31)
        elif request.report_type == "yearly":
            # 年次：查询指定年份范围
            actual_start = date(request.period_start.year, 1, 1)
            actual_end = date(request.period_end.year, 12, 31)
        else:
            # custom：使用传入的具体时间段
            actual_start = request.period_start
            actual_end = request.period_end

        # 期间过滤器 - 优先使用payment_date，如果为空则使用created_at
        base_filters = (
            (Q(payment_date__gte=actual_start) & Q(payment_date__lte=actual_end)) |
            (Q(payment_date__isnull=True) & Q(created_at__gte=datetime.combine(actual_start, time.min)) & Q(created_at__lte=datetime.combine(actual_end, time.max)))
        )

        # 获取实际查询范围内的所有交易
        all_transactions = await FinanceTransaction.filter(base_filters).all()

        # === 1. 基础统计 ===
        total_transactions = len(all_transactions)
        global_total_income = sum(txn.amount for txn in all_transactions if txn.transaction_type == FinanceTransactionType.INCOME)
        global_total_expense = sum(txn.amount for txn in all_transactions if txn.transaction_type == FinanceTransactionType.EXPENSE)
        net_profit = global_total_income - global_total_expense

        # === 2. 状态统计 ===
        status_stats = {}

        # 按处理状态统计
        for status in [FinanceStatus.PENDING, FinanceStatus.PROCESSING, FinanceStatus.COMPLETED, FinanceStatus.CANCELLED]:
            status_txns = [txn for txn in all_transactions if txn.status == status.value]
            status_stats[status.value] = {
                "count": len(status_txns),
                "total_amount": sum(txn.amount for txn in status_txns),
                "income_amount": sum(txn.amount for txn in status_txns if txn.transaction_type == FinanceTransactionType.INCOME),
                "expense_amount": sum(txn.amount for txn in status_txns if txn.transaction_type == FinanceTransactionType.EXPENSE),
                "status_label": status.value
            }

        # 按承认状态统计
        approval_stats = {}
        for approval_status in [FinanceApprovalStatus.PENDING, FinanceApprovalStatus.APPROVED, FinanceApprovalStatus.REJECTED, FinanceApprovalStatus.WITHDRAWN]:
            approval_txns = [txn for txn in all_transactions if txn.approval_status == approval_status.value]
            approval_stats[approval_status.value] = {
                "count": len(approval_txns),
                "total_amount": sum(txn.amount for txn in approval_txns),
                "income_amount": sum(txn.amount for txn in approval_txns if txn.transaction_type == FinanceTransactionType.INCOME),
                "expense_amount": sum(txn.amount for txn in approval_txns if txn.transaction_type == FinanceTransactionType.EXPENSE),
                "status_label": approval_status.value
            }

        # === 3. 見込み分析 ===
        # 排除完了、取消、拒绝、撤回的交易
        pending_transactions = [
            txn for txn in all_transactions
            if txn.status != FinanceStatus.COMPLETED.value
            and txn.status != FinanceStatus.CANCELLED.value
            and txn.approval_status != FinanceApprovalStatus.REJECTED.value
            and txn.approval_status != FinanceApprovalStatus.WITHDRAWN.value
        ]

        pending_total_amount = sum(txn.amount for txn in pending_transactions)
        pending_income = sum(txn.amount for txn in pending_transactions if txn.transaction_type == FinanceTransactionType.INCOME)
        pending_expense = sum(txn.amount for txn in pending_transactions if txn.transaction_type == FinanceTransactionType.EXPENSE)

        # === 4. 分类统计 ===
        category_stats = {}
        categories = set(txn.category for txn in all_transactions if txn.category)
        for category in categories:
            category_txns = [txn for txn in all_transactions if txn.category == category]
            category_stats[category] = {
                "count": len(category_txns),
                "total_amount": sum(txn.amount for txn in category_txns),
                "income_amount": sum(txn.amount for txn in category_txns if txn.transaction_type == FinanceTransactionType.INCOME),
                "expense_amount": sum(txn.amount for txn in category_txns if txn.transaction_type == FinanceTransactionType.EXPENSE),
                "avg_amount": sum(txn.amount for txn in category_txns) / len(category_txns) if category_txns else 0
            }

        # === 5. 要员统计分析（总体数据）===
        # 要员收入（请求书回款）- category="要員"
        personnel_income_txns = [txn for txn in all_transactions
                               if txn.transaction_type == FinanceTransactionType.INCOME
                               and txn.category == "要員"]
        total_personnel_income = sum(txn.amount for txn in personnel_income_txns)

        # 费用支出（ExpenseApplication相关的交易）
        expense_application_txns = [txn for txn in all_transactions
                                  if txn.transaction_type == FinanceTransactionType.EXPENSE]
        total_expense_applications = sum(txn.amount for txn in expense_application_txns)

        # 基本给总额（从合同数据计算）
        try:
            from app.models.contract import Contract
            from app.models.enums import ContractItemType, ContractStatus

            # 获取所有有效合同的基本给
            active_contracts = await Contract.filter(status=ContractStatus.ACTIVE).all()
            total_base_salary_monthly = 0.0

            for contract in active_contracts:
                calculation_items = await contract.calculation_items.filter(
                    item_type=ContractItemType.BASIC_SALARY
                ).all()
                for item in calculation_items:
                    total_base_salary_monthly += item.amount

            # 计算期间内的基本给总额
            months_in_period = ((request.period_end.year - request.period_start.year) * 12 +
                               request.period_end.month - request.period_start.month + 1)
            total_base_salary_period = total_base_salary_monthly * months_in_period

        except Exception as e:
            # 如果获取合同数据失败，使用估算值
            total_base_salary_period = 0.0

        # 总cost = 费用支出 + 基本给
        total_personnel_cost = total_expense_applications + total_base_salary_period

        # 营利 = 请求书回款 - 总cost
        total_personnel_profit = total_personnel_income - total_personnel_cost

        personnel_stats = {
            "total_income": total_personnel_income,  # 请求书回款总额
            "total_expense_applications": total_expense_applications,  # 费用申请总额
            "total_base_salary": total_base_salary_period,  # 基本给总额
            "total_cost": total_personnel_cost,  # 总成本（费用+基本给）
            "total_profit": total_personnel_profit,  # 总营利
            "profit_margin": (total_personnel_profit / total_personnel_income * 100) if total_personnel_income > 0 else 0,
            "active_personnel_count": len(active_contracts) if 'active_contracts' in locals() else 0
        }

        # === 6. 按交易类型统计 ===
        income_txns = [txn for txn in all_transactions if txn.transaction_type == FinanceTransactionType.INCOME]
        expense_txns = [txn for txn in all_transactions if txn.transaction_type == FinanceTransactionType.EXPENSE]

        # 计算全局收入支出总额
        global_total_income = sum(txn.amount for txn in income_txns)
        global_total_expense = sum(txn.amount for txn in expense_txns)

        transaction_type_stats = {
            FinanceTransactionType.INCOME.value: {
                "count": len(income_txns),
                "total_amount": global_total_income,
                "avg_amount": global_total_income / len(income_txns) if len(income_txns) > 0 else 0
            },
            FinanceTransactionType.EXPENSE.value: {
                "count": len(expense_txns),
                "total_amount": global_total_expense,
                "avg_amount": global_total_expense / len(expense_txns) if len(expense_txns) > 0 else 0
            }
        }

        # === 7. 要员趋势分析（三条线图：売り上げ、净收益、cost）===
        trend_analysis = {}

        # 根据report_type决定时间维度和周期
        periods = []

        if request.report_type == "monthly":
            # 月次 - 返回这一年所有12个月的数据
            year = request.period_start.year
            for month in range(1, 13):
                month_start = date(year, month, 1)
                if month == 12:
                    month_end = date(year, 12, 31)
                else:
                    month_end = date(year, month + 1, 1) - timedelta(days=1)
                periods.append({
                    "start": month_start,
                    "end": month_end,
                    "label": f"{year}-{month:02d}"
                })

        elif request.report_type == "quarterly":
            # 四半期 - 返回这一年所有4个季度的数据
            year = request.period_start.year
            for quarter in range(1, 5):
                q_start_month = (quarter - 1) * 3 + 1
                q_end_month = quarter * 3
                quarter_start = date(year, q_start_month, 1)
                if q_end_month == 12:
                    quarter_end = date(year, 12, 31)
                else:
                    quarter_end = date(year, q_end_month + 1, 1) - timedelta(days=1)
                periods.append({
                    "start": quarter_start,
                    "end": quarter_end,
                    "label": f"{year}Q{quarter}"
                })

        elif request.report_type == "yearly":
            # 年次 - 返回指定年份范围的完整年数据
            for year in range(request.period_start.year, request.period_end.year + 1):
                periods.append({
                    "start": date(year, 1, 1),
                    "end": date(year, 12, 31),
                    "label": str(year)
                })

        else:
            # custom - 才使用period_start和period_end的实际时间段
            periods = [{
                "start": request.period_start,
                "end": request.period_end,
                "label": f"{request.period_start}~{request.period_end}"
            }]

        # 获取要员基本给信息
        try:
            from app.models.personnel import Personnel
            from app.models.contract import Contract
            from app.models.enums import ContractItemType, ContractStatus

            all_personnel = await Personnel.all()
            total_base_salary_monthly = 0.0

            for personnel in all_personnel:
                active_contract = await Contract.filter(
                    personnel_id=personnel.id,
                    status=ContractStatus.ACTIVE
                ).first()

                if active_contract:
                    calculation_items = await active_contract.calculation_items.filter(
                        item_type=ContractItemType.BASIC_SALARY
                    ).all()
                    for item in calculation_items:
                        total_base_salary_monthly += item.amount

            # 按时间段计算要员数据
            trend_data = []
            for period_info in periods:
                period_start = period_info["start"]
                period_end = period_info["end"]

                # 获取该时间段的所有交易 - 优先使用payment_date
                period_filters = (
                    (Q(payment_date__gte=period_start) & Q(payment_date__lte=period_end)) |
                    (Q(payment_date__isnull=True) & Q(created_at__gte=datetime.combine(period_start, time.min)) & Q(created_at__lte=datetime.combine(period_end, time.max)))
                )
                period_transactions = await FinanceTransaction.filter(period_filters).all()

                # 要員収入 (请求书回款) - 売り上げ
                period_income = sum(txn.amount for txn in period_transactions
                                  if txn.transaction_type == FinanceTransactionType.INCOME
                                  and txn.category == "要員")

                # 费用申请支出
                period_expense = sum(txn.amount for txn in period_transactions
                                   if txn.transaction_type == FinanceTransactionType.EXPENSE)

                # 基本给计算（按月数计算）
                if request.report_type == "monthly":
                    period_base_salary = total_base_salary_monthly
                elif request.report_type == "quarterly":
                    period_base_salary = total_base_salary_monthly * 3
                elif request.report_type == "yearly":
                    period_base_salary = total_base_salary_monthly * 12
                else:
                    # custom 按实际天数计算
                    days = (period_info["end"] - period_info["start"]).days + 1
                    period_base_salary = total_base_salary_monthly * (days / 30)

                # cost = 费用申请 + 基本给
                period_cost = period_expense + period_base_salary

                # 净收益 = 売り上げ - cost
                period_profit = period_income - period_cost

                trend_data.append({
                    "period": period_info["label"],
                    "start_date": period_info["start"].strftime("%Y-%m-%d"),
                    "end_date": period_info["end"].strftime("%Y-%m-%d"),
                    "売り上げ": float(period_income),
                    "净收益": float(period_profit),
                    "cost": float(period_cost),
                    "transaction_count": len(period_transactions)  # 调试用：显示交易数量
                })

            # === 堆叠柱状图数据 (Stacked Column) ===
            # 按时间段分组统计收支的category分布
            stacked_column_data = []

            for period_info in periods:
                period_start = period_info["start"]
                period_end = period_info["end"]

                # 获取该时间段的所有交易 - 优先使用payment_date
                period_filters = (
                    (Q(payment_date__gte=period_start) & Q(payment_date__lte=period_end)) |
                    (Q(payment_date__isnull=True) & Q(created_at__gte=datetime.combine(period_start, time.min)) & Q(created_at__lte=datetime.combine(period_end, time.max)))
                )
                period_transactions = await FinanceTransaction.filter(period_filters).all()

                # 该时间段收益按category分组
                income_by_category = {}
                for txn in period_transactions:
                    if txn.transaction_type == FinanceTransactionType.INCOME:
                        category = txn.category or "其他"
                        if category not in income_by_category:
                            income_by_category[category] = 0
                        income_by_category[category] += txn.amount

                # 该时间段支出按category分组
                expense_by_category = {}
                for txn in period_transactions:
                    if txn.transaction_type == FinanceTransactionType.EXPENSE:
                        category = txn.category or "其他"
                        if category not in expense_by_category:
                            expense_by_category[category] = 0
                        expense_by_category[category] += txn.amount

                stacked_column_data.append({
                    "period": period_info["label"],
                    "income": {
                        "total": sum(income_by_category.values()),
                        "categories": [
                            {"name": category, "value": float(amount)}
                            for category, amount in sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)
                        ]
                    },
                    "expense": {
                        "total": sum(expense_by_category.values()),
                        "categories": [
                            {"name": category, "value": float(amount)}
                            for category, amount in sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)
                        ]
                    }
                })

            trend_analysis = {
                "type": request.report_type,
                "trend_data": trend_data,
                "chart_config": {
                    "lines": [
                        {"key": "売り上げ", "label": "売り上げ", "color": "#1890ff"},
                        {"key": "净收益", "label": "净收益", "color": "#52c41a"},
                        {"key": "cost", "label": "Cost", "color": "#ff4d4f"}
                    ]
                }
            }

        except Exception as e:
            trend_analysis = {
                "error": f"要员趋势分析失败: {str(e)}",
                "trend_data": [],
                "chart_config": {}
            }

        # === 8. 组织报表数据 ===
        period_days = (request.period_end - request.period_start).days + 1

        report_data = {
            "report_info": {
                "period_start": request.period_start.strftime("%Y-%m-%d"),
                "period_end": request.period_end.strftime("%Y-%m-%d"),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_transactions": total_transactions,
                "period_days": period_days
            },
            "financial_summary": {
                "total_income": global_total_income,
                "total_expense": global_total_expense,
                "net_profit": net_profit,
                "profit_margin": (net_profit / global_total_income * 100) if global_total_income > 0 else 0
            },
            "status_analysis": {
                "by_status": status_stats,
                "by_approval": approval_stats
            },
            "pending_analysis": {
                "total_count": len(pending_transactions),
                "total_amount": pending_total_amount,
                "income_amount": pending_income,
                "expense_amount": pending_expense,
                "description": "見込み分析（完了・取消・拒绝・撤回を除く）"
            },
            "category_analysis": category_stats,
            "personnel_analysis": personnel_stats,
            "transaction_type_analysis": transaction_type_stats,
            "trend_analysis": trend_analysis,
            "stacked_column_analysis": stacked_column_data  # 新增：堆叠柱状图数据
        }

        # === 9. 详细交易数据（可选）===
        transaction_details = []
        if request.include_details:
            for txn in all_transactions:
                transaction_details.append(await txn.to_dict())

        return {
            "report": report_data,
            "analytics": report_data,  # API层需要这个字段
            "transaction_details": transaction_details if request.include_details else None,
            "message": f"{request.period_start}～{request.period_end}期間の財務分析レポートが生成されました"
        }


    # ==================== 費用申請管理 ====================

    async def create_expense_application(self, data: ExpenseApplicationCreate, token: str = None) -> Dict[str, Any]:
        """費用申請を作成"""
        # 現在のユーザー情報を取得
        user_id = CTX_USER_ID.get()
        user_info = CTX_USER_INFO.get()

        application_data = data.dict()

        # ユーザー情報を自動設定
        application_data["applicant_id"] = user_id
        application_data["applicant_name"] = user_info.get("name", "")
        application_data["department"] = user_info.get("department", "")

        # 申請番号を自動生成
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        application_data["application_number"] = f"EXP{timestamp}{user_id:04d}"

        application = await ExpenseApplication.create(**application_data)

        # 工作流を自動開始（tokenが提供された場合）
        if token:
            try:
                process_instance_id = await process_client.run_process(
                    process_key=EXPENSE_APPROVAL_PROCESS_KEY,
                    business_key=str(application.id),
                    variables=json.dumps({
                        "applicant_id": user_id,
                        "applicant_name": user_info.get("name", ""),
                        "amount": application.amount,
                        "application_type": application.application_type
                    }),
                    token=token
                )
                if process_instance_id:
                    application.process_instance_id = process_instance_id
                    await application.save()
            except Exception as e:
                # 工作流启动失败不影响申请创建，只记录日志
                print(f"工作流启动失败: {e}")

        return {
            "application": await application.to_dict(),
            "message": "費用申請が正常に作成されました"
        }

    async def get_expense_application_list(self, query: ExpenseApplicationListQuery, token: str = None) -> Dict[str, Any]:
        """費用申請一覧を取得"""
        filters = Q()

        # フィルタ条件構築
        if query.application_type:
            filters &= Q(application_type=query.application_type)
        if query.status:
            filters &= Q(status=query.status)
        if query.applicant_id:
            filters &= Q(applicant_id=query.applicant_id)
        if query.priority:
            filters &= Q(priority=query.priority)
        if query.application_date_from:
            filters &= Q(application_date__gte=query.application_date_from)
        if query.application_date_to:
            filters &= Q(application_date__lte=query.application_date_to)
        if query.expense_date_from:
            filters &= Q(expense_date_from__gte=query.expense_date_from)
        if query.expense_date_to:
            filters &= Q(expense_date_to__lte=query.expense_date_to)
        if query.amount_min is not None:
            filters &= Q(amount__gte=query.amount_min)
        if query.amount_max is not None:
            filters &= Q(amount__lte=query.amount_max)
        if query.case_id:
            filters &= Q(case_id=query.case_id)
        if query.contract_id:
            filters &= Q(contract_id=query.contract_id)
        if query.personnel_id:
            filters &= Q(personnel_id=query.personnel_id)
        if query.search_keyword:
            filters &= Q(
                Q(title__icontains=query.search_keyword) |
                Q(description__icontains=query.search_keyword) |
                Q(applicant_name__icontains=query.search_keyword)
            )

        # 総数取得
        total = await ExpenseApplication.filter(filters).count()

        # データ取得
        applications = await ExpenseApplication.filter(filters).select_related(
            "case"
        ).order_by("-created_at").offset(
            (query.page - 1) * query.page_size
        ).limit(query.page_size).all()

        # 获取所有申请者用户信息
        applicant_ids = [app.applicant_id for app in applications if app.applicant_id]
        user_info_map = {}
        if applicant_ids and token:
            try:
                user_info_map = await user_client.get_users_by_ids(applicant_ids, token)
            except Exception as e:
                print(f"获取用户信息失败: {e}")

        application_list = []
        for app in applications:
            app_dict = await app.to_dict()
            # プロパティ値を追加
            app_dict["is_approved"] = app.is_approved
            app_dict["is_paid"] = app.is_paid
            app_dict["can_be_cancelled"] = app.can_be_cancelled

            # 添加用户详细信息
            if app.applicant_id in user_info_map:
                user_info = user_info_map[app.applicant_id]
                app_dict["applicant_detail"] = {
                    "user_id": user_info.get("id"),
                    "username": user_info.get("username"),
                    "nickname": user_info.get("nickname"),
                    "email": user_info.get("email"),
                    "mobile": user_info.get("mobile"),
                    "avatar": user_info.get("avatar")
                }
            application_list.append(app_dict)

        # 状态统计（見込み）- 排除被拒绝的申请
        base_filters = Q()
        # 复制原始过滤条件，但排除status过滤
        if query.application_type:
            base_filters &= Q(application_type=query.application_type)
        if query.applicant_id:
            base_filters &= Q(applicant_id=query.applicant_id)
        if query.priority:
            base_filters &= Q(priority=query.priority)
        if query.application_date_from:
            base_filters &= Q(application_date__gte=query.application_date_from)
        if query.application_date_to:
            base_filters &= Q(application_date__lte=query.application_date_to)
        if query.expense_date_from:
            base_filters &= Q(expense_date_from__gte=query.expense_date_from)
        if query.expense_date_to:
            base_filters &= Q(expense_date_to__lte=query.expense_date_to)
        if query.amount_min is not None:
            base_filters &= Q(amount__gte=query.amount_min)
        if query.amount_max is not None:
            base_filters &= Q(amount__lte=query.amount_max)
        if query.case_id:
            base_filters &= Q(case_id=query.case_id)
        if query.contract_id:
            base_filters &= Q(contract_id=query.contract_id)
        if query.personnel_id:
            base_filters &= Q(personnel_id=query.personnel_id)
        if query.search_keyword:
            base_filters &= Q(
                Q(title__icontains=query.search_keyword) |
                Q(description__icontains=query.search_keyword) |
                Q(applicant_name__icontains=query.search_keyword)
            )

        # 各状态统计
        # 草稿状态
        draft_count = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.DRAFT)).count()
        draft_applications = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.DRAFT)).all()
        draft_amount = sum(app.amount for app in draft_applications)

        # 申请中状态
        submitted_count = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.SUBMITTED)).count()
        submitted_applications = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.SUBMITTED)).all()
        submitted_amount = sum(app.amount for app in submitted_applications)

        # 审查中状态
        under_review_count = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.UNDER_REVIEW)).count()
        under_review_applications = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.UNDER_REVIEW)).all()
        under_review_amount = sum(app.amount for app in under_review_applications)

        # 承认済み状态
        approved_count = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.APPROVED)).count()
        approved_applications = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.APPROVED)).all()
        approved_amount = sum(app.amount for app in approved_applications)

        # 支払済み状态
        paid_count = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.PAID)).count()
        paid_applications = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.PAID)).all()
        paid_amount = sum(app.amount for app in paid_applications)

        # キャンセル状态
        cancelled_count = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.CANCELLED)).count()
        cancelled_applications = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.CANCELLED)).all()
        cancelled_amount = sum(app.amount for app in cancelled_applications)

        # 被拒绝状态（单独统计，不计入見込み）
        rejected_count = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.REJECTED)).count()
        rejected_applications = await ExpenseApplication.filter(base_filters & Q(status=ApplicationStatus.REJECTED)).all()
        rejected_amount = sum(app.amount for app in rejected_applications)

        # 見込み总计（排除被拒绝的）
        pending_total_count = draft_count + submitted_count + under_review_count + approved_count
        pending_total_amount = draft_amount + submitted_amount + under_review_amount + approved_amount

        status_stats = {
            "draft": {
                "count": draft_count,
                "total_amount": draft_amount,
                "status_label": "草稿"
            },
            "submitted": {
                "count": submitted_count,
                "total_amount": submitted_amount,
                "status_label": "申請中"
            },
            "under_review": {
                "count": under_review_count,
                "total_amount": under_review_amount,
                "status_label": "審査中"
            },
            "approved": {
                "count": approved_count,
                "total_amount": approved_amount,
                "status_label": "承認済み"
            },
            "paid": {
                "count": paid_count,
                "total_amount": paid_amount,
                "status_label": "支払済み"
            },
            "cancelled": {
                "count": cancelled_count,
                "total_amount": cancelled_amount,
                "status_label": "キャンセル"
            },
            "rejected": {
                "count": rejected_count,
                "total_amount": rejected_amount,
                "status_label": "却下"
            },
            "pending_total": {
                "count": pending_total_count,
                "total_amount": pending_total_amount,
                "description": "見込み総額（却下を除く）"
            }
        }

        return {
            "applications": application_list,
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "total_pages": (total + query.page_size - 1) // query.page_size,
            "status_statistics": status_stats
        }

    async def get_expense_application_detail(self, application_id: int, token: str = None) -> Dict[str, Any]:
        """費用申請詳細を取得"""
        application = await ExpenseApplication.filter(id=application_id).select_related(
            "case"
        ).first()

        if not application:
            raise ValueError("指定された申請が見つかりません")

        # 承認履歴取得
        approval_history = await ExpenseApprovalHistory.filter(
            application_id=application_id
        ).order_by("-action_date").all()

        # 获取申请者用户信息
        applicant_detail = {}
        if application.applicant_id and token:
            try:
                user_info = await user_client.get_user_by_id(application.applicant_id, token)
                applicant_detail = {
                    "user_id": user_info.get("id"),
                    "username": user_info.get("username"),
                    "nickname": user_info.get("nickname"),
                    "email": user_info.get("email"),
                    "mobile": user_info.get("mobile"),
                    "avatar": user_info.get("avatar")
                }
            except Exception as e:
                print(f"获取用户信息失败: {e}")

        application_dict = await application.to_dict()
        if applicant_detail:
            application_dict["applicant_detail"] = applicant_detail

        return {
            "application": application_dict,
            "approval_history": [await hist.to_dict() for hist in approval_history],
            "is_approved": application.is_approved,
            "is_paid": application.is_paid,
            "can_be_cancelled": application.can_be_cancelled
        }

    async def get_expense_application_by_process(self, process_instance_id: str, token: str = None) -> Dict[str, Any]:
        """プロセスインスタンスIDによる費用申請詳細を取得"""
        application = await ExpenseApplication.filter(
            process_instance_id=process_instance_id
        ).select_related("case").first()

        if not application:
            raise ValueError("指定されたプロセスに関連する費用申請が見つかりません")

        # 承認履歴取得
        approval_history = await ExpenseApprovalHistory.filter(
            application_id=application.id
        ).order_by("-action_date").all()

        # 获取申请者用户信息
        applicant_detail = {}
        if application.applicant_id and token:
            try:
                user_info = await user_client.get_user_by_id(application.applicant_id, token)
                applicant_detail = {
                    "user_id": user_info.get("id"),
                    "username": user_info.get("username"),
                    "nickname": user_info.get("nickname"),
                    "email": user_info.get("email"),
                    "mobile": user_info.get("mobile"),
                    "avatar": user_info.get("avatar")
                }
            except Exception as e:
                print(f"获取用户信息失败: {e}")

        application_dict = await application.to_dict()
        if applicant_detail:
            application_dict["applicant_detail"] = applicant_detail

        return {
            "application": application_dict,
            "approval_history": [await hist.to_dict() for hist in approval_history],
            "is_approved": application.is_approved,
            "is_paid": application.is_paid,
            "can_be_cancelled": application.can_be_cancelled
        }

    async def update_expense_application(self, application_id: int, data: ExpenseApplicationUpdate) -> Dict[str, Any]:
        """費用申請を更新"""
        application = await ExpenseApplication.get_or_none(id=application_id)
        if not application:
            raise ValueError("指定された申請が見つかりません")

        # 草稿状態のみ更新可能
        if application.status != ApplicationStatus.DRAFT:
            raise ValueError("草稿状態の申請のみ更新可能です")

        update_data = clean_dict(data.dict(exclude_unset=True))
        await application.update_from_dict(update_data)
        await application.save()

        return {
            "application": await application.to_dict(),
            "message": "費用申請が正常に更新されました"
        }

    async def submit_expense_application(self, application_id: int, notes: str = None) -> Dict[str, Any]:
        """費用申請を提出"""
        user_id, user_name = self._get_current_user_info()

        application = await ExpenseApplication.get_or_none(id=application_id)
        if not application:
            raise ValueError("指定された申請が見つかりません")

        await application.submit_application(user_name)

        return {
            "application": await application.to_dict(),
            "message": "費用申請が正常に提出されました"
        }

    async def approve_expense_application(self, application_id: int, action: str, notes: str = None) -> Dict[str, Any]:
        """費用申請を承認/拒否"""
        user_id, user_name = self._get_current_user_info()

        application = await ExpenseApplication.get_or_none(id=application_id)
        if not application:
            raise ValueError("指定された申請が見つかりません")

        if action == "approve":
            await application.approve_application(user_name, notes)
            message = "費用申請が承認されました"
        elif action == "reject":
            await application.reject_application(user_name, notes or "理由未記載")
            message = "費用申請が却下されました"
        elif action == "cancel":
            if application.can_be_cancelled:
                application.status = ApplicationStatus.CANCELLED
                await application.save()
                message = "費用申請がキャンセルされました"
            else:
                raise ValueError("この申請はキャンセルできません")
        else:
            raise ValueError("不正なアクション")

        return {
            "application": await application.to_dict(),
            "message": message
        }

    async def mark_expense_as_paid(self, application_id: int, payment_date: date = None) -> Dict[str, Any]:
        """費用申請を支払完了マーク"""
        application = await ExpenseApplication.get_or_none(id=application_id)
        if not application:
            raise ValueError("指定された申請が見つかりません")

        await application.mark_as_paid(payment_date)

        return {
            "application": await application.to_dict(),
            "message": "費用申請が支払完了としてマークされました"
        }

    async def get_expense_application_stats(self,
                                          period_start: date = None,
                                          period_end: date = None,
                                          applicant_id: int = None) -> Dict[str, Any]:
        """費用申請統計を取得"""
        if not period_start:
            period_start = date.today().replace(day=1)
        if not period_end:
            period_end = date.today()

        filters = Q(
            application_date__gte=period_start,
            application_date__lte=period_end
        )

        if applicant_id:
            filters &= Q(applicant_id=applicant_id)

        # 全申請データ取得
        applications = await ExpenseApplication.filter(filters).all()

        # 基本統計
        total_applications = len(applications)
        pending_applications = len([a for a in applications if a.status in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]])
        approved_applications = len([a for a in applications if a.status == ApplicationStatus.APPROVED])
        rejected_applications = len([a for a in applications if a.status == ApplicationStatus.REJECTED])

        total_amount = sum(a.amount for a in applications)
        approved_amount = sum(a.amount for a in applications if a.status == ApplicationStatus.APPROVED)
        paid_amount = sum(a.amount for a in applications if a.status == ApplicationStatus.PAID)

        # 種別別統計
        by_type = {}
        for app in applications:
            app_type = app.application_type
            if app_type not in by_type:
                by_type[app_type] = {"count": 0, "amount": 0.0}
            by_type[app_type]["count"] += 1
            by_type[app_type]["amount"] += app.amount

        # ステータス別統計
        by_status = {}
        for app in applications:
            status = app.status
            if status not in by_status:
                by_status[status] = {"count": 0, "amount": 0.0}
            by_status[status]["count"] += 1
            by_status[status]["amount"] += app.amount

        # 月次推移（簡単な実装）
        monthly_trend = []
        current_date = period_start
        while current_date <= period_end:
            month_start = current_date.replace(day=1)
            if current_date.month == 12:
                month_end = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)

            month_applications = [a for a in applications if month_start <= a.application_date <= month_end]
            monthly_trend.append({
                "period": month_start.strftime("%Y-%m"),
                "count": len(month_applications),
                "amount": sum(a.amount for a in month_applications)
            })

            current_date = month_end + timedelta(days=1)

        return {
            "total_applications": total_applications,
            "pending_applications": pending_applications,
            "approved_applications": approved_applications,
            "rejected_applications": rejected_applications,
            "total_amount": total_amount,
            "approved_amount": approved_amount,
            "paid_amount": paid_amount,
            "by_type": by_type,
            "by_status": by_status,
            "monthly_trend": monthly_trend
        }