from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ImportPersonSchema(BaseModel):
    """统一要员信息Schema"""

    # 基本信息
    id: int = Field(..., description="ID")
    name: str = Field(..., description="氏名")
    code: Optional[str] = Field(None, description="要员代码")
    type: str = Field(..., description="要员类型", example="bp_employee|freelancer|employee")

    # 基本个人信息
    age: Optional[int] = Field(None, description="年龄")
    sex: Optional[int] = Field(None, description="性别")
    birthday: Optional[date] = Field(None, description="生年月日")
    nationality: Optional[str] = Field(None, description="国籍")
    photo_url: Optional[str] = Field(None, description="照片URL")

    # 联系方式
    phone: Optional[str] = Field(None, description="电话番号")
    email: Optional[str] = Field(None, description="邮件地址")
    address: Optional[str] = Field(None, description="住所")

    # 工作状态
    employment_status: Optional[str] = Field(None, description="就业状态")
    is_active: bool = Field(True, description="是否活跃")
    available_start_date: Optional[date] = Field(None, description="可开始工作日期")

    # 技能和经验
    it_experience_years: Optional[float] = Field(None, description="IT经验年数")
    standard_unit_price: Optional[float] = Field(None, description="标准单价")

    # 签证信息（外国人）
    visa_status: Optional[str] = Field(None, description="签证状态")
    visa_expire_date: Optional[date] = Field(None, description="签证到期日")

    # 当前契約
    contract: Optional[Dict[str, Any]] = Field(None, description="当前契约信息")
    current_case_id: Optional[int] = Field(None, description="当前案件ID")
    current_case_name: Optional[str] = Field(None, description="当前案件名称")
    current_contract_id: Optional[int] = Field(None, description="当前契约ID")

    # 今の案件
    case: Optional[Dict[str, Any]] = Field(None, description="案件信息")

    # 计算属性
    current_age: Optional[int] = Field(None, description="当前年龄")
    is_visa_expiring_soon: Optional[bool] = Field(None, description="签证是否即将到期")

    # 统计信息
    total_projects: Optional[int] = Field(None, description="参与项目总数")
    total_contracts: Optional[int] = Field(None, description="契约总数")
    average_rating: Optional[float] = Field(None, description="平均评价")

    # 系统字段
    updated_at: Optional[str] = Field(None, description="更新时间")


class ImportPersonListSchema(BaseModel):
    """要员列表响应Schema"""

    items: List[ImportPersonSchema] = Field(..., description="要员列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页大小")


class ImportPersonDetailSchema(ImportPersonSchema):
    """要员详细信息Schema"""

    # 详细个人信息
    free_kana_name: Optional[str] = Field(None, description="片假名姓名")
    station: Optional[str] = Field(None, description="最近车站")
    marriage_status: Optional[str] = Field(None, description="婚姻状态")
    zip_code: Optional[str] = Field(None, description="邮编")
    work_address: Optional[str] = Field(None, description="工作地址")

    # 紧急联系人
    emergency_contact_name: Optional[str] = Field(None, description="紧急联系人姓名")
    emergency_contact_phone: Optional[str] = Field(None, description="紧急联系人电话")
    emergency_contact_relation: Optional[str] = Field(None, description="紧急联系人关系")

    # 教育和资格
    education_level: Optional[str] = Field(None, description="最终学历")
    major: Optional[str] = Field(None, description="专业")
    certifications: Optional[str] = Field(None, description="资格证书")

    # 单价信息（主要针对Freelancer）
    min_unit_price: Optional[float] = Field(None, description="最低单价")
    max_unit_price: Optional[float] = Field(None, description="最高单价")
    hourly_rate: Optional[float] = Field(None, description="时薪")

    # 希望条件
    preferred_location: Optional[str] = Field(None, description="希望工作地点")
    preferred_project_type: Optional[str] = Field(None, description="希望项目类型")
    preferred_work_style: Optional[str] = Field(None, description="希望工作方式")

    # 其他
    photo_url: Optional[str] = Field(None, description="照片URL")
    resume_url: Optional[str] = Field(None, description="简历URL")
    remark: Optional[str] = Field(None, description="备注")

    # 契約
    contract: Optional[Dict[str, Any]] = Field(None, description="当前契约信息")
    case: Optional[Dict[str, Any]] = Field(None, description="案件信息")

    # 技能列表
    skills: List[Dict[str, Any]] = Field(default_factory=list, description="技能列表")

    # 特化信息
    specialized_info: Optional[Dict[str, Any]] = Field(None, description="特化信息（根据人员类型不同）")


