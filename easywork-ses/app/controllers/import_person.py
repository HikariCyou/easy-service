from typing import List, Dict, Any, Optional, Union
from datetime import date, datetime, timedelta

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models import ContractStatus
from app.models.bp import BPEmployee
from app.models.freelancer import Freelancer, FreelancerEvaluation
from app.models.employee import Employee
from app.models.case import Case
from app.models.contract import Contract
from app.schemas.import_person import (
    ImportPersonSchema,
    ImportPersonDetailSchema,
    ImportPersonHistorySchema,
    ImportPersonCurrentAssignmentSchema,
    ImportPersonStatsSchema
)


class ImportPersonController:
    """统一要员管理控制器"""

    def __init__(self):
        pass

    def _decimal_to_float(self, value) -> Optional[float]:
        """将Decimal安全转换为float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    # ===== 主要业务方法 =====
    
    async def get_staff_list(self, page: int = 1, page_size: int = 10, search_params: Dict = None,
                           include_inactive: bool = False) -> Dict[str, Any]:
        """获取所有要员列表（包含工作状态）"""
        if search_params is None:
            search_params = {}
            
        # 构建查询条件
        bp_query, freelancer_query, employee_query = self._build_search_queries(search_params, include_inactive)
        
        # 分别查询三个表的数据
        bp_employees = await BPEmployee.filter(bp_query).prefetch_related('skills__skill', 'contracts').all()
        freelancers = await Freelancer.filter(freelancer_query).prefetch_related('skills__skill', 'contracts').all()
        employees = await Employee.filter(employee_query).all()  # Employee暂时不包含skills关联
        
        # 转换为统一格式
        staff_list = []
        
        # 处理BP员工
        for bp in bp_employees:
            staff_item = await self._convert_bp_employee_to_schema(bp)
            staff_list.append(staff_item.dict())
        
        # 处理自由职业者
        for freelancer in freelancers:
            staff_item = await self._convert_freelancer_to_schema(freelancer)
            staff_list.append(staff_item.dict())
            
        # 处理正式员工
        for employee in employees:
            staff_item = await self._convert_employee_to_schema(employee)
            staff_list.append(staff_item.dict())
        
        # 排序（按更新时间倒序）
        staff_list.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        
        # 分页处理
        total = len(staff_list)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_list = staff_list[start_idx:end_idx]
        
        return {
            "items": paginated_list,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    async def get_staff_detail(self, person_id: int, person_type: str = None) -> Optional[ImportPersonDetailSchema]:
        """获取要员详情（包含履历）"""
        if person_type:
            # 如果指定了类型，直接查询
            person = await self._get_person_by_type_and_id(person_type, person_id)
            if not person:
                return None
            return await self._convert_to_detail_schema(person, person_type)
        else:
            # 如果未指定类型，依次尝试查找
            for p_type in ['bp_employee', 'freelancer', 'employee']:
                person = await self._get_person_by_type_and_id(p_type, person_id)
                if person:
                    return await self._convert_to_detail_schema(person, p_type)
            return None

    async def get_staff_history(self, person_id: int, person_type: str = None , page:int = 1, page_size:int = 10) -> List[ImportPersonHistorySchema]:
        """获取要员的工作履历"""
        person = None
        if person_type:
            person = await self._get_person_by_type_and_id(person_type, person_id)
        else:
            # 尝试查找person和其类型
            for p_type in ['bp_employee', 'freelancer', 'employee']:
                person = await self._get_person_by_type_and_id(p_type, person_id)
                if person:
                    person_type = p_type
                    break
        
        if not person:
            return []

        histories = []
        
        # 获取契约履历
        if person_type == 'bp_employee':
            query =  Contract.filter(bp_employee=person).prefetch_related('case').order_by('-contract_start_date')
        elif person_type == 'freelancer':
            query = await Contract.filter(freelancer=person).prefetch_related('case').order_by('-contract_start_date')
        else:  # employee
            query = await Contract.filter(employee=person).prefetch_related('case').order_by('-contract_start_date')

        total = await query.count()
        contracts = await query.offset((page - 1) * page_size).limit(page_size)
        for contract in contracts:
            try:
                case_info = contract.case if hasattr(contract, 'case') and contract.case else None
                client_company = await  case_info.client_company
                
                history_item = ImportPersonHistorySchema(
                    id=contract.id,
                    person_id=person.id,
                    person_name=person.name,
                    person_type=person_type,
                    case_id=case_info.id if case_info else None,
                    case_name=case_info.title if case_info else None,
                    case_location=case_info.location if case_info else None,
                    contract_id=contract.id,
                    contract_number=contract.contract_number,
                    contract_start_date=contract.contract_start_date,
                    contract_end_date=contract.contract_end_date,
                    unit_price=self._decimal_to_float(contract.unit_price),
                    status=contract.status,
                    client_name=client_company.company_name if client_company else None,
                    project_description=case_info.description if case_info else None,
                    created_at=contract.created_at.date() if contract.created_at else None
                )
                
                # 如果是自由职业者，尝试获取评价信息
                if person_type == 'freelancer':
                    evaluation = await FreelancerEvaluation.filter(
                        freelancer=person,
                        contract=contract
                    ).first()
                    if evaluation:
                        history_item.evaluation_id = evaluation.id
                        history_item.overall_rating = evaluation.overall_rating
                
                histories.append(history_item)
            except Exception as e:
                # 如果某个contract有问题，跳过继续处理其他的
                print(f"Error processing contract {contract.id}: {e}")
                continue
        
        return histories , total

    async def get_staff_current_assignments(self, person_id: int, person_type: str = None) -> Optional[ImportPersonCurrentAssignmentSchema]:
        """获取要员当前的案件和合同信息"""
        person = None
        if person_type:
            person = await self._get_person_by_type_and_id(person_type, person_id)
        else:
            for p_type in ['bp_employee', 'freelancer', 'employee']:
                person = await self._get_person_by_type_and_id(p_type, person_id)
                if person:
                    person_type = p_type
                    break
        
        if not person:
            return None

        # 获取当前活跃的契约
        current_contracts = []
        expiring_contracts = []
        current_case = None
        
        if person_type == 'bp_employee':
            contracts = await Contract.filter(bp_employee=person, status='active').prefetch_related('case').all()
        elif person_type == 'freelancer':
            contracts = await Contract.filter(freelancer=person, status='active').prefetch_related('case').all()
        else:  # employee
            contracts = await Contract.filter(employee=person, status='active').prefetch_related('case').all()
        
        # 30天内到期的契约
        expiry_threshold = date.today() + timedelta(days=30)
        
        for contract in contracts:
            try:
                contract_dict = {
                    "id": contract.id,
                    "contract_number": contract.contract_number,
                    "start_date": contract.contract_start_date,
                    "end_date": contract.contract_end_date,
                    "unit_price": self._decimal_to_float(contract.unit_price),
                    "status": contract.status,
                    "case_name": contract.case.name if hasattr(contract, 'case') and contract.case else None,
                    "case_id": contract.case.id if hasattr(contract, 'case') and contract.case else None
                }
                
                current_contracts.append(contract_dict)
                
                # 检查是否即将到期
                if contract.contract_end_date and contract.contract_end_date <= expiry_threshold:
                    expiring_contracts.append(contract_dict)
                
                # 获取当前主要案件（第一个活跃的案件）
                if not current_case and hasattr(contract, 'case') and contract.case:
                    current_case = {
                        "id": contract.case.id,
                        "name": contract.case.name,
                        "code": contract.case.code,
                        "client_name": contract.case.client_name,
                        "status": contract.case.status
                    }
            except Exception:
                continue
        
        # 判断工作状态
        work_status = "available"
        if current_contracts:
            work_status = "working"
        elif not getattr(person, 'is_active', True):
            work_status = "unavailable"
        
        return ImportPersonCurrentAssignmentSchema(
            person_id=person.id,
            person_name=person.name,
            person_type=person_type,
            current_case=current_case,
            current_contracts=current_contracts,
            expiring_contracts=expiring_contracts,
            work_status=work_status,
            available_from=getattr(person, 'available_start_date', None)
        )

    async def update_staff_status(self, person_id: int, person_type: str, status_data: Dict[str, Any]) -> bool:
        """更新要员工作状态"""
        person = await self._get_person_by_type_and_id(person_type, person_id)
        if not person:
            return False
        
        async with in_transaction():
            # 更新就业状态
            if 'employment_status' in status_data:
                person.employment_status = status_data['employment_status']
            
            # 更新活跃状态
            if 'is_active' in status_data:
                person.is_active = status_data['is_active']
            
            # 更新可用开始日期
            if 'available_start_date' in status_data:
                person.available_start_date = status_data['available_start_date']
            
            await person.save()
            return True

    async def get_staff_stats(self) -> ImportPersonStatsSchema:
        """获取要员统计信息"""
        # 分别统计三个表
        bp_employees = await BPEmployee.filter(is_active=True).all()
        freelancers = await Freelancer.filter(is_active=True).all()
        employees = await Employee.filter(is_active=True).all()
        
        total_staff = len(bp_employees) + len(freelancers) + len(employees)
        
        # 按状态统计
        available_count = 0
        working_count = 0
        unavailable_count = 0
        
        # 按国籍统计
        japanese_count = 0
        foreign_count = 0
        
        # 签证到期统计
        visa_expiring_count = 0
        expiry_threshold = date.today() + timedelta(days=90)
        
        # 经验统计
        senior_count = 0
        junior_count = 0
        
        # 统计BP员工
        for bp in bp_employees:
            if bp.employment_status == 'available':
                available_count += 1
            elif bp.employment_status == 'working':
                working_count += 1
            else:
                unavailable_count += 1
            
            if bp.nationality and bp.nationality.lower() in ['日本', 'japan', 'japanese']:
                japanese_count += 1
            else:
                foreign_count += 1
            
            if bp.visa_expire_date and bp.visa_expire_date <= expiry_threshold:
                visa_expiring_count += 1
            
            if bp.it_experience_years and bp.it_experience_years >= 5:
                senior_count += 1
            elif bp.it_experience_years and bp.it_experience_years <= 3:
                junior_count += 1
        
        # 统计自由职业者
        for fl in freelancers:
            if fl.employment_status == 'available':
                available_count += 1
            elif fl.employment_status == 'working':
                working_count += 1
            else:
                unavailable_count += 1
            
            if fl.nationality and fl.nationality.lower() in ['日本', 'japan', 'japanese']:
                japanese_count += 1
            else:
                foreign_count += 1
            
            if fl.visa_expire_date and fl.visa_expire_date <= expiry_threshold:
                visa_expiring_count += 1
            
            if fl.it_experience_years and fl.it_experience_years >= 5:
                senior_count += 1
            elif fl.it_experience_years and fl.it_experience_years <= 3:
                junior_count += 1
        
        # 统计正式员工
        for emp in employees:
            # Employee表的状态字段可能不同，需要适配
            emp_status = getattr(emp, 'employment_status', 'working')
            if emp_status == 'available':
                available_count += 1
            elif emp_status == 'working':
                working_count += 1
            else:
                unavailable_count += 1
            
            if emp.nationality and emp.nationality.lower() in ['日本', 'japan', 'japanese']:
                japanese_count += 1
            else:
                foreign_count += 1
            
            if hasattr(emp, 'visa_expire_date') and emp.visa_expire_date and emp.visa_expire_date <= expiry_threshold:
                visa_expiring_count += 1
            
            if hasattr(emp, 'it_experience_years') and emp.it_experience_years:
                if emp.it_experience_years >= 5:
                    senior_count += 1
                elif emp.it_experience_years <= 3:
                    junior_count += 1
        
        return ImportPersonStatsSchema(
            total_staff=total_staff,
            bp_employees=len(bp_employees),
            freelancers=len(freelancers),
            employees=len(employees),
            available_staff=available_count,
            working_staff=working_count,
            unavailable_staff=unavailable_count,
            japanese_staff=japanese_count,
            foreign_staff=foreign_count,
            visa_expiring_soon=visa_expiring_count,
            senior_staff=senior_count,
            junior_staff=junior_count
        )

    # ===== 内部辅助方法 =====
    
    def _build_search_queries(self, search_params: Dict, include_inactive: bool = False) -> tuple:
        """构建搜索查询条件"""
        base_q = Q()
        if not include_inactive:
            base_q = Q(is_active=True)
        
        # 基本搜索条件
        if search_params.get('keyword'):
            name_q = Q(name__icontains=search_params['keyword']) | Q(code__icontains=search_params['keyword'])
            bp_query = base_q & name_q
            freelancer_query = base_q & name_q
            employee_query = base_q & name_q
        else:
            bp_query = freelancer_query = employee_query = base_q
        
        # 代码搜索
        if search_params.get('code'):
            code_q = Q(code__icontains=search_params['code'])
            bp_query &= code_q
            freelancer_query &= code_q
            employee_query &= code_q
        
        # 就业状态搜索
        if search_params.get('employment_status'):
            status_q = Q(employment_status=search_params['employment_status'])
            bp_query &= status_q
            freelancer_query &= status_q
            employee_query &= status_q
        
        # 国籍搜索
        if search_params.get('nationality'):
            nationality_q = Q(nationality__icontains=search_params['nationality'])
            bp_query &= nationality_q
            freelancer_query &= nationality_q
            employee_query &= nationality_q
        
        # 经验年数筛选
        if search_params.get('min_experience_years'):
            exp_q = Q(it_experience_years__gte=search_params['min_experience_years'])
            bp_query &= exp_q
            freelancer_query &= exp_q
            # Employee表可能没有it_experience_years字段，需要检查
        
        # 单价筛选（主要针对BP员工和自由职业者）
        if search_params.get('min_unit_price'):
            price_q = Q(standard_unit_price__gte=search_params['min_unit_price'])
            bp_query &= price_q
            freelancer_query &= price_q
        
        # 签证到期筛选
        if search_params.get('visa_expiring_within_days'):
            days = search_params['visa_expiring_within_days']
            expiry_date = date.today() + timedelta(days=days)
            visa_q = Q(visa_expire_date__lte=expiry_date, visa_expire_date__gte=date.today())
            bp_query &= visa_q
            freelancer_query &= visa_q
            # Employee表可能没有visa_expire_date字段
        
        return bp_query, freelancer_query, employee_query

    async def _get_person_by_type_and_id(self, person_type: str, person_id: int):
        """根据类型和ID获取人员"""
        if person_type == 'bp_employee':
            return await BPEmployee.get_or_none(id=person_id)
        elif person_type == 'freelancer':
            return await Freelancer.get_or_none(id=person_id)
        elif person_type == 'employee':
            return await Employee.get_or_none(id=person_id)
        return None

    async def _convert_bp_employee_to_schema(self, bp: BPEmployee) -> ImportPersonSchema:
        """将BP员工转换为统一Schema"""
        # 获取当前案件和契约信息
        current_case_id = None
        current_case_name = None
        current_contract_id = None
        contract = None
        total_contracts = 0
        
        try:
            active_contracts = await Contract.filter(bp_employee=bp, status=ContractStatus.ACTIVE.value).prefetch_related('case').all()
            total_contracts = await Contract.filter(bp_employee=bp).count()
            
            if active_contracts:
                contract = active_contracts[0]
                current_contract_id = contract.id
                if hasattr(contract, 'case') and contract.case:
                    current_case_id = contract.case.id
                    current_case_name = contract.case.title
        except Exception as e:
            print(e)
        
        return ImportPersonSchema(
            id=bp.id,
            name=bp.name,
            code=bp.code,
            type="bp_employee",
            age=bp.age,
            sex=bp.sex,
            birthday=bp.birthday,
            nationality=bp.nationality,
            phone=bp.phone,
            email=bp.email,
            address=bp.address,
            employment_status=bp.employment_status,
            photo_url = bp.photo_url,
            is_active=bp.is_active,
            available_start_date=bp.available_start_date,
            it_experience_years=self._decimal_to_float(bp.it_experience_years),
            standard_unit_price=self._decimal_to_float(bp.standard_unit_price),
            visa_status=bp.visa_status,
            visa_expire_date=bp.visa_expire_date,
            current_case_id=current_case_id,
            current_case_name=current_case_name,
            current_contract_id=current_contract_id,
            contract = await contract.to_dict() if contract is not None else None,
            case = await contract.case.to_dict() if contract is not None and contract.case is not None else None,
            current_age=bp.current_age if hasattr(bp, 'current_age') else bp.age,
            is_visa_expiring_soon=bp.is_visa_expiring_soon() if hasattr(bp, 'is_visa_expiring_soon') else False,
            total_contracts=total_contracts,
            updated_at=bp.updated_at.isoformat() if bp.updated_at else None
        )

    async def _convert_freelancer_to_schema(self, freelancer: Freelancer) -> ImportPersonSchema:
        """将自由职业者转换为统一Schema"""
        # 获取当前案件和契约信息
        contract = None
        current_case_id = None
        current_case_name = None
        current_contract_id = None
        total_contracts = 0
        average_rating = None
        
        try:
            active_contracts = await Contract.filter(freelancer=freelancer, status='active').prefetch_related('case').all()
            total_contracts = await Contract.filter(freelancer=freelancer).count()
            
            if active_contracts:
                contract = active_contracts[0]
                current_contract_id = contract.id
                if hasattr(contract, 'case') and contract.case:
                    current_case_id = contract.case.id
                    current_case_name = contract.case.title
            
            # 计算平均评分
            evaluations = await FreelancerEvaluation.filter(freelancer=freelancer).all()
            if evaluations:
                total_rating = sum(e.overall_rating for e in evaluations)
                average_rating = round(total_rating / len(evaluations), 2)
        except Exception:
            pass
        
        return ImportPersonSchema(
            id=freelancer.id,
            name=freelancer.name,
            code=freelancer.code,
            type="freelancer",
            age=freelancer.age,
            sex=freelancer.sex,
            birthday=freelancer.birthday,
            nationality=freelancer.nationality,
            photo_url = freelancer.photo_url,
            phone=freelancer.phone,
            email=freelancer.email,
            address=freelancer.address,
            employment_status=freelancer.employment_status,
            is_active=freelancer.is_active,
            available_start_date=freelancer.available_start_date,
            it_experience_years=self._decimal_to_float(freelancer.it_experience_years),
            standard_unit_price=self._decimal_to_float(freelancer.standard_unit_price),
            visa_status=freelancer.visa_status,
            visa_expire_date=freelancer.visa_expire_date,
            current_case_id=current_case_id,
            contract =  await contract.to_dict() if contract is not None else None,
            case=await contract.case.to_dict() if contract is not None and contract.case is not None else None,
            current_case_name=current_case_name,
            current_contract_id=current_contract_id,
            current_age=freelancer.current_age if hasattr(freelancer, 'current_age') else freelancer.age,
            is_visa_expiring_soon=freelancer.is_visa_expiring_soon() if hasattr(freelancer, 'is_visa_expiring_soon') else False,
            total_contracts=total_contracts,
            average_rating=average_rating,
            updated_at=freelancer.updated_at.isoformat() if freelancer.updated_at else None
        )

    async def _convert_employee_to_schema(self, employee: Employee) -> ImportPersonSchema:
        """将正式员工转换为统一Schema"""
        # 获取当前案件和契约信息
        current_case_id = None
        current_case_name = None
        current_contract_id = None
        total_contracts = 0
        
        try:
            active_contracts = await Contract.filter(employee=employee, status='active').prefetch_related('case').all()
            total_contracts = await Contract.filter(employee=employee).count()
            
            if active_contracts:
                contract = active_contracts[0]
                current_contract_id = contract.id
                if hasattr(contract, 'case') and contract.case:
                    current_case_id = contract.case.id
                    current_case_name = contract.case.name
        except Exception:
            pass
        
        return ImportPersonSchema(
            id=employee.id,
            name=employee.name,
            code=employee.code,
            type="employee",
            age=employee.age,
            sex=employee.sex,
            birthday=employee.birthday,
            nationality=employee.nationality,
            phone=employee.phone,
            email=employee.email,
            address=employee.address,
            employment_status=getattr(employee, 'employment_status', 'working'),
            is_active=getattr(employee, 'is_active', True),
            available_start_date=getattr(employee, 'available_start_date', None),
            it_experience_years=self._decimal_to_float(getattr(employee, 'it_experience_years', None)),
            standard_unit_price=self._decimal_to_float(getattr(employee, 'standard_unit_price', None)),
            visa_status=getattr(employee, 'visa_status', None),
            visa_expire_date=getattr(employee, 'visa_expire_date', None),
            current_case_id=current_case_id,
            current_case_name=current_case_name,
            current_contract_id=current_contract_id,
            current_age=employee.current_age if hasattr(employee, 'current_age') else employee.age,
            is_visa_expiring_soon=employee.is_visa_expiring_soon() if hasattr(employee, 'is_visa_expiring_soon') else False,
            total_contracts=total_contracts,
            updated_at=employee.updated_at.isoformat() if employee.updated_at else None
        )

    async def _convert_to_detail_schema(self, person: Union[BPEmployee, Freelancer, Employee], person_type: str) -> ImportPersonDetailSchema:
        """转换为详细信息Schema"""
        # 先获取基本Schema
        if person_type == 'bp_employee':
            base_schema = await self._convert_bp_employee_to_schema(person)
        elif person_type == 'freelancer':
            base_schema = await self._convert_freelancer_to_schema(person)
        else:  # employee
            base_schema = await self._convert_employee_to_schema(person)
        
        # 获取技能信息
        skills = []
        try:
            if person_type in ['bp_employee', 'freelancer']:
                if hasattr(person, 'skills'):
                    skill_relations = await person.skills.all().prefetch_related('skill')
                    for skill_rel in skill_relations:
                        if hasattr(skill_rel, 'skill') and skill_rel.skill:
                            skills.append({
                                "id": skill_rel.id,
                                "skill_id": skill_rel.skill.id,
                                "skill_name": skill_rel.skill.name,
                                "category": skill_rel.skill.category,
                                "proficiency": skill_rel.proficiency,
                                "years_of_experience": self._decimal_to_float(skill_rel.years_of_experience),
                                "is_primary_skill": skill_rel.is_primary_skill,
                                "remark": skill_rel.remark
                            })
        except Exception:
            pass
        
        # 构建详细Schema
        detail_data = base_schema.dict()
        detail_data.update({
            "free_kana_name": getattr(person, 'free_kana_name', None),
            "station": getattr(person, 'station', None),
            "marriage_status": getattr(person, 'marriage_status', None),
            "zip_code": getattr(person, 'zip_code', None),
            "work_address": getattr(person, 'work_address', None),
            "emergency_contact_name": getattr(person, 'emergency_contact_name', None),
            "emergency_contact_phone": getattr(person, 'emergency_contact_phone', None),
            "emergency_contact_relation": getattr(person, 'emergency_contact_relation', None),
            "education_level": getattr(person, 'education_level', None),
            "major": getattr(person, 'major', None),
            "certifications": getattr(person, 'certifications', None),
            "min_unit_price": self._decimal_to_float(getattr(person, 'min_unit_price', None)),
            "max_unit_price": self._decimal_to_float(getattr(person, 'max_unit_price', None)),
            "hourly_rate": self._decimal_to_float(getattr(person, 'hourly_rate', None)),
            "preferred_location": getattr(person, 'preferred_location', None),
            "preferred_project_type": getattr(person, 'preferred_project_type', None),
            "preferred_work_style": getattr(person, 'preferred_work_style', None),
            "photo_url": getattr(person, 'photo_url', None),
            "resume_url": getattr(person, 'resume_url', None),
            "remark": getattr(person, 'remark', None),
            "skills": skills,
        })
        
        return ImportPersonDetailSchema(**detail_data)


# 创建全局实例
import_person_controller = ImportPersonController()