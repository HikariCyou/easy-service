from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.contract import Contract
from app.models.enums import PersonType
from app.models.personnel import (
    BPEmployeeDetail,
    EmployeeDetail,
    FreelancerDetail,
    Personnel,
    PersonnelSkill,
)
from app.models.skill import Skill
from app.utils.common import clean_dict


class PersonnelController:
    """統一人材管理コントローラー"""

    def __init__(self):
        pass

    # ===== 社員管理 =====
    async def list_employees(
        self, page: int = 1, page_size: int = 10, search_params: Dict = None, include_details: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """社員一覧取得"""
        query = Personnel.filter(person_type=PersonType.EMPLOYEE)

        if search_params:
            # 名前検索
            if search_params.get("name"):
                query = query.filter(name__icontains=search_params["name"])
            # コード検索
            if search_params.get("code"):
                query = query.filter(code__icontains=search_params["code"])
            # 稼働ステータス
            if search_params.get("employment_status"):
                query = query.filter(employment_status=search_params["employment_status"])
            # 国籍
            if search_params.get("nationality"):
                query = query.filter(nationality__icontains=search_params["nationality"])
            # 稼働可能開始日
            if search_params.get("available_from"):
                query = query.filter(available_start_date__gte=search_params["available_from"])
            if search_params.get("available_to"):
                query = query.filter(available_start_date__lte=search_params["available_to"])
            # 経験年数
            if search_params.get("min_experience_years"):
                query = query.filter(it_experience_years__gte=search_params["min_experience_years"])
            # スキル検索
            if search_params.get("skill_name"):
                query = query.filter(skills__skill__name__icontains=search_params["skill_name"])

        total = await query.count()
        personnel_list = (
            await query.prefetch_related("employee_detail", "skills__skill")
            .order_by("-updated_at")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )

        # Detail情報付きの辞書リストに変換
        result_data = []
        for personnel in personnel_list:
            data = await self._personnel_to_dict_with_details(personnel, include_details)
            result_data.append(data)

        return result_data, total

    async def get_employee_by_id(self, employee_id: int, include_details: bool = True) -> Optional[Dict[str, Any]]:
        """ID指定で社員取得"""
        personnel = (
            await Personnel.filter(id=employee_id, person_type=PersonType.EMPLOYEE)
            .prefetch_related("employee_detail", "skills__skill")
            .first()
        )
        if personnel:
            return await self._personnel_to_dict_with_details(personnel, include_details)
        return None

    async def get_employee_by_user_id(self, user_id: int) -> Optional[Personnel]:
        """ユーザーID指定で社員取得"""
        return await Personnel.filter(user_id=user_id, person_type=PersonType.EMPLOYEE).first()

    async def create_employee(self, employee_data: Dict[str, Any]) -> Personnel:
        """社員作成"""
        async with in_transaction():
            # 社員タイプを設定
            employee_data["person_type"] = PersonType.EMPLOYEE

            # 詳細情報を分離
            detail_fields = {}
            for field in [
                "joining_time",
                "position",
                "employment_type",
                "business_content",
                "salary_payment_type",
                "salary",
            ]:
                if field in employee_data:
                    detail_fields[field] = employee_data.pop(field)

            # Personnel作成
            personnel = await Personnel.create(**clean_dict(employee_data))

            # EmployeeDetail作成
            if detail_fields:
                detail_fields["personnel"] = personnel
                await EmployeeDetail.create(**clean_dict(detail_fields))

            return personnel

    async def update_employee(self, employee_id: int, employee_data: Dict[str, Any]) -> Optional[Personnel]:
        """社員更新"""
        personnel = await Personnel.filter(id=employee_id, person_type=PersonType.EMPLOYEE).first()
        if not personnel:
            return None

        async with in_transaction():
            # 詳細情報を分離
            detail_fields = {}
            for field in [
                "joining_time",
                "position",
                "employment_type",
                "business_content",
                "salary_payment_type",
                "salary",
            ]:
                if field in employee_data:
                    detail_fields[field] = employee_data.pop(field)

            # Personnel更新
            if employee_data:
                await personnel.update_from_dict(clean_dict(employee_data))
                await personnel.save()

            # EmployeeDetail更新
            if detail_fields:
                detail = await EmployeeDetail.filter(personnel=personnel).first()
                if detail:
                    await detail.update_from_dict(clean_dict(detail_fields))
                    await detail.save()
                else:
                    detail_fields["personnel"] = personnel
                    await EmployeeDetail.create(**clean_dict(detail_fields))

            return personnel

    async def delete_employee(self, employee_id: int) -> bool:
        """社員削除"""
        personnel = await Personnel.filter(id=employee_id, person_type=PersonType.EMPLOYEE).first()
        if personnel:
            async with in_transaction():
                await personnel.delete()  # 関連データも CASCADE 削除
            return True
        return False

    # ===== フリーランス管理 =====
    async def list_freelancers(
        self, page: int = 1, page_size: int = 10, search_params: Dict = None, include_details: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """フリーランス一覧取得"""
        query = Personnel.filter(person_type=PersonType.FREELANCER)

        if search_params:
            # 基本検索条件（社員と同じ）
            if search_params.get("name"):
                query = query.filter(name__icontains=search_params["name"])
            if search_params.get("code"):
                query = query.filter(code__icontains=search_params["code"])
            if search_params.get("employment_status"):
                query = query.filter(employment_status=search_params["employment_status"])
            if search_params.get("nationality"):
                query = query.filter(nationality__icontains=search_params["nationality"])
            # フリーランス特有の検索
            if search_params.get("business_name"):
                query = query.filter(freelancer_detail__business_name__icontains=search_params["business_name"])

        total = await query.count()
        personnel_list = (
            await query.prefetch_related("freelancer_detail", "skills__skill")
            .order_by("-updated_at")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )

        # Detail情報付きの辞書リストに変換
        result_data = []
        for personnel in personnel_list:
            data = await self._personnel_to_dict_with_details(personnel, include_details)
            result_data.append(data)

        return result_data, total

    async def get_freelancer_by_id(self, freelancer_id: int, include_details: bool = True) -> Optional[Dict[str, Any]]:
        """ID指定でフリーランス取得"""
        personnel = (
            await Personnel.filter(id=freelancer_id, person_type=PersonType.FREELANCER)
            .prefetch_related("freelancer_detail", "skills__skill")
            .first()
        )
        if personnel:
            return await self._personnel_to_dict_with_details(personnel, include_details)
        return None

    async def create_freelancer(self, freelancer_data: Dict[str, Any]) -> Personnel:
        """フリーランス作成"""
        async with in_transaction():
            # フリーランスタイプを設定
            freelancer_data["person_type"] = PersonType.FREELANCER

            # 詳細情報を分離
            detail_fields = {}
            for field in [
                "business_name",
                "tax_number",
                "business_start_date",
                "freelance_experience_years",
                "preferred_project_type",
                "preferred_work_style",
                "ng_client_companies",
                "interview_available",
            ]:
                if field in freelancer_data:
                    detail_fields[field] = freelancer_data.pop(field)

            # Personnel作成
            personnel = await Personnel.create(**clean_dict(freelancer_data))

            # FreelancerDetail作成
            if detail_fields:
                detail_fields["personnel"] = personnel
                await FreelancerDetail.create(**clean_dict(detail_fields))

            return personnel

    async def update_freelancer(self, freelancer_id: int, freelancer_data: Dict[str, Any]) -> Optional[Personnel]:
        """フリーランス更新"""
        personnel = await Personnel.filter(id=freelancer_id, person_type=PersonType.FREELANCER).first()
        if not personnel:
            return None

        async with in_transaction():
            # 詳細情報を分離
            detail_fields = {}
            for field in [
                "business_name",
                "tax_number",
                "business_start_date",
                "freelance_experience_years",
                "preferred_project_type",
                "preferred_work_style",
                "ng_client_companies",
                "interview_available",
            ]:
                if field in freelancer_data:
                    detail_fields[field] = freelancer_data.pop(field)

            # Personnel更新
            if freelancer_data:
                await personnel.update_from_dict(clean_dict(freelancer_data))
                await personnel.save()

            # FreelancerDetail更新
            if detail_fields:
                detail = await FreelancerDetail.filter(personnel=personnel).first()
                if detail:
                    await detail.update_from_dict(clean_dict(detail_fields))
                    await detail.save()
                else:
                    detail_fields["personnel"] = personnel
                    await FreelancerDetail.create(**clean_dict(detail_fields))

            return personnel

    async def delete_freelancer(self, freelancer_id: int) -> bool:
        """フリーランス削除"""
        personnel = await Personnel.filter(id=freelancer_id, person_type=PersonType.FREELANCER).first()
        if personnel:
            async with in_transaction():
                await personnel.delete()
            return True
        return False

    # ===== BP社員管理 =====
    async def list_bp_employees(
        self, page: int = 1, page_size: int = 10, search_params: Dict = None, include_details: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """BP社員一覧取得"""
        query = Personnel.filter(person_type=PersonType.BP_EMPLOYEE)

        if search_params:
            # 基本検索条件
            if search_params.get("name"):
                query = query.filter(name__icontains=search_params["name"])
            if search_params.get("code"):
                query = query.filter(code__icontains=search_params["code"])
            if search_params.get("employment_status"):
                query = query.filter(employment_status=search_params["employment_status"])
            # BP会社指定
            if search_params.get("bp_company_id"):
                query = query.filter(bp_employee_detail__bp_company_id=search_params["bp_company_id"])

        total = await query.count()
        personnel_list = (
            await query.prefetch_related(
                "bp_employee_detail", "bp_employee_detail__bp_company", "skills__skill", "contracts", "contracts__case"
            )
            .order_by("-updated_at")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )

        # Detail情報付きの辞書リストに変換
        result_data = []
        for personnel in personnel_list:
            data = await self._personnel_to_dict_with_details(personnel, include_details)
            result_data.append(data)

        return result_data, total

    async def get_bp_employee_by_id(
        self, bp_employee_id: int, include_details: bool = True
    ) -> Optional[Dict[str, Any]]:
        """ID指定でBP社員取得"""
        personnel = (
            await Personnel.filter(id=bp_employee_id, person_type=PersonType.BP_EMPLOYEE)
            .prefetch_related("bp_employee_detail", "bp_employee_detail__bp_company", "skills__skill")
            .first()
        )
        if personnel:
            return await self._personnel_to_dict_with_details(personnel, include_details)
        return None

    async def create_bp_employee(self, bp_employee_data: Dict[str, Any]) -> Personnel:
        """BP社員作成"""
        async with in_transaction():
            # BP社員タイプを設定
            bp_employee_data["person_type"] = PersonType.BP_EMPLOYEE

            # 詳細情報を分離
            detail_fields = {}
            for field in ["interview_available"]:
                if field in bp_employee_data:
                    detail_fields[field] = bp_employee_data.pop(field)

            # bp_company_idをbp_companyに変換
            if "bp_company_id" in bp_employee_data:
                detail_fields["bp_company_id"] = bp_employee_data.pop("bp_company_id")

            # Personnel作成
            personnel = await Personnel.create(**clean_dict(bp_employee_data))

            # BPEmployeeDetail作成
            if detail_fields:
                detail_fields["personnel"] = personnel
                await BPEmployeeDetail.create(**clean_dict(detail_fields))

            return personnel

    async def update_bp_employee(self, bp_employee_id: int, bp_employee_data: Dict[str, Any]) -> Optional[Personnel]:
        """BP社員更新"""
        personnel = await Personnel.filter(id=bp_employee_id, person_type=PersonType.BP_EMPLOYEE).first()
        if not personnel:
            return None

        async with in_transaction():
            # 詳細情報を分離
            detail_fields = {}
            for field in ["interview_available"]:
                if field in bp_employee_data:
                    detail_fields[field] = bp_employee_data.pop(field)

            # bp_company_idをbp_companyに変換
            if "bp_company_id" in bp_employee_data:
                detail_fields["bp_company_id"] = bp_employee_data.pop("bp_company_id")

            # Personnel更新
            if bp_employee_data:
                await personnel.update_from_dict(clean_dict(bp_employee_data))
                await personnel.save()

            # BPEmployeeDetail更新
            if detail_fields:
                detail = await BPEmployeeDetail.filter(personnel=personnel).first()
                if detail:
                    await detail.update_from_dict(clean_dict(detail_fields))
                    await detail.save()
                else:
                    detail_fields["personnel"] = personnel
                    await BPEmployeeDetail.create(**clean_dict(detail_fields))

            return personnel

    async def delete_bp_employee(self, bp_employee_id: int) -> bool:
        """BP社員削除"""
        personnel = await Personnel.filter(id=bp_employee_id, person_type=PersonType.BP_EMPLOYEE).first()
        if personnel:
            async with in_transaction():
                await personnel.delete()
            return True
        return False

    # ===== スキル管理（全人材共通） =====
    async def get_personnel_skills(
        self, personnel_id: int, page: int = 1, page_size: int = 10
    ) -> Tuple[List[PersonnelSkill], int]:
        """人材スキル一覧取得"""
        query = PersonnelSkill.filter(personnel_id=personnel_id).select_related("skill")

        total = await query.count()
        skills = (
            await query.order_by("-is_primary_skill", "-proficiency", "-years_of_experience")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )

        return skills, total

    async def add_personnel_skill(self, personnel_id: int, skill_data: Dict[str, Any]) -> PersonnelSkill:
        """人材スキル追加"""
        personnel = await Personnel.get(id=personnel_id)
        skill_name = skill_data.get("skill_name")
        category = skill_data.get("category")

        if not skill_name:
            raise ValueError("スキル名称は必須です")

        async with in_transaction():
            # スキル検索または作成
            skill, created = await Skill.get_or_create(name=skill_name, defaults={"category": category})

            # 既存スキル関連チェック
            existing = await PersonnelSkill.get_or_none(personnel=personnel, skill=skill)
            if existing:
                raise ValueError(f"既にスキルを保有しています: {skill_name}")

            # スキル関連作成
            personnel_skill = await PersonnelSkill.create(
                personnel=personnel,
                skill=skill,
                proficiency=skill_data.get("proficiency", 1),
                years_of_experience=skill_data.get("years_of_experience"),
                last_used_date=skill_data.get("last_used_date"),
                is_primary_skill=skill_data.get("is_primary_skill", False),
                remark=skill_data.get("remark"),
            )

            return personnel_skill

    async def update_personnel_skill(self, skill_id: int, skill_data: Dict[str, Any]) -> PersonnelSkill:
        """人材スキル更新"""
        personnel_skill = await PersonnelSkill.get_or_none(id=skill_id)
        if not personnel_skill:
            raise ValueError("スキル記録が存在しません")

        async with in_transaction():
            # スキル名更新
            skill_name = skill_data.get("skill_name")
            category = skill_data.get("category")

            if skill_name:
                skill, created = await Skill.get_or_create(name=skill_name, defaults={"category": category})
                personnel_skill.skill = skill

            # その他フィールド更新
            update_fields = ["proficiency", "years_of_experience", "last_used_date", "is_primary_skill", "remark"]
            for field in update_fields:
                if field in skill_data:
                    setattr(personnel_skill, field, skill_data[field])

            await personnel_skill.save()
            return personnel_skill

    async def delete_personnel_skill(self, skill_id: int) -> bool:
        """人材スキル削除"""
        personnel_skill = await PersonnelSkill.get_or_none(id=skill_id)
        if personnel_skill:
            async with in_transaction():
                await personnel_skill.delete()
            return True
        return False

    # ===== ヘルパーメソッド =====
    async def _personnel_to_dict_with_details(
        self, personnel: Personnel, include_details: bool = True
    ) -> Dict[str, Any]:
        """PersonnelをDetail情報付きの辞書に変換"""
        # 基本Personnel情報を辞書化
        data = await personnel.to_dict()

        if include_details:
            # person_typeに応じて対応するDetail情報を追加
            if personnel.person_type == PersonType.EMPLOYEE:
                if personnel.employee_detail:
                    detail = await personnel.employee_detail
                    data["employee_detail"] = await detail.to_dict()

            elif personnel.person_type == PersonType.FREELANCER:
                if personnel.freelancer_detail:
                    detail = await personnel.freelancer_detail
                    data["freelancer_detail"] = await detail.to_dict()

            elif personnel.person_type == PersonType.BP_EMPLOYEE:
                if personnel.bp_employee_detail:
                    detail = await personnel.bp_employee_detail
                    data["bp_employee_detail"] = await detail.to_dict()
                    # BP会社情報も含める
                    bp_company = await detail.bp_company
                    if bp_company:
                        data["bp_company"] = await bp_company.to_dict()

            # スキル情報を追加
            personnel_skills = (
                await PersonnelSkill.filter(personnel=personnel)
                .select_related("skill")
                .order_by("-is_primary_skill", "-proficiency", "-years_of_experience")
                .all()
            )
            skills_data = []
            for ps in personnel_skills:
                skill_dict = await ps.to_dict()
                skill_dict["skill_name"] = ps.skill.name
                skill_dict["skill_category"] = ps.skill.category
                skills_data.append(skill_dict)
            data["skills"] = skills_data

            # 现在有效契约信息を追加（一つだけ返す）
            current_date = date.today()
            current_contract = None

            # contracts がある場合、現在有効な契約を検索
            contracts = (
                await personnel.contracts.filter(
                    contract_start_date__lte=current_date, contract_end_date__gte=current_date, status="有効"
                )
                .prefetch_related("case", "calculation_items")
                .all()
            )

            if contracts:
                current_contract = contracts[0]  # 最初の有効契約を取得

            if current_contract:
                contract_data = await current_contract.to_dict()
                # 関連する案件情報も含める
                if current_contract.case:
                    case_data = await current_contract.case.to_dict()
                    contract_data["case"] = case_data
                # 契約精算項目も含める
                calculation_items = await current_contract.calculation_items.all()
                contract_data["calculation_items"] = [await item.to_dict() for item in calculation_items]
                data["current_contract"] = contract_data
            else:
                data["current_contract"] = None

        return data

    # ===== 業務ロジック =====
    async def get_available_personnel(
        self,
        person_type: PersonType = None,
        project_start_date: date = None,
        required_skills: List[str] = None,
        min_experience_years: float = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Personnel], int]:
        """稼働可能人材取得"""
        query = Q(is_active=True, employment_status="稼働可能")

        # 人材タイプ指定
        if person_type:
            query &= Q(person_type=person_type)

        # プロジェクト開始日フィルタ
        if project_start_date:
            query &= Q(available_start_date__lte=project_start_date) | Q(available_start_date__isnull=True)

        # スキル要件フィルタ
        if required_skills:
            for skill in required_skills:
                query &= Q(skills__skill__name__icontains=skill)

        # 経験年数フィルタ
        if min_experience_years:
            query &= Q(it_experience_years__gte=min_experience_years)

        total = await Personnel.filter(query).count()
        personnel_list = (
            await Personnel.filter(query)
            .order_by("-it_experience_years", "-updated_at")
            .limit(page_size)
            .offset((page - 1) * page_size)
            .all()
        )

        return personnel_list, total

    async def check_visa_expiring_soon(self, days: int = 90) -> List[Personnel]:
        """ビザ期限間近人材チェック"""
        from datetime import timedelta

        expiry_date = date.today() + timedelta(days=days)
        return await Personnel.filter(
            visa_expire_date__lte=expiry_date, visa_expire_date__gte=date.today(), is_active=True
        ).all()


# グローバルインスタンス
personnel_controller = PersonnelController()
