from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.bank import ClientBankAccount
from app.models.client import ClientCompany, ClientCompanyContract, ClientContact
from app.schemas.client import (
    AddClientBankAccountSchema,
    AddClientCompanyContractSchema,
    UpdateClientBankAccountSchema,
    UpdateClientCompanyContractSchema,
)
from app.schemas.cp import AddClientCompanySchema, UpdateClientCompanySchema
from app.utils.common import clean_dict


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

    # === 銀行口座管理 ===

    async def get_bank_accounts_by_company(self, client_company_id: int):
        """顧客会社の銀行口座一覧取得"""
        accounts = (
            await ClientBankAccount.filter(client_company_id=client_company_id, is_active=True)
            .prefetch_related("bank", "branch")
            .all()
        )
        return accounts

    async def add_bank_account(self, account_data: AddClientBankAccountSchema):
        """銀行口座作成"""
        data = clean_dict(account_data.model_dump(exclude_unset=True))
        account = await ClientBankAccount.create(**data)
        return account

    async def update_bank_account(self, account_data: UpdateClientBankAccountSchema):
        """銀行口座更新"""
        account = await ClientBankAccount.get_or_none(id=account_data.id)
        if account:
            dict_data = clean_dict(account_data.model_dump(exclude_unset=True, exclude={"id"}))
            account.update_from_dict(dict_data)
            await account.save()
        return account

    async def delete_bank_account(self, account_id: int):
        """銀行口座削除"""
        account = await ClientBankAccount.get_or_none(id=account_id)
        if account:
            async with in_transaction():
                await account.delete()
            return True
        return False

    # === 契約管理 ===

    async def list_client_contracts(
        self, page: int = 1, page_size: int = 10, client_company_id: int = None, search: Q = None, orders: list = []
    ):
        """顧客会社契約一覧取得"""
        query = ClientCompanyContract.all()
        if client_company_id:
            query = query.filter(client_company_id=client_company_id)
        if search:
            query = query.filter(search)

        total = await query.count()
        contracts = (
            await query.prefetch_related("client_company")
            .offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(*orders)
        )
        return contracts, total

    async def get_contract_by_id(self, contract_id: int):
        """契約取得"""
        contract = await ClientCompanyContract.get_or_none(id=contract_id).prefetch_related("client_company")
        return contract

    async def add_client_contract(self, contract_data: AddClientCompanyContractSchema):
        """顧客会社契約作成"""
        # 顧客会社の存在確認
        client_company = await ClientCompany.get_or_none(id=contract_data.client_company_id)
        if not client_company:
            raise ValueError("指定された顧客会社が見つかりません")

        data = clean_dict(contract_data.model_dump(exclude_unset=True))

        # contract_documentsの処理
        if "contract_documents" in data and data["contract_documents"]:
            # Pydantic modelをdictに変換
            documents = []
            for doc in data["contract_documents"]:
                if hasattr(doc, "model_dump"):
                    documents.append(doc.model_dump())
                else:
                    documents.append(doc)
            data["contract_documents"] = documents

        contract = await ClientCompanyContract.create(**data)
        return contract

    async def update_client_contract(self, contract_data: UpdateClientCompanyContractSchema):
        """顧客会社契約更新"""
        contract = await ClientCompanyContract.get_or_none(id=contract_data.id)
        if contract:
            dict_data = clean_dict(contract_data.model_dump(exclude_unset=True, exclude={"id"}))

            # contract_documentsの処理
            if "contract_documents" in dict_data and dict_data["contract_documents"] is not None:
                documents = []
                for doc in dict_data["contract_documents"]:
                    if hasattr(doc, "model_dump"):
                        documents.append(doc.model_dump())
                    else:
                        documents.append(doc)
                dict_data["contract_documents"] = documents

            contract.update_from_dict(dict_data)
            await contract.save()
        return contract

    async def delete_client_contract(self, contract_id: int):
        """顧客会社契約削除"""
        contract = await ClientCompanyContract.get_or_none(id=contract_id)
        if contract:
            async with in_transaction():
                await contract.delete()
            return True
        return False

    async def get_contract_documents(self, contract_id: int):
        """契約文書一覧取得"""
        contract = await ClientCompanyContract.get_or_none(id=contract_id)
        if contract:
            return contract.get_contract_documents()
        return []


cp_controller = CPCompanyController()
