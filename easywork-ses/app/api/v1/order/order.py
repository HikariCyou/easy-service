from typing import List, Optional
from fastapi import APIRouter, Query, Header
from fastapi.responses import JSONResponse
import logging

from app.controllers.order import OrderController, OrderBatchController
from app.controllers.mail import MailController
from app.utils.mail_sender import mail_sender
from app.utils.s3_client import s3_client
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderDetail, OrderListItem,
    OrderBatchCreate, OrderBatchDetail, OrderGenerationRequest,
    OrderSendRequest, OrderStatusUpdate
)
from app.schemas.mail import MailTemplateRequest, SendMailRequest
from app.schemas import Success, Fail
from app.models.enums import ApproveStatus, OrderStatus
from app.core.ctx import CTX_USER_ID

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create", summary="注文書作成")
async def create_order(order_data: OrderCreate):
    """注文書を作成する"""
    try:
        order = await OrderController.create_order(order_data)
        detail = await order.get_full_details()
        detail["id"] = order.id
        detail["created_at"] = order.created_at
        detail["updated_at"] = order.updated_at
        return Success(data=detail)
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=f"注文書作成でエラーが発生しました: {str(e)}")


@router.get("/list", summary="注文書一覧取得")
async def get_orders_list(
    year_month: Optional[str] = Query(None, description="対象年月（YYYY-MM）"),
    bp_company_id: Optional[int] = Query(None, description="BP会社ID"),
    status: Optional[ApproveStatus] = Query(None, description="ステータス"),
    is_sent: Optional[bool] = Query(None, description="送信済みフラグ"),
    is_collected: Optional[bool] = Query(None, description="回収完了フラグ"),
    page: int = Query(1, description="ページ番号"),
    pageSize: int = Query(100, description="ページサイズ"),
):
    """注文書一覧を取得する"""
    try:
        result = await OrderController.get_orders_list(
            year_month=year_month,
            bp_company_id=bp_company_id,
            status=status,
            is_sent=is_sent,
            is_collected=is_collected,
            page=page,
            pageSize=pageSize
        )
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=f"注文書一覧取得でエラーが発生しました: {str(e)}")


@router.get("/detail/{order_id}", summary="注文書詳細取得")
async def get_order_detail(
    order_id: int,
):
    """注文書詳細を取得する"""
    try:
        detail = await OrderController.get_order_detail(order_id)
        if not detail:
            return Fail(msg="注文書が見つかりません")
        
        order = await OrderController.get_order_by_id(order_id)
        detail["id"] = order.id
        detail["created_at"] = order.created_at
        detail["updated_at"] = order.updated_at
        
        return Success(data=detail)
    except Exception as e:
        return Fail(msg=f"注文書詳細取得でエラーが発生しました: {str(e)}")


@router.put("/update/{order_id}", summary="注文書更新")
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
):
    """注文書を更新する"""
    try:
        order = await OrderController.update_order(order_id, order_data)
        if not order:
            return Fail(msg="注文書が見つかりません")
        
        detail = await order.get_full_details()
        detail["id"] = order.id
        detail["created_at"] = order.created_at
        detail["updated_at"] = order.updated_at
        return Success(data=detail)
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=f"注文書更新でエラーが発生しました: {str(e)}")


@router.delete("/delete/{order_id}", summary="注文書削除")
async def delete_order(
    order_id: int,
):
    """注文書を削除する"""
    try:
        success = await OrderController.delete_order(order_id)
        if not success:
            return Fail(msg="注文書が見つかりません")
        
        return Success(data={"message": "注文書を削除しました"})
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=f"注文書削除でエラーが発生しました: {str(e)}")


@router.post("/generate", summary="月度注文書一括生成")
async def generate_orders(
    request: OrderGenerationRequest,
):
    """指定月の注文書を一括生成する"""
    try:
        response = await OrderController.generate_orders_for_month(request)
        return Success(data=response)
    except Exception as e:
        return Fail(msg=f"注文書生成でエラーが発生しました: {str(e)}")


@router.post("/send", summary="注文書一括送信")
async def send_orders(
    request: OrderSendRequest,
):
    """注文書を一括送信する"""
    try:
        response = await OrderController.send_orders(request)
        return Success(data=response)
    except Exception as e:
        return Fail(msg=f"注文書送信でエラーが発生しました: {str(e)}")


