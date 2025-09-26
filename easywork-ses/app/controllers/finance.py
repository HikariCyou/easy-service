from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.core.ctx import CTX_USER_ID, CTX_USER_INFO
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

        return {
            "transactions": transaction_list,
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "total_pages": (total + query.page_size - 1) // query.page_size
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
        """月次財務レポートを生成"""
        user_id, user_name = self._get_current_user_info()

        # 期間設定
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            period_end = date(year, month + 1, 1) - timedelta(days=1)

        # 分析データ取得
        analytics_query = FinanceAnalyticsQuery(
            period_start=period_start,
            period_end=period_end
        )
        analytics_data = await self.get_financial_analytics(analytics_query)

        # レポート作成
        report = await FinanceReport.create(
            report_name=f"{year}年{month}月度財務レポート",
            report_type="monthly",
            period_start=period_start,
            period_end=period_end,
            total_income=analytics_data["summary"]["total_income"],
            total_expense=analytics_data["summary"]["total_expense"],
            net_profit=analytics_data["summary"]["net_profit"],
            profit_margin=analytics_data["summary"]["profit_margin"],
            category_breakdown=analytics_data["category_breakdown"],
            monthly_trend=analytics_data["trend_data"],
            personnel_cost=analytics_data["category_breakdown"].get(FinanceCategory.PERSONNEL_COST, {}).get("expense", 0),
            generated_by=user_name,
            is_auto_generated=False
        )

        return {
            "report": await report.to_dict(),
            "analytics": analytics_data,
            "message": f"{year}年{month}月度の財務レポートが生成されました"
        }

    # ==================== 費用申請管理 ====================

    async def create_expense_application(self, data: ExpenseApplicationCreate) -> Dict[str, Any]:
        """費用申請を作成"""
        application_data = data.dict()

        # 申請番号は後でsignalで自動生成される
        application_data.pop("application_number", None)

        application = await ExpenseApplication.create(**application_data)

        return {
            "application": await application.to_dict(),
            "message": "費用申請が正常に作成されました"
        }

    async def get_expense_application_list(self, query: ExpenseApplicationListQuery) -> Dict[str, Any]:
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
            "case", "contract", "personnel"
        ).order_by("-created_at").offset(
            (query.page - 1) * query.page_size
        ).limit(query.page_size).all()

        application_list = []
        for app in applications:
            app_dict = await app.to_dict()
            # プロパティ値を追加
            app_dict["is_approved"] = app.is_approved
            app_dict["is_paid"] = app.is_paid
            app_dict["can_be_cancelled"] = app.can_be_cancelled
            application_list.append(app_dict)

        return {
            "applications": application_list,
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
            "total_pages": (total + query.page_size - 1) // query.page_size
        }

    async def get_expense_application_detail(self, application_id: int) -> Dict[str, Any]:
        """費用申請詳細を取得"""
        application = await ExpenseApplication.filter(id=application_id).select_related(
            "case", "contract", "personnel"
        ).first()

        if not application:
            raise ValueError("指定された申請が見つかりません")

        # 承認履歴取得
        approval_history = await ExpenseApprovalHistory.filter(
            application_id=application_id
        ).order_by("-action_date").all()

        return {
            "application": await application.to_dict(),
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