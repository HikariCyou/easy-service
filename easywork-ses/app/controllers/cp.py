from tortoise.expressions import Q

from app.models.client import ClientCompany
from app.schemas.cp import AddClientCompanySchema, UpdateClientCompanySchema


class CPCompanyController:
    def __init__(self):
        pass

    async def list_client_companies(self, page: int = 1, page_size: int = 10, search: Q = None, orders: list = []):
        query = ClientCompany.filter(search)
        total = await query.count()
        companies = await query.offset((page - 1) * page_size).limit(page_size).order_by(*orders)
        return companies, total

    async def get_company_by_id(self, id: int):
        company = await ClientCompany.get_or_none(id=id)
        return company

    async def add_client_company(self, company_data: AddClientCompanySchema):
        company = await ClientCompany.create(**company_data.model_dump(exclude_unset=True))
        return company

    async def update_client_company(self, company_data: UpdateClientCompanySchema):
        company = await ClientCompany.get_or_none(id=company_data.id)
        if company:
            dict_data = company_data.model_dump(exclude_unset=True)
            company.update_from_dict(dict_data)
            await company.save()
        return company

    async def delete_client_company(self, id: int):
        company = await ClientCompany.get_or_none(id=id)
        if company:
            await company.delete()
        return company


cp_controller = CPCompanyController()