@router.post("/send/{order_id}", summary="注文書個別送信")
async def send_single_order(
    order_id: int,
    sent_by: str = Query(..., description="送信者名"),
):
    """注文書を個別送信する"""
    try:
        order = await OrderController.get_order_by_id(order_id)
        if not order:
            return Fail(msg="注文書が見つかりません")
        
        if order.is_sent:
            return Fail(msg="この注文書は既に送信済みです")
        
        await order.mark_as_sent(sent_by)
        return Success(data={"message": "注文書を送信しました"})
    except Exception as e:
        return Fail(msg=f"注文書送信でエラーが発生しました: {str(e)}")


@router.post("/{order_id}/collect", summary="注文書回収完了")
async def mark_order_collected(
    order_id: int,
):
    """注文書の回収完了をマークする"""
    try:
        success = await OrderController.mark_as_collected(order_id)
        if not success:
            return Fail(msg="注文書が見つかりません")
        
        return Success(data={"message": "注文書の回収完了をマークしました"})
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=f"回収完了処理でエラーが発生しました: {str(e)}")


@router.put("/{order_id}/status", summary="注文書ステータス変更")
async def update_order_status(
    order_id: int,
    status: OrderStatus,
):
    """注文書のステータスを変更する"""
    try:
        order = await OrderController.get_order_by_id(order_id)
        if not order:
            return Fail(msg="注文書が見つかりません")
        
        order.status = status
        await order.save()
        
        return Success(data={"message": f"注文書ステータスを{status.value}に変更しました"})
    except Exception as e:
        return Fail(msg=f"ステータス変更でエラーが発生しました: {str(e)}")


# バッチ処理関連のエンドポイント
@router.post("/batches/create", summary="注文書バッチ作成")
async def create_order_batch(
    batch_data: OrderBatchCreate,
):
    """注文書バッチを作成する"""
    try:
        batch = await OrderBatchController.create_batch(batch_data)
        await batch.fetch_related('orders')
        
        batch_detail = {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "year_month": batch.year_month,
            "batch_type": batch.batch_type,
            "filter_bp_company_id": batch.filter_bp_company_id,
            "filter_sales_rep_id": batch.filter_sales_rep_id,
            "status": batch.status,
            "total_orders": batch.total_orders,
            "sent_orders": batch.sent_orders,
            "completion_rate": batch.completion_rate,
            "created_by": batch.created_by,
            "processed_date": batch.processed_date,
            "processed_by": batch.processed_by,
            "remark": batch.remark,
            "created_at": batch.created_at,
            "updated_at": batch.updated_at
        }
        return Success(data=batch_detail)
    except Exception as e:
        return Fail(msg=f"バッチ作成でエラーが発生しました: {str(e)}")


@router.get("/batches/{batch_id}", summary="注文書バッチ詳細取得")
async def get_batch_detail(
    batch_id: int,
):
    """注文書バッチ詳細を取得する"""
    try:
        batch = await OrderBatchController.get_batch_detail(batch_id)
        if not batch:
            return Fail(msg="バッチが見つかりません")
        
        batch_detail = {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "year_month": batch.year_month,
            "batch_type": batch.batch_type,
            "filter_bp_company_id": batch.filter_bp_company_id,
            "filter_sales_rep_id": batch.filter_sales_rep_id,
            "status": batch.status,
            "total_orders": batch.total_orders,
            "sent_orders": batch.sent_orders,
            "completion_rate": batch.completion_rate,
            "created_by": batch.created_by,
            "processed_date": batch.processed_date,
            "processed_by": batch.processed_by,
            "remark": batch.remark,
            "created_at": batch.created_at,
            "updated_at": batch.updated_at
        }
        return Success(data=batch_detail)
    except Exception as e:
        return Fail(msg=f"バッチ取得でエラーが発生しました: {str(e)}")


@router.post("/batches/{batch_id}/add-orders", summary="バッチに注文書追加")
async def add_orders_to_batch(
    batch_id: int,
    order_ids: List[int],
):
    """バッチに注文書を追加する"""
    try:
        success = await OrderBatchController.add_orders_to_batch(batch_id, order_ids)
        if not success:
            return Fail(msg="バッチが見つかりません")
        
        return Success(data={"message": f"{len(order_ids)}件の注文書をバッチに追加しました"})
    except Exception as e:
        return Fail(msg=f"バッチ追加でエラーが発生しました: {str(e)}")


@router.post("/batches/{batch_id}/process", summary="バッチ処理実行")
async def process_batch(
    batch_id: int,
    processed_by: str = Query(..., description="処理者名"),
):
    """バッチ処理を実行する"""
    try:
        success = await OrderBatchController.process_batch(batch_id, processed_by)
        if not success:
            return Fail(msg="バッチが見つかりません")
        
        return Success(data={"message": "バッチ処理を完了しました"})
    except Exception as e:
        return Fail(msg=f"バッチ処理でエラーが発生しました: {str(e)}")


