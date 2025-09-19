from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import BusinessClassification, ContractCompanyType


class CaseTerminationSchema(BaseModel):
    """案件終了リクエスト"""

    case_id: int = Field(..., description="案件ID")
    termination_date: Optional[date] = Field(None, description="終了日（未指定の場合は今日）")
    reason: Optional[str] = Field("案件終了", description="終了理由")
    terminated_by: Optional[str] = Field(None, description="終了実行者")


class AddCaseSchema(BaseModel):
    title: str = Field(..., description="案件タイトル")
    client_company_id: int = Field(..., description="取引先会社ID")
    client_sales_representative_id: Optional[int] = Field(None, description="取引先担当営業ID")
    company_sales_representative_id: Optional[int] = Field(None, description="自社担当営業ID")
    location: Optional[str] = Field(None, description="勤務地")
    station: Optional[str] = Field(None, description="最寄駅")
    start_date: Optional[date] = Field(None, description="開始日")
    end_date: Optional[date] = Field(None, description="終了日")
    required_skills: Optional[str] = Field(None, description="必要スキル")
    preferred_skills: Optional[str] = Field(None, description="歓迎スキル")
    unit_price: Optional[Decimal] = Field(None, description="単価（月額）")
    required_members: int = Field(1, description="必要人数")
    status: Optional[str] = Field("open", description="ステータス")
    manager: Optional[int] = Field(None, description="案件マネージャーID")
    description: Optional[str] = Field(None, description="詳細・備考")
    contract_company_type: Optional[ContractCompanyType] = Field(None, description="契約会社種別")
    business_classification: Optional[BusinessClassification] = Field(None, description="事業分類")
    department: Optional[str] = Field(None, description="所属部署")


class UpdateCaseSchema(BaseModel):
    id: int = Field(..., description="案件ID")
    title: Optional[str] = Field(None, description="案件タイトル")
    client_company_id: Optional[int] = Field(None, description="取引先会社ID")
    client_sales_representative_id: Optional[int] = Field(None, description="取引先担当営業ID")
    company_sales_representative_id: Optional[int] = Field(None, description="自社担当営業ID")
    location: Optional[str] = Field(None, description="勤務地")
    station: Optional[str] = Field(None, description="最寄駅")
    start_date: Optional[date] = Field(None, description="開始日")
    end_date: Optional[date] = Field(None, description="終了日")
    required_skills: Optional[str] = Field(None, description="必要スキル")
    preferred_skills: Optional[str] = Field(None, description="歓迎スキル")
    unit_price: Optional[Decimal] = Field(None, description="単価（月額）")
    required_members: Optional[int] = Field(None, description="必要人数")
    status: Optional[str] = Field(None, description="ステータス")
    manager: Optional[int] = Field(None, description="案件マネージャーID")
    description: Optional[str] = Field(None, description="詳細・備考")
    contract_company_type: Optional[ContractCompanyType] = Field(None, description="契約会社種別")
    business_classification: Optional[BusinessClassification] = Field(None, description="事業分類")
    department: Optional[str] = Field(None, description="所属部署")


class AddCaseCandidateSchema(BaseModel):
    case_id: int = Field(..., description="案件ID")
    bp_employee_id: Optional[int] = Field(None, description="BP社員ID")
    employee_id: Optional[int] = Field(None, description="自社社員ID")
    freelancer_id: Optional[int] = Field(None, description="フリーランスID")
    recommend_date: Optional[date] = Field(None, description="推薦日")
    interview_date: Optional[datetime] = Field(None, description="面談日時")
    decision_date: Optional[date] = Field(None, description="決定日")
    status: Optional[str] = Field("pending", description="状態")
    proposed_unit_price: Optional[Decimal] = Field(None, description="提案単価")
    contract_start_date: Optional[date] = Field(None, description="契約開始日")
    contract_end_date: Optional[date] = Field(None, description="契約終了日")
    remark: Optional[str] = Field(None, description="備考")


class UpdateCaseCandidateSchema(BaseModel):
    id: int = Field(..., description="候補者ID")
    case_id: Optional[int] = Field(None, description="案件ID")
    bp_employee_id: Optional[int] = Field(None, description="BP社員ID")
    employee_id: Optional[int] = Field(None, description="自社社員ID")
    freelancer_id: Optional[int] = Field(None, description="フリーランスID")
    recommend_date: Optional[date] = Field(None, description="推薦日")
    interview_date: Optional[datetime] = Field(None, description="面談日時")
    decision_date: Optional[date] = Field(None, description="決定日")
    status: Optional[str] = Field(None, description="状態")
    proposed_unit_price: Optional[Decimal] = Field(None, description="提案単価")
    contract_start_date: Optional[date] = Field(None, description="契約開始日")
    contract_end_date: Optional[date] = Field(None, description="契約終了日")
    remark: Optional[str] = Field(None, description="備考")


class CaseHistorySchema(BaseModel):
    """案件変更履歴Schema"""

    id: int = Field(..., description="履歴ID")
    case_id: int = Field(..., description="案件ID")
    change_type: str = Field(..., description="変更タイプ")

    # 変更者情報
    changed_by: int = Field(..., description="変更者ユーザーID")
    changed_by_name: Optional[str] = Field(None, description="変更者名")

    # 変更内容
    field_name: Optional[str] = Field(None, description="変更フィールド名")
    old_value: Optional[str] = Field(None, description="変更前の値")
    new_value: Optional[str] = Field(None, description="変更後の値")

    # 変更詳細
    change_details: Optional[Dict[str, Any]] = Field(None, description="変更詳細（JSON）")

    # 変更理由・コメント
    comment: Optional[str] = Field(None, description="変更理由・コメント")

    # IP アドレス
    ip_address: Optional[str] = Field(None, description="変更者IPアドレス")

    # タイムスタンプ
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class CreateCaseHistorySchema(BaseModel):
    """案件変更履歴作成Schema"""

    case_id: int = Field(..., description="案件ID")
    change_type: str = Field(..., description="変更タイプ")
    changed_by: int = Field(..., description="変更者ユーザーID")
    changed_by_name: Optional[str] = Field(None, description="変更者名")
    field_name: Optional[str] = Field(None, description="変更フィールド名")
    old_value: Optional[str] = Field(None, description="変更前の値")
    new_value: Optional[str] = Field(None, description="変更後の値")
    change_details: Optional[Dict[str, Any]] = Field(None, description="変更詳細（JSON）")
    comment: Optional[str] = Field(None, description="変更理由・コメント")
    ip_address: Optional[str] = Field(None, description="変更者IPアドレス")


class CaseHistorySearchSchema(BaseModel):
    """案件変更履歴検索Schema"""

    case_id: Optional[int] = Field(None, description="案件ID")
    change_type: Optional[str] = Field(None, description="変更タイプ")
    changed_by: Optional[int] = Field(None, description="変更者ユーザーID")
    field_name: Optional[str] = Field(None, description="変更フィールド名")
    start_date: Optional[date] = Field(None, description="検索開始日")
    end_date: Optional[date] = Field(None, description="検索終了日")


class CaseHistoryStatsSchema(BaseModel):
    """案件変更履歴統計Schema"""

    total_changes: int = Field(..., description="総変更数")
    change_type_counts: Dict[str, int] = Field(..., description="変更タイプ別件数")
    most_changed_cases: List[Dict[str, Any]] = Field(..., description="変更回数の多い案件Top10")
    most_active_users: List[Dict[str, Any]] = Field(..., description="変更回数の多いユーザーTop10")
    recent_changes: List[Dict[str, Any]] = Field(..., description="最近の変更履歴")
    period: str = Field(..., description="統計期間")
