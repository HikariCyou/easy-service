import json
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.params import Depends, Header

from app.controllers.employee import  employee_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import get_current_employee
from app.core.user_client import user_client
from app.core.process_client import  process_client
from app.models import EmployeeAddress, EmployeeEmergencyContact
from app.schemas import Success,Fail
from app.schemas.employee import EmployeeAddressSchema, EmployeeSchema, EmployeeEmergencyContactSchema, \
    EmployeeBankSchema, EmployeeResidenceStatusSchema, EmployeeUpdateSchema, EmployeePassportSchema, \
    EmployeeSocialInsuranceSchema, EmployeeEmploymentInsuranceSchema

router = APIRouter()

JOIN_PROCESS_KEY = "TOB_JOIN"

@router.get("/list", summary="従業員リストを取得")
async  def get_employee_list(
        page: Optional[int] = Query(1, description="ページ番号", ge=1),
        page_size: Optional[int] = Query(10, description="1ページあたりの従業員数", ge=1, le=100),
        authorization: str = Header(..., description="token验证")
):
    employees , total = await employee_controller.list_employees(
        page=page,
        page_size=page_size
    )
    user_ids = [e.user_id for e in employees]
    user_map = await user_client.get_users_by_ids(user_ids,token=authorization)

    result = []
    for e in employees:
        employee_dict = await e.to_dict()
        user_info = user_map.get(e.user_id)
        result.append({
            **user_info,
            **employee_dict
        })

    return Success(data=result, total=total )


@router.get("/get", summary="従業員情報を取得")
async def get_employee_info(
    employee_id: int = Query(..., description="従業員ID"),
    authorization: str = Header(..., description="token验证")
):
    """
    従業員情報を取得
    """
    employee = await employee_controller.get_employee_by_id(employee_id)
    if not employee:
        return Fail(msg="従業員が見つかりません")

    data = await employee_controller.get_full_employee_info(employee=employee , token=authorization)

    return Success(data= data)



@router.get("/get_by_process_instance_id", summary="プロセスインスタンスIDから従業員情報を取得")
async def get_employee_by_process_instance_id(
    process_instance_id: str = Query(..., description="プロセスインスタンスID"),
    authorization: str = Header(..., description="token验证")
):
    """
    プロセスインスタンスIDから従業員情報を取得
    """
    employee = await employee_controller.get_employee_by_process_instance_id(process_instance_id=process_instance_id)
    if not employee:
        return Fail(msg="従業員が見つかりません")

    data = await employee_controller.get_full_employee_info(employee=employee, token=authorization)
    return Success(data=data)

@router.post("/register", summary="従業員を登録")
async def register_employee(
    employee_data: EmployeeSchema
):
    """
    新しい従業員を登録
    """
    login_user_id = CTX_USER_ID.get()
    employee_data.user_id = login_user_id
    employee = await employee_controller.register_employee(user_id= login_user_id,employee_data=employee_data)
    return Success(data=await employee.to_dict())


@router.put("/update", summary="従業員情報を更新")
async def update_employee(
    employee_data: EmployeeUpdateSchema,
):
    employee = await employee_controller.get_employee_by_id(employee_id=employee_data.id)
    if not employee:
        return Fail(msg="従業員が見つかりません")
    # 更新処理
    await employee_controller.update_employee_info(employee=employee, employee_data=employee_data)
    return Success(data=await employee.to_dict())


# 住所と連絡先の情報を取得
@router.get("/address/get", summary="従業員の住所と連絡先を取得")
async def get_employee_address(
    employee = Depends(get_current_employee)
):
    """
    従業員の住所と連絡先情報を取得
    """
    employee_id = employee.id
    employee_address = await EmployeeAddress.get_or_none(employee_id=employee_id)
    if  employee_address:
        return Success(data=await employee_address.to_dict())
    return None



# 住所と連絡先 save
@router.post("/address/save", summary="従業員情報を保存")
async def save_employee_address(
    address_data: EmployeeAddressSchema,
    employee = Depends(get_current_employee)
):
    address_data.employee_id = employee.id
    await employee_controller.save_employee_address_info(address_data= address_data)

    return Success(msg="従業員の住所情報を保存しました")

# 緊急連絡先取得
@router.get("/emergency_contact/get", summary="緊急連絡先を取得")
async def get_emergency_contact(
    employee = Depends(get_current_employee)
):
    """
    従業員の緊急連絡先情報を取得
    """
    employee_id = employee.id
    emergency_contact = await EmployeeEmergencyContact.get_or_none(employee_id=employee_id)
    if emergency_contact:
        return Success(data=await emergency_contact.to_dict())
    return Fail(msg="緊急連絡先が見つかりません")

# 緊急連絡先保存
@router.post("/emergency_contact/save", summary="緊急連絡先を保存")
async def save_emergency_contact(
    contact_data: EmployeeEmergencyContactSchema,
    employee = Depends(get_current_employee)
):
    """
    従業員の緊急連絡先情報を保存
    """
    contact_data.employee_id = employee.id
    contact_info = await employee_controller.save_employee_emergency_contact_info(contact_data=contact_data)
    if not contact_info:
        return Fail(msg="緊急連絡先の保存に失敗しました")

    return Success(msg="緊急連絡先を保存しました")