@router.get("/statistics/monthly", summary="月度統計情報")
async def get_monthly_statistics(
    year_month: str = Query(..., description="対象年月（YYYY-MM）"),
):
    """指定月の注文書統計情報を取得する"""
    try:
        # 基本統計
        total_orders = await OrderController.get_orders_list(year_month=year_month, page=1, pageSize=10000)
        total_count = total_orders["total"]
        
        # より効率的な統計計算のため、実際のデータを取得
        all_orders = total_orders["items"]
        sent_count = len([o for o in all_orders if o["is_sent"]])
        collected_count = len([o for o in all_orders if o["is_collected"]])
        
        # ステータス別統計
        status_stats = {}
        for order in all_orders:
            status = order["status"]
            status_stats[status] = status_stats.get(status, 0) + 1
        
        # BP会社別統計
        bp_company_stats = {}
        for order in all_orders:
            bp_company = order["bp_company_name"]
            if bp_company:
                bp_company_stats[bp_company] = bp_company_stats.get(bp_company, 0) + 1
        
        statistics = {
            "year_month": year_month,
            "total_orders": total_count,
            "sent_orders": sent_count,
            "collected_orders": collected_count,
            "send_rate": (sent_count / total_count * 100) if total_count > 0 else 0,
            "collection_rate": (collected_count / total_count * 100) if total_count > 0 else 0,
            "status_breakdown": status_stats,
            "bp_company_breakdown": bp_company_stats
        }
        
        return Success(data=statistics)
    except Exception as e:
        return Fail(msg=f"統計情報取得でエラーが発生しました: {str(e)}")


@router.get("/mail-template", summary="注文書邮件模板获取")
async def get_order_mail_template(
    template_id: Optional[int] = Query(None, description="模板ID"),
    order_id: Optional[int] = Query(None, description="注文書ID"),
    authorization: Optional[str] = Header(None),
):
    """获取填充后的注文書邮件模板"""
    try:
        result = await MailController.get_filled_template(
            template_id=template_id,
            order_id=order_id,
            token=authorization
        )
        return Success(data=result)
    except Exception as e:
        return Fail(msg=f"邮件模板获取でエラーが発生しました: {str(e)}")


@router.post("/{order_id}/send-mail", summary="注文書邮件发送")
async def send_order_mail(
    order_id: int,
    request: SendMailRequest,
    authorization: Optional[str] = Header(None),
):
    """发送注文書邮件给BP公司"""
    try:
        # 获取注文書信息
        order = await OrderController.get_order_by_id(order_id)
        if not order:
            return Fail(msg="注文書が見つかりません")

        # 准备附件 - 从S3下载PDF文件
        attachment_files = []
        if order.order_document_url:
            try:
                # 从S3 URL提取key
                if "amazonaws.com/" in order.order_document_url:
                    s3_key = order.order_document_url.split("amazonaws.com/")[-1].split("?")[0]
                elif "s3." in order.order_document_url and "/" in order.order_document_url:
                    # 处理其他S3 URL格式
                    url_parts = order.order_document_url.split("/")
                    bucket_and_key = "/".join(url_parts[3:])  # 跳过 https://bucket.s3.region/
                    s3_key = bucket_and_key
                else:
                    # 假设直接是key
                    s3_key = order.order_document_url

                # 从S3获取文件内容
                file_content = await s3_client.get_file_content(s3_key)
                if file_content:
                    # 生成文件名
                    filename = f"注文書_{order_id}_{order.year_month.replace('-', '')}.pdf"
                    attachment_files.append((filename, file_content, "application/pdf"))

            except Exception as e:
                logger.error(f"S3ファイル取得エラー: {str(e)}")
                # 即使附件失败也继续发送邮件，只记录错误

        # 发送主邮件
        await mail_sender.send_mail_with_attachments(
            mail=request.to,
            attachment_files=attachment_files,
            template_params={
                "subject": request.subject,
                "content": request.content,
                "cc": ",".join(request.cc) if request.cc else "",
                "bcc": ",".join(request.bcc) if request.bcc else ""
            }
        )

        # 如果有密码邮件内容，发送密码邮件
        # if request.password_subject and request.password_content:
        #     await mail_sender.send_mail_with_attachments(
        #         mail=request.to,
        #         attachment_files=None,
        #         template_params={
        #             "subject": request.password_subject,
        #             "content": request.password_content
        #         }
        #     )

        return Success(data={
            "message": "邮件发送成功",
            "attachment_count": len(attachment_files)
        })
    except Exception as e:
        return Fail(msg=f"邮件发送でエラーが発生しました: {str(e)}")