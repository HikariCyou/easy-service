from typing import Optional

from fastapi import APIRouter, Query
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from app.controllers.cp import cp_controller
from app.models.client import ClientContact
from app.schemas import Fail, Success
from app.schemas.cp import AddClientCompanySchema, UpdateClientCompanySchema
from app.schemas.client import AddClientSalesRepresentativeSchema, UpdateClientSalesRepresentativeSchema

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
