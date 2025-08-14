from tortoise import fields

from app.models.base import BaseModel, TimestampMixin


class Skill(BaseModel, TimestampMixin):
    """
    技能字典表 (スキル辞書)
    """

    name = fields.CharField(max_length=100, unique=True, description="技能名称")
    category = fields.CharField(max_length=100, null=True, description="技能分类 (如：编程语言, 数据库, 框架)")

    class Meta:
        table = "ses_skill"
        table_description = "技能字典表"
