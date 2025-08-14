from app.models import Skill
from app.schemas.skill import AddSkillSchema, UpdateSkillSchema


class SkillController:
    async def add_skill(self, skill_data: AddSkillSchema):
        pass

    async def update_skill(self, skill_data: UpdateSkillSchema):
        pass

    async def delete_skill(self, skill_data_id: int):
        pass

    async def get_skills(self, page: int = 1, page_size: int = 10):
        query = Skill.filter()
        total = await query.count()
        skills = await query.limit(page_size).offset((page - 1) * page_size).all()
        return skills, total


skill_controller = SkillController()
