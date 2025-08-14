from typing import Optional

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.bp import BPCompany, BPEmployee, BPEmployeeSkill
from app.models.skill import Skill
from app.schemas.bp import (AddBPCompanySchema, UpdateBPCompanySchema, UpdateBPEmployeeSchema)
from app.schemas.skill import AddBPEmployeeSkillSchema, UpdateSkillSchema
from app.utils.common import clean_dict


class BPCompanyController:

    async def get_bp_companies(
        self, page: Optional[int] = 1, page_size: Optional[int] = 10, search: Q = None, order: list = []
    ):
        query = BPCompany.filter(search)

        total = await query.count()
        bp_companies = await query.order_by(*order).limit(page_size).offset((page - 1) * page_size).all()
        return bp_companies, total

    async def get_bp_companies_with_filters(
        self,
        page: Optional[int] = 1,
        page_size: Optional[int] = 10,
        name: Optional[str] = None,
        representative: Optional[str] = None,
        status: Optional[str] = None,
    ):
        q = Q()
        if name:
            q &= Q(name__icontains=name)
        if representative:
            q &= Q(representative__icontains=representative)
        if status:
            q &= Q(status=status)

        companies, total = await self.get_bp_companies(page=page, page_size=page_size, search=q)
        data = [await company.to_dict() for company in companies]
        return data, total

    async def get_bp_company_by_id(self, bp_company_id: int):
        bp_company = await BPCompany.get_or_none(id=bp_company_id)
        return bp_company

    async def get_bp_company_dict_by_id(self, bp_company_id: int):
        company = await self.get_bp_company_by_id(bp_company_id)
        if company:
            return await company.to_dict()
        return None

    async def create_bp_company(self, bp_company: AddBPCompanySchema):
        async with in_transaction():
            data_dict = clean_dict(bp_company.model_dump(exclude_unset=True))
            bp_company = await BPCompany.create(**data_dict)
            return bp_company

    async def create_bp_company_dict(self, bp_company: AddBPCompanySchema):
        company = await self.create_bp_company(bp_company)
        return await company.to_dict()

    async def update_bp_company(self, bp_company: UpdateBPCompanySchema):
        company = await BPCompany.get_or_none(id=bp_company.id)
        if company:
            async with in_transaction():
                data_dict = bp_company.model_dump(exclude_unset=True)
                await company.update_from_dict(data_dict)
                await company.save()
        return company

    async def update_bp_company_dict(self, bp_company: UpdateBPCompanySchema):
        company = await self.update_bp_company(bp_company)
        if company:
            return await company.to_dict()
        return None

    async def delete_bp_company(self, bp_company_id: int):
        bp_company = await BPCompany.get_or_none(id=bp_company_id)
        if bp_company:
            async with in_transaction():
                await bp_company.delete()
        return bp_company


