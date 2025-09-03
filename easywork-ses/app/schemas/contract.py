from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class CreateContract(BaseModel):
    contract_type: str = Field(..., description="契約種別（BP/自社/フリーランス）", examples=["BP", "自社", "フリーランス"])
    case_id: int = Field(..., description="案件ID", examples=[1])
    personnel_id: int = Field(..., description="要員ID（統一Personnel）", examples=[1])
    contract_start_date: Optional[date] = Field(None, description="契約開始日", examples=["2022-01-01"])
    contract_end_date: Optional[date] = Field(None, description="契約終了日", examples=["2022-12-31"])
    unit_price: Optional[float] = Field(None, description="単価", examples=["10000"])
    standard_working_hours: Optional[float] = Field(None, description="標準労働時間", examples=["8"])
    min_working_hours: Optional[float] = Field(None, description="最低労働時間", examples=["4"])
    max_working_hours: Optional[float] = Field(None, description="最高労働時間", examples=["12"])
    overtime_rate: Optional[float] = Field(None, description="残業率", examples=["1.5"])
    shortage_rate: Optional[float] = Field(None, description="不足率", examples=["1.5"])
    min_guaranteed_hours: Optional[float] = Field(None, description="最低保証時間", examples=["4"])
    free_overtime_hours: Optional[float] = Field(None, description="フリーオーバータイム時間", examples=["2"])
    status: Optional[str] = Field(None, description="契約ステータス", examples=["契約中", "契約解除"])
    remark: Optional[str] = Field(None, description="備考", examples=["契約内容の詳細"])


class UpdateContract(CreateContract):
    id: int = Field(..., description="契約ID", examples=[1])


# 契約変更関連のSchemas
class ContractChangeRequest(BaseModel):
    """契約変更申請"""
    contract_id: int = Field(..., description="対象契約ID", examples=[1])
    change_type: str = Field(..., description="変更種別", 
                           examples=["契約更新", "早期解約", "条件変更", "期間延長", "期間短縮"])
    change_reason: Optional[str] = Field(None, description="変更理由",
                                       examples=["クライアント要望", "人材要望", "プロジェクト変更"])
    effective_date: Optional[date] = Field(None, description="変更効力発生日")
    description: Optional[str] = Field(None, description="変更内容の詳細説明")
    requested_by: Optional[str] = Field(None, description="変更申請者")


class EarlyTerminationRequest(BaseModel):
    """早期解約申請"""
    contract_id: int = Field(..., description="対象契約ID", examples=[1])
    termination_date: date = Field(..., description="解約日", examples=["2024-01-31"])
    reason: str = Field(..., description="解約理由", 
                       examples=["クライアント要望", "パフォーマンス問題", "プロジェクト変更"])
    description: Optional[str] = Field(None, description="解約理由の詳細")
    requested_by: Optional[str] = Field(None, description="解約申請者")


class ContractConditionUpdate(BaseModel):
    """契約条件変更"""
    contract_id: int = Field(..., description="対象契約ID", examples=[1])
    new_unit_price: Optional[Decimal] = Field(None, description="新単価", examples=[650000])
    new_working_hours: Optional[Decimal] = Field(None, description="新標準稼働時間", examples=[180.0])
    new_contract_end_date: Optional[date] = Field(None, description="新契約終了日")
    reason: str = Field(default="クライアント要望", description="変更理由")
    effective_date: Optional[date] = Field(None, description="変更効力発生日")
    requested_by: Optional[str] = Field(None, description="変更申請者")
    description: Optional[str] = Field(None, description="変更内容の詳細")


class ContractAmendmentCreate(BaseModel):
    """契約修正書作成"""
    original_contract_id: int = Field(..., description="元契約ID", examples=[1])
    amendment_title: str = Field(..., description="修正書タイトル", 
                                examples=["単価変更に関する修正契約書"])
    amendment_type: str = Field(..., description="修正種別", examples=["条件変更"])
    amendment_reason: str = Field(..., description="修正理由", examples=["クライアント要望"])
    amendment_details: str = Field(..., description="修正内容詳細")
    
    effective_start_date: date = Field(..., description="修正効力開始日")
    effective_end_date: Optional[date] = Field(None, description="修正効力終了日")
    
    # 修正後の契約条件
    new_unit_price: Optional[Decimal] = Field(None, description="修正後単価")
    new_contract_end_date: Optional[date] = Field(None, description="修正後契約終了日")
    new_working_hours: Optional[Decimal] = Field(None, description="修正後標準稼働時間")


class ContractAmendmentApproval(BaseModel):
    """契約修正書承認"""
    amendment_id: int = Field(..., description="修正書ID", examples=[1])
    approval_type: str = Field(..., description="承認種別", 
                              examples=["client", "company", "personnel"])
    signature: str = Field(..., description="署名者", examples=["田中太郎"])
    comment: Optional[str] = Field(None, description="承認コメント")


class ContractHistoryResponse(BaseModel):
    """契約変更履歴レスポンス"""
    id: int = Field(..., description="履歴ID")
    contract_id: int = Field(..., description="契約ID")
    change_type: str = Field(..., description="変更種別")
    change_reason: Optional[str] = Field(None, description="変更理由")
    before_values: Optional[Dict[str, Any]] = Field(None, description="変更前の値")
    after_values: Optional[Dict[str, Any]] = Field(None, description="変更後の値")
    change_description: Optional[str] = Field(None, description="変更内容説明")
    effective_date: Optional[date] = Field(None, description="効力発生日")
    requested_by: Optional[str] = Field(None, description="申請者")
    approved_by: Optional[str] = Field(None, description="承認者")
    approval_date: Optional[datetime] = Field(None, description="承認日時")
    created_at: datetime = Field(..., description="作成日時")


class ContractAmendmentResponse(BaseModel):
    """契約修正書レスポンス"""
    id: int = Field(..., description="修正書ID")
    original_contract_id: int = Field(..., description="元契約ID")
    amendment_number: str = Field(..., description="修正書番号")
    amendment_title: str = Field(..., description="修正書タイトル")
    amendment_type: str = Field(..., description="修正種別")
    amendment_reason: str = Field(..., description="修正理由")
    effective_start_date: date = Field(..., description="効力開始日")
    effective_end_date: Optional[date] = Field(None, description="効力終了日")
    status: str = Field(..., description="ステータス")
    client_approved: bool = Field(..., description="クライアント承認")
    company_approved: bool = Field(..., description="自社承認")
    personnel_acknowledged: bool = Field(..., description="人材確認")
    created_at: datetime = Field(..., description="作成日時")


