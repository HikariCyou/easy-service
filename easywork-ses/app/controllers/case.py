from typing import Optional

from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.case import Case, CaseCandidate
from app.schemas.case import (AddCaseCandidateSchema, AddCaseSchema,
                              UpdateCaseCandidateSchema, UpdateCaseSchema)
from app.utils.common import clean_dict


class CaseController:
    def __init__(self):
        pass

    async def list_cases(self, page: int = 1, page_size: int = 10, search: Q = None, order: list = []):
        query = Case.filter(search)
        total = await query.count()
        cases = await query.select_related("client_company").order_by(*order).limit(page_size).offset((page - 1) * page_size).all()
        return cases, total

    async def get_cases_with_filters(
        self,
        page: Optional[int] = 1,
        page_size: Optional[int] = 10,
        title: Optional[str] = None,
        status: Optional[str] = None,
        client_company_id: Optional[int] = None,
    ):
        q = Q()
        if title:
            q &= Q(title__icontains=title)
        if status:
            q &= Q(status=status)
        if client_company_id:
            q &= Q(client_company_id=client_company_id)

        cases, total = await self.list_cases(page=page, page_size=page_size, search=q)
        data = []
        for case in cases:
            case_dict = await case.to_dict()
            if case.client_company:
                case_dict['client_company'] = await case.client_company.to_dict()
            data.append(case_dict)
        return data, total

    async def get_case_by_id(self, case_id: int):
        case = await Case.get_or_none(id=case_id).select_related("client_company")
        return case

    async def get_case_dict_by_id(self, case_id: int):
        case = await self.get_case_by_id(case_id)
        if case:
            case_dict = await case.to_dict()
            # 添加客户公司信息
            if case.client_company:
                case_dict['client_company'] = await case.client_company.to_dict()
            return case_dict
        return None

    async def create_case(self, case_data: AddCaseSchema):
        async with in_transaction():
            data_dict = clean_dict(case_data.model_dump(exclude_unset=True))
            case = await Case.create(**data_dict)
            return case

    async def create_case_dict(self, case_data: AddCaseSchema):
        case = await self.create_case(case_data)
        return await case.to_dict()

    async def update_case(self, case_data: UpdateCaseSchema):
        case = await Case.get_or_none(id=case_data.id)
        if case:
            async with in_transaction():
                data_dict = clean_dict(case_data.model_dump(exclude_unset=True))
                await case.update_from_dict(data_dict)
                await case.save()
        return case

    async def update_case_dict(self, case_data: UpdateCaseSchema):
        case = await self.update_case(case_data)
        if case:
            return await case.to_dict()
        return None

    async def delete_case(self, case_id: int):
        case = await Case.get_or_none(id=case_id)
        if case:
            async with in_transaction():
                await case.delete()
        return case


class CaseCandidateController:
    def __init__(self):
        pass

    async def list_candidates(self, page: int = 1, page_size: int = 10, search: Q = None, order: list = []):
        query = CaseCandidate.filter(search)
        total = await query.count()
        candidates = (
            await query.order_by(*order)
            .limit(page_size)
            .offset((page - 1) * page_size)
            .select_related("case", "bp_employee", "employee", "freelancer")
            .all()
        )
        return candidates, total

    async def get_candidates_by_case_id(self, case_id: int, page: int = 1, page_size: int = 10):
        q = Q(case_id=case_id)
        candidates, total = await self.list_candidates(page=page, page_size=page_size, search=q)
        data = []
        for candidate in candidates:
            candidate_dict = await candidate.to_dict()
            candidate_dict["candidate_name"] = candidate.candidate_name
            candidate_dict["candidate_type"] = candidate.candidate_type
            data.append(candidate_dict)
        return data, total

    async def get_candidate_by_id(self, candidate_id: int):
        candidate = await CaseCandidate.get_or_none(id=candidate_id).select_related(
            "case", "bp_employee", "employee", "freelancer"
        )
        return candidate

    async def get_candidate_dict_by_id(self, candidate_id: int):
        candidate = await self.get_candidate_by_id(candidate_id)
        if candidate:
            candidate_dict = await candidate.to_dict()
            candidate_dict["candidate_name"] = candidate.candidate_name
            candidate_dict["candidate_type"] = candidate.candidate_type
            return candidate_dict
        return None

    async def add_candidate(self, candidate_data: AddCaseCandidateSchema):
        async with in_transaction():
            data_dict = clean_dict(candidate_data.model_dump(exclude_unset=True))
            candidate = await CaseCandidate.create(**data_dict)
            return candidate

    async def add_candidate_dict(self, candidate_data: AddCaseCandidateSchema):
        candidate = await self.add_candidate(candidate_data)
        candidate_dict = await candidate.to_dict()
        candidate_dict["candidate_name"] = candidate.candidate_name
        candidate_dict["candidate_type"] = candidate.candidate_type
        return candidate_dict

    async def update_candidate(self, candidate_data: UpdateCaseCandidateSchema):
        candidate = await CaseCandidate.get_or_none(id=candidate_data.id)
        if candidate:
            async with in_transaction():
                data_dict = clean_dict(candidate_data.model_dump(exclude_unset=True))
                await candidate.update_from_dict(data_dict)
                await candidate.save()
        return candidate

    async def update_candidate_dict(self, candidate_data: UpdateCaseCandidateSchema):
        candidate = await self.update_candidate(candidate_data)
        if candidate:
            candidate_dict = await candidate.to_dict()
            candidate_dict["candidate_name"] = candidate.candidate_name
            candidate_dict["candidate_type"] = candidate.candidate_type
            return candidate_dict
        return None

    async def delete_candidate(self, candidate_id: int):
        candidate = await CaseCandidate.get_or_none(id=candidate_id)
        if candidate:
            async with in_transaction():
                await candidate.delete()
        return candidate


case_controller = CaseController()
case_candidate_controller = CaseCandidateController()
