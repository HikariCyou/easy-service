from tortoise import fields

from app.models.base import BaseModel, TimestampMixin
from app.models.enums import (PersonType, EmploymentStatus, MarriageStatus, 
                              ResidenceStatus, JapaneseLevel, EmployeeType, 
                              SalaryPaymentType, DecimalProcessingType)


class Personnel(BaseModel, TimestampMixin):
    """
    统一要员基础表 - 所有人员的共同信息
    包含：BP员工、自社员工、自由职业者
    """
    
    # === 系统关联 ===
    user_id = fields.BigIntField(null=True, index=True, description="关联系统账号ID (用于登录/考勤)")
    person_type = fields.CharEnumField(PersonType, description="人员类型")
    code = fields.CharField(max_length=50, null=True, unique=True, description="要员编号")
    
    # === 基本信息 ===
    name = fields.CharField(max_length=100, description="姓名")
    free_kana_name = fields.CharField(max_length=100, null=True, description="姓名（片假名）")
    age = fields.IntField(null=True, description="年龄")
    sex = fields.IntField(null=True, default=0, description="性别 (0:男, 1:女)")
    birthday = fields.DateField(null=True, description="生年月日")
    station = fields.CharField(max_length=255, null=True, description="最寄车站")
    marriage_status = fields.CharEnumField(
        MarriageStatus, null=True, default=MarriageStatus.SINGLE, description="婚姻状况"
    )
    
    # === 联系方式 ===
    phone = fields.CharField(max_length=50, null=True, description="电话号码")
    email = fields.CharField(max_length=100, null=True, description="邮箱")
    emergency_contact_name = fields.CharField(max_length=100, null=True, description="紧急联系人姓名")
    emergency_contact_phone = fields.CharField(max_length=50, null=True, description="紧急联系人电话")
    emergency_contact_relation = fields.CharField(max_length=50, null=True, description="紧急联系人关系")
    
    # === 地址信息 ===
    zip_code = fields.CharField(max_length=10, null=True, description="邮政编码")
    address = fields.CharField(max_length=255, null=True, description="住址")
    work_address = fields.CharField(max_length=255, null=True, description="工作地址")
    
    # === 外国人对应 ===
    nationality = fields.CharField(max_length=50, null=True, description="国籍")
    visa_status = fields.CharEnumField(ResidenceStatus, null=True, description="在留资格")
    visa_expire_date = fields.DateField(null=True, description="在留期限")
    japanese_level = fields.CharEnumField(JapaneseLevel, null=True, description="日语水平")
    
    # === 技能・经验 ===
    total_experience_years = fields.FloatField(null=True, description="总经验年数")
    it_experience_years = fields.FloatField(null=True, description="IT经验年数")
    education_level = fields.CharField(max_length=100, null=True, description="最终学历")
    major = fields.CharField(max_length=100, null=True, description="专业")
    certifications = fields.TextField(null=True, description="持有资格（换行分割）")
    
    # === 单价・稼働 ===
    standard_unit_price = fields.FloatField(null=True, description="标准单价（月额）")
    min_unit_price = fields.FloatField(null=True, description="最低承接单价")
    max_unit_price = fields.FloatField(null=True, description="最高承接单价")
    hourly_rate = fields.FloatField(null=True, description="时间单价")
    
    # === 稼働状况 ===
    employment_status = fields.CharEnumField(
        EmploymentStatus, default=EmploymentStatus.AVAILABLE, description="稼働状态"
    )
    is_active = fields.BooleanField(default=True, description="是否有效")
    available_start_date = fields.DateField(null=True, description="可稼働开始日")
    current_project_end_date = fields.DateField(null=True, description="当前项目结束预定日")
    
    # === 希望条件 ===
    preferred_location = fields.CharField(max_length=255, null=True, description="希望工作地")
    remote_work_available = fields.BooleanField(default=False, description="远程工作可能")
    overtime_available = fields.BooleanField(default=False, description="加班可能")
    
    # === 其他 ===
    photo_url = fields.CharField(max_length=500, null=True, description="照片URL")
    resume_url = fields.CharField(max_length=500, null=True, description="简历URL")
    portfolio_url = fields.CharField(max_length=500, null=True, description="作品集URL")
    website_url = fields.CharField(max_length=500, null=True, description="个人网站URL")
    remark = fields.TextField(null=True, description="备注")

    process_instance_id = fields.CharField(max_length=255, null=True, description="工作流实例ID")
    
    # === 关联 ===
    # 特化信息（根据person_type）
    employee_detail: fields.ReverseRelation["EmployeeDetail"]
    freelancer_detail: fields.ReverseRelation["FreelancerDetail"]
    bp_employee_detail: fields.ReverseRelation["BPEmployeeDetail"]
    
    # 业务关联
    skills: fields.ReverseRelation["PersonnelSkill"]
    contracts: fields.ReverseRelation["Contract"]
    evaluations: fields.ReverseRelation["PersonEvaluation"]
    case_candidates: fields.ReverseRelation["CaseCandidate"]

    class Meta:
        table = "ses_personnel"
        table_description = "要员管理"
        indexes = [
            ("user_id",),
            ("person_type",),
            ("employment_status",),
            ("nationality", "visa_status"),
            ("available_start_date",),
            ("standard_unit_price",),
            ("is_active", "person_type"),
        ]

    @property
    def current_age(self) -> int:
        if not self.birthday:
            return self.age or 0

        from datetime import date
        today = date.today()
        return today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))

    def is_visa_expiring_soon(self, days: int = 90) -> bool:
        if not self.visa_expire_date:
            return False

        from datetime import date, timedelta
        return self.visa_expire_date <= date.today() + timedelta(days=days)

    async def get_detail(self):
        if self.person_type == PersonType.EMPLOYEE:
            return await self.employee_detail if hasattr(self, 'employee_detail') else None
        elif self.person_type == PersonType.FREELANCER:
            return await self.freelancer_detail if hasattr(self, 'freelancer_detail') else None
        elif self.person_type == PersonType.BP_EMPLOYEE:
            return await self.bp_employee_detail if hasattr(self, 'bp_employee_detail') else None
        return None

    async def update_employment_status_to_working(self, project_end_date=None):
        """契約開始時に稼働状態を「稼働中」に更新"""
        self.employment_status = EmploymentStatus.WORKING
        if project_end_date:
            self.current_project_end_date = project_end_date
        await self.save()

    async def update_employment_status_to_available(self):
        """契約終了時に稼働状態を「稼働可能」に更新"""
        self.employment_status = EmploymentStatus.AVAILABLE
        self.current_project_end_date = None
        await self.save()

    async def update_employment_status_to_vacation(self):
        """休暇中に状態を更新"""
        self.employment_status = EmploymentStatus.VACATION
        await self.save()

    async def update_employment_status_to_unavailable(self, reason: str = None):
        """稼働不可に状態を更新"""
        self.employment_status = EmploymentStatus.UNAVAILABLE
        if reason:
            self.remark = f"{self.remark or ''}\n稼働不可理由: {reason}".strip()
        await self.save()

    async def check_and_update_status_by_contracts(self):
        """契約状況に基づいて稼働状態を自動更新"""
        from datetime import date
        from app.models.enums import ContractStatus
        
        # 現在有効な契約があるかチェック
        active_contracts = await self.contracts.filter(
            status=ContractStatus.ACTIVE,
            contract_start_date__lte=date.today(),
            contract_end_date__gte=date.today()
        ).count()
        
        if active_contracts > 0:
            # 有効な契約がある場合は「稼働中」
            if self.employment_status != EmploymentStatus.WORKING:
                await self.update_employment_status_to_working()
        else:
            # 有効な契約がない場合は「稼働可能」（退職・稼働不可でない限り）
            if self.employment_status == EmploymentStatus.WORKING:
                await self.update_employment_status_to_available()


