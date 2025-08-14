from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CreateContract(BaseModel):
    contract_type: str = Field(..., description="契約種別（BP/自社/フリーランス）", examples=["BP", "自社", "フリーランス"])
    case_id: int = Field(..., description="案件ID", examples=[1])
    bp_employee_id: Optional[int] = Field(None, description="BP担当者ID", examples=[1])
    employee_id: Optional[int] = Field(None, description="自社担当者ID", examples=[1])
    freelancer_id: Optional[int] = Field(None, description="フリーランスID", examples=[1])
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


