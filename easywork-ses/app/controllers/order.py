import os
import tempfile
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader
from tortoise.queryset import QuerySet
from tortoise.transactions import in_transaction
from weasyprint import HTML

from app.models.case import Case
from app.models.contract import Contract
from app.models.enums import (
    ApproveStatus,
    ContractItemType,
    ContractStatus,
    OrderStatus,
    PersonType,
)
from app.models.order import Order, OrderBatch
from app.models.personnel import Personnel
from app.schemas.order import (
    OrderBatchCreate,
    OrderBatchDetail,
    OrderCreate,
    OrderDetail,
    OrderGenerationRequest,
    OrderListItem,
    OrderSendRequest,
    OrderUpdate,
)
from app.settings import settings
from app.utils.s3_client import s3_client


class OrderController:
    """注文書コントローラー"""

    @staticmethod
    async def create_order(order_data: OrderCreate) -> Order:
        """注文書作成"""
        # 重複チェック
        existing = await Order.filter(personnel_id=order_data.personnel_id, year_month=order_data.year_month).first()

        if existing:
            raise ValueError(f"対象要員の{order_data.year_month}の注文書は既に存在します")

        # 関連データの検証
        personnel = await Personnel.get_or_none(id=order_data.personnel_id)
        if not personnel:
            raise ValueError("指定された要員が見つかりません")

        case = await Case.get_or_none(id=order_data.case_id)
        if not case:
            raise ValueError("指定された案件が見つかりません")

        contract = await Contract.get_or_none(id=order_data.contract_id)
        if not contract:
            raise ValueError("指定された契約が見つかりません")

        # 契約が有効かチェック
        if contract.status != ContractStatus.ACTIVE:
            raise ValueError("指定された契約は有効ではありません")

        # 注文番号生成
        order_number = await OrderController._generate_order_number(order_data.year_month)

        # 注文書作成
        order = await Order.create(
            order_number=order_number,
            year_month=order_data.year_month,
            personnel_id=order_data.personnel_id,
            case_id=order_data.case_id,
            contract_id=order_data.contract_id,
            remark=order_data.remark,
        )

        return order

    @staticmethod
    async def _generate_order_number(year_month: str) -> str:
        """注文番号生成"""
        # 年月から番号生成（例：2024-01 → 202401-001）
        year_month_str = year_month.replace("-", "")

        # 同一月の最大番号を取得
        last_order = await Order.filter(year_month=year_month).order_by("-order_number").first()

        if last_order and last_order.order_number.startswith(year_month_str):
            # 既存の番号から連番を取得
            try:
                last_seq = int(last_order.order_number.split("-")[-1])
                next_seq = last_seq + 1
            except (IndexError, ValueError):
                next_seq = 1
        else:
            next_seq = 1

        return f"{year_month_str}-{next_seq:03d}"

    @staticmethod
    async def get_order_by_id(order_id: int) -> Optional[Order]:
        """ID指定での注文書取得"""
        return await Order.get_or_none(id=order_id)

    @staticmethod
    async def get_order_detail(order_id: int) -> Optional[Dict[str, Any]]:
        """注文書詳細取得"""
        order = await Order.get_or_none(id=order_id)
        if not order:
            return None

        return await order.get_full_details()

    @staticmethod
    async def update_order(order_id: int, order_data: OrderUpdate) -> Optional[Order]:
        """注文書更新"""
        order = await Order.get_or_none(id=order_id)
        if not order:
            return None

        # 送信済みの注文書は更新制限
        if order.is_sent and order_data.remark is None:
            raise ValueError("送信済みの注文書は備考のみ更新可能です")

        update_data = order_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)

        await order.save()
        return order

    @staticmethod
    async def delete_order(order_id: int) -> bool:
        """注文書削除"""
        order = await Order.get_or_none(id=order_id)
        if not order:
            return False

        # 送信済みの注文書は削除不可
        if order.is_sent:
            raise ValueError("送信済みの注文書は削除できません")

        await order.delete()
        return True

    @staticmethod
    async def get_orders_list(
        year_month: Optional[str] = None,
        bp_company_id: Optional[int] = None,
        status: Optional[ApproveStatus] = None,
        is_sent: Optional[bool] = None,
        is_collected: Optional[bool] = None,
        page: int = 1,
        pageSize: int = 100,
    ) -> Dict[str, Any]:
        """注文書一覧取得"""
        query = Order.all()

        # フィルター条件
        if year_month:
            query = query.filter(year_month=year_month)
        if status:
            query = query.filter(status=status)
        if is_sent is not None:
            if is_sent:
                query = query.filter(sent_date__isnull=False)
            else:
                query = query.filter(sent_date__isnull=True)
        if is_collected is not None:
            query = query.filter(is_collected=is_collected)

        # BP会社フィルター（Personnel経由）
        if bp_company_id:
            query = query.filter(personnel__bp_employee_detail__bp_company_id=bp_company_id)

        # 总数获取
        total = await query.count()

        offset = (page - 1) * pageSize
        orders = (
            await query.offset(offset)
            .limit(pageSize)
            .prefetch_related(
                "personnel__bp_employee_detail__bp_company",
                "case__company_sales_representative",
                "contract__calculation_items",
            )
        )

        # 詳細情報を含むリストを構築
        items = []
        for order in orders:
            detail = await order.get_full_details()
            items.append(
                {
                    "id": order.id,
                    "order_number": detail["order_number"],
                    "year_month": detail["year_month"],
                    "year_month_display": detail["year_month_display"],
                    "bp_company_name": detail["bp_company_name"],
                    "bp_company_id": detail["bp_company_id"],
                    "personnel_name": detail["personnel_name"],
                    "case_title": detail["case_title"],
                    "sales_representative_name": detail["sales_representative_name"],
                    "basic_salary": detail["contract_details"]["basic_salary"],
                    "status": detail["status"],
                    "is_sent": detail["is_sent"],
                    "is_collected": detail["is_collected"],
                    "created_at": order.created_at,
                }
            )

        return {"items": items, "total": total}

    @staticmethod
    async def generate_orders_for_month(request: OrderGenerationRequest):
        """月度注文書一括生成"""
        orders = []

        async with in_transaction():
            # 指定されたBP会社の指定された要員の有効契約を取得
            contracts = (
                await Contract.filter(
                    status=ContractStatus.ACTIVE,
                    personnel_id__in=request.personnel_ids,
                    personnel__bp_employee_detail__bp_company_id=request.bp_company_id,
                    personnel__person_type=PersonType.BP_EMPLOYEE,
                )
                .prefetch_related(
                    "personnel__bp_employee_detail__bp_company",
                    "case__company_sales_representative",
                    "calculation_items",
                )
                .all()
            )

            for contract in contracts:
                # 既存チェック
                if request.exclude_existing:
                    existing = await Order.filter(
                        personnel_id=contract.personnel_id, year_month=request.year_month
                    ).exists()

                    if existing:
                        continue

                # 注文書作成
                order_number = await OrderController._generate_order_number(request.year_month)

                order = await Order.create(
                    order_number=order_number,
                    year_month=request.year_month,
                    personnel_id=contract.personnel_id,
                    case_id=contract.case_id,
                    contract_id=contract.id,
                )

                # PDF生成とS3アップロード
                pdf_url = await OrderController._generate_and_upload_order_pdf(order, contract)
                order.order_document_url = pdf_url
                order.status = OrderStatus.GENERATED  # PDF生成完了で状态変更
                await order.save()

                orders.append(
                    {
                        "order_id": order.id,
                        "order_number": order.order_number,
                        "personnel_id": contract.personnel_id,
                        "pdf_url": pdf_url,
                    }
                )

        return {"orders": orders}

    @staticmethod
    async def _generate_and_upload_order_pdf(order: Order, contract: Contract) -> str:
        """注文書PDF生成とS3アップロード"""
        # テンプレート環境設定
        template_dir = os.path.join(settings.BASE_DIR, "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("partner_member_order.html")

        # 契約詳細情報取得
        personnel = await contract.personnel
        bp_employee_detail = await personnel.bp_employee_detail
        bp_company = await bp_employee_detail.bp_company
        case = await contract.case

        # 基本給取得
        basic_salary = 0.0
        calculation_items = await contract.calculation_items.all()
        for item in calculation_items:
            if item.item_type == ContractItemType.BASIC_SALARY.value:
                basic_salary = item.amount
                break

        # テンプレートデータ準備
        year, month = order.year_month.split("-")
        work_period = f"{year}年{month}月1日〜{year}年{month}月末日"

        html_content = template.render(
            order_number=order.order_number,
            order_date=datetime.now().strftime("%Y-%m-%d"),
            recipient_company=bp_company.name,
            issuer_company="株式会社TOB",  # 発注会社名（設定から取得すべき）
            issuer_address_line1="東京都千代田区神田神保町3-2-28",  # 設定から取得すべき
            issuer_address_line2="ACN神保町ビル9階",
            issuer_tel="03-4500-9760",
            issuer_fax="",
            creator=(await case.company_sales_representative).name if await case.company_sales_representative else "",
            work_name=case.title,
            work_period=work_period,
            responsibility_ko=personnel.name,
            contact_ko=personnel.name,
            responsibility_ot="",  # 必要に応じて設定
            contact_ot="",
            work_responsible=personnel.name,
            base_fee=f"{basic_salary:,.0f}",
            shortage_fee="2,125",  # 契約から取得すべき
            excess_fee="1,700",  # 契約から取得すべき
            standard_time=f"{contract.standard_working_hours}h〜{contract.max_working_hours or contract.standard_working_hours}h/月",
            work_place=case.location or "弊社指定場所",
            deliverable="月別作業報告書",
            payment_terms="作業報告書査収による毎月末締め、翌々月末に現金振込",  # 契約から取得すべき
            contract_terms="本作業に関わる著作権は、甲に一切帰属する。",  # 契約から取得すべき
            company_seal_url="inkan.png",  # 印鑑画像URL
        )

        # 一時ファイルでPDF生成
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            HTML(string=html_content).write_pdf(temp_file.name)

            # S3アップロード
            s3_key = f"orders/{order.year_month}/{order.order_number}.pdf"
            s3_url = await s3_client.upload_file(temp_file.name, s3_key, "application/pdf")

            # 一時ファイル削除
            os.unlink(temp_file.name)

        return s3_url

    @staticmethod
    async def send_orders(request: OrderSendRequest) -> Dict[str, Any]:
        """注文書一括送信"""
        sent_count = 0
        failed_count = 0
        errors = []

        orders = await Order.filter(id__in=request.order_ids).all()

        for order in orders:
            try:
                if order.is_sent:
                    errors.append(f"注文書 {order.order_number} は既に送信済みです")
                    failed_count += 1
                    continue

                await order.mark_as_sent(request.sent_by)
                sent_count += 1

            except Exception as e:
                failed_count += 1
                errors.append(f"注文書 {order.order_number}: {str(e)}")

        return {
            "message": f"送信完了: 成功{sent_count}件、失敗{failed_count}件",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "errors": errors,
        }

    @staticmethod
    async def mark_as_collected(order_id: int) -> bool:
        """回収完了マーク"""
        order = await Order.get_or_none(id=order_id)
        if not order:
            return False

        if not order.is_sent:
            raise ValueError("未送信の注文書は回収完了にできません")

        await order.mark_as_collected()
        return True


class OrderBatchController:
    """注文書バッチコントローラー"""

    @staticmethod
    async def create_batch(batch_data: OrderBatchCreate) -> OrderBatch:
        """バッチ作成"""
        # バッチ番号生成
        batch_number = await OrderBatchController._generate_batch_number(batch_data.year_month)

        batch = await OrderBatch.create(
            batch_number=batch_number,
            year_month=batch_data.year_month,
            batch_type=batch_data.batch_type,
            filter_bp_company_id=batch_data.filter_bp_company_id,
            filter_sales_rep_id=batch_data.filter_sales_rep_id,
            created_by=batch_data.created_by,
            remark=batch_data.remark,
        )

        return batch

    @staticmethod
    async def _generate_batch_number(year_month: str) -> str:
        """バッチ番号生成"""
        year_month_str = year_month.replace("-", "")

        # 同一月の最大番号を取得
        last_batch = await OrderBatch.filter(year_month=year_month).order_by("-batch_number").first()

        if last_batch and last_batch.batch_number.startswith(f"BATCH-{year_month_str}"):
            try:
                last_seq = int(last_batch.batch_number.split("-")[-1])
                next_seq = last_seq + 1
            except (IndexError, ValueError):
                next_seq = 1
        else:
            next_seq = 1

        return f"BATCH-{year_month_str}-{next_seq:03d}"

    @staticmethod
    async def get_batch_detail(batch_id: int) -> Optional[OrderBatch]:
        """バッチ詳細取得"""
        return await OrderBatch.get_or_none(id=batch_id).prefetch_related("orders")

    @staticmethod
    async def add_orders_to_batch(batch_id: int, order_ids: List[int]) -> bool:
        """バッチに注文書を追加"""
        batch = await OrderBatch.get_or_none(id=batch_id)
        if not batch:
            return False

        orders = await Order.filter(id__in=order_ids).all()
        await batch.orders.add(*orders)
        await batch.update_counts()

        return True

    @staticmethod
    async def process_batch(batch_id: int, processed_by: str) -> bool:
        """バッチ処理実行"""
        batch = await OrderBatch.get_or_none(id=batch_id)
        if not batch:
            return False

        await batch.mark_as_processed(processed_by)
        return True
