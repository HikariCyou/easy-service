from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from app.models.enums import ApproveStatus


class OrderBase(BaseModel):
    """注文書基本スキーマ"""
    year_month: str = Field(..., description="対象年月（YYYY-MM）")
    personnel_id: int = Field(..., description="対象要員ID")
    case_id: int = Field(..., description="案件ID")
    contract_id: int = Field(..., description="契約ID")
    remark: Optional[str] = Field(None, description="備考")

    @validator('year_month')
    def validate_year_month(cls, v):
        """年月フォーマット検証"""
        if not v:
            raise ValueError('年月は必須です')
        
        parts = v.split('-')
        if len(parts) != 2:
            raise ValueError('年月はYYYY-MM形式で入力してください')
        
        try:
            year, month = int(parts[0]), int(parts[1])
            if year < 2020 or year > 2030:
                raise ValueError('年は2020-2030の範囲で入力してください')
            if month < 1 or month > 12:
                raise ValueError('月は1-12の範囲で入力してください')
        except ValueError:
            raise ValueError('年月は有効な数値で入力してください')
        
        return v


class OrderCreate(OrderBase):
    """注文書作成スキーマ"""
    pass


class OrderUpdate(BaseModel):
    """注文書更新スキーマ"""
    remark: Optional[str] = Field(None, description="備考")
    order_document_url: Optional[str] = Field(None, description="注文書PDF URL")
    order_request_url: Optional[str] = Field(None, description="注文請書PDF URL")


class OrderStatusUpdate(BaseModel):
    """注文書ステータス更新スキーマ"""
    status: ApproveStatus = Field(..., description="ステータス")


class ContractDetailsSchema(BaseModel):
    """契約詳細スキーマ"""
    contract_number: str = Field("", description="契約番号")
    contract_start_date: Optional[date] = Field(None, description="契約開始日")
    contract_end_date: Optional[date] = Field(None, description="契約終了日")
    basic_salary: float = Field(0.0, description="基本給")
    standard_working_hours: float = Field(160.0, description="標準稼働時間")
    min_working_hours: Optional[float] = Field(None, description="最低稼働時間")
    max_working_hours: Optional[float] = Field(None, description="最高稼働時間")


class OrderDetail(BaseModel):
    """注文書詳細レスポンススキーマ"""
    id: int
    order_number: str = Field(..., description="注文番号")
    year_month: str = Field(..., description="対象年月")
    year_month_display: str = Field(..., description="年月表示（2024年1月）")
    
    # 関連情報
    bp_company_name: str = Field("", description="BP会社名")
    personnel_name: str = Field("", description="要員名")
    case_title: str = Field("", description="案件名")
    sales_representative_name: str = Field("", description="担当営業名")
    
    # 契約詳細
    contract_details: ContractDetailsSchema
    
    # ステータス情報
    status: ApproveStatus
    is_sent: bool = Field(False, description="送信済みフラグ")
    is_collected: bool = Field(False, description="回収完了フラグ")
    sent_date: Optional[datetime] = Field(None, description="送信日時")
    collected_date: Optional[datetime] = Field(None, description="回収日時")
    
    # 文書情報
    order_document_url: Optional[str] = Field(None, description="注文書PDF URL")
    order_request_url: Optional[str] = Field(None, description="注文請書PDF URL")
    
    # その他
    remark: Optional[str] = Field(None, description="備考")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderListItem(BaseModel):
    """注文書一覧項目スキーマ"""
    id: int
    order_number: str
    year_month: str
    year_month_display: str
    bp_company_name: str
    personnel_name: str
    case_title: str
    sales_representative_name: str
    basic_salary: float
    status: ApproveStatus
    is_sent: bool
    is_collected: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrderBatchBase(BaseModel):
    """注文書バッチ基本スキーマ"""
    year_month: str = Field(..., description="対象年月（YYYY-MM）")
    batch_type: str = Field(..., description="バッチタイプ")
    filter_bp_company_id: Optional[int] = Field(None, description="対象BP会社ID")
    filter_sales_rep_id: Optional[int] = Field(None, description="担当営業ID")
    remark: Optional[str] = Field(None, description="備考")

    @validator('batch_type')
    def validate_batch_type(cls, v):
        """バッチタイプ検証"""
        valid_types = ["all", "by_bp_company", "by_sales_rep"]
        if v not in valid_types:
            raise ValueError(f'バッチタイプは {valid_types} から選択してください')
        return v

    @validator('year_month')
    def validate_year_month(cls, v):
        """年月フォーマット検証"""
        if not v:
            raise ValueError('年月は必須です')
        
        parts = v.split('-')
        if len(parts) != 2:
            raise ValueError('年月はYYYY-MM形式で入力してください')
        
        try:
            year, month = int(parts[0]), int(parts[1])
            if year < 2020 or year > 2030:
                raise ValueError('年は2020-2030の範囲で入力してください')
            if month < 1 or month > 12:
                raise ValueError('月は1-12の範囲で入力してください')
        except ValueError:
            raise ValueError('年月は有効な数値で入力してください')
        
        return v


class OrderBatchCreate(OrderBatchBase):
    """注文書バッチ作成スキーマ"""
    created_by: str = Field(..., description="作成者")


class OrderBatchDetail(BaseModel):
    """注文書バッチ詳細レスポンススキーマ"""
    id: int
    batch_number: str
    year_month: str
    batch_type: str
    filter_bp_company_id: Optional[int]
    filter_sales_rep_id: Optional[int]
    status: ApproveStatus
    total_orders: int
    sent_orders: int
    completion_rate: float
    created_by: str
    processed_date: Optional[datetime]
    processed_by: Optional[str]
    remark: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderBatchListItem(BaseModel):
    """注文書バッチ一覧項目スキーマ"""
    id: int
    batch_number: str
    year_month: str
    batch_type: str
    status: ApproveStatus
    total_orders: int
    sent_orders: int
    completion_rate: float
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrderGenerationRequest(BaseModel):
    """注文書生成リクエストスキーマ"""
    year_month: str = Field(..., description="対象年月（YYYY-MM）")
    bp_company_id: int = Field(..., description="対象BP会社ID")
    personnel_ids: List[int] = Field(..., description="対象要員IDリスト")
    exclude_existing: bool = Field(True, description="既存注文書を除外するか")

    @validator('year_month')
    def validate_year_month(cls, v):
        """年月フォーマット検証"""
        if not v:
            raise ValueError('年月は必須です')
        
        parts = v.split('-')
        if len(parts) != 2:
            raise ValueError('年月はYYYY-MM形式で入力してください')
        
        try:
            year, month = int(parts[0]), int(parts[1])
            if year < 2020 or year > 2030:
                raise ValueError('年は2020-2030の範囲で入力してください')
            if month < 1 or month > 12:
                raise ValueError('月は1-12の範囲で入力してください')
        except ValueError:
            raise ValueError('年月は有効な数値で入力してください')
        
        return v




class OrderSendRequest(BaseModel):
    """注文書送信リクエストスキーマ"""
    order_ids: List[int] = Field(..., description="送信対象注文書IDリスト")
    sent_by: str = Field(..., description="送信者名")

