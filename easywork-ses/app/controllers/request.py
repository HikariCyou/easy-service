import os
import tempfile
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from tortoise.queryset import QuerySet
from tortoise.transactions import in_transaction
from weasyprint import HTML

from app.core.user_client import sso_client
from app.models.case import Case
from app.models.client import ClientCompany
from app.models.contract import Contract
from app.models.enums import ContractItemType, ContractStatus, RequestStatus
from app.models.personnel import Personnel
from app.models.request import Request, RequestItem
from app.schemas.request import (
    RequestCreate,
    RequestDetail,
    RequestGenerationRequest,
    RequestListItem,
    RequestPaymentUpdate,
    RequestSendRequest,
    RequestUpdate,
)
from app.settings import settings
from app.utils.s3_client import s3_client


class RequestController:
    """請求書コントローラー"""

    @staticmethod
    async def create_request(request_data: RequestCreate) -> Request:
        """請求書作成（複数要員対応）"""

        # 重複チェック
        existing = await Request.filter(
            client_company_id=request_data.client_company_id,
            year_month=request_data.year_month
        ).first()

        if existing:
            raise ValueError(f"対象Client会社の{request_data.year_month}の請求書は既に存在します")

        # Client会社検証
        client_company = await ClientCompany.get_or_none(id=request_data.client_company_id)
        if not client_company:
            raise ValueError("指定されたClient会社が見つかりません")

        # 明細項目の検証
        if not request_data.items:
            raise ValueError("請求書明細項目は必須です")

        validated_items = []
        total_amount = 0

        for item_data in request_data.items:
            # 要員検証
            personnel = await Personnel.get_or_none(id=item_data.personnel_id)
            if not personnel:
                raise ValueError(f"要員ID {item_data.personnel_id} が見つかりません")

            # 案件検証
            case = await Case.get_or_none(id=item_data.case_id)
            if not case:
                raise ValueError(f"案件ID {item_data.case_id} が見つかりません")

            # 案件がClient会社に属するかチェック
            if case.client_company_id != request_data.client_company_id:
                raise ValueError(f"案件ID {item_data.case_id} は指定されたClient会社に属していません")

            # 契約検証
            contract = await Contract.get_or_none(id=item_data.contract_id)
            if not contract:
                raise ValueError(f"契約ID {item_data.contract_id} が見つかりません")

            # 契約が有効かチェック
            if contract.status != ContractStatus.ACTIVE:
                raise ValueError(f"契約ID {item_data.contract_id} は有効ではありません")

            # 契約と案件・要員の関連チェック
            if contract.case_id != item_data.case_id:
                raise ValueError(f"契約ID {item_data.contract_id} は案件ID {item_data.case_id} に関連していません")

            if contract.personnel_id != item_data.personnel_id:
                raise ValueError(f"契約ID {item_data.contract_id} は要員ID {item_data.personnel_id} に関連していません")

            validated_items.append({
                'item_data': item_data,
                'personnel': personnel,
                'case': case,
                'contract': contract
            })
            total_amount += float(item_data.item_amount)

        # 請求番号生成
        request_number = await RequestController._generate_request_number(request_data.year_month)

        # 税抜き金額と税込み金額計算
        tax_excluded_amount = total_amount
        tax_amount = tax_excluded_amount * float(request_data.tax_rate) / 100
        request_amount = tax_excluded_amount + tax_amount

        # 請求書作成
        async with in_transaction():
            request = await Request.create(
                request_number=request_number,
                year_month=request_data.year_month,
                client_company_id=request_data.client_company_id,
                request_amount=request_amount,
                calculation_amount=request_amount,  # 初期値として税込み金額をセット
                tax_excluded_amount=tax_excluded_amount,
                tax_rate=request_data.tax_rate,
                payment_due_date=request_data.payment_due_date,
                remark=request_data.remark,
            )

            # 明細項目作成
            for item_info in validated_items:
                item_data = item_info['item_data']
                await RequestItem.create(
                    request_id=request.id,
                    personnel_id=item_data.personnel_id,
                    case_id=item_data.case_id,
                    contract_id=item_data.contract_id,
                    item_amount=item_data.item_amount,
                    work_hours=item_data.work_hours or 160.0,
                    unit_price=item_data.unit_price,
                    item_remark=item_data.item_remark,
                )

        return request

    @staticmethod
    async def _generate_request_number(year_month: str) -> str:
        """請求番号生成"""
        # 年月から番号生成（例：2024-01 → REQ202401-001）
        year_month_str = year_month.replace("-", "")

        # 同一月の最大番号を取得
        last_request = await Request.filter(year_month=year_month).order_by("-request_number").first()

        if last_request and last_request.request_number.startswith(f"REQ{year_month_str}"):
            # 既存の番号から連番を取得
            try:
                last_seq = int(last_request.request_number.split("-")[-1])
                next_seq = last_seq + 1
            except (IndexError, ValueError):
                next_seq = 1
        else:
            next_seq = 1

        return f"REQ{year_month_str}-{next_seq:03d}"

    @staticmethod
    async def get_request_by_id(request_id: int) -> Optional[Request]:
        """ID指定での請求書取得"""
        return await Request.get_or_none(id=request_id)

    @staticmethod
    async def get_request_detail(request_id: int) -> Optional[Dict[str, Any]]:
        """請求書詳細取得"""
        request = await Request.get_or_none(id=request_id)
        if not request:
            return None

        return await request.get_full_details()

    @staticmethod
    async def update_request(request_id: int, request_data: RequestUpdate) -> Optional[Request]:
        """請求書更新"""
        request = await Request.get_or_none(id=request_id)
        if not request:
            return None

        # 送信済みの請求書は一部項目のみ更新可能
        if request.is_sent:
            allowed_fields = ["remark", "order_document_url"]
            update_data = request_data.dict(exclude_unset=True, include=set(allowed_fields))
            if len(request_data.dict(exclude_unset=True)) > len(update_data):
                raise ValueError("送信済みの請求書は備考と注文書URLのみ更新可能です")
        else:
            update_data = request_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(request, field, value)

        await request.save()
        return request

    @staticmethod
    async def delete_request(request_id: int) -> bool:
        """請求書削除"""
        request = await Request.get_or_none(id=request_id)
        if not request:
            return False

        # 送信済みの請求書は削除不可
        if request.is_sent:
            raise ValueError("送信済みの請求書は削除できません")

        await request.delete()
        return True

    @staticmethod
    async def get_requests_list(
        year_month: Optional[str] = None,
        client_company_id: Optional[int] = None,
        case_id: Optional[int] = None,
        status: Optional[RequestStatus] = None,
        is_sent: Optional[bool] = None,
        is_paid: Optional[bool] = None,
        page: int = 1,
        pageSize: int = 100,
    ) -> Dict[str, Any]:
        """請求書一覧取得"""
        query = Request.all()

        # フィルター条件
        if year_month:
            query = query.filter(year_month=year_month)
        if case_id:
            # 新しい構造では、case_idは明細項目(RequestItem)にあるため、JOINが必要
            query = query.filter(items__case_id=case_id)
        if status:
            query = query.filter(status=status)
        if is_sent is not None:
            if is_sent:
                query = query.filter(sent_date__isnull=False)
            else:
                query = query.filter(sent_date__isnull=True)
        if is_paid is not None:
            query = query.filter(is_paid=is_paid)

        # Client会社フィルター（直接）
        if client_company_id:
            query = query.filter(client_company_id=client_company_id)

        # 総数取得
        total = await query.count()

        offset = (page - 1) * pageSize
        requests = (
            await query.offset(offset)
            .limit(pageSize)
            .prefetch_related(
                "client_company", "items__personnel", "items__case", "items__contract"
            )
        )

        # 詳細情報を含むリストを構築
        items = []
        for request in requests:
            detail = await request.get_full_details()
            items.append({
                "id": request.id,
                "created_at": request.created_at,
                **detail
            })

        return {"items": items, "total": total}

    @staticmethod
    async def generate_requests_for_month(request: RequestGenerationRequest, token: str = None):
        """月度請求書一括生成（要員ベース）"""

        # Client会社検証
        client_company = await ClientCompany.get_or_none(id=request.client_company_id)
        if not client_company:
            raise ValueError("指定されたClient会社が見つかりません")

        # 既存請求書チェック - 存在してもPDF再生成は可能
        if request.exclude_existing:
            existing_request = await Request.filter(
                client_company_id=request.client_company_id,
                year_month=request.year_month
            ).first()

            if existing_request:
                # 既存の請求書があればPDFを再生成して返す
                pdf_url = await RequestController._generate_and_upload_request_pdf(existing_request)
                existing_request.request_document_url = pdf_url
                existing_request.status = RequestStatus.GENERATED
                await existing_request.save()

                return {
                    "request_id": existing_request.id,
                    "request_number": existing_request.request_number,
                    "year_month": request.year_month,
                    "client_company_id": request.client_company_id,
                    "personnel_count": len(request.personnel_ids),
                    "request_amount": float(existing_request.request_amount) * 10000,
                    "pdf_url": pdf_url,
                    "status": existing_request.status
                }

        # 指定された要員の有効契約を取得
        contracts = (
            await Contract.filter(
                status=ContractStatus.ACTIVE,
                personnel_id__in=request.personnel_ids,
                case__client_company_id=request.client_company_id,
            )
            .prefetch_related(
                "case", "personnel", "calculation_items"
            )
            .all()
        )

        if not contracts:
            raise ValueError("指定された要員の有効契約が見つかりません")

        # 获取动态税率
        try:
            tax_rate = await sso_client.get_tax_rate(token)
        except Exception:
            tax_rate = 10.0  # 默认税率

        # 要員ごとに明細項目を準備
        request_items = []
        total_amount = 0

        for contract in contracts:
            # 基本給取得（万元存储）
            basic_salary = 0.0
            calculation_items = await contract.calculation_items.all()
            for item in calculation_items:
                if item.item_type == ContractItemType.BASIC_SALARY.value:
                    basic_salary = float(item.amount)  # 万元，直接存储
                    break

            # 明细項目作成用データ（以万元存储）
            item_data = {
                'personnel_id': contract.personnel_id,
                'case_id': contract.case_id,
                'contract_id': contract.id,
                'item_amount': basic_salary,
                'work_hours': contract.standard_working_hours or 160.0,
                'unit_price': basic_salary,  # 月額の場合，单价=基本給
                'item_remark': f"{request.year_month}分"
            }
            request_items.append(item_data)
            total_amount += basic_salary

        # 税額計算（使用动态税率）
        tax_excluded_amount = total_amount
        tax_amount = tax_excluded_amount * (tax_rate / 100.0)
        request_amount = tax_excluded_amount + tax_amount

        # 請求番号生成
        request_number = await RequestController._generate_request_number(request.year_month)

        # 請求書とRequestItem作成
        async with in_transaction():
            new_request = await Request.create(
                request_number=request_number,
                year_month=request.year_month,
                client_company_id=request.client_company_id,
                request_amount=request_amount,
                calculation_amount=request_amount,
                tax_excluded_amount=tax_excluded_amount,
                tax_rate=tax_rate,
                remark=f"{request.year_month}の月度請求書"
            )

            # 明細項目を作成
            for item_data in request_items:
                await RequestItem.create(
                    request_id=new_request.id,
                    **item_data
                )

        # 生成PDF並上传到S3
        pdf_url = await RequestController._generate_and_upload_request_pdf(new_request)
        new_request.request_document_url = pdf_url
        new_request.status = RequestStatus.GENERATED
        await new_request.save()

        return {
            "request_id": new_request.id,
            "request_number": new_request.request_number,
            "year_month": request.year_month,
            "client_company_id": request.client_company_id,
            "personnel_count": len(request.personnel_ids),
            "request_amount": float(new_request.request_amount) * 10000,
            "pdf_url": pdf_url,
            "status": new_request.status
        }

    @staticmethod
    async def _generate_and_upload_request_pdf(request: Request) -> str:
        """請求書PDF生成とS3アップロード（新しい多要員対応版）"""
        # テンプレート環境設定
        template_dir = os.path.join(settings.BASE_DIR, "templates")
        env = Environment(loader=FileSystemLoader(template_dir))

        # 請求書テンプレート使用
        template = env.get_template("client_member_request.html")

        # 関連データ取得
        await request.fetch_related("client_company")
        client_company = request.client_company
        sales_rep = await request.get_sales_representative()

        # 明細項目取得
        items = await request.items.all().prefetch_related("personnel", "case", "contract")

        # テンプレートデータ準備
        year, month = request.year_month.split("-")

        # 明細項目をテンプレート用に変換
        detail_items = []
        for index, item in enumerate(items, 1):
            detail_items.append({
                "number": str(index),
                "name": f"{item.personnel.name if item.personnel else ''} ({item.case.title if item.case else ''})",
                "unit_price": f"{float(item.unit_price) * 10000:,.0f}",
                "work_hours": f"{float(item.work_hours):,.0f}",
                "rate": "100%",
                "min_max_hours": f"{int(float(item.work_hours)*0.875)}/{int(float(item.work_hours)*1.125)}",  # ±12.5%
                "shortage_rate": "0.6",
                "excess_rate": "1.25",
                "other": "",
                "amount": f"{float(item.item_amount) * 10000:,.0f}",
                "remarks": item.item_remark or ""
            })

        html_content = template.render(
            # ヘッダー情報（Client会社の情報を使用）
            company_postal_code=client_company.zip_code if client_company else "",
            company_address_line1=client_company.address if client_company else "",
            company_address_line2="",  # 通常は1行にまとめる
            registration_number=client_company.invoice_number if client_company else "",
            company_tel=client_company.phone if client_company else "",

            # 請求書基本情報
            invoice_number=request.request_number,
            issue_date=datetime.now().strftime("%Y年%m月%d日"),

            # クライアント会社情報
            client_company=client_company.company_name if client_company else "",

            # 金額情報（万元转为元显示）
            total_amount=f"{float(request.request_amount) * 10000:,.0f}",
            subtotal_amount=f"{float(request.tax_excluded_amount) * 10000:,.0f}",
            tax_amount=f"{(float(request.request_amount) - float(request.tax_excluded_amount)) * 10000:,.0f}",
            tax_rate=f"{float(request.tax_rate)}",
            final_total_amount=f"{float(request.request_amount) * 10000:,.0f}",

            # 作業期間
            work_start_date=f"{year}年{month}月1日",
            work_end_date=f"{year}年{month}月末日",

            # 支払期限
            payment_due_date=request.payment_due_date.strftime("%Y年%m月%d日")
            if request.payment_due_date
            else "請求書発行日より30日後",

            # 請求会社情報
            billing_postal_code="101-0051",
            billing_address="東京都千代田区神田神保町3-2-28 ACN神保町ビル9階",
            billing_company="株式会社TOB",
            billing_tel="03-4500-9760",
            president_title="代表取締役",
            president_name="田中太郎",

            # 明細項目
            detail_items=detail_items,

            # 調整項目
            deduction_amount="",
            addition_amount="",

            # 銀行情報
            bank_name="三菱UFJ銀行",
            branch_name="神保町支店",
            branch_code="001",
            account_type="普通",
            account_number="1234567",
            account_holder="カ）ティーオービー",
            account_holder_address="東京都千代田区神田神保町3-2-28",
            account_holder_tel="03-4500-9760",

            # その他
            company_seal_url="inkan.png",
            title="御請求書",
        )

        # 一時ファイルでPDF生成
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            HTML(string=html_content).write_pdf(temp_file.name)

            # S3アップロード
            s3_key = f"requests/{request.year_month}/{request.request_number}.pdf"
            s3_url = await s3_client.upload_file(temp_file.name, s3_key, "application/pdf")

            # 一時ファイル削除
            os.unlink(temp_file.name)

        return s3_url

    @staticmethod
    async def send_requests(request: RequestSendRequest) -> Dict[str, Any]:
        """請求書一括送信"""
        sent_count = 0
        failed_count = 0
        errors = []

        requests = await Request.filter(id__in=request.request_ids).all()

        for req in requests:
            try:
                if req.is_sent:
                    errors.append(f"請求書 {req.request_number} は既に送信済みです")
                    failed_count += 1
                    continue

                await req.mark_as_sent(request.sent_by)
                sent_count += 1

            except Exception as e:
                failed_count += 1
                errors.append(f"請求書 {req.request_number}: {str(e)}")

        return {
            "message": f"送信完了: 成功{sent_count}件、失敗{failed_count}件",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "errors": errors,
        }

    @staticmethod
    async def mark_as_paid(request_id: int, payment_data: RequestPaymentUpdate) -> bool:
        """支払完了マーク"""
        request = await Request.get_or_none(id=request_id)
        if not request:
            return False

        if not request.is_sent:
            raise ValueError("未送信の請求書は支払完了にできません")

        # 支払金額が指定されている場合はセット
        if payment_data.payment_amount:
            request.payment_amount = payment_data.payment_amount

        # 支払確認日時が指定されている場合はセット
        if payment_data.payment_received_date:
            request.payment_received_date = payment_data.payment_received_date
        else:
            request.payment_received_date = datetime.now()

        await request.mark_as_paid(float(payment_data.payment_amount) if payment_data.payment_amount else None)
        return True

    @staticmethod
    async def upload_order_document(request_id: int, file_path: str) -> bool:
        """注文書ファイルアップロード"""
        request = await Request.get_or_none(id=request_id)
        if not request:
            return False

        # S3アップロード
        s3_key = f"requests/{request.year_month}/orders/{request.request_number}_order.pdf"
        s3_url = await s3_client.upload_file(file_path, s3_key, "application/pdf")

        request.order_document_url = s3_url
        await request.save()
        return True

    @staticmethod
    async def get_monthly_statistics(year_month: str) -> Dict[str, Any]:
        """月度統計情報取得"""
        requests = await Request.filter(year_month=year_month).all()

        total_count = len(requests)
        sent_count = len([r for r in requests if r.is_sent])
        paid_count = len([r for r in requests if r.is_paid])

        total_amount = sum(float(r.request_amount) for r in requests)
        paid_amount = sum(float(r.payment_amount or 0) for r in requests if r.is_paid)

        # ステータス別統計
        status_stats = {}
        for req in requests:
            status = req.status.value
            status_stats[status] = status_stats.get(status, 0) + 1

        return {
            "year_month": year_month,
            "total_requests": total_count,
            "sent_requests": sent_count,
            "paid_requests": paid_count,
            "send_rate": (sent_count / total_count * 100) if total_count > 0 else 0,
            "payment_rate": (paid_count / total_count * 100) if total_count > 0 else 0,
            "total_amount": total_amount,
            "paid_amount": paid_amount,
            "outstanding_amount": total_amount - paid_amount,
            "status_breakdown": status_stats,
        }
