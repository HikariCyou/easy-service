import logging
import os
import tempfile
from typing import List, Optional

from fastapi import APIRouter, File, Form, Header, Query, UploadFile
from fastapi.responses import JSONResponse

from app.controllers.mail import MailController
from app.controllers.request import RequestController
from app.models.enums import RequestStatus
from app.schemas import Fail, Success
from app.schemas.mail import MailTemplateRequest, SendMailRequest
from app.schemas.request import (
    RequestAttachmentCreate,
    RequestCreate,
    RequestGenerationRequest,
    RequestPaymentUpdate,
    RequestSendRequest,
    RequestUpdate,
)
from app.utils.mail_sender import mail_sender
from app.utils.s3_client import s3_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/create", summary="請求書作成")
async def create_request(
    request_data: RequestCreate,
    authorization: Optional[str] = Header(None)
):
    """請求書を作成する"""
    try:
        request = await RequestController.create_request(request_data, authorization)
        detail = await request.get_full_details()
        detail["id"] = request.id
        return Success(data=detail)
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=f"請求書作成でエラーが発生しました: {str(e)}")


@router.get("/list", summary="請求書一覧取得")
async def get_requests_list(
    year_month: Optional[str] = Query(None, description="対象年月（YYYY-MM）"),
    client_company_id: Optional[int] = Query(None, description="Client会社ID"),
    case_id: Optional[int] = Query(None, description="案件ID"),
    status: Optional[RequestStatus] = Query(None, description="ステータス"),
    is_sent: Optional[bool] = Query(None, description="送信済みフラグ"),
    is_paid: Optional[bool] = Query(None, description="支払済みフラグ"),
    page: int = Query(1, description="ページ番号"),
    pageSize: int = Query(100, description="ページサイズ"),
):
    """請求書一覧を取得する"""
    try:
        result = await RequestController.get_requests_list(
            year_month=year_month,
            client_company_id=client_company_id,
            case_id=case_id,
            status=status,
            is_sent=is_sent,
            is_paid=is_paid,
            page=page,
            pageSize=pageSize,
        )
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=f"請求書一覧取得でエラーが発生しました: {str(e)}")


@router.get("/detail/{request_id}", summary="請求書詳細取得")
async def get_request_detail(request_id: int):
    """請求書詳細を取得する"""
    try:
        detail = await RequestController.get_request_detail(request_id)
        if not detail:
            return Fail(msg="請求書が見つかりません")

        request = await RequestController.get_request_by_id(request_id)
        detail["id"] = request.id
        detail["created_at"] = request.created_at
        detail["updated_at"] = request.updated_at

        return Success(data=detail)
    except Exception as e:
        return Fail(msg=f"請求書詳細取得でエラーが発生しました: {str(e)}")


@router.put("/update/{request_id}", summary="請求書更新")
async def update_request(request_id: int, request_data: RequestUpdate):
    """請求書を更新する"""
    try:
        request = await RequestController.update_request(request_id, request_data)
        if not request:
            return Fail(msg="請求書が見つかりません")

        detail = await request.get_full_details()
        detail["id"] = request.id
        detail["created_at"] = request.created_at
        detail["updated_at"] = request.updated_at
        return Success(data=detail)
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=f"請求書更新でエラーが発生しました: {str(e)}")


@router.delete("/delete/{request_id}", summary="請求書削除")
async def delete_request(request_id: int):
    """請求書を削除する"""
    try:
        success = await RequestController.delete_request(request_id)
        if not success:
            return Fail(msg="請求書が見つかりません")

        return Success(data={"message": "請求書を削除しました"})
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=f"請求書削除でエラーが発生しました: {str(e)}")


@router.post("/generate", summary="月度請求書一括生成")
async def generate_requests(
    request: RequestGenerationRequest,
    authorization: Optional[str] = Header(None)
):
    """指定月の請求書を一括生成する"""
    try:
        response = await RequestController.generate_requests_for_month(request, authorization)
        return Success(data=response)
    except Exception as e:
        return Fail(msg=f"請求書生成でエラーが発生しました: {str(e)}")


@router.post("/send", summary="請求書一括送信")
async def send_requests(request: RequestSendRequest):
    """請求書を一括送信する"""
    try:
        response = await RequestController.send_requests(request)
        return Success(data=response)
    except Exception as e:
        return Fail(msg=f"請求書送信でエラーが発生しました: {str(e)}")


@router.post("/send/{request_id}", summary="請求書個別送信")
async def send_single_request(
    request_id: int,
    sent_by: str = Query(..., description="送信者名"),
):
    """請求書を個別送信する"""
    try:
        request = await RequestController.get_request_by_id(request_id)
        if not request:
            return Fail(msg="請求書が見つかりません")

        if request.is_sent:
            return Fail(msg="この請求書は既に送信済みです")

        await request.mark_as_sent(sent_by)
        return Success(data={"message": "請求書を送信しました"})
    except Exception as e:
        return Fail(msg=f"請求書送信でエラーが発生しました: {str(e)}")


