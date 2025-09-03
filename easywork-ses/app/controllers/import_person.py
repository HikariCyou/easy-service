from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import date, datetime, timedelta

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models import ContractStatus
from app.models.personnel import Personnel
from app.models.evaluation import PersonEvaluation
from app.models.enums import PersonType
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
    """统一要员管理控制器（Personnel系统）"""

    def __init__(self):
        pass

    async def get_staff(self, person_id: int):
        """获取要员基本信息"""
        personnel = await Personnel.get_or_none(id=person_id).prefetch_related(
            'skills', 'contracts', 'contracts__case'
        )
        if not personnel:
            return None

        return personnel

    def _decimal_to_float(self, value) -> Optional[float]:
        """将Decimal安全转换为float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def get_staff_list(self, page: int = 1, page_size: int = 10, search_params: Dict = None,
                           person_type: str = None, sort_by: str = None, include_inactive: bool = False) -> Dict[str, Any]:
        """获取要员一览（Personnel统一系统）"""
        if search_params is None:
            search_params = {}

        # 构建查询条件
        query = Q()
        
        # 活跃状态过滤
        if not include_inactive:
            query &= Q(is_active=True)

        # 人员类型过滤（优先使用search_params中的，然后是直接参数）
        target_person_type = search_params.get('person_type') or person_type
        if target_person_type:
            if target_person_type == 'bp_employee':
                query &= Q(person_type=PersonType.BP_EMPLOYEE)
            elif target_person_type == 'freelancer':
                query &= Q(person_type=PersonType.FREELANCER)
            elif target_person_type == 'employee':
                query &= Q(person_type=PersonType.EMPLOYEE)

        # 搜索条件
        if search_params.get('keyword'):
            keyword = search_params['keyword']
            query &= (Q(name__icontains=keyword) | Q(code__icontains=keyword))
        if search_params.get('employment_status'):
            query &= Q(employment_status=search_params['employment_status'])
        if search_params.get('is_active') is not None:
            query &= Q(is_active=search_params['is_active'])
        if search_params.get('skill_name'):
            query &= Q(skills__skill__name__icontains=search_params['skill_name'])
        if search_params.get('min_experience_years'):
            query &= Q(it_experience_years__gte=search_params['min_experience_years'])
        if search_params.get('max_experience_years'):
            query &= Q(it_experience_years__lte=search_params['max_experience_years'])
        if search_params.get('min_unit_price'):
            query &= Q(standard_unit_price__gte=search_params['min_unit_price'])
        if search_params.get('max_unit_price'):
            query &= Q(standard_unit_price__lte=search_params['max_unit_price'])
        if search_params.get('nationality'):
            query &= Q(nationality__icontains=search_params['nationality'])
        if search_params.get('preferred_location'):
            query &= Q(preferred_location__icontains=search_params['preferred_location'])
        if search_params.get('visa_expiring_within_days'):
            days = search_params['visa_expiring_within_days']
            expiry_date = date.today() + timedelta(days=days)
            query &= Q(visa_expire_date__lte=expiry_date, visa_expire_date__gte=date.today())
        if search_params.get('case_id'):
            query &= Q(contracts__case_id=search_params['case_id'])

        # 获取总数
        total = await Personnel.filter(query).count()

        # 排序
        order_by = '-updated_at'
        if sort_by == 'name':
            order_by = 'name'
        elif sort_by == 'created_at':
            order_by = '-created_at'

        # 获取数据
        personnel_list = await Personnel.filter(query).prefetch_related(
            'skills', 'contracts', 'contracts__case'
        ).order_by(order_by).limit(page_size).offset((page - 1) * page_size).all()

        # 转换为schema
        items = []
        for personnel in personnel_list:
            schema = await self._convert_personnel_to_schema(personnel)
            items.append(schema)

        return {
            "items": items,
            "total": total
        }

    async def get_staff_detail(self, person_id: int) -> Optional[ImportPersonDetailSchema]:
        """获取要员详细信息"""
        personnel = await Personnel.get_or_none(id=person_id).prefetch_related(
            'skills', 'contracts', 'contracts__case',
            'employee_detail', 'freelancer_detail', 'bp_employee_detail'
        )
        if not personnel:
            return None

        return await self._convert_to_detail_schema(personnel)

    async def get_staff_history(self, person_id: int, page: int = 1, page_size: int = 10) -> List[ImportPersonHistorySchema]:
        """获取要员履歴（基于契约和评价）"""
        personnel = await Personnel.get_or_none(id=person_id)
        if not personnel:
            return []

        # 获取契约履歴
        query =  Contract.filter(
            personnel=personnel
        ).prefetch_related('case', 'case__client_company')

        contracts = await  query.order_by('-contract_start_date').limit(page_size).offset((page - 1) * page_size).all()
        total = await query.count()
        result = []
        for contract in contracts:
            # 获取相关评价
            evaluation = await PersonEvaluation.filter(
                person_id=personnel.id,
                person_type=personnel.person_type,
                contract=contract
            ).first()

            history = ImportPersonHistorySchema(
                id=contract.id,  # 使用契约ID作为履历ID
                person_id=personnel.id,
                person_name=personnel.name,
                person_type=personnel.person_type.value,
                case_id=contract.case.id if contract.case else None,
                case_name=contract.case.title if contract.case else "不明",
                case_code=getattr(contract.case, 'code', None),
                case_location=getattr(contract.case, 'location', None),
                contract_id=contract.id,
                contract_number=contract.contract_number,
                contract_start_date=contract.contract_start_date,
                contract_end_date=contract.contract_end_date,
                unit_price=self._decimal_to_float(contract.unit_price),
                status=contract.status.value if contract.status else None,
                client_name=getattr(getattr(contract.case, 'client_company', None), 'company_name', None) if contract.case else None,
                project_description=getattr(contract.case, 'description', None),
                evaluation_id=evaluation.id if evaluation else None,
                overall_rating=evaluation.overall_rating if evaluation else None,
                created_at=contract.created_at.date() if contract.created_at else None
            )
            result.append(history)

        return result,total

    async def get_staff_current_assignments(self, person_id: int) -> Optional[ImportPersonCurrentAssignmentSchema]:
        """获取要员当前参与案件"""
        personnel = await Personnel.get_or_none(id=person_id)
        if not personnel:
            return None

        # 获取当前有效契约
        current_date = date.today()
        current_contract = await Contract.filter(
            personnel=personnel,
            contract_start_date__lte=current_date,
            contract_end_date__gte=current_date,
            status='active'
        ).prefetch_related('case').first()

        if not current_contract:
            return None

        return ImportPersonCurrentAssignmentSchema(
            project_name=current_contract.case.title if current_contract.case else "不明",
            client_company=getattr(current_contract.case, 'client_company', None),
            contract_start_date=current_contract.contract_start_date,
            contract_end_date=current_contract.contract_end_date,
            unit_price=self._decimal_to_float(current_contract.unit_price),
            working_hours=self._decimal_to_float(current_contract.standard_working_hours),
            location=getattr(current_contract.case, 'location', None),
            status=current_contract.status,
            remark=current_contract.remark
        )

    async def update_staff_status(self, person_id: int, person_type: str, status_data: Dict[str, Any]) -> bool:
        """更新要员状态"""
        personnel = await Personnel.get_or_none(id=person_id)
        if not personnel:
            return False

        async with in_transaction():
            # 更新基本状态字段
            if 'employment_status' in status_data:
                personnel.employment_status = status_data['employment_status']
            if 'available_start_date' in status_data:
                personnel.available_start_date = status_data['available_start_date']
            if 'current_project_end_date' in status_data:
                personnel.current_project_end_date = status_data['current_project_end_date']
            if 'remark' in status_data:
                personnel.remark = status_data['remark']

            await personnel.save()

        return True

    async def get_staff_stats(self) -> ImportPersonStatsSchema:
        """获取要员统计信息"""
        # 各类型人员统计
        bp_employee_count = await Personnel.filter(person_type=PersonType.BP_EMPLOYEE, is_active=True).count()
        freelancer_count = await Personnel.filter(person_type=PersonType.FREELANCER, is_active=True).count()
        employee_count = await Personnel.filter(person_type=PersonType.EMPLOYEE, is_active=True).count()
        total_count = bp_employee_count + freelancer_count + employee_count

        # 状态统计
        available_count = await Personnel.filter(employment_status="稼働可能", is_active=True).count()
        working_count = await Personnel.filter(employment_status="稼働中", is_active=True).count()
        unavailable_count = await Personnel.filter(employment_status="稼働不可", is_active=True).count()

        # 国籍统计
        japanese_count = await Personnel.filter(nationality="日本", is_active=True).count()
        foreign_count = total_count - japanese_count

        # 签证即将到期统计（外国人）
        visa_expiring_count = len(await self._get_visa_expiring_personnel())

        # 经验统计
        senior_count = await Personnel.filter(it_experience_years__gte=5.0, is_active=True).count()
        junior_count = await Personnel.filter(it_experience_years__lte=3.0, is_active=True).count()

        return ImportPersonStatsSchema(
            total_staff=total_count,
            bp_employees=bp_employee_count,
            freelancers=freelancer_count,
            employees=employee_count,
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
    
    async def _get_visa_expiring_personnel(self, days: int = 90) -> List[Personnel]:
        """获取签证即将到期的人员"""
        expiry_date = date.today() + timedelta(days=days)
        return await Personnel.filter(
            visa_expire_date__lte=expiry_date,
            visa_expire_date__gte=date.today(),
            is_active=True
        ).all()

    async def _convert_personnel_to_schema(self, personnel: Personnel):
        """将Personnel转换为ImportPersonSchema"""
        dict_data = await personnel.to_dict()
        
        # 字段名映射
        dict_data['type'] = dict_data.get('person_type', '')
        
        # 简单获取关联数据
        skills = await personnel.skills.all()
        if skills:
            dict_data['skills'] = [await skill.to_dict() for skill in skills]
        else:
            dict_data['skills'] = []
            
        # 获取契约数据
        contracts = await personnel.contracts.all()
        
        if contracts:
            dict_data['contracts'] = [await contract.to_dict() for contract in contracts]
            
            # 获取当前活跃契约
            current_date = date.today()
            current_contract = None
            for contract in contracts:
                if (contract.contract_start_date and contract.contract_end_date and
                    contract.contract_start_date <= current_date and 
                    contract.contract_end_date >= current_date):
                    current_contract = contract
                    break
                    
            if current_contract:
                dict_data['contract'] = await current_contract.to_dict()
                # 获取关联的案件
                case = await current_contract.case
                if case:
                    dict_data['case'] = await case.to_dict()
                else:
                    dict_data['case'] = None
            else:
                dict_data['contract'] = None
                dict_data['case'] = None
        else:
            dict_data['contracts'] = []
            dict_data['contract'] = None
            dict_data['case'] = None

        return dict_data


    async def _convert_to_detail_schema(self, personnel: Personnel) -> ImportPersonDetailSchema:
        """将Personnel转换为ImportPersonDetailSchema"""
        # 基本schema
        base_schema = await self._convert_personnel_to_schema(personnel)
        
        # 详细信息
        emergency_contact_info = {
            "name": personnel.emergency_contact_name,
            "phone": personnel.emergency_contact_phone,
            "relation": personnel.emergency_contact_relation
        }

        # 获取特化信息
        specialized_info = {}
        if personnel.person_type == PersonType.EMPLOYEE:
            if personnel.employee_detail:
                employee_detail = await personnel.employee_detail
                specialized_info = {
                    "joining_time": employee_detail.joining_time,
                    "position": employee_detail.position,
                    "employment_type": employee_detail.employment_type,
                    "salary": employee_detail.salary
                }
        elif personnel.person_type == PersonType.FREELANCER:
            if personnel.freelancer_detail:
                freelancer_detail = await personnel.freelancer_detail
                specialized_info = {
                    "business_name": freelancer_detail.business_name,
                    "tax_number": freelancer_detail.tax_number,
                    "business_start_date": freelancer_detail.business_start_date,
                    "preferred_work_style": freelancer_detail.preferred_work_style
                }
        elif personnel.person_type == PersonType.BP_EMPLOYEE:
            if personnel.bp_employee_detail:
                bp_detail = await personnel.bp_employee_detail
                bp_company = await bp_detail.bp_company
                specialized_info = {
                    "bp_company_name": bp_company.name if bp_company else None,
                    "interview_available": bp_detail.interview_available
                }

        # 将特化信息添加到base_schema中
        base_schema.update({
            "specialized_info": specialized_info
        })
        
        return ImportPersonDetailSchema(**base_schema)


# グローバルインスタンス
import_person_controller = ImportPersonController()