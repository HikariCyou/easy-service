from typing import List
from datetime import date, datetime
from decimal import Decimal

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.employee import Employee, EmployeeSkill, EmployeeEvaluation
from app.models.skill import Skill
from app.utils.common import clean_dict


class EmployeeController:
    """自社員工控制器"""

    def __init__(self):
        pass

    async def list_employees(self, page: int = 1, page_size: int = 10, search: Q = None, order: list = [], 
                           include_skills: bool = False):
        """获取员工列表"""
        if search is None:
            search = Q()
            
        query = Employee.filter(search)
        if include_skills:
            query = query.prefetch_related('skills__skill')

        total = await query.count()
        employees = await query.order_by(*order).limit(page_size).offset((page - 1) * page_size).all()
        return employees, total

    async def search_employees(self, search_params: dict, page: int = 1, page_size: int = 10):
        """高级员工搜索"""
        query = Q()
        
        # 基本信息搜索
        if search_params.get('name'):
            query &= Q(name__icontains=search_params['name'])
        if search_params.get('code'):
            query &= Q(code__icontains=search_params['code'])
        if search_params.get('employment_status'):
            query &= Q(employment_status=search_params['employment_status'])
        if search_params.get('nationality'):
            query &= Q(nationality__icontains=search_params['nationality'])
            
        # 日期范围搜索
        if search_params.get('available_from'):
            query &= Q(available_start_date__gte=search_params['available_from'])
        if search_params.get('available_to'):
            query &= Q(available_start_date__lte=search_params['available_to'])
            
        # 经验年数搜索
        if search_params.get('min_experience_years'):
            query &= Q(it_experience_years__gte=search_params['min_experience_years'])
        
        # 技能搜索
        if search_params.get('skill_name'):
            query &= Q(skills__skill__name__icontains=search_params['skill_name'])
            
        return await self.list_employees(page, page_size, query, ['-updated_at'], include_skills=True)

    async def get_employee_by_id(self, employee_id: int, include_relations: bool = False):
        """根据ID获取员工"""
        query = Employee.filter(id=employee_id)
        if include_relations:
            query = query.prefetch_related('skills__skill', 'contracts', 'evaluations')
        employee = await query.first()
        return employee

    async def get_employee_by_user_id(self, user_id: int, include_relations: bool = False):
        """根据用户ID获取员工"""
        query = Employee.filter(user_id=user_id)
        if include_relations:
            query = query.prefetch_related('skills__skill', 'contracts', 'evaluations')
        employee = await query.first()
        return employee

    async def create_employee(self, employee_data: dict):
        """创建员工"""
        async with in_transaction():
            employee = await Employee.create(**employee_data)
            return employee

    async def update_employee(self, employee_id: int, employee_data: dict):
        """更新员工信息"""
        employee = await Employee.get_or_none(id=employee_id)
        if employee:
            async with in_transaction():
                data_dict = clean_dict(employee_data)
                await employee.update_from_dict(data_dict)
                await employee.save()
        return employee

    async def delete_employee(self, employee_id: int):
        """删除员工"""
        employee = await Employee.get_or_none(id=employee_id)
        if employee:
            async with in_transaction():
                await employee.delete()
        return employee

    async def get_employee_skills(self, employee: Employee, page: int = 1, page_size: int = 10):
        """获取员工技能列表"""
        query = EmployeeSkill.filter(employee=employee).select_related("skill")

        total = await query.count()
        skills = (
            await query.order_by("-is_primary_skill", "-proficiency", "-years_of_experience")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )
        return skills, total

    async def get_employee_skill_by_id(self, skill_id: int):
        """根据ID获取员工技能"""
        skill = await EmployeeSkill.get_or_none(id=skill_id).select_related("skill", "employee")
        return skill

    async def add_employee_skill(self, employee: Employee, skill_data: dict):
        """添加员工技能"""
        skill_name = skill_data.get("skill_name")
        category = skill_data.get("category")

        if not skill_name:
            raise ValueError("技能名称不能为空")

        async with in_transaction():
            # 查找或创建技能
            skill, created = await Skill.get_or_create(name=skill_name, defaults={"category": category})

            # 检查是否已存在该技能关联
            existing = await EmployeeSkill.get_or_none(employee=employee, skill=skill)
            if existing:
                raise ValueError(f"员工已拥有技能: {skill_name}")

            # 创建员工技能关联
            employee_skill = await EmployeeSkill.create(
                employee=employee,
                skill=skill,
                proficiency=skill_data.get("proficiency", 1),
                years_of_experience=skill_data.get("years_of_experience"),
                last_used_date=skill_data.get("last_used_date"),
                is_primary_skill=skill_data.get("is_primary_skill", False),
                remark=skill_data.get("remark"),
            )
            return employee_skill

    async def update_employee_skill(self, skill_id: int, skill_data: dict):
        """更新员工技能"""
        employee_skill = await EmployeeSkill.get_or_none(id=skill_id)
        if not employee_skill:
            raise ValueError("技能记录不存在")

        async with in_transaction():
            # 更新技能信息
            skill_name = skill_data.get("skill_name")
            category = skill_data.get("category")

            if skill_name:
                skill, created = await Skill.get_or_create(name=skill_name, defaults={"category": category})
                employee_skill.skill = skill

            # 更新其他字段
            update_fields = ["proficiency", "years_of_experience", "last_used_date", "is_primary_skill", "remark"]
            for field in update_fields:
                if field in skill_data:
                    setattr(employee_skill, field, skill_data[field])

            await employee_skill.save()
            return employee_skill

    async def delete_employee_skill(self, skill_id: int):
        """删除员工技能"""
        employee_skill = await EmployeeSkill.get_or_none(id=skill_id)
        if employee_skill:
            async with in_transaction():
                await employee_skill.delete()
        return employee_skill

    async def batch_update_employee_skills(self, employee: Employee, skills_data: List[dict]):
        """批量更新员工技能"""
        async with in_transaction():
            # 删除现有技能关联
            await EmployeeSkill.filter(employee=employee).delete()

            # 添加新的技能关联
            if skills_data:
                for skill_item in skills_data:
                    try:
                        await self.add_employee_skill(employee, skill_item)
                    except ValueError:
                        # 忽略重复技能错误，继续处理其他技能
                        continue

    # === 评价管理 ===
    async def get_employee_evaluations(self, employee: Employee, page: int = 1, page_size: int = 10):
        """获取员工评价列表"""
        query = EmployeeEvaluation.filter(freelancer=employee).select_related("case", "contract")
        
        total = await query.count()
        evaluations = (
            await query.order_by("-evaluation_date", "-created_at")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )
        return evaluations, total

    async def create_employee_evaluation(self, employee: Employee, evaluation_data: dict, evaluator_id: int):
        """创建员工评价"""
        async with in_transaction():
            evaluation_data['freelancer'] = employee
            evaluation_data['evaluator_id'] = evaluator_id
            evaluation = await EmployeeEvaluation.create(**evaluation_data)
            return evaluation

    async def get_employee_evaluation_summary(self, employee: Employee):
        """获取员工评价汇总"""
        evaluations = await EmployeeEvaluation.filter(freelancer=employee).all()
        
        if not evaluations:
            return {
                "total_evaluations": 0,
                "average_overall_rating": 0,
                "average_technical_skill": 0,
                "average_communication": 0,
                "average_reliability": 0,
                "recommendation_rate": 0,
            }

        total = len(evaluations)
        return {
            "total_evaluations": total,
            "average_overall_rating": round(sum(e.overall_rating for e in evaluations) / total, 2),
            "average_technical_skill": round(sum(e.technical_skill for e in evaluations) / total, 2),
            "average_communication": round(sum(e.communication for e in evaluations) / total, 2),
            "average_reliability": round(sum(e.reliability for e in evaluations) / total, 2),
            "recommendation_rate": round(sum(1 for e in evaluations if e.recommendation) / total * 100, 1),
        }

    # === 业务逻辑方法 ===
    async def get_available_employees(self, project_start_date: date = None, required_skills: List[str] = None,
                                    min_experience_years: Decimal = None, page: int = 1, page_size: int = 10):
        """获取可用员工列表（根据项目需求筛选）"""
        query = Q(is_active=True, employment_status="available")
        
        # 项目开始日期筛选
        if project_start_date:
            query &= Q(available_start_date__lte=project_start_date) | Q(available_start_date__isnull=True)
        
        # 技能要求筛选
        if required_skills:
            for skill in required_skills:
                query &= Q(skills__skill__name__icontains=skill)
        
        # 经验年数筛选
        if min_experience_years:
            query &= Q(it_experience_years__gte=min_experience_years)
        
        return await self.list_employees(page, page_size, query, ['-it_experience_years', '-updated_at'], 
                                       include_skills=True)

    async def check_visa_expiring_soon(self, days: int = 90):
        """检查签证即将到期的员工"""
        from datetime import timedelta
        
        expiry_date = date.today() + timedelta(days=days)
        employees = await Employee.filter(
            visa_expire_date__lte=expiry_date,
            visa_expire_date__gte=date.today(),
            is_active=True
        ).all()
        
        return employees

    async def get_employee_dashboard_stats(self, employee: Employee):
        """获取员工仪表板统计信息"""
        # 技能统计
        skills_count = await EmployeeSkill.filter(employee=employee).count()
        primary_skills_count = await EmployeeSkill.filter(employee=employee, is_primary_skill=True).count()
        
        # 项目/合同统计
        total_contracts = await employee.contracts.all().count()
        active_contracts = await employee.contracts.filter(status="active").count()
        
        # 评价统计
        evaluation_summary = await self.get_employee_evaluation_summary(employee)
        
        return {
            "basic_info": {
                "name": employee.name,
                "code": employee.code,
                "position": employee.position,
                "current_age": employee.current_age if hasattr(employee, 'current_age') else employee.age,
                "employment_status": employee.employment_status,
                "is_visa_expiring": employee.is_visa_expiring_soon() if hasattr(employee, 'is_visa_expiring_soon') else False,
            },
            "skills_stats": {
                "total_skills": skills_count,
                "primary_skills": primary_skills_count,
            },
            "contract_stats": {
                "total_contracts": total_contracts,
                "active_contracts": active_contracts,
            },
            "evaluation_stats": evaluation_summary,
        }

    async def employees_to_dict(self, employees: List[Employee], include_relations: bool = False):
        """将员工列表转换为字典"""
        result = []
        for employee in employees:
            employee_dict = await employee.to_dict()
            
            if include_relations:
                # 添加技能信息
                skills = []
                if hasattr(employee, 'skills'):
                    for skill_relation in employee.skills:
                        skill_dict = await skill_relation.to_dict()
                        if hasattr(skill_relation, 'skill'):
                            skill_dict['skill'] = await skill_relation.skill.to_dict()
                        skills.append(skill_dict)
                employee_dict['skills'] = skills
                
                # 添加计算属性
                employee_dict['current_age'] = employee.current_age if hasattr(employee, 'current_age') else employee.age
                if hasattr(employee, 'is_visa_expiring_soon'):
                    employee_dict['is_visa_expiring_soon'] = employee.is_visa_expiring_soon()
            
            result.append(employee_dict)
        return result

    async def employee_to_dict(self, employee: Employee, include_relations: bool = False):
        """将单个员工转换为字典"""
        if not employee:
            return None
        return (await self.employees_to_dict([employee], include_relations))[0]


employee_controller = EmployeeController()
