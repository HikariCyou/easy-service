from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class AddSkillSchema(BaseModel):
    name: str = Field(None, description="スキル名")
    category: Optional[str] = Field(None, description="スキルカテゴリ")


class UpdateSkillSchema(AddSkillSchema):
    id: int = Field(None, description="スキルID")


class AddBPEmployeeSkillSchema(BaseModel):
    employee_id: int = Field(None, description="協力会社要員のID")
    skill_name: str = Field(None, description="スキル名")
    category: Optional[str] = Field(None, description="スキルカテゴリ")
    proficiency: Optional[int] = Field(None, description="スキルの熟練度")
    years_of_experience: Optional[float] = Field(None, description="経験年数")
    last_used_date: Optional[date] = Field(None, description="最終使用日")
    is_primary_skill: Optional[bool] = Field(None, description="主なスキルかどうか")
    remark: Optional[str] = Field(None, description="備考")


class UpdateBPEmployeeSkillSchema(AddBPEmployeeSkillSchema):
    id: int = Field(None, description="スキルID")
