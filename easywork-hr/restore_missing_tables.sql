-- 恢复所有可能丢失的HR特化表结构
-- 执行前请先备份当前数据库！

USE easywork_hr;

-- 1. 员工地址表
CREATE TABLE IF NOT EXISTS hr_employee_address (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    is_overseas BOOLEAN NULL DEFAULT FALSE,
    postal_code VARCHAR(10) NOT NULL,
    prefecture VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    street_address VARCHAR(255) NOT NULL,
    building_name VARCHAR(255) NULL,
    address_kana VARCHAR(255) NULL,
    head_of_household_name VARCHAR(255) NULL,
    head_of_household_relationship VARCHAR(20) NULL DEFAULT '本人',
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='従業員住所情報';

-- 2. 员工住民票住址表
CREATE TABLE IF NOT EXISTS hr_employee_resident_address (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    postal_code VARCHAR(10) NOT NULL,
    prefecture VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    street_address VARCHAR(255) NOT NULL,
    building_name VARCHAR(255) NULL,
    address_kana VARCHAR(255) NULL,
    head_of_household_name VARCHAR(255) NULL,
    head_of_household_relationship VARCHAR(20) NULL DEFAULT '本人',
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='従業員住民票住址';

-- 3. 紧急联系人表
CREATE TABLE IF NOT EXISTS hr_employee_emergency_contact (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    name VARCHAR(255) NOT NULL,
    name_kana VARCHAR(255) NULL,
    relationship VARCHAR(100) NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    email VARCHAR(255) NULL,
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='緊急連絡先';

-- 4. 银行账户表
CREATE TABLE IF NOT EXISTS hr_employee_bank_account (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    bank_name VARCHAR(255) NOT NULL,
    branch_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    account_number VARCHAR(20) NOT NULL,
    account_holder_name VARCHAR(255) NOT NULL,
    bank_images JSON NULL,
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='口座情報';

-- 5. 在留资格表
CREATE TABLE IF NOT EXISTS hr_employee_residence_status (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT '技術・人文知識・国際業務',
    residence_card_number VARCHAR(50) NULL,
    expiration_date DATE NULL,
    permission_for_activities BOOLEAN NULL DEFAULT FALSE,
    card_images JSON NULL,
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='在留資格';

-- 6. 护照旅券表
CREATE TABLE IF NOT EXISTS hr_employee_passport (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    passport_number VARCHAR(50) NOT NULL,
    expiration_date DATE NOT NULL,
    country_of_issue VARCHAR(100) NOT NULL,
    passport_images JSON NULL,
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='パスポート旅券';

-- 7. 社会保险表
CREATE TABLE IF NOT EXISTS hr_employee_social_insurance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    pension_basic_number VARCHAR(20) NULL,
    pension_number_reason VARCHAR(100) NULL,
    first_join_pension BOOLEAN DEFAULT FALSE,
    pension_images JSON NULL,
    qualification_acquisition_date DATE NULL,
    health_insurance_number VARCHAR(50) NULL,
    health_insurance_qualification_date DATE NULL,
    health_insurance_number_reason VARCHAR(50) NULL,
    health_insurance_images JSON NULL,
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社会保険';

-- 8. 雇用保险表
CREATE TABLE IF NOT EXISTS hr_employee_employment_insurance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    employment_insurance_number VARCHAR(50) NULL,
    employment_number_reason VARCHAR(100) NULL,
    employment_images JSON NULL,
    employment_qualification_date DATE NULL,
    qualification_type VARCHAR(50) NULL,
    insured_reason VARCHAR(100) NULL,
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='雇用保険';

-- 9. 工资记录表
CREATE TABLE IF NOT EXISTS hr_employee_salary_record (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    basic_salary DECIMAL(12,2) NOT NULL,
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='給与改定記録';

-- 10. 文档表
CREATE TABLE IF NOT EXISTS hr_employee_document (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    file_url VARCHAR(255) NOT NULL,
    document_type VARCHAR(50) NULL DEFAULT 'その他',
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='従業員書類';

-- 11. 历史记录表
CREATE TABLE IF NOT EXISTS hr_employee_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    personnel_id BIGINT NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    data JSON NOT NULL,
    version INT NOT NULL,
    changed_by BIGINT NULL,
    
    INDEX idx_personnel_id (personnel_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='従業員履歴';

-- 12. 确保Personnel表存在（如果被删除了）
CREATE TABLE IF NOT EXISTS hr_personnel (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    
    -- 系统关联
    user_id BIGINT NULL,
    person_type VARCHAR(20) NOT NULL DEFAULT 'employee',
    code VARCHAR(50) NULL UNIQUE,
    
    -- 基本信息
    name VARCHAR(100) NOT NULL DEFAULT '',
    free_kana_name VARCHAR(100) NULL,
    age INT NULL,
    sex INT NULL DEFAULT 0,
    birthday DATE NULL,
    station VARCHAR(255) NULL,
    marriage_status VARCHAR(20) NULL DEFAULT '独身',
    
    -- 联系方式
    phone VARCHAR(50) NULL,
    email VARCHAR(100) NULL,
    emergency_contact_name VARCHAR(100) NULL,
    emergency_contact_phone VARCHAR(50) NULL,
    emergency_contact_relation VARCHAR(50) NULL,
    
    -- 地址信息
    zip_code VARCHAR(10) NULL,
    address VARCHAR(255) NULL,
    work_address VARCHAR(255) NULL,
    
    -- 外国人对应
    nationality VARCHAR(50) NULL,
    visa_status VARCHAR(50) NULL,
    visa_expire_date DATE NULL,
    japanese_level VARCHAR(20) NULL,
    
    -- 技能・经验
    total_experience_years FLOAT NULL,
    it_experience_years FLOAT NULL,
    education_level VARCHAR(100) NULL,
    major VARCHAR(100) NULL,
    certifications TEXT NULL,
    
    -- 单价・稼働
    standard_unit_price FLOAT NULL,
    min_unit_price FLOAT NULL,
    max_unit_price FLOAT NULL,
    hourly_rate FLOAT NULL,
    
    -- 稼働状况
    employment_status VARCHAR(20) NOT NULL DEFAULT '稼働可能',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    available_start_date DATE NULL,
    current_project_end_date DATE NULL,
    
    -- 希望条件
    preferred_location VARCHAR(255) NULL,
    remote_work_available BOOLEAN NOT NULL DEFAULT FALSE,
    overtime_available BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- 其他
    photo_url VARCHAR(500) NULL,
    resume_url VARCHAR(500) NULL,
    portfolio_url VARCHAR(500) NULL,
    website_url VARCHAR(500) NULL,
    remark TEXT NULL,
    
    -- HR特化信息
    joining_time DATE NULL,
    position VARCHAR(255) NULL,
    employment_type VARCHAR(255) NULL DEFAULT '契約社員',
    business_content VARCHAR(255) NULL,
    salary_payment_type VARCHAR(20) NULL DEFAULT '月給制',
    salary INT NULL DEFAULT 0,
    process_instance_id VARCHAR(255) NULL,
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_person_type (person_type),
    INDEX idx_employment_status (employment_status),
    INDEX idx_nationality_visa (nationality, visa_status),
    INDEX idx_available_start_date (available_start_date),
    INDEX idx_standard_unit_price (standard_unit_price),
    INDEX idx_active_type (is_active, person_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='统一人员管理表';

-- 添加外键约束（如果hr_personnel表存在）
-- 注意：只有在确认hr_personnel表有数据时才执行外键约束

-- ALTER TABLE hr_employee_address ADD CONSTRAINT fk_hr_employee_address_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;
-- ALTER TABLE hr_employee_resident_address ADD CONSTRAINT fk_hr_employee_resident_address_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;
-- ALTER TABLE hr_employee_emergency_contact ADD CONSTRAINT fk_hr_employee_emergency_contact_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;
-- ALTER TABLE hr_employee_bank_account ADD CONSTRAINT fk_hr_employee_bank_account_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;
-- ALTER TABLE hr_employee_residence_status ADD CONSTRAINT fk_hr_employee_residence_status_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;
-- ALTER TABLE hr_employee_passport ADD CONSTRAINT fk_hr_employee_passport_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;
-- ALTER TABLE hr_employee_social_insurance ADD CONSTRAINT fk_hr_employee_social_insurance_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;
-- ALTER TABLE hr_employee_employment_insurance ADD CONSTRAINT fk_hr_employee_employment_insurance_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;
-- ALTER TABLE hr_employee_salary_record ADD CONSTRAINT fk_hr_employee_salary_record_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;
-- ALTER TABLE hr_employee_document ADD CONSTRAINT fk_hr_employee_document_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;
-- ALTER TABLE hr_employee_history ADD CONSTRAINT fk_hr_employee_history_personnel_id FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;

-- 检查结果
SELECT 
    TABLE_NAME,
    TABLE_COMMENT,
    TABLE_ROWS
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'easywork_hr' 
    AND TABLE_NAME LIKE 'hr_%'
ORDER BY TABLE_NAME;