# 銀行口座情報を取得
@router.get("/bank/get", summary="銀行口座情報を取得")
async def get_employee_bank_info(
    employee = Depends(get_current_employee)
):
    """
    従業員の銀行口座情報を取得
    """
    bank_info = await employee_controller.get_employee_bank_info(employee_id=employee.id)
    if  bank_info:
        return Success(data=await bank_info.to_dict())

    return  None

# 銀行口座情報を保存
@router.post("/bank/save", summary="銀行口座情報を保存")
async def save_employee_bank_info(
    bank_data: EmployeeBankSchema,
    employee = Depends(get_current_employee)
):
    """
    従業員の銀行口座情報を保存
    """
    bank_data.employee_id = employee.id
    bank_info = await employee_controller.save_employee_bank_info(bank_data=bank_data)
    if not bank_info:
        return Fail(msg="銀行口座情報の保存に失敗しました")

    return Success(msg="銀行口座情報を保存しました")

# 在留カード情報を取得
@router.get("/resident_card/get", summary="在留カード情報を取得")
async def get_employee_resident_card_info(
    employee = Depends(get_current_employee)
):
    """
    従業員の在留カード情報を取得
    """
    resident_card_info = await employee_controller.get_employee_resident_card_info(employee_id=employee.id)
    if resident_card_info:
        return Success(data=await resident_card_info.to_dict())

    return None


# 在留カード情報を保存
@router.post("/resident_card/save", summary="在留カード情報を保存")
async def save_employee_resident_card_info(
    resident_data: EmployeeResidenceStatusSchema,
    employee = Depends(get_current_employee)
):
    """
    従業員の在留カード情報を保存
    """
    resident_data.employee_id = employee.id
    resident_card_info = await employee_controller.save_employee_resident_card_info(resident_data=resident_data)
    if not resident_card_info:
        return Fail(msg="在留カード情報の保存に失敗しました")

    return Success(msg="在留カード情報を保存しました")


# 旅券情報を取得
@router.get("/passport/get", summary="旅券情報を取得")
async def get_employee_passport_info(
    employee = Depends(get_current_employee)
):
    """
    従業員の旅券情報を取得
    """
    passport_info = await employee_controller.get_employee_passport_info(employee_id=employee.id)
    if passport_info:
        return Success(data=await passport_info.to_dict())

    return None


@router.post("/passport/save", summary="旅券情報を保存")
async def save_employee_passport_info(
    passport_data: EmployeePassportSchema,
    employee = Depends(get_current_employee)
):
    passport_data.employee_id = employee.id
    passport_info = await employee_controller.save_employee_passport_info(passport_data=passport_data)
    if not passport_info:
        return Fail(msg="旅券情報の保存に失敗しました")

    return Success(msg="旅券情報を保存しました")


# 社会保険
@router.get("/social_ins/get", summary="社会保険情報を取得")
async def get_employee_social_ins_info(
    employee = Depends(get_current_employee)
):
    """
    従業員の社会保険情報を取得
    """
    employee_id = employee.id
    social_ins_info = await employee_controller.get_employee_social_ins_info(employee_id=employee_id)
    if social_ins_info:
        return Success(data=await social_ins_info.to_dict())

    return None

@router.post("/social_ins/save", summary="社会保険情報の保存")
async def save_employee_social_ins_info(
    insurance_data: EmployeeSocialInsuranceSchema,
    employee=Depends(get_current_employee)
):
    insurance_data.employee_id = employee.id
    insurance_info = await employee_controller.save_employee_social_ins_info(insurance_data=insurance_data)
    if not insurance_info:
        return Fail(msg="社会保険情報の保存に失敗しました")

    return Success(msg="社会保険情報を保存しました")


# 雇用保険
@router.get("/employment_ins/get", summary="雇用保険情報を取得")
async def get_employee_employment_ins_info(
    employee_id: Optional[int] = Query(default=None),
    employee = Depends(get_current_employee)
):
    """
    従業員の雇用保険情報を取得
    """
    if not employee_id:
        employee_id = employee.id
    employment_ins_info = await employee_controller.get_employee_employment_ins_info(employee_id=employee_id)
    if employment_ins_info:
        return Success(data=await employment_ins_info.to_dict())

    return None

@router.post("/employment_ins/save", summary="雇用保険情報の保存")
async def save_employee_employment_ins_info(
    employment_data: EmployeeEmploymentInsuranceSchema,
    employee = Depends(get_current_employee)
):
    """
    従業員の雇用保険情報を保存
    """
    if not employment_data.employee_id:
        employment_data.employee_id = employee.id
    employment_ins_info = await employee_controller.save_employee_employment_ins_info(employment_data=employment_data)
    if not employment_ins_info:
        return Fail(msg="雇用保険情報の保存に失敗しました")

    return Success(msg="雇用保険情報を保存しました")


@router.post("/run_process", summary="従業員のプロセスを実行")
async def run_employee_process(
    employee = Depends(get_current_employee),
    authorization: str = Header(..., description="token验证")
):
    """
    従業員入職手続きのプロセスを実行
    """
    result = await process_client.run_process(
        process_key=JOIN_PROCESS_KEY,
        business_key=employee.id,
        variables=json.dumps({"showSign": False}),
        token=authorization
    )
    if result:
        employee.process_instance_id = result
        await employee.save()
        return Success(msg="プロセスが正常に実行されました")


    return Fail(msg="プロセスの実行に失敗しました")