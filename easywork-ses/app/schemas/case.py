from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class AddCaseSchema(BaseModel):
    title: str = Field(..., description="案件タイトル", examples=["Webアプリケーション開発"])
    client_company_id: int = Field(..., description="取引先会社ID")
    location: Optional[str] = Field(None, description="勤務地", examples=["東京都港区"])
    station: Optional[str] = Field(None, description="最寄駅", examples=["品川駅"])
    start_date: Optional[date] = Field(None, description="開始日", examples=["2024-04-01"])
    end_date: Optional[date] = Field(None, description="終了日", examples=["2024-12-31"])
    required_skills: Optional[str] = Field(None, description="必要スキル", examples=["Java, Spring Boot, MySQL"])
    preferred_skills: Optional[str] = Field(None, description="歓迎スキル", examples=["AWS, Docker"])
    unit_price: Optional[Decimal] = Field(None, description="単価（月額）", examples=[800000])
    required_members: int = Field(1, description="必要人数", examples=[2])
    status: Optional[str] = Field("open", description="ステータス", examples=["open"])
    manager: Optional[int] = Field(None, description="案件マネージャーID")
    description: Optional[str] = Field(None, description="詳細・備考", examples=["新規Webサービス開発プロジェクト"])


class UpdateCaseSchema(BaseModel):
    id: int = Field(..., description="案件ID")
    title: Optional[str] = Field(None, description="案件タイトル", examples=["Webアプリケーション開発"])
    client_company_id: Optional[int] = Field(None, description="取引先会社ID")
    location: Optional[str] = Field(None, description="勤務地", examples=["東京都港区"])
    station: Optional[str] = Field(None, description="最寄駅", examples=["品川駅"])
    start_date: Optional[date] = Field(None, description="開始日", examples=["2024-04-01"])
    end_date: Optional[date] = Field(None, description="終了日", examples=["2024-12-31"])
    required_skills: Optional[str] = Field(None, description="必要スキル", examples=["Java, Spring Boot, MySQL"])
    preferred_skills: Optional[str] = Field(None, description="歓迎スキル", examples=["AWS, Docker"])
    unit_price: Optional[Decimal] = Field(None, description="単価（月額）", examples=[800000])
    required_members: Optional[int] = Field(None, description="必要人数", examples=[2])
    status: Optional[str] = Field(None, description="ステータス", examples=["open"])
    manager: Optional[int] = Field(None, description="案件マネージャーID")
    description: Optional[str] = Field(None, description="詳細・備考", examples=["新規Webサービス開発プロジェクト"])


class AddCaseCandidateSchema(BaseModel):
    case_id: int = Field(..., description="案件ID")
    bp_employee_id: Optional[int] = Field(None, description="BP社員ID")
    employee_id: Optional[int] = Field(None, description="自社社員ID")
    freelancer_id: Optional[int] = Field(None, description="フリーランスID")
    recommend_date: Optional[date] = Field(None, description="推薦日", examples=["2024-01-15"])
    interview_date: Optional[datetime] = Field(None, description="面談日時", examples=["2024-01-20T14:00:00"])
    decision_date: Optional[date] = Field(None, description="決定日", examples=["2024-01-25"])
    status: Optional[str] = Field("pending", description="状態", examples=["pending"])
    proposed_unit_price: Optional[Decimal] = Field(None, description="提案単価", examples=[750000])
    contract_start_date: Optional[date] = Field(None, description="契約開始日", examples=["2024-02-01"])
    contract_end_date: Optional[date] = Field(None, description="契約終了日", examples=["2024-12-31"])
    remark: Optional[str] = Field(None, description="備考", examples=["面談後フォローアップ要"])


class UpdateCaseCandidateSchema(BaseModel):
    id: int = Field(..., description="候補者ID")
    case_id: Optional[int] = Field(None, description="案件ID")
    bp_employee_id: Optional[int] = Field(None, description="BP社員ID")
    employee_id: Optional[int] = Field(None, description="自社社員ID")
    freelancer_id: Optional[int] = Field(None, description="フリーランスID")
    recommend_date: Optional[date] = Field(None, description="推薦日", examples=["2024-01-15"])
    interview_date: Optional[datetime] = Field(None, description="面談日時", examples=["2024-01-20T14:00:00"])
    decision_date: Optional[date] = Field(None, description="決定日", examples=["2024-01-25"])
    status: Optional[str] = Field(None, description="状態", examples=["pending"])
    proposed_unit_price: Optional[Decimal] = Field(None, description="提案単価", examples=[750000])
    contract_start_date: Optional[date] = Field(None, description="契約開始日", examples=["2024-02-01"])
    contract_end_date: Optional[date] = Field(None, description="契約終了日", examples=["2024-12-31"])
    remark: Optional[str] = Field(None, description="備考", examples=["面談後フォローアップ要"])