class ImportPersonHistorySchema(BaseModel):
    """要员工作履历Schema"""

    id: int = Field(..., description="履历ID")
    person_id: int = Field(..., description="要员ID")
    person_name: str = Field(..., description="要员姓名")
    person_type: str = Field(..., description="要员类型")

    # 案件信息
    case_id: Optional[int] = Field(None, description="案件ID")
    case_name: Optional[str] = Field(None, description="案件名称")
    case_code: Optional[str] = Field(None, description="案件代码")
    case_location: Optional[str] = Field(None, description="案件地点")

    # 契约信息
    contract_id: Optional[int] = Field(None, description="契约ID")
    contract_number: Optional[str] = Field(None, description="契约番号")
    contract_start_date: Optional[date] = Field(None, description="契约开始日")
    contract_end_date: Optional[date] = Field(None, description="契约结束日")
    unit_price: Optional[float] = Field(None, description="单价")
    status: Optional[str] = Field(None, description="状态")

    # 项目信息
    client_name: Optional[str] = Field(None, description="客户名称")
    project_description: Optional[str] = Field(None, description="项目描述")

    # 评价信息
    evaluation_id: Optional[int] = Field(None, description="评价ID")
    overall_rating: Optional[int] = Field(None, description="总体评价")

    created_at: Optional[date] = Field(None, description="记录创建日期")


class ImportPersonCurrentAssignmentSchema(BaseModel):
    """要员当前分配信息Schema"""

    person_id: int = Field(..., description="要员ID")
    person_name: str = Field(..., description="要员姓名")
    person_type: str = Field(..., description="要员类型")

    # 当前案件
    current_case: Optional[Dict[str, Any]] = Field(None, description="当前案件信息")

    # 当前契约
    current_contracts: List[Dict[str, Any]] = Field(default_factory=list, description="当前契约列表")

    # 即将到期的契约
    expiring_contracts: List[Dict[str, Any]] = Field(default_factory=list, description="即将到期契约")

    # 工作状态
    work_status: str = Field(..., description="工作状态")
    available_from: Optional[date] = Field(None, description="可用开始日期")


class ImportPersonStatsSchema(BaseModel):
    """要员统计信息Schema"""

    total_staff: int = Field(..., description="总要员数")

    # 按类型统计
    bp_employees: int = Field(..., description="BP员工数")
    freelancers: int = Field(..., description="自由职业者数")
    employees: int = Field(..., description="正式员工数")

    # 按状态统计
    available_staff: int = Field(..., description="可用要员数")
    working_staff: int = Field(..., description="工作中要员数")
    unavailable_staff: int = Field(..., description="不可用要员数")

    # 按国籍统计
    japanese_staff: int = Field(..., description="日本人要员数")
    foreign_staff: int = Field(..., description="外国人要员数")

    # 签证到期警告
    visa_expiring_soon: int = Field(..., description="签证即将到期人数")

    # 经验统计
    senior_staff: int = Field(..., description="高级要员数（5年以上经验）")
    junior_staff: int = Field(..., description="初级要员数（3年以下经验）")


class ImportPersonSearchSchema(BaseModel):
    """要员搜索Schema"""

    # 基本搜索
    name: Optional[str] = Field(None, description="姓名搜索")
    code: Optional[str] = Field(None, description="代码搜索")
    person_type: Optional[str] = Field(None, description="要员类型筛选")

    # 状态筛选
    employment_status: Optional[str] = Field(None, description="就业状态筛选")
    is_active: Optional[bool] = Field(None, description="是否活跃筛选")

    # 技能筛选
    skill_name: Optional[str] = Field(None, description="技能名称搜索")

    # 经验筛选
    min_experience_years: Optional[float] = Field(None, description="最低经验年数")
    max_experience_years: Optional[float] = Field(None, description="最高经验年数")

    # 单价筛选
    min_unit_price: Optional[float] = Field(None, description="最低单价")
    max_unit_price: Optional[float] = Field(None, description="最高单价")

    # 地点筛选
    preferred_location: Optional[str] = Field(None, description="希望工作地点")
    nationality: Optional[str] = Field(None, description="国籍筛选")

    # 日期筛选
    available_from: Optional[date] = Field(None, description="可用开始日期")
    available_to: Optional[date] = Field(None, description="可用结束日期")

    # 签证筛选
    visa_expiring_within_days: Optional[int] = Field(None, description="签证N天内到期")

    # 案件绑定筛选
    has_active_case: Optional[bool] = Field(None, description="是否有活跃案件")
    case_id: Optional[int] = Field(None, description="特定案件ID筛选")


class UpdatePersonStatusSchema(BaseModel):
    """更新要员状态Schema"""

    person_id: int = Field(..., description="要员ID")
    person_type: str = Field(..., description="要员类型")
    employment_status: str = Field(..., description="新的就业状态")
    is_active: Optional[bool] = Field(None, description="是否活跃")
    available_start_date: Optional[date] = Field(None, description="可用开始日期")
    remark: Optional[str] = Field(None, description="状态变更备注")
