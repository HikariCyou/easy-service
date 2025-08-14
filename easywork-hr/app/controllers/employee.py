from app.core.user_client import user_client
from app.models import EmployeeAddress
from app.models.employee import Employee, EmployeeEmergencyContact, EmployeeBankAccount, EmployeeResidenceStatus, \
    EmployeePassport, EmployeeSocialInsurance, EmployeeEmploymentInsurance
from tortoise.expressions import  Q

from app.schemas.employee import EmployeeAddressSchema, EmployeeSchema, EmployeeEmergencyContactSchema, \
    EmployeeBankSchema, EmployeeResidenceStatusSchema, EmployeeUpdateSchema, EmployeePassportSchema, \
    EmployeeSocialInsuranceSchema, EmployeeEmploymentInsuranceSchema


class EmployeeController:
    async def list_employees(self , q = Q(), page: int = 1, page_size: int = 10 , orders: list = []):
        """
        従業員リストを取得
        """
        query = Employee.filter(q)
        total = await  query.count()
        employees = await query.offset((page - 1) * page_size).limit(page_size).order_by(*orders)
        return employees, total

    async  def get_full_employee_info(self, employee: any , token: str = None):
        employee_info = {}
        user_info = await user_client.get_user_by_id(employee.user_id , token=token)

        if user_info:
            employee_info['user'] = user_info

        # 基本的な従業員情報
        employee_info['employee'] = await employee.to_dict()
        # address info
        employee_address = await EmployeeAddress.get_or_none(employee_id=employee.id)
        if employee_address:
            employee_info['address'] = await employee_address.to_dict()
        else:
            employee_info['address'] = None

        # emergency contact info
        emergency_contact = await EmployeeEmergencyContact.get_or_none(employee_id=employee.id)
        if emergency_contact:
            employee_info['emergency_contact'] = await emergency_contact.to_dict()
        else:
            employee_info['emergency_contact'] = None

        # bank info
        bank_info = await EmployeeBankAccount.get_or_none(employee_id=employee.id)
        if bank_info:
            employee_info['bank_account'] = await bank_info.to_dict()
        else:
            employee_info['bank_account'] = None

        # 在留カード情報
        resident_info = await EmployeeResidenceStatus.get_or_none(employee_id=employee.id)
        if resident_info:
            employee_info['residence_status'] = await resident_info.to_dict()
        else:
            employee_info['residence_status'] = None

        # パスポート情報
        passport_info = await EmployeePassport.get_or_none(employee_id=employee.id)
        if passport_info:
            employee_info['passport'] = await passport_info.to_dict()
        else:
            employee_info['passport'] = None

        # 社会保険
        social_insurance_info = await EmployeeSocialInsurance.get_or_none(employee_id=employee.id)
        if social_insurance_info:
            employee_info['social_insurance'] = await social_insurance_info.to_dict()
        else:
            employee_info['social_insurance'] = None

        # 雇用保険
        employment_insurance_info = await EmployeeEmploymentInsurance.get_or_none(employee_id=employee.id)
        if employment_insurance_info:
            employee_info['employment_insurance'] = await employment_insurance_info.to_dict()
        else:
            employee_info['employment_insurance'] = None

        return employee_info

    async def get_employee_by_user_id(self, user_id: int):
        """
        ユーザーIDで従業員情報を取得
        """
        employee = await Employee.get_or_none(user_id=user_id)
        return employee

    async def get_employee_by_id(self, employee_id: int):
        """
        従業員情報をIDで取得
        """
        employee = await Employee.get_or_none(id=employee_id)
        return employee

    async def get_employee_by_process_instance_id(self, process_instance_id: str):
        """
        プロセスインスタンスIDから従業員情報を取得
        """
        employee = await Employee.get_or_none(process_instance_id=process_instance_id)
        return employee

    async def register_employee(self,user_id:int, employee_data: EmployeeSchema):
        """
        新しい従業員を作成
        """
        employee = await Employee.get_or_none(user_id=user_id)
        if employee:
            # 既存の従業員がいる場合は更新
            dict_data = employee_data.model_dump(exclude_unset=True)
            employee.update_from_dict(dict_data)
            await employee.save()
        else:
            # 新しい従業員を作成
            employee = await Employee.create(**employee_data.model_dump())

        return employee

    async def update_employee_info(self, employee: Employee, employee_data: EmployeeUpdateSchema):
        """
        従業員情報を更新
        """
        update_data = employee_data.model_dump(exclude_unset=True)
        employee.update_from_dict(update_data)
        await employee.save()
        return employee

    async def save_employee_address_info(self , address_data: EmployeeAddressSchema):
        """
        従業員の住所情報を保存
        """
        employee_address = await EmployeeAddress.get_or_none(employee_id=address_data.employee_id)
        if employee_address:
            # 既存の住所情報がある場合は更新
            dict_data = address_data.model_dump(exclude_unset=True)
            employee_address.update_from_dict(dict_data)
            await employee_address.save()
        else:
            # 新しい住所情報を作成
            employee_address = await EmployeeAddress.create(**address_data.model_dump())
        return employee_address

    async def save_employee_emergency_contact_info(self, contact_data: EmployeeEmergencyContactSchema):
        """
        従業員の緊急連絡先情報を保存
        """
        # ここで緊急連絡先の保存ロジックを実装
        # 例えば、EmergencyContactモデルを使用して保存する
        employee_emergency_contact = await EmployeeEmergencyContact.get_or_none(employee_id=contact_data.employee_id)
        if employee_emergency_contact:
            # 既存の緊急連絡先情報がある場合は更新
            dict_data = contact_data.model_dump(exclude_unset=True)
            employee_emergency_contact.update_from_dict(dict_data)
            await employee_emergency_contact.save()
        else:
            # 新しい緊急連絡先情報を作成
            employee_emergency_contact = await EmployeeEmergencyContact.create(**contact_data.model_dump())

        return employee_emergency_contact

    async def get_employee_bank_info(self, employee_id: int):
        """
        従業員の銀行情報を取得
        """
        bank_info = await EmployeeBankAccount.get_or_none(employee_id=employee_id)
        return bank_info

    async def save_employee_bank_info(self, bank_data: EmployeeBankSchema):
        """
        従業員の銀行情報を保存
        """

        employee_bank = await EmployeeBankAccount.get_or_none(employee_id=bank_data.employee_id)
        if employee_bank:
            # 既存の銀行情報がある場合は更新
            dict_data = bank_data.model_dump(exclude_unset=True)
            employee_bank.update_from_dict(dict_data)
            await employee_bank.save()
        else:
            # 新しい銀行情報を作成
            employee_bank = await EmployeeBankAccount.create(**bank_data.model_dump())
        return employee_bank


    async def get_employee_resident_card_info(self, employee_id: int):
        """
        従業員の在留カード情報を取得
        """
        resident_card_info = await EmployeeResidenceStatus.get_or_none(employee_id=employee_id)
        return resident_card_info


    async def get_employee_passport_info(self, employee_id: int):
        """
        従業員のパスポート情報を取得
        """
        passport_info = await EmployeePassport.get_or_none(employee_id=employee_id)
        return passport_info


    async def save_employee_passport_info(self, passport_data: EmployeePassportSchema):
        employee_passport = await EmployeePassport.get_or_none(employee_id=passport_data.employee_id)
        if employee_passport:
            # 既存のパスポート情報がある場合は更新
            dict_data = passport_data.model_dump(exclude_unset=True)
            employee_passport.update_from_dict(dict_data)
            await employee_passport.save()
        else:
            # 新しいパスポート情報を作成
            employee_passport = await EmployeePassport.create(**passport_data.model_dump())
        return employee_passport

    async def save_employee_resident_card_info(self, resident_data: EmployeeResidenceStatusSchema):
        """
        従業員の在留カード情報を保存
        """
        employee_resident = await EmployeeResidenceStatus.get_or_none(employee_id=resident_data.employee_id)
        if employee_resident:
            # 既存の住民票情報がある場合は更新
            dict_data = resident_data.model_dump(exclude_unset=True)
            employee_resident.update_from_dict(dict_data)
            await employee_resident.save()
        else:
            # 新しい住民票情報を作成
            employee_resident = await EmployeeResidenceStatus.create(**resident_data.model_dump())
        return employee_resident


    async def get_employee_social_ins_info(self, employee_id: int):
        employee_social_ins = await EmployeeSocialInsurance.get_or_none(employee_id=employee_id)
        return employee_social_ins

    async def save_employee_social_ins_info(self, insurance_data: EmployeeSocialInsuranceSchema):
        """
        従業員の社会保険情報を保存
        """
        employee_social_ins = await EmployeeSocialInsurance.get_or_none(employee_id=insurance_data.employee_id)
        if employee_social_ins:
            dict_data = insurance_data.model_dump(exclude_unset=True)
            employee_social_ins.update_from_dict(dict_data)
            await employee_social_ins.save()
        else:
            employee_social_ins = await EmployeeSocialInsurance.create(**insurance_data.model_dump())
        return employee_social_ins

    async def get_employee_employment_ins_info(self, employee_id: int):
        employee_employment_ins = await EmployeeEmploymentInsurance.get_or_none(employee_id=employee_id)
        return employee_employment_ins

    async def save_employee_employment_ins_info(self, employment_data: EmployeeEmploymentInsuranceSchema):
        """
        従業員の雇用保険情報を保存
        """
        employee_employment_ins = await EmployeeEmploymentInsurance.get_or_none(employee_id=employment_data.employee_id)
        if employee_employment_ins:
            dict_data = employment_data.model_dump(exclude_unset=True)
            employee_employment_ins.update_from_dict(dict_data)
            await employee_employment_ins.save()
        else:
            employee_employment_ins = await EmployeeEmploymentInsurance.create(**employment_data.model_dump())
        return employee_employment_ins


employee_controller = EmployeeController()