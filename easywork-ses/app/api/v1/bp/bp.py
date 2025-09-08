from typing import Optional

from fastapi import APIRouter, Query
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from app.controllers.bp_company import bp_company_controller as bp_controller
from app.models.bp import BPOrderEmailConfig, BPPaymentEmailConfig
from app.schemas import Fail, Success
from app.schemas.bp import (
    AddBPCompanySchema, 
    UpdateBPCompanySchema,
    AddBPSalesRepresentativeSchema, 
    UpdateBPSalesRepresentativeSchema,
    AddBPOrderEmailConfigSchema,
    UpdateBPOrderEmailConfigSchema,
    AddBPPaymentEmailConfigSchema,
    UpdateBPPaymentEmailConfigSchema
)

router = APIRouter()


@router.get("/list", summary="協力会社一覧取得")
async def get_bp_list(
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
    representative: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    try:
        data, total = await bp_controller.get_bp_companies_with_filters(
            page=page, page_size=pageSize, name=name, representative=representative, status=status
        )
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/get", summary="idで協力会社取得")
async def get_bp_company(id: int = Query(...)):
    try:
        data = await bp_controller.get_bp_company_dict_by_id(bp_company_id=id)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="協力会社が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/add", summary="協力会社新規")
async def add_bp_company(company_data: AddBPCompanySchema):
    try:
        data = await bp_controller.create_bp_company_dict(bp_company=company_data)
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/update", summary="協力会社更新")
async def update_bp_company(company_data: UpdateBPCompanySchema):
    try:
        data = await bp_controller.update_bp_company_dict(bp_company=company_data)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="協力会社が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/delete", summary="協力会社削除")
async def delete_bp_company(id: int = Query(...)):
    try:
        await bp_controller.delete_bp_company(bp_company_id=id)
        return Success()
    except Exception as e:
        return Fail(msg=str(e))


# ==================== 営業担当者関連のAPI ====================

@router.get("/sales-rep/list", summary="BP営業担当者一覧取得")
async def get_bp_sales_rep_list(
    bp_company_id: Optional[int] = Query(None, description="BP会社ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None, description="氏名"),
    email: Optional[str] = Query(None, description="メールアドレス"),
    is_active: Optional[bool] = Query(None, description="有効フラグ"),
):
    try:
        q = Q()
        if bp_company_id is not None:
            q &= Q(bp_company_id=bp_company_id)
        if name:
            q &= Q(name__icontains=name)
        if email:
            q &= Q(email__icontains=email)
        if is_active is not None:
            q &= Q(is_active=is_active)

        data, total = await bp_controller.get_bp_sales_reps_with_filters(
            page=page, page_size=pageSize, search=q
        )
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/sales-rep/get", summary="BP営業担当者取得")
async def get_bp_sales_rep(id: int = Query(..., description="営業担当者ID")):
    try:
        data = await bp_controller.get_bp_sales_rep_dict_by_id(sales_rep_id=id)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="営業担当者が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/sales-rep/add", summary="BP営業担当者新規作成")
