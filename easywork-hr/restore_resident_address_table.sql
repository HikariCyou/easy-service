-- 立即恢复 hr_employee_resident_address 表
-- 执行方法: mysql -u root -p easywork_hr < restore_resident_address_table.sql

USE easywork_hr;

-- 恢复 hr_employee_resident_address 表
CREATE TABLE IF NOT EXISTS hr_employee_resident_address (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    
    -- 关联字段 (注意：现在关联到personnel_id)
    personnel_id BIGINT NOT NULL,
    
    -- 住址基本信息
    postal_code VARCHAR(10) NOT NULL COMMENT '郵便番号',
    prefecture VARCHAR(100) NOT NULL COMMENT '住所（都道府県）',
    city VARCHAR(100) NOT NULL COMMENT '住所（市区町村）',
    street_address VARCHAR(255) NOT NULL COMMENT '住所（丁目・番地）',
    building_name VARCHAR(255) NULL COMMENT '住所（建物名・部屋番号）',
    
    -- 住址读音
    address_kana VARCHAR(255) NULL COMMENT '住所（ヨミガナ）',
    
    -- 世带主信息
    head_of_household_name VARCHAR(255) NULL COMMENT '世帯主の氏名',
    head_of_household_relationship VARCHAR(20) NULL DEFAULT '本人' COMMENT '世帯主の続柄',
    
    -- 索引
    INDEX idx_personnel_id (personnel_id),
    INDEX idx_postal_code (postal_code)
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='従業員住民票住址';

-- 如果需要添加外键约束（在确认hr_personnel表存在后执行）
-- ALTER TABLE hr_employee_resident_address 
-- ADD CONSTRAINT fk_hr_employee_resident_address_personnel_id 
-- FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE;

-- 验证表创建结果
SELECT 
    TABLE_NAME,
    TABLE_COMMENT,
    TABLE_ROWS
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'easywork_hr' 
    AND TABLE_NAME = 'hr_employee_resident_address';

-- 查看表结构
DESCRIBE hr_employee_resident_address;