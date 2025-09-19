from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.models.enums import RequestStatus


class RequestItemCreate(BaseModel):
    """請求書明細項目作成スキーマ"""
    personnel_id: int = Field(..., description="対象要員ID")
    case_id: int = Field(..., description="案件ID")
    contract_id: int = Field(..., description="契約ID")
    item_amount: Decimal = Field(..., description="明細金額（税抜）")
    work_hours: Optional[Decimal] = Field(160.0, description="作業時間")
    unit_price: Decimal = Field(..., description="単価")
    item_remark: Optional[str] = Field(None, description="明細備考")

    @validator("item_amount", "unit_price")
    def validate_amounts(cls, v):
        """金額検証"""
        if v is not None and v < 0:
            raise ValueError("金額は0以上で入力してください")
        return v

    @validator("work_hours")
    def validate_work_hours(cls, v):
        """作業時間検証"""
        if v is not None and v < 0:
            raise ValueError("作業時間は0以上で入力してください")
        return v


class RequestBase(BaseModel):
    """請求書基本スキーマ"""
    year_month: str = Field(..., description="対象年月（YYYY-MM）")
    client_company_id: int = Field(..., description="Client会社ID")
    items: List[RequestItemCreate] = Field(..., description="請求書明細項目リスト")
    tax_rate: Decimal = Field(10.0, description="税率（%）")
    payment_due_date: Optional[date] = Field(None, description="支払期限")
    remark: Optional[str] = Field(None, description="備考")

    @validator("year_month")
    def validate_year_month(cls, v):
        """年月フォーマット検証"""
        if not v:
            raise ValueError("年月は必須です")

        parts = v.split("-")
        if len(parts) != 2:
            raise ValueError("年月はYYYY-MM形式で入力してください")

        try:
            year, month = int(parts[0]), int(parts[1])
            if year < 2020 or year > 2030:
                raise ValueError("年は2020-2030の範囲で入力してください")
            if month < 1 or month > 12:
                raise ValueError("月は1-12の範囲で入力してください")
        except ValueError:
            raise ValueError("年月は有効な数値で入力してください")

        return v

    @validator("tax_rate")
    def validate_tax_rate(cls, v):
        """税率検証"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("税率は0-100の範囲で入力してください")
        return v

    @validator("items")
    def validate_items(cls, v):
        """明細項目検証"""
        if not v:
            raise ValueError("請求書明細項目は最低1つ必要です")
        return v


class RequestCreate(RequestBase):
    """請求書作成スキーマ"""

    pass


class RequestUpdate(BaseModel):
    """請求書更新スキーマ"""

    tax_rate: Optional[Decimal] = Field(None, description="税率（%）")
    payment_due_date: Optional[date] = Field(None, description="支払期限")
    request_document_url: Optional[str] = Field(None, description="請求書PDF URL")
    order_document_url: Optional[str] = Field(None, description="注文書PDF URL")
    remark: Optional[str] = Field(None, description="備考")

    @validator("tax_rate")
    def validate_tax_rate(cls, v):
        """税率検証"""
        if v is not None and (v < 0 or v > 100):
            raise ValueError("税率は0-100の範囲で入力してください")
        return v


class RequestPaymentUpdate(BaseModel):
    """請求書支払い更新スキーマ"""

    payment_amount: Optional[Decimal] = Field(None, description="入金金額")
    payment_received_date: Optional[datetime] = Field(None, description="入金確認日時")

    @validator("payment_amount")
    def validate_payment_amount(cls, v):
        """入金金額検証"""
        if v is not None and v <= 0:
            raise ValueError("入金金額は0より大きい値で入力してください")
        return v


class ContractDetailsSchema(BaseModel):
    """契約詳細スキーマ"""

    contract_number: str = Field("", description="契約番号")
    contract_start_date: Optional[date] = Field(None, description="契約開始日")
    contract_end_date: Optional[date] = Field(None, description="契約終了日")
    standard_working_hours: float = Field(160.0, description="標準稼働時間")
    min_working_hours: Optional[float] = Field(None, description="最低稼働時間")
    max_working_hours: Optional[float] = Field(None, description="最高稼働時間")


class RequestItemDetail(BaseModel):
    """請求書明細項目詳細スキーマ"""

    id: int
    personnel_name: str = Field("", description="要員名")
    case_title: str = Field("", description="案件名")
    item_amount: float = Field(..., description="明細金額（税抜）")
    work_hours: float = Field(..., description="作業時間")
    unit_price: float = Field(..., description="単価")
    item_remark: Optional[str] = Field(None, description="明細備考")

    class Config:
        from_attributes = True


class RequestDetail(BaseModel):
    """請求書詳細レスポンススキーマ"""

    id: int
    request_number: str = Field(..., description="請求番号")
    year_month: str = Field(..., description="対象年月")
    year_month_display: str = Field(..., description="年月表示（2024年1月）")

    # 関連情報
    client_company_name: str = Field("", description="Client会社名")
    client_company_id: Optional[int] = Field(None, description="Client会社ID")

    # 金額詳細（明細の合計）
    request_amount: float = Field(..., description="請求金額（税込）")
    calculation_amount: float = Field(..., description="精算金額")
    tax_excluded_amount: float = Field(..., description="税抜き金額")
    tax_rate: float = Field(..., description="税率（%）")

    # 明細項目
    items: List[RequestItemDetail] = Field([], description="請求書明細項目")

    # ステータス情報
    status: RequestStatus
    is_sent: bool = Field(False, description="送信済みフラグ")
    is_paid: bool = Field(False, description="支払済みフラグ")
    sent_date: Optional[datetime] = Field(None, description="送信日時")
    payment_due_date: Optional[date] = Field(None, description="支払期限")
    payment_received_date: Optional[datetime] = Field(None, description="入金確認日時")
    payment_amount: Optional[float] = Field(None, description="入金金額")

    # 文書情報
    request_document_url: Optional[str] = Field(None, description="請求書PDF URL")
    order_document_url: Optional[str] = Field(None, description="注文書PDF URL")

    # その他
    remark: Optional[str] = Field(None, description="備考")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequestListItem(BaseModel):
    """請求書一覧項目スキーマ"""

    id: int
    request_number: str
    year_month: str
    year_month_display: str
    client_company_name: str
    case_title: str
    sales_representative_name: str
    request_amount: float
    calculation_amount: float
    status: RequestStatus
    is_sent: bool
    is_paid: bool
    payment_due_date: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True


class RequestGenerationRequest(BaseModel):
    """請求書生成リクエストスキーマ"""

    year_month: str = Field(..., description="対象年月（YYYY-MM）")
    client_company_id: int = Field(..., description="対象Client会社ID")
    case_ids: list[int] = Field(..., description="対象案件IDリスト")
    personnel_ids: list[int] = Field(..., description="対象要員IDリスト")
    exclude_existing: bool = Field(True, description="既存請求書を除外するか")

    @validator("year_month")
    def validate_year_month(cls, v):
        """年月フォーマット検証"""
        if not v:
            raise ValueError("年月は必須です")

        parts = v.split("-")
        if len(parts) != 2:
            raise ValueError("年月はYYYY-MM形式で入力してください")

        try:
            year, month = int(parts[0]), int(parts[1])
            if year < 2020 or year > 2030:
                raise ValueError("年は2020-2030の範囲で入力してください")
            if month < 1 or month > 12:
                raise ValueError("月は1-12の範囲で入力してください")
        except ValueError:
            raise ValueError("年月は有効な数値で入力してください")

        return v


class RequestSendRequest(BaseModel):
    """請求書送信リクエストスキーマ"""

    request_ids: list[int] = Field(..., description="送信対象請求書IDリスト")
    sent_by: str = Field(..., description="送信者名")


class FileUploadRequest(BaseModel):
    """ファイルアップロードリクエストスキーマ"""

    file_type: str = Field(..., description="ファイルタイプ (order_document/request_document)")

    @validator("file_type")
    def validate_file_type(cls, v):
        """ファイルタイプ検証"""
        valid_types = ["order_document", "request_document"]
        if v not in valid_types:
            raise ValueError(f"ファイルタイプは {valid_types} から選択してください")
        return v
