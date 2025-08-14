from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class AddSkillSchema(BaseModel):
    name: str = Field(None, description="スキル名", examples="Java")
    category: Optional[str] = Field(None, description="スキルカテゴリ", examples="プログラミング")


class UpdateSkillSchema(AddSkillSchema):
    id: int = Field(None, description="スキルID", examples="1")


class AddBPEmployeeSkillSchema(BaseModel):
    employee_id: int = Field(None, description="協力会社要員のID", examples="テスト太郎")
    skill_name: str = Field(None, description="スキル名", examples="Java")
    category: Optional[str] = Field(None, description="スキルカテゴリ", examples="プログラミング")
    proficiency: Optional[int] = Field(None, description="スキルの熟練度", examples="3")
    years_of_experience: Optional[float] = Field(None, description="経験年数", examples="3.5")
    last_used_date: Optional[date] = Field(None, description="最終使用日", examples="2023-01-01")
    is_primary_skill: Optional[bool] = Field(None, description="主なスキルかどうか", examples=True)
    remark: Optional[str] = Field(None, description="備考", examples="テスト用")


class UpdateBPEmployeeSkillSchema(AddBPEmployeeSkillSchema):
    id: int = Field(None, description="スキルID", examples="1")
