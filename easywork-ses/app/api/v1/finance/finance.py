import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, Body, Header

from app.controllers.finance import FinanceController
from app.core.process_client import process_client
from app.models.finance import ExpenseApplication
from app.schemas import Fail, Success, SuccessExtra
from app.schemas.finance import (
    FinanceTransactionCreate,
    FinanceTransactionUpdate,
    FinanceTransactionListQuery,
    FinanceTransactionApproval,
    FinanceRecurrenceRuleCreate,
    FinanceRecurrenceRuleUpdate,
    FinanceBudgetCreate,
    FinanceBudgetUpdate,
    FinanceAnalyticsQuery,
    ExpenseApplicationCreate,
    ExpenseApplicationUpdate,
    ExpenseApplicationListQuery,
    ExpenseApplicationApproval,
    ExpenseApplicationSubmit,
    ExpenseApplicationPayment,
)

router = APIRouter()
finance_controller = FinanceController()

# 费用申请工作流KEY
EXPENSE_APPROVAL_PROCESS_KEY = "TOB_COMMUTING"


# ==================== 財務取引管理 ====================

@router.post("/transactions", summary="財務取引作成")
async def create_transaction(data: FinanceTransactionCreate):
    try:
        result = await finance_controller.create_transaction(data)
        return Success(data=result["transaction"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/transactions", summary="財務取引一覧取得")
async def get_transaction_list(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    transaction_type: Optional[str] = Query(None, description="取引種別"),
    category: Optional[str] = Query(None, description="カテゴリ"),
    status: Optional[str] = Query(None, description="ステータス"),
    approval_status: Optional[str] = Query(None, description="承認ステータス"),
    payment_date_from: Optional[date] = Query(None, description="支払日From"),
    payment_date_to: Optional[date] = Query(None, description="支払日To"),
    amount_min: Optional[float] = Query(None, description="金額下限"),
    amount_max: Optional[float] = Query(None, description="金額上限"),
    counterpart: Optional[str] = Query(None, description="取引先"),
    case_id: Optional[int] = Query(None, description="案件ID"),
    contract_id: Optional[int] = Query(None, description="契約ID"),
    personnel_id: Optional[int] = Query(None, description="人材ID"),
    search_keyword: Optional[str] = Query(None, description="検索キーワード"),
):
    try:
        query = FinanceTransactionListQuery(
            page=page,
            page_size=page_size,
            transaction_type=transaction_type,
            category=category,
            status=status,
            approval_status=approval_status,
            payment_date_from=payment_date_from,
            payment_date_to=payment_date_to,
            amount_min=amount_min,
            amount_max=amount_max,
            counterpart=counterpart,
            case_id=case_id,
            contract_id=contract_id,
            personnel_id=personnel_id,
            search_keyword=search_keyword,
        )

        result = await finance_controller.get_transaction_list(query)

        return SuccessExtra(
            data=result["transactions"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/transactions/{transaction_id}", summary="財務取引詳細取得")
async def get_transaction_detail(transaction_id: int):
    try:
        result = await finance_controller.get_transaction_detail(transaction_id)
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/transactions/{transaction_id}", summary="財務取引更新")
async def update_transaction(transaction_id: int, data: FinanceTransactionUpdate):
    try:
        result = await finance_controller.update_transaction(transaction_id, data)
        return Success(data=result["transaction"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/transactions/{transaction_id}/approval", summary="財務取引承認/拒否")
async def approve_transaction(transaction_id: int, approval_data: FinanceTransactionApproval):
    try:
        result = await finance_controller.approve_transaction(
            transaction_id,
            approval_data.action,
            approval_data.notes
        )
        return Success(data=result["transaction"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/transactions/{transaction_id}", summary="財務取引削除")
async def delete_transaction(transaction_id: int):
    try:
        result = await finance_controller.delete_transaction(transaction_id)
        return Success(msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


# ==================== 定期取引ルール管理 ====================

@router.post("/recurrence-rules", summary="定期取引ルール作成")
async def create_recurrence_rule(data: FinanceRecurrenceRuleCreate):
    try:
        result = await finance_controller.create_recurrence_rule(data)
        return Success(data=result["rule"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/recurrence-rules", summary="定期取引ルール一覧取得")
async def get_recurrence_rule_list(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
):
    try:
        result = await finance_controller.get_recurrence_rule_list(page, page_size)
        return SuccessExtra(
            data=result["rules"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/recurrence-rules/{rule_id}", summary="定期取引ルール更新")
async def update_recurrence_rule(rule_id: int, data: FinanceRecurrenceRuleUpdate):
    try:
        result = await finance_controller.update_recurrence_rule(rule_id, data)
        return Success(data=result["rule"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/recurrence-rules/execute", summary="定期取引ルール実行")
async def execute_recurrence_rules():
    try:
        result = await finance_controller.execute_recurrence_rules()
        return Success(
            data={
                "executed_count": result["executed_count"],
                "created_transactions": result["created_transactions"]
            },
            msg=result["message"]
        )
    except Exception as e:
        return Fail(msg=str(e))


# ==================== 予算管理 ====================

@router.post("/budgets", summary="予算作成")
async def create_budget(data: FinanceBudgetCreate):
    try:
        result = await finance_controller.create_budget(data)
        return Success(data=result["budget"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/budgets", summary="予算一覧取得")
async def get_budget_list(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    category: Optional[str] = Query(None, description="カテゴリ"),
):
    try:
        result = await finance_controller.get_budget_list(page, page_size, category)
        return SuccessExtra(
            data=result["budgets"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/budgets/{budget_id}", summary="予算更新")
async def update_budget(budget_id: int, data: FinanceBudgetUpdate):
    try:
        result = await finance_controller.update_budget(budget_id, data)
        return Success(data=result["budget"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


# ==================== 財務分析・レポート ====================

@router.post("/analytics", summary="財務分析データ取得")
async def get_financial_analytics(query: FinanceAnalyticsQuery):
    try:
        result = await finance_controller.get_financial_analytics(query)
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/dashboard/summary", summary="財務ダッシュボード サマリー取得")
async def get_dashboard_summary():
    try:
        result = await finance_controller.get_dashboard_summary()
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/reports/monthly", summary="月次財務レポート生成")
async def generate_monthly_report(
    year: int = Body(..., description="年"),
    month: int = Body(..., ge=1, le=12, description="月"),
):
    try:
        result = await finance_controller.generate_monthly_report(year, month)
        return Success(
            data={
                "report": result["report"],
                "analytics": result["analytics"]
            },
            msg=result["message"]
        )
    except Exception as e:
        return Fail(msg=str(e))



# ==================== 費用申請管理 ====================

@router.post("/expense-applications", summary="費用申請作成")
async def create_expense_application(
    data: ExpenseApplicationCreate,
    authorization: Optional[str] = Header(None, description="token验证")
):
    try:
        result = await finance_controller.create_expense_application(data, token=authorization)
        return Success(data=result["application"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/expense-applications", summary="費用申請一覧取得")
async def get_expense_application_list(
    page: int = Query(1, ge=1, description="ページ番号"),
    page_size: int = Query(20, ge=1, le=100, description="ページサイズ"),
    application_type: Optional[str] = Query(None, description="申請種別"),
    status: Optional[str] = Query(None, description="ステータス"),
    applicant_id: Optional[int] = Query(None, description="申請者ID"),
    priority: Optional[str] = Query(None, description="優先度"),
    application_date_from: Optional[date] = Query(None, description="申請日From"),
    application_date_to: Optional[date] = Query(None, description="申請日To"),
    expense_date_from: Optional[date] = Query(None, description="費用発生日From"),
    expense_date_to: Optional[date] = Query(None, description="費用発生日To"),
    amount_min: Optional[float] = Query(None, description="金額下限"),
    amount_max: Optional[float] = Query(None, description="金額上限"),
    search_keyword: Optional[str] = Query(None, description="検索キーワード"),
    authorization: Optional[str] = Header(None, description="token验证")
):
    try:
        query = ExpenseApplicationListQuery(
            page=page,
            page_size=page_size,
            application_type=application_type,
            status=status,
            applicant_id=applicant_id,
            priority=priority,
            application_date_from=application_date_from,
            application_date_to=application_date_to,
            expense_date_from=expense_date_from,
            expense_date_to=expense_date_to,
            amount_min=amount_min,
            amount_max=amount_max,
            search_keyword=search_keyword,
        )

        result = await finance_controller.get_expense_application_list(query, token=authorization)

        return SuccessExtra(
            data=result["applications"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/expense-applications/{application_id}", summary="費用申請詳細取得")
async def get_expense_application_detail(
    application_id: int,
    authorization: Optional[str] = Header(None, description="token验证")
):
    try:
        result = await finance_controller.get_expense_application_detail(application_id, token=authorization)
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/expense-applications/by-process/{process_instance_id}", summary="プロセスIDによる費用申請詳細取得")
async def get_expense_application_by_process(
    process_instance_id: str,
    authorization: Optional[str] = Header(None, description="token验证")
):
    try:
        result = await finance_controller.get_expense_application_by_process(process_instance_id, token=authorization)
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/expense-applications/{application_id}", summary="費用申請更新")
async def update_expense_application(application_id: int, data: ExpenseApplicationUpdate):
    try:
        result = await finance_controller.update_expense_application(application_id, data)
        return Success(data=result["application"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/expense-applications/{application_id}/submit", summary="費用申請提出")
async def submit_expense_application(application_id: int, submit_data: ExpenseApplicationSubmit):
    try:
        result = await finance_controller.submit_expense_application(application_id, submit_data.notes)
        return Success(data=result["application"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/expense-applications/{application_id}/approval", summary="費用申請承認/拒否")
async def approve_expense_application(application_id: int, approval_data: ExpenseApplicationApproval):
    try:
        result = await finance_controller.approve_expense_application(
            application_id,
            approval_data.action,
            approval_data.notes
        )
        return Success(data=result["application"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/expense-applications/{application_id}/mark-paid", summary="費用申請支払完了マーク")
async def mark_expense_as_paid(application_id: int, payment_data: ExpenseApplicationPayment):
    try:
        result = await finance_controller.mark_expense_as_paid(application_id, payment_data.payment_date)
        return Success(data=result["application"], msg=result["message"])
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/expense-applications/stats/summary", summary="費用申請統計取得")
async def get_expense_application_stats(
    period_start: Optional[date] = Query(None, description="期間開始日"),
    period_end: Optional[date] = Query(None, description="期間終了日"),
    applicant_id: Optional[int] = Query(None, description="申請者ID"),
):
    try:
        result = await finance_controller.get_expense_application_stats(
            period_start, period_end, applicant_id
        )
        return Success(data=result)
    except Exception as e:
        return Fail(msg=str(e))

# ==================== ワークフロー管理 ====================

@router.post("/expense-applications/{application_id}/start-workflow", summary="費用申請ワークフロー開始")
async def start_expense_workflow(
    application_id: int,
    authorization: str = Header(..., description="token验证")
):
    """費用申請のワークフローを手動で開始"""
    try:

        # 申請が存在するかチェック
        application = await ExpenseApplication.get_or_none(id=application_id)
        if not application:
            return Fail(msg="費用申請が見つかりません")

        # 既にワークフロー実行中なら重複開始を防ぐ
        if application.process_instance_id:
            return Fail(msg="ワークフローは既に開始されています")

        # ワークフロー開始
        process_instance_id = await process_client.run_process(
            process_key=EXPENSE_APPROVAL_PROCESS_KEY,
            business_key=str(application.id),
            variables=json.dumps({
                "applicant_id": application.applicant_id,
                "applicant_name": application.applicant_name,
                "amount": application.amount,
                "application_type": application.application_type,
                "application_number": application.application_number
            }),
            token=authorization
        )

        if process_instance_id:
            application.process_instance_id = process_instance_id
            await application.save()
            return Success(
                data={"process_instance_id": process_instance_id},
                msg="ワークフローが正常に開始されました"
            )
        else:
            return Fail(msg="ワークフローの開始に失敗しました")

    except Exception as e:
        return Fail(msg=str(e))