from typing import Optional

from fastapi import APIRouter, Query
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from app.controllers.cp import cp_controller
from app.models.client import ClientContact
from app.schemas import Fail, Success
from app.schemas.cp import AddClientCompanySchema, UpdateClientCompanySchema, AddClientSalesRepresentativeSchema, \
    UpdateClientSalesRepresentativeSchema
from app.schemas.client import (
    AddClientBankAccountSchema, UpdateClientBankAccountSchema,
    AddClientCompanyContractSchema, UpdateClientCompanyContractSchema
)

router = APIRouter()


@router.get("/list", summary="取り先会社一覧を取得")
async def get_cp_list(
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1),
    company_name: Optional[str] = Query(None),
    representative: Optional[str] = Query(None),
):
    try:
        q = Q()
        if company_name:
            q &= Q(company_name__icontains=company_name)
        if representative:
            q &= Q(representative__icontains=representative)

        companies, total = await cp_controller.list_client_companies(page=page, page_size=pageSize, search=q)
        data = [await company.to_dict() for company in companies]

        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="取り先会社取得")
async def get_cp_company(id: int = Query(..., description="取り先会社ID")):
    try:
        company = await cp_controller.get_company_by_id(id)
        if company:
            company_dict = await company.to_dict()
            return Success(data=company_dict)
        else:
            return Fail(msg="取り先会社が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/add", summary="取り先会社新規")
async def add_cp_company(company_data: AddClientCompanySchema):
    await cp_controller.add_client_company(company_data=company_data)
    return Success()


@router.put("/update", summary="取り先会社更新")
async def update_cp_company(company_data: UpdateClientCompanySchema):
    await cp_controller.update_client_company(company_data=company_data)
    return Success()


@router.delete("/delete", summary="取り先会社削除")
async def delete_cp_company(id: Optional[int] = Query(...)):
    result = await cp_controller.delete_client_company(id=id)
    if result:
        return Success()
    else:
        return Fail()


# ==================== 取り先会社営業担当者関連のAPI ====================