class BPEmployeeController:
    def __init__(self):
        pass

    async def list_bp_employees(self, page: int = 1, page_size: int = 10, search: Q = None, order: list = []):
        query = BPEmployee.filter(search)

        total = await query.count()
        employees = await query.order_by(*order).limit(page_size).offset((page - 1) * page_size).all()
        return employees, total

    async def list_bp_employees_with_filters(self, page: int = 1, page_size: int = 10, name: Optional[str] = None):
        q = Q()
        if name:
            q &= Q(name__icontains=name)

        employees, total = await self.list_bp_employees(page=page, page_size=page_size, search=q)
        data = [await employee.to_dict() for employee in employees]
        return data, total

    async def get_bp_employee_by_id(self, bp_employee_id: int):
        employee = await BPEmployee.get_or_none(id=bp_employee_id)
        return employee

    async def get_bp_employee_dict_by_id(self, bp_employee_id: int):
        employee = await self.get_bp_employee_by_id(bp_employee_id)
        if employee:
            return await employee.to_dict()
        return None

    async def add_bp_employee(self, bp_employee: UpdateBPEmployeeSchema):
        bp_employee_id = bp_employee.id
        async with in_transaction():
            if bp_employee_id:
                employee = await BPEmployee.get_or_none(id=bp_employee_id)
                if employee:
                    data_dict = clean_dict(bp_employee.model_dump(exclude_unset=True))
                    await employee.update_from_dict(data_dict)
                    await employee.save()
                    return employee
            else:
                data_dict = clean_dict(bp_employee.model_dump(exclude_unset=True))
                employee = await BPEmployee.create(**data_dict)
                return employee

    async def add_bp_employee_dict(self, bp_employee: UpdateBPEmployeeSchema):
        employee = await self.add_bp_employee(bp_employee)
        if employee:
            return await employee.to_dict()
        return None

    async def update_bp_employee(self, bp_employee: UpdateBPEmployeeSchema):
        bp_employee_id = bp_employee.id
        async with in_transaction():
            if bp_employee_id:
                employee = await BPEmployee.get_or_none(id=bp_employee_id)
                if employee:
                    data_dict = clean_dict(bp_employee.model_dump(exclude_unset=True))
                    await employee.update_from_dict(data_dict)
                    await employee.save()
                    return employee

    async def update_bp_employee_dict(self, bp_employee: UpdateBPEmployeeSchema):
        employee = await self.update_bp_employee(bp_employee)
        if employee:
            return await employee.to_dict()
        return None

    async def delete_bp_employee(self, bp_employee_id: int):
        bp_employee = await BPEmployee.get_or_none(id=bp_employee_id)
        if bp_employee:
            async with in_transaction():
                await bp_employee.delete()
        return bp_employee

    async def get_skills(self, employee: BPEmployee, page: int = 1, pageSize: int = 10):
        """获取BP员工技能列表"""
        query = BPEmployeeSkill.filter(bp_employee=employee).select_related("skill")

        total = await query.count()
        skills = (
            await query.order_by("-is_primary_skill", "-proficiency", "-years_of_experience")
            .limit(pageSize)
            .offset((page - 1) * pageSize)
            .all()
        )
        return skills, total

    async def get_skills_with_details(self, employee_id: int, page: int = 1, pageSize: int = 10):
        """获取BP员工技能列表（包含技能名称和分类信息）"""
        employee = await self.get_bp_employee_by_id(employee_id)
        if not employee:
            return None, 0

        skills, total = await self.get_skills(employee=employee, page=page, pageSize=pageSize)
        data = []
        for skill in skills:
            skill_dict = await skill.to_dict()
            skill_obj = await skill.skill
            skill_dict["skill_name"] = skill_obj.name
            skill_dict["category"] = skill_obj.category
            data.append(skill_dict)
        return data, total

    async def add_skill(self, bp_employee: BPEmployee, skill: Skill, skill_data: AddBPEmployeeSkillSchema):
        employee_skill = await BPEmployeeSkill.create(
            bp_employee=bp_employee,
            skill=skill,
            proficiency=skill_data.proficiency,
            years_of_experience=skill_data.years_of_experience,
            is_primary_skill=skill_data.is_primary_skill,
            last_used_date=skill_data.last_used_date,
            remark=skill_data.remark,
        )
        return employee_skill

    async def add_skill_with_validation(self, skill_data):
        """添加技能（包含完整的验证和创建逻辑）"""

        employee = await self.get_bp_employee_by_id(skill_data.employee_id)
        if not employee:
            return None, "要員が見つかりません"

        # 查找或创建技能
        skill, created = await Skill.get_or_create(
            name=skill_data.skill_name, defaults={"category": skill_data.category}
        )

        # 检查是否已存在该技能关联
        existing = await BPEmployeeSkill.get_or_none(bp_employee=employee, skill=skill)
        if existing:
            return None, f"要員は既にスキル「{skill_data.skill_name}」を持っています"

        # 创建技能关联
        employee_skill = await self.add_skill(bp_employee=employee, skill=skill, skill_data=skill_data)

        skill_dict = await employee_skill.to_dict()
        skill_dict["skill_name"] = skill.name
        skill_dict["category"] = skill.category

        return skill_dict, None

    async def get_skill_by_id(self, skill_id: int):
        """根据ID获取技能记录（包含技能名称和分类信息）"""
        skill = await BPEmployeeSkill.get_or_none(id=skill_id).select_related("skill", "bp_employee")
        if not skill:
            return None

        skill_dict = await skill.to_dict()
        skill_obj = await skill.skill
        skill_dict["skill_name"] = skill_obj.name
        skill_dict["category"] = skill_obj.category
        return skill_dict

    async def update_skill(self, skill_data: UpdateSkillSchema):
        """更新技能记录"""

        employee_skill = await BPEmployeeSkill.get_or_none(id=skill_data.id)
        if not employee_skill:
            return None, "スキル記録が見つかりません"

        # 更新技能信息
        if skill_data.skill_name:
            skill, created = await Skill.get_or_create(
                name=skill_data.skill_name, defaults={"category": skill_data.category}
            )
            employee_skill.skill = skill

        # 更新其他字段
        if skill_data.proficiency is not None:
            employee_skill.proficiency = skill_data.proficiency
        if skill_data.years_of_experience is not None:
            employee_skill.years_of_experience = skill_data.years_of_experience
        if skill_data.is_primary_skill is not None:
            employee_skill.is_primary_skill = skill_data.is_primary_skill
        if skill_data.last_used_date:
            try:
                employee_skill.last_used_date = skill_data.last_used_date
            except ValueError:
                return None, "日付の形式が正しくありません (YYYY-MM-DD)"
        if skill_data.remark is not None:
            employee_skill.remark = skill_data.remark

        await employee_skill.save()
        skill_dict = await employee_skill.to_dict()
        skill_obj = await employee_skill.skill
        skill_dict["skill_name"] = skill_obj.name
        skill_dict["category"] = skill_obj.category

        return skill_dict, None

    async def delete_skill(self, skill_id: int):
        """删除技能记录"""
        employee_skill = await BPEmployeeSkill.get_or_none(id=skill_id)
        if not employee_skill:
            return False, "スキル記録が見つかりません"

        await employee_skill.delete()
        return True, None


bp_controller = BPCompanyController()
bp_employee_controller = BPEmployeeController()