async def add_bp_sales_rep(rep_data: AddBPSalesRepresentativeSchema):
    try:
        data = await bp_controller.create_bp_sales_rep_dict(sales_rep_data=rep_data)
        return Success(data=data)
    except ValueError as ve:
        return Fail(msg=str(ve))
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/sales-rep/update", summary="BP営業担当者更新")
async def update_bp_sales_rep(rep_data: UpdateBPSalesRepresentativeSchema):
    try:
        data = await bp_controller.update_bp_sales_rep_dict(sales_rep_data=rep_data)
        if data:
            return Success(data=data)
        else:
            return Fail(msg="営業担当者が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.delete("/sales-rep/delete", summary="BP営業担当者削除")
async def delete_bp_sales_rep(id: int = Query(..., description="営業担当者ID")):
    try:
        result = await bp_controller.delete_bp_sales_rep(sales_rep_id=id)
        if result:
            return Success(msg="営業担当者を削除しました")
        else:
            return Fail(msg="営業担当者が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


@router.get("/sales-rep/by-company/{bp_company_id}", summary="BP会社の営業担当者取得")
async def get_sales_reps_by_company(bp_company_id: int):
    try:
        data = await bp_controller.get_sales_reps_by_company(bp_company_id=bp_company_id)
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


# ==================== 注文書メール設定関連のAPI ====================

@router.get("/order-email-config/list", summary="注文書メール設定一覧取得")
async def get_order_email_config_list(
    bp_company_id: Optional[int] = Query(None, description="BP会社ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    is_active: Optional[bool] = Query(None, description="有効フラグ"),
):
    try:
        query = BPOrderEmailConfig.all()
        
        if bp_company_id is not None:
            query = query.filter(bp_company_id=bp_company_id)
        if is_active is not None:
            query = query.filter(is_active=is_active)
            
        total = await query.count()
        offset = (page - 1) * pageSize
        configs = await query.prefetch_related("bp_company", "sender_sales_rep").offset(offset).limit(pageSize).all()
        
        data = []
        for config in configs:
            config_data = await config.to_dict()
            config_data["bp_company_name"] = config.bp_company.name
            config_data["sender_name"] = config.sender_sales_rep.name if config.sender_sales_rep else config.sender_name
            config_data["sender_email"] = config.sender_sales_rep.email if config.sender_sales_rep else config.sender_email
            data.append(config_data)
        
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/order-email-config/add", summary="注文書メール設定新規作成")
async def add_order_email_config(config_data: AddBPOrderEmailConfigSchema):
    try:
        config = await BPOrderEmailConfig.create(**config_data.model_dump())
        created_config = await BPOrderEmailConfig.get(id=config.id).prefetch_related("bp_company", "sender_sales_rep")
        
        data = await created_config.to_dict()
        data["bp_company_name"] = created_config.bp_company.name
        data["sender_name"] = created_config.sender_sales_rep.name if created_config.sender_sales_rep else created_config.sender_name
        
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))


@router.put("/order-email-config/update", summary="注文書メール設定更新")
async def update_order_email_config(config_data: UpdateBPOrderEmailConfigSchema):
    try:
        config = await BPOrderEmailConfig.get(id=config_data.id)
        
        update_data = config_data.model_dump(exclude_unset=True, exclude={"id"})
        for field, value in update_data.items():
            setattr(config, field, value)
        
        await config.save()
        updated_config = await BPOrderEmailConfig.get(id=config.id).prefetch_related("bp_company", "sender_sales_rep")
        
        data = await updated_config.to_dict()
        data["bp_company_name"] = updated_config.bp_company.name
        data["sender_name"] = updated_config.sender_sales_rep.name if updated_config.sender_sales_rep else updated_config.sender_name
        
        return Success(data=data)
    except DoesNotExist:
        return Fail(msg="注文書メール設定が見つかりませんでした")
    except Exception as e:
        return Fail(msg=str(e))


# ==================== 支払通知書メール設定関連のAPI ====================

@router.get("/payment-email-config/list", summary="支払通知書メール設定一覧取得")
async def get_payment_email_config_list(
    bp_company_id: Optional[int] = Query(None, description="BP会社ID"),
    page: Optional[int] = Query(1, ge=1),
    pageSize: Optional[int] = Query(10, ge=1, le=100),
    is_active: Optional[bool] = Query(None, description="有効フラグ"),
):
    try:
        query = BPPaymentEmailConfig.all()
        
        if bp_company_id is not None:
            query = query.filter(bp_company_id=bp_company_id)
        if is_active is not None:
            query = query.filter(is_active=is_active)
            
        total = await query.count()
        offset = (page - 1) * pageSize
        configs = await query.prefetch_related("bp_company", "sender_sales_rep").offset(offset).limit(pageSize).all()
        
        data = []
        for config in configs:
            config_data = await config.to_dict()
            config_data["bp_company_name"] = config.bp_company.name
            config_data["sender_name"] = config.sender_sales_rep.name if config.sender_sales_rep else config.sender_name
            config_data["sender_email"] = config.sender_sales_rep.email if config.sender_sales_rep else config.sender_email
            data.append(config_data)
        
        return Success(data=data, total=total)
    except Exception as e:
        return Fail(msg=str(e))


@router.post("/payment-email-config/add", summary="支払通知書メール設定新規作成")
async def add_payment_email_config(config_data: AddBPPaymentEmailConfigSchema):
    try:
        config = await BPPaymentEmailConfig.create(**config_data.model_dump())
        created_config = await BPPaymentEmailConfig.get(id=config.id).prefetch_related("bp_company", "sender_sales_rep")
        
        data = await created_config.to_dict()
        data["bp_company_name"] = created_config.bp_company.name
        data["sender_name"] = created_config.sender_sales_rep.name if created_config.sender_sales_rep else created_config.sender_name
        
        return Success(data=data)
    except Exception as e:
        return Fail(msg=str(e))