@router.post("/{request_id}/payment", summary="請求書支払完了")
async def mark_request_paid(request_id: int, payment_data: RequestPaymentUpdate):
    """請求書の支払完了をマークする"""
    try:
        success = await RequestController.mark_as_paid(request_id, payment_data)
        if not success:
            return Fail(msg="請求書が見つかりません")

        return Success(data={"message": "請求書の支払完了をマークしました"})
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=f"支払完了処理でエラーが発生しました: {str(e)}")


@router.put("/{request_id}/status", summary="請求書ステータス変更")
async def update_request_status(request_id: int, status: RequestStatus):
    """請求書のステータスを変更する"""
    try:
        request = await RequestController.get_request_by_id(request_id)
        if not request:
            return Fail(msg="請求書が見つかりません")

        request.status = status
        await request.save()

        return Success(data={"message": f"請求書ステータスを{status.value}に変更しました"})
    except Exception as e:
        return Fail(msg=f"ステータス変更でエラーが発生しました: {str(e)}")


@router.post("/{request_id}/upload-order", summary="注文書ファイルアップロード")
async def upload_order_document(request_id: int, file: UploadFile = File(..., description="注文書PDFファイル")):
    """請求書に関連する注文書ファイルをアップロードする"""
    try:
        request = await RequestController.get_request_by_id(request_id)
        if not request:
            return Fail(msg="請求書が見つかりません")

        # ファイル形式チェック
        if not file.filename.lower().endswith(".pdf"):
            return Fail(msg="PDFファイルのみアップロード可能です")

        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            # S3アップロードと請求書更新
            success = await RequestController.upload_order_document(request_id, temp_file.name)

            # 一時ファイル削除
            os.unlink(temp_file.name)

            if not success:
                return Fail(msg="ファイルアップロードに失敗しました")

        return Success(data={"message": "注文書ファイルをアップロードしました"})
    except Exception as e:
        return Fail(msg=f"ファイルアップロードでエラーが発生しました: {str(e)}")


@router.get("/statistics/monthly", summary="月度統計情報")
async def get_monthly_statistics(
    year_month: str = Query(..., description="対象年月（YYYY-MM）"),
):
    """指定月の請求書統計情報を取得する"""
    try:
        statistics = await RequestController.get_monthly_statistics(year_month)
        return Success(data=statistics)
    except Exception as e:
        return Fail(msg=f"統計情報取得でエラーが発生しました: {str(e)}")


@router.get("/mail-template", summary="請求書邮件模板获取")
async def get_request_mail_template(
    template_id: Optional[int] = Query(None, description="模板ID"),
    request_id: Optional[int] = Query(None, description="請求書ID"),
    authorization: Optional[str] = Header(None),
):
    """获取填充后的請求書邮件模板"""
    try:
        result = await MailController.get_filled_template(
            template_id=template_id, request_id=request_id, token=authorization
        )
        return Success(data=result)
    except Exception as e:
        return Fail(msg=f"邮件模板获取でエラーが発生しました: {str(e)}")


@router.post("/{request_id}/send-mail", summary="請求書メール送信")
async def send_request_mail(
    request_id: int,
    request: SendMailRequest,
):
    """請求書メールをClient会社に送信する"""
    try:
        # 請求書情報取得
        req = await RequestController.get_request_by_id(request_id)
        if not req:
            return Fail(msg="請求書が見つかりません")

        # 添付ファイル準備
        attachment_files = []

        # 1. 請求書PDFを添付
        if req.request_document_url:
            try:
                # S3 URLからkeyを抽出
                if "amazonaws.com/" in req.request_document_url:
                    s3_key = req.request_document_url.split("amazonaws.com/")[-1].split("?")[0]
                elif "s3." in req.request_document_url and "/" in req.request_document_url:
                    url_parts = req.request_document_url.split("/")
                    bucket_and_key = "/".join(url_parts[3:])
                    s3_key = bucket_and_key
                else:
                    s3_key = req.request_document_url

                # S3からファイル内容取得
                file_content = await s3_client.get_file_content(s3_key)
                if file_content:
                    filename = f"請求書_{request_id}_{req.year_month.replace('-', '')}.pdf"
                    attachment_files.append((filename, file_content, "application/pdf"))

            except Exception as e:
                logger.error(f"請求書PDFファイル取得エラー: {str(e)}")

        try:
            from app.models.request import RequestAttachment
            attachments = await RequestAttachment.filter(request_id=request_id).all()

            for attachment in attachments:
                try:
                    # S3 URLからkeyを抽出
                    if "amazonaws.com/" in attachment.file_url:
                        s3_key = attachment.file_url.split("amazonaws.com/")[-1].split("?")[0]
                    else:
                        s3_key = attachment.file_url

                    # S3からファイル内容取得
                    file_content = await s3_client.get_file_content(s3_key)
                    if file_content:
                        # ファイル名を推測（URLの最後の部分）
                        filename = s3_key.split("/")[-1]
                        # MIMEタイプを推測
                        content_type = "application/octet-stream"
                        if filename.endswith('.pdf'):
                            content_type = "application/pdf"
                        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                        attachment_files.append((filename, file_content, content_type))

                except Exception as e:
                    logger.error(f"附件ファイル取得エラー ({attachment.id}): {str(e)}")

        except Exception as e:
            logger.error(f"附件リスト取得エラー: {str(e)}")

        # メール送信
        await mail_sender.send_mail_with_attachments(
            mail=request.to,
            attachment_files=attachment_files,
            template_params={
                "subject": request.subject,
                "content": request.content,
                "cc": ",".join(request.cc) if request.cc else "",
                "bcc": ",".join(request.bcc) if request.bcc else "",
            },
        )

        # メール送信成功後、請求書ステータス更新
        if req.status == RequestStatus.DRAFT or req.status == RequestStatus.GENERATED:
            req.status = RequestStatus.SENT
            await req.save()

        return Success(data={"message": "メール送信成功", "attachment_count": len(attachment_files)})
    except Exception as e:
        return Fail(msg=f"メール送信でエラーが発生しました: {str(e)}")


