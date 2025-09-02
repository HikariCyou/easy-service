#!/usr/bin/env python3
"""
数据迁移脚本: Employee -> Personnel 统一模型
将现有的Employee数据迁移到新的Personnel模型，并更新所有关联表的外键引用

执行步骤:
1. 创建新的hr_personnel表
2. 将hr_employee数据迁移到hr_personnel
3. 更新所有HR特化表的外键引用 (employee_id -> personnel_id)
4. 删除旧的hr_employee表

使用方法:
python migrate_to_personnel_unified.py
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from tortoise.transactions import in_transaction


class PersonnelMigration:
    """Personnel统一模型迁移类"""
    
    def __init__(self):
        self.migration_log = []
        
    def log(self, message: str):
        """记录迁移日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.migration_log.append(log_message)
    
    async def backup_existing_data(self):
        """备份现有数据"""
        self.log("开始备份现有数据...")
        
        # 获取当前连接
        conn = Tortoise.get_connection("default")
        
        # 备份Employee数据
        employees = await conn.execute_query_dict("SELECT * FROM hr_employee")
        
        # 备份所有相关表
        tables_to_backup = [
            "hr_employee_address",
            "hr_employee_resident_address", 
            "hr_employee_emergency_contact",
            "hr_employee_bank_account",
            "hr_employee_residence_status",
            "hr_employee_passport",
            "hr_employee_social_insurance",
            "hr_employee_employment_insurance",
            "hr_employee_salary_record",
            "hr_employee_document",
            "hr_employee_history"
        ]
        
        backup_data = {"hr_employee": employees}
        
        for table in tables_to_backup:
            try:
                data = await conn.execute_query_dict(f"SELECT * FROM {table}")
                backup_data[table] = data
                self.log(f"备份表 {table}: {len(data)} 条记录")
            except Exception as e:
                self.log(f"备份表 {table} 失败: {str(e)}")
        
        # 保存备份到文件
        import json
        backup_file = f"backup_employee_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
        
        self.log(f"数据备份完成，保存至: {backup_file}")
        return backup_data
    
    async def create_personnel_table(self):
        """创建Personnel表"""
        self.log("创建Personnel表...")
        
        conn = Tortoise.get_connection("default")
        
        # 创建Personnel表的SQL
        create_personnel_sql = """
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
        """
        
        await conn.execute_script(create_personnel_sql)
        self.log("Personnel表创建完成")
    
    async def migrate_employee_data(self):
        """迁移Employee数据到Personnel"""
        self.log("开始迁移Employee数据到Personnel...")
        
        conn = Tortoise.get_connection("default")
        
        # 获取所有Employee数据
        employees = await conn.execute_query_dict("SELECT * FROM hr_employee")
        
        migrated_count = 0
        for employee in employees:
            try:
                # 构建Personnel数据
                personnel_data = {
                    'id': employee['id'],
                    'created_at': employee.get('created_at'),
                    'updated_at': employee.get('updated_at'),
                    'user_id': employee.get('user_id'),
                    'person_type': 'employee',  # 设置为员工类型
                    'code': employee.get('code'),
                    'name': employee.get('user_id', ''),  # 临时使用user_id，稍后需要从user服务获取真实姓名
                    'joining_time': employee.get('joining_time'),
                    'position': employee.get('position'),
                    'employment_type': employee.get('employment_type'),
                    'business_content': employee.get('business_content'),
                    'salary_payment_type': employee.get('salary_payment_type'),
                    'salary': employee.get('salary'),
                    'is_active': employee.get('is_active', True),
                    'process_instance_id': employee.get('process_instance_id')
                }
                
                # 插入到Personnel表
                insert_sql = """
                INSERT INTO hr_personnel (
                    id, created_at, updated_at, user_id, person_type, code,
                    name, joining_time, position, employment_type, business_content,
                    salary_payment_type, salary, is_active, process_instance_id
                ) VALUES (
                    %(id)s, %(created_at)s, %(updated_at)s, %(user_id)s, %(person_type)s, %(code)s,
                    %(name)s, %(joining_time)s, %(position)s, %(employment_type)s, %(business_content)s,
                    %(salary_payment_type)s, %(salary)s, %(is_active)s, %(process_instance_id)s
                )
                """
                
                await conn.execute_query(insert_sql, personnel_data)
                migrated_count += 1
                
            except Exception as e:
                self.log(f"迁移Employee ID {employee['id']} 失败: {str(e)}")
        
        self.log(f"Employee数据迁移完成: {migrated_count}/{len(employees)} 条记录")
    
    async def update_foreign_keys(self):
        """更新所有关联表的外键引用"""
        self.log("开始更新关联表的外键引用...")
        
        conn = Tortoise.get_connection("default")
        
        # 需要更新的表和字段映射
        tables_to_update = {
            "hr_employee_address": "employee_id",
            "hr_employee_resident_address": "employee_id", 
            "hr_employee_emergency_contact": "employee_id",
            "hr_employee_bank_account": "employee_id",
            "hr_employee_residence_status": "employee_id",
            "hr_employee_passport": "employee_id",
            "hr_employee_social_insurance": "employee_id",
            "hr_employee_employment_insurance": "employee_id",
            "hr_employee_salary_record": "employee_id",
            "hr_employee_document": "employee_id",
            "hr_employee_history": "employee_id"
        }
        
        for table_name, old_column in tables_to_update.items():
            try:
                # 1. 添加新的personnel_id字段
                add_column_sql = f"""
                ALTER TABLE {table_name} 
                ADD COLUMN personnel_id BIGINT NULL
                """
                
                try:
                    await conn.execute_script(add_column_sql)
                    self.log(f"为表 {table_name} 添加 personnel_id 字段")
                except Exception as e:
                    if "Duplicate column name" not in str(e):
                        raise e
                
                # 2. 复制数据: employee_id -> personnel_id
                copy_data_sql = f"""
                UPDATE {table_name} 
                SET personnel_id = {old_column}
                WHERE {old_column} IS NOT NULL
                """
                
                result = await conn.execute_query(copy_data_sql)
                
                # 3. 添加外键约束
                add_fk_sql = f"""
                ALTER TABLE {table_name}
                ADD CONSTRAINT fk_{table_name}_personnel_id 
                FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE
                """
                
                try:
                    await conn.execute_script(add_fk_sql)
                    self.log(f"为表 {table_name} 添加外键约束")
                except Exception as e:
                    if "foreign key constraint already exists" not in str(e).lower():
                        self.log(f"添加外键约束失败 {table_name}: {str(e)}")
                
                # 4. 删除旧的employee_id字段 (暂时保留，等验证完成后再删除)
                # drop_column_sql = f"ALTER TABLE {table_name} DROP COLUMN {old_column}"
                # await conn.execute_script(drop_column_sql)
                
                self.log(f"表 {table_name} 外键更新完成")
                
            except Exception as e:
                self.log(f"更新表 {table_name} 外键失败: {str(e)}")
        
        self.log("关联表外键更新完成")
    
    async def verify_migration(self):
        """验证迁移结果"""
        self.log("开始验证迁移结果...")
        
        conn = Tortoise.get_connection("default")
        
        # 验证Personnel表数据
        personnel_count = await conn.execute_query_dict("SELECT COUNT(*) as count FROM hr_personnel")
        employee_count = await conn.execute_query_dict("SELECT COUNT(*) as count FROM hr_employee")
        
        self.log(f"Personnel表记录数: {personnel_count[0]['count']}")
        self.log(f"Employee表记录数: {employee_count[0]['count']}")
        
        if personnel_count[0]['count'] != employee_count[0]['count']:
            self.log("⚠️  警告: Personnel和Employee记录数不匹配!")
            return False
        
        # 验证关联表数据完整性
        tables_to_verify = [
            "hr_employee_address",
            "hr_employee_emergency_contact", 
            "hr_employee_bank_account",
            "hr_employee_residence_status",
            "hr_employee_passport",
            "hr_employee_social_insurance",
            "hr_employee_employment_insurance"
        ]
        
        for table_name in tables_to_verify:
            try:
                # 检查是否有personnel_id为NULL的记录
                null_count = await conn.execute_query_dict(f"""
                    SELECT COUNT(*) as count FROM {table_name} 
                    WHERE employee_id IS NOT NULL AND personnel_id IS NULL
                """)
                
                if null_count[0]['count'] > 0:
                    self.log(f"⚠️  警告: 表 {table_name} 有 {null_count[0]['count']} 条记录的personnel_id为NULL")
                    return False
                
            except Exception as e:
                self.log(f"验证表 {table_name} 失败: {str(e)}")
        
        self.log("✅ 迁移验证通过")
        return True
    
    async def cleanup_old_data(self):
        """清理旧数据 (可选)"""
        self.log("开始清理旧数据...")
        
        conn = Tortoise.get_connection("default")
        
        # 删除旧的Employee表 (谨慎操作)
        # await conn.execute_script("DROP TABLE IF EXISTS hr_employee")
        # self.log("删除旧的hr_employee表")
        
        # 或者先重命名表
        await conn.execute_script("RENAME TABLE hr_employee TO hr_employee_backup")
        self.log("将hr_employee表重命名为hr_employee_backup")
    
    async def run_migration(self):
        """执行完整迁移流程"""
        self.log("=== 开始Personnel统一模型迁移 ===")
        
        try:
            # 初始化数据库连接
            await Tortoise.init(
                db_url="mysql://root:123456@127.0.0.1:3306/easywork_hr",
                modules={"models": ["app.models"]}
            )
            
            async with in_transaction():
                # 1. 备份数据
                await self.backup_existing_data()
                
                # 2. 创建Personnel表
                await self.create_personnel_table()
                
                # 3. 迁移Employee数据
                await self.migrate_employee_data()
                
                # 4. 更新外键引用
                await self.update_foreign_keys()
                
                # 5. 验证迁移结果
                if await self.verify_migration():
                    self.log("✅ 迁移成功完成!")
                    
                    # 可选: 清理旧数据
                    # await self.cleanup_old_data()
                else:
                    self.log("❌ 迁移验证失败，请检查数据")
                    raise Exception("Migration verification failed")
            
        except Exception as e:
            self.log(f"❌ 迁移失败: {str(e)}")
            raise e
        
        finally:
            await Tortoise.close_connections()
            
            # 保存迁移日志
            log_file = f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.migration_log))
            
            self.log(f"迁移日志保存至: {log_file}")


async def main():
    """主函数"""
    migration = PersonnelMigration()
    await migration.run_migration()


if __name__ == "__main__":
    print("Personnel统一模型迁移脚本")
    print("⚠️  警告: 此操作将修改数据库结构和数据，请确保已备份数据库!")
    
    confirm = input("确定要继续吗? (yes/no): ")
    if confirm.lower() == 'yes':
        asyncio.run(main())
    else:
        print("迁移已取消")