class EmployeeDetail(BaseModel, TimestampMixin):
    """自社员工特化信息"""
    
    personnel = fields.OneToOneField(
        "models.Personnel", related_name="employee_detail", description="关联要员"
    )
    
    # === HR系统关联 ===
    joining_time = fields.DateField(null=True, description="入社时间")
    
    # === 职位信息 ===
    position = fields.CharField(max_length=255, null=True, description="职位")
    employment_type = fields.CharField(
        max_length=255, null=True, default=EmployeeType.CONTRACT.value, description="雇用形态"
    )
    business_content = fields.CharField(max_length=255, null=True, description="业务内容")
    
    # === 给与关联 ===
    salary_payment_type = fields.CharEnumField(
        SalaryPaymentType, default=SalaryPaymentType.MONTHLY, null=True, description="给与支给形态"
    )
    salary = fields.IntField(default=0, null=True, description="给与额")


    class Meta:
        table = "ses_employee_detail"
        table_description = "自社员工详细信息"


class FreelancerDetail(BaseModel, TimestampMixin):
    """自由职业者特化信息"""
    
    personnel = fields.OneToOneField(
        "models.Personnel", related_name="freelancer_detail", description="关联要员"
    )
    
    # === 事业者信息 ===
    business_name = fields.CharField(max_length=255, null=True, description="商号")
    tax_number = fields.CharField(max_length=50, null=True, description="发票号码")
    business_start_date = fields.DateField(null=True, description="开业日")
    freelance_experience_years = fields.FloatField(null=True, description="自由职业经验年数")
    
    # === 希望条件 ===
    preferred_project_type = fields.TextField(null=True, description="希望项目类型")
    preferred_work_style = fields.CharField(max_length=100, null=True, description="希望工作形态（常驻/远程等）")
    ng_client_companies = fields.TextField(null=True, description="NG客户（换行分割）")
    interview_available = fields.BooleanField(default=False, description="面谈可能")

    class Meta:
        table = "ses_freelancer_detail"
        table_description = "自由职业者详细信息"


class BPEmployeeDetail(BaseModel, TimestampMixin):
    """BP员工特化信息"""
    
    personnel = fields.OneToOneField(
        "models.Personnel", related_name="bp_employee_detail", description="关联要员"
    )
    
    # === BP会社关联 ===
    bp_company = fields.ForeignKeyField("models.BPCompany", related_name="personnel_details", description="所属BP会社")
    
    # === BP特有设定 ===
    interview_available = fields.BooleanField(default=False, description="面谈可能")

    class Meta:
        table = "ses_bp_employee_detail"
        table_description = "BP员工详细信息"


class PersonnelSkill(BaseModel, TimestampMixin):
    """
    统一人员技能关联表
    替代：EmployeeSkill, BPEmployeeSkill, FreelancerSkill
    """
    
    personnel = fields.ForeignKeyField("models.Personnel", related_name="skills", description="要员")
    skill = fields.ForeignKeyField("models.Skill", related_name="personnel", description="技能")
    proficiency = fields.IntField(default=1, description="熟练度 (1-5)")
    years_of_experience = fields.FloatField(null=True, description="经验年数")
    last_used_date = fields.DateField(null=True, description="最终使用日")
    is_primary_skill = fields.BooleanField(default=False, description="是否主要技能")
    remark = fields.TextField(null=True, description="备注（使用项目等）")

    class Meta:
        table = "ses_personnel_skill"
        table_description = "要员技能关联"
        unique_together = (("personnel", "skill"),)
        indexes = [
            ("personnel_id", "is_primary_skill"),
            ("skill_id",),
            ("proficiency",),
        ]