@router.get("/by-client/{client_company_id}", summary="Client会社別請求書一覧")
async def get_requests_by_client(
    client_company_id: int,
    year_month: Optional[str] = Query(None, description="対象年月（YYYY-MM）"),
    status: Optional[RequestStatus] = Query(None, description="ステータス"),
    page: int = Query(1, description="ページ番号"),
    pageSize: int = Query(100, description="ページサイズ"),
):
    """指定Client会社の請求書一覧を取得する"""
    try:
        result = await RequestController.get_requests_list(
            year_month=year_month, client_company_id=client_company_id, status=status, page=page, pageSize=pageSize
        )
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=f"Client会社別請求書一覧取得でエラーが発生しました: {str(e)}")


@router.get("/by-case/{case_id}", summary="案件別請求書一覧")
async def get_requests_by_case(
    case_id: int,
    year_month: Optional[str] = Query(None, description="対象年月（YYYY-MM）"),
    status: Optional[RequestStatus] = Query(None, description="ステータス"),
    page: int = Query(1, description="ページ番号"),
    pageSize: int = Query(100, description="ページサイズ"),
):
    """指定案件の請求書一覧を取得する"""
    try:
        result = await RequestController.get_requests_list(
            year_month=year_month, case_id=case_id, status=status, page=page, pageSize=pageSize
        )
        return Success(data=result["items"], total=result["total"])
    except Exception as e:
        return Fail(msg=f"案件別請求書一覧取得でエラーが発生しました: {str(e)}")


# 附件管理接口
@router.post("/{request_id}/attachments", summary="添加请求书附件")
async def add_request_attachment(
    request_id: int,
    attachment_data: RequestAttachmentCreate
):
    """添加请求书附件记录"""
    try:
        # 验证请求书存在
        request = await RequestController.get_request_by_id(request_id)
        if not request:
            return Fail(msg="請求書が見つかりません")

        # 创建附件记录
        from app.models.request import RequestAttachment
        attachment = await RequestAttachment.create(
            request_id=request_id,
            file_url=attachment_data.file_url,
            attachment_type=attachment_data.attachment_type
        )

        return Success(data={
            "id": attachment.id,
            "file_url": attachment.file_url,
            "attachment_type": attachment.attachment_type
        })
    except Exception as e:
        return Fail(msg=f"附件添加でエラーが発生しました: {str(e)}")


@router.get("/{request_id}/attachments", summary="请求书附件列表")
async def get_request_attachments(request_id: int):
    """获取请求书附件列表"""
    try:
        from app.models.request import RequestAttachment
        attachments = await RequestAttachment.filter(request_id=request_id).all()

        attachment_list = []
        for attachment in attachments:
            attachment_list.append({
                "id": attachment.id,
                "file_url": attachment.file_url,
                "attachment_type": attachment.attachment_type,
                "remark": attachment.remark,
                "created_at": attachment.created_at
            })

        return Success(data=attachment_list)
    except Exception as e:
        return Fail(msg=f"附件列表取得でエラーが発生しました: {str(e)}")


@router.delete("/attachments/{attachment_id}", summary="删除请求书附件")
async def delete_request_attachment(attachment_id: int):
    """删除请求书附件"""
    try:
        from app.models.request import RequestAttachment
        attachment = await RequestAttachment.get_or_none(id=attachment_id)
        if not attachment:
            return Fail(msg="附件が見つかりません")

        # 从S3删除文件
        try:
            if "amazonaws.com/" in attachment.file_url:
                s3_key = attachment.file_url.split("amazonaws.com/")[-1].split("?")[0]
                await s3_client.delete_file(s3_key)
        except Exception as e:
            logger.error(f"S3ファイル削除エラー: {str(e)}")

        # 删除数据库记录
        await attachment.delete()

        return Success(data={"message": "附件を削除しました"})
    except Exception as e:
        return Fail(msg=f"附件削除でエラーが発生しました: {str(e)}")