@router.get("/sales-rep/list", summary="取り先会社営業担当者一覧取得")
async def get_client_sales_rep_list(
    client_company_id: Optional[int] = Query(None, description="取り先会社ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None, description="担当者名"),
    email: Optional[str] = Query(None, description="メールアドレス"),
    is_active: Optional[bool] = Query(None, description="有効フラグ"),
):
    try:
        query = ClientContact.all()
        
        if client_company_id is not None:
            query = query.filter(client_company_id=client_company_id)
        if name:
            query = query.filter(name__icontains=name)
        if email:
            query = query.filter(email__icontains=email)
        if is_active is not None:
            query = query.filter(is_active=is_active)
            
        total = await query.count()
        offset = (page - 1) * pageSize
        sales_reps = await query.prefetch_related("client_company").offset(offset).limit(pageSize).all()
        
        data = []
        for rep in sales_reps:
            rep_data = await rep.to_dict()
            rep_data["client_company_name"] = rep.client_company.company_name
            data.append(rep_data)
        
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/sales-rep/get", summary="取り先会社営業担当者取得")
async def get_client_sales_rep(id: int = Query(..., description="営業担当者ID")):
    try:
        rep = await ClientContact.get(id=id).prefetch_related("client_company")
        
        data = await rep.to_dict()
        data["client_company_name"] = rep.client_company.company_name
        
        return Success(data=data)
    except DoesNotExist:
        return Fail(msg="営業担当者が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/sales-rep/add", summary="取り先会社営業担当者新規作成")
async def add_client_sales_rep(rep_data: AddClientSalesRepresentativeSchema):
    try:
        # 取り先会社の存在確認
        from app.models.client import ClientCompany
        client_company = await ClientCompany.filter(id=rep_data.client_company_id).first()
        if not client_company:
            return Fail(msg="指定された取り先会社が見つかりませんでした")
        
        rep = await ClientContact.create(**rep_data.model_dump())
        created_rep = await ClientContact.get(id=rep.id).prefetch_related("client_company")
        
        data = await created_rep.to_dict()
        data["client_company_name"] = created_rep.client_company.company_name
        
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/sales-rep/update", summary="取り先会社営業担当者更新")
async def update_client_sales_rep(rep_data: UpdateClientSalesRepresentativeSchema):
    try:
        rep = await ClientContact.get(id=rep_data.id)
        
        update_data = rep_data.model_dump(exclude_unset=True, exclude={"id"})
        for field, value in update_data.items():
            setattr(rep, field, value)
        
        await rep.save()
        updated_rep = await ClientContact.get(id=rep.id).prefetch_related("client_company")
        
        data = await updated_rep.to_dict()
        data["client_company_name"] = updated_rep.client_company.company_name
        
        return Success(data=data)
    except DoesNotExist:
        return Fail(msg="営業担当者が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/sales-rep/delete", summary="取り先会社営業担当者削除")
async def delete_client_sales_rep(id: int = Query(..., description="営業担当者ID")):
    try:
        rep = await ClientContact.get(id=id)
        await rep.delete()
        
        return Success(msg="営業担当者を削除しました")
    except DoesNotExist:
        return Fail(msg="営業担当者が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/sales-rep/by-company/{client_company_id}", summary="取り先会社の営業担当者取得")
async def get_sales_reps_by_client_company(client_company_id: int):
    try:
        reps = await ClientContact.filter(
            client_company_id=client_company_id, 
            is_active=True
        ).all()
        
        data = []
        for rep in reps:
            rep_data = await rep.to_dict(exclude_fields=["client_company_id", "gender", "is_active", "remark", "created_at", "updated_at"])
            data.append(rep_data)
        
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


# ==================== 銀行口座関連のAPI ====================

@router.get("/bank-account/list", summary="顧客会社銀行口座一覧取得")
async def get_client_bank_accounts_list(
    client_company_id: int = Query(..., description="顧客会社ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
):
    try:
        accounts = await cp_controller.get_bank_accounts_by_company(client_company_id)
        
        data = []
        for account in accounts:
            account_dict = await account.to_dict()
            account_dict["bank_name"] = account.bank.name if account.bank else None
            account_dict["branch_name"] = account.branch.name if account.branch else None
            data.append(account_dict)
        
        return Success(data=data, total=len(data))
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/bank-account/add", summary="顧客会社銀行口座新規作成")
async def add_client_bank_account(account_data: AddClientBankAccountSchema):
    try:
        account = await cp_controller.add_bank_account(account_data)
        account_dict = await account.to_dict()
        return Success(data=account_dict)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/bank-account/update", summary="顧客会社銀行口座更新")
async def update_client_bank_account(account_data: UpdateClientBankAccountSchema):
    try:
        account = await cp_controller.update_bank_account(account_data)
        if account:
            account_dict = await account.to_dict()
            return Success(data=account_dict)
        else:
            return Fail(msg="口座が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/bank-account/delete", summary="顧客会社銀行口座削除")
async def delete_client_bank_account(id: int = Query(..., description="口座ID")):
    try:
        result = await cp_controller.delete_bank_account(id)
        if result:
            return Success(msg="口座を削除しました")
        else:
            return Fail(msg="口座が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


# ==================== 契約関連のAPI ====================

@router.get("/contract/list", summary="顧客会社契約一覧取得")
async def get_client_contracts_list(
    client_company_id: Optional[int] = Query(None, description="顧客会社ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None, description="契約ステータス"),
    contract_form: Optional[str] = Query(None, description="SES契約形態"),
):
    try:
        from tortoise.expressions import Q
        
        search = Q()
        if status:
            search &= Q(status=status)
        if contract_form:
            search &= Q(contract_form=contract_form)
        
        contracts, total = await cp_controller.list_client_contracts(
            page=page, page_size=pageSize, client_company_id=client_company_id, search=search, orders=['-updated_at']
        )
        
        data = []
        for contract in contracts:
            contract_dict = await contract.to_dict()
            contract_dict["client_company_name"] = contract.client_company.company_name if contract.client_company else None
            data.append(contract_dict)
        
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/contract/get", summary="顧客会社契約取得")
async def get_client_contract(id: int = Query(..., description="契約ID")):
    try:
        contract = await cp_controller.get_contract_by_id(id)
        if contract:
            contract_dict = await contract.to_dict()
            contract_dict["client_company_name"] = contract.client_company.company_name if contract.client_company else None
            return Success(data=contract_dict)
        else:
            return Fail(msg="契約が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/contract/add", summary="顧客会社契約新規作成")
async def add_client_contract(contract_data: AddClientCompanyContractSchema):
    try:
        contract = await cp_controller.add_client_contract(contract_data)
        contract_dict = await contract.to_dict()
        return Success(data=contract_dict)
    except ValueError as e:
        return Fail(msg=str(e))
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/contract/update", summary="顧客会社契約更新")
async def update_client_contract(contract_data: UpdateClientCompanyContractSchema):
    try:
        contract = await cp_controller.update_client_contract(contract_data)
        if contract:
            contract_dict = await contract.to_dict()
            return Success(data=contract_dict)
        else:
            return Fail(msg="契約が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/contract/delete", summary="顧客会社契約削除")
async def delete_client_contract(id: int = Query(..., description="契約ID")):
    try:
        result = await cp_controller.delete_client_contract(id)
        if result:
            return Success(msg="契約を削除しました")
        else:
            return Fail(msg="契約が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/contract/documents/{contract_id}", summary="契約文書一覧取得")
async def get_contract_documents(contract_id: int):
    try:
        documents = await cp_controller.get_contract_documents(contract_id)
        return Success(data=documents)
    except Exception as e:
        return Fail(msg=str(e))
