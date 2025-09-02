#!/usr/bin/env python3
"""
Personnel迁移回滚脚本
用于回滚Personnel统一模型迁移，恢复到原始Employee模型

执行步骤:
1. 从备份文件恢复Employee表数据
2. 恢复所有HR特化表的外键引用 (personnel_id -> employee_id)
3. 删除Personnel表
4. 验证回滚结果

使用方法:
python rollback_personnel_migration.py [backup_file.json]
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from tortoise.transactions import in_transaction


class PersonnelRollback:
    """Personnel迁移回滚类"""
    
    def __init__(self, backup_file: str = None):
        self.backup_file = backup_file
        self.rollback_log = []
        
    def log(self, message: str):
        """记录回滚日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        self.rollback_log.append(log_message)
    
    async def load_backup_data(self) -> Dict[str, Any]:
        """加载备份数据"""
        if not self.backup_file:
            # 查找最新的备份文件
            backup_files = [f for f in os.listdir('.') if f.startswith('backup_employee_data_') and f.endswith('.json')]
            if not backup_files:
                raise Exception("没有找到备份文件，无法回滚")
            
            backup_files.sort(reverse=True)
            self.backup_file = backup_files[0]
            self.log(f"使用最新备份文件: {self.backup_file}")
        
        self.log(f"加载备份数据: {self.backup_file}")
        
        with open(self.backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        self.log(f"备份数据加载完成: {len(backup_data)} 个表")
        return backup_data
    
    async def restore_employee_table(self, backup_data: Dict[str, Any]):
        """恢复Employee表"""
        self.log("恢复Employee表...")
        
        conn = Tortoise.get_connection("default")
        
        # 检查是否存在备份表
        try:
            await conn.execute_query("SELECT 1 FROM hr_employee_backup LIMIT 1")
            # 如果备份表存在，直接恢复
            await conn.execute_script("RENAME TABLE hr_employee_backup TO hr_employee")
            self.log("从hr_employee_backup恢复Employee表")
            return
        except:
            pass
        
        # 创建Employee表
        create_employee_sql = """
        CREATE TABLE IF NOT EXISTS hr_employee (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            user_id BIGINT NOT NULL,
            code VARCHAR(50) NULL UNIQUE,
            joining_time DATE NULL,
            position VARCHAR(255) NULL,
            employment_type VARCHAR(255) NULL DEFAULT '契約社員',
            business_content VARCHAR(255) NULL,
            salary_payment_type VARCHAR(20) NULL DEFAULT '月給制',
            salary INT NULL DEFAULT 0,
            is_active BOOLEAN NULL DEFAULT FALSE,
            process_instance_id VARCHAR(255) NULL,
            
            INDEX idx_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='従業員管理';
        """
        
        await conn.execute_script(create_employee_sql)
        
        # 从备份数据恢复Employee记录
        if 'hr_employee' in backup_data:
            employees = backup_data['hr_employee']
            
            for employee in employees:
                insert_sql = """
                INSERT INTO hr_employee (
                    id, created_at, updated_at, user_id, code, joining_time,
                    position, employment_type, business_content, salary_payment_type,
                    salary, is_active, process_instance_id
                ) VALUES (
                    %(id)s, %(created_at)s, %(updated_at)s, %(user_id)s, %(code)s, %(joining_time)s,
                    %(position)s, %(employment_type)s, %(business_content)s, %(salary_payment_type)s,
                    %(salary)s, %(is_active)s, %(process_instance_id)s
                )
                """
                
                await conn.execute_query(insert_sql, employee)
            
            self.log(f"恢复Employee数据: {len(employees)} 条记录")
    
    async def restore_foreign_keys(self):
        """恢复关联表的外键引用"""
        self.log("恢复关联表的外键引用...")
        
        conn = Tortoise.get_connection("default")
        
        # 需要恢复的表
        tables_to_restore = [
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
        
        for table_name in tables_to_restore:
            try:
                # 检查表是否存在
                try:
                    await conn.execute_query(f"SELECT 1 FROM {table_name} LIMIT 1")
                except:
                    self.log(f"表 {table_name} 不存在，跳过")
                    continue
                
                # 检查personnel_id字段是否存在
                try:
                    await conn.execute_query(f"SELECT personnel_id FROM {table_name} LIMIT 1")
                except:
                    self.log(f"表 {table_name} 没有personnel_id字段，跳过")
                    continue
                
                # 删除personnel相关的外键约束
                try:
                    drop_fk_sql = f"""
                    ALTER TABLE {table_name}
                    DROP FOREIGN KEY fk_{table_name}_personnel_id
                    """
                    await conn.execute_script(drop_fk_sql)
                    self.log(f"删除表 {table_name} 的personnel外键约束")
                except Exception as e:
                    self.log(f"删除外键约束失败 {table_name}: {str(e)}")
                
                # 删除personnel_id字段
                try:
                    drop_column_sql = f"ALTER TABLE {table_name} DROP COLUMN personnel_id"
                    await conn.execute_script(drop_column_sql)
                    self.log(f"删除表 {table_name} 的personnel_id字段")
                except Exception as e:
                    self.log(f"删除personnel_id字段失败 {table_name}: {str(e)}")
                
                # 添加Employee外键约束
                try:
                    add_fk_sql = f"""
                    ALTER TABLE {table_name}
                    ADD CONSTRAINT fk_{table_name}_employee_id 
                    FOREIGN KEY (employee_id) REFERENCES hr_employee(id) ON DELETE CASCADE
                    """
                    await conn.execute_script(add_fk_sql)
                    self.log(f"为表 {table_name} 添加employee外键约束")
                except Exception as e:
                    self.log(f"添加employee外键约束失败 {table_name}: {str(e)}")
                
            except Exception as e:
                self.log(f"恢复表 {table_name} 外键失败: {str(e)}")
        
        self.log("关联表外键恢复完成")
    
    async def remove_personnel_table(self):
        """删除Personnel表"""
        self.log("删除Personnel表...")
        
        conn = Tortoise.get_connection("default")
        
        try:
            # 先重命名为备份，以防需要恢复
            await conn.execute_script("RENAME TABLE hr_personnel TO hr_personnel_backup_rollback")
            self.log("Personnel表已重命名为hr_personnel_backup_rollback")
        except Exception as e:
            self.log(f"删除Personnel表失败: {str(e)}")
    
    async def verify_rollback(self) -> bool:
        """验证回滚结果"""
        self.log("验证回滚结果...")
        
        conn = Tortoise.get_connection("default")
        
        # 验证Employee表存在且有数据
        try:
            employee_count = await conn.execute_query_dict("SELECT COUNT(*) as count FROM hr_employee")
            self.log(f"Employee表记录数: {employee_count[0]['count']}")
            
            if employee_count[0]['count'] == 0:
                self.log("⚠️  警告: Employee表没有数据!")
                return False
        except Exception as e:
            self.log(f"验证Employee表失败: {str(e)}")
            return False
        
        # 验证Personnel表不存在或已备份
        try:
            await conn.execute_query("SELECT 1 FROM hr_personnel LIMIT 1")
            self.log("⚠️  警告: Personnel表仍然存在!")
            return False
        except:
            self.log("✅ Personnel表已删除")
        
        # 验证关联表外键
        tables_to_verify = [
            "hr_employee_address",
            "hr_employee_emergency_contact",
            "hr_employee_bank_account"
        ]
        
        for table_name in tables_to_verify:
            try:
                # 检查是否还有personnel_id字段
                try:
                    await conn.execute_query(f"SELECT personnel_id FROM {table_name} LIMIT 1")
                    self.log(f"⚠️  警告: 表 {table_name} 仍有personnel_id字段!")
                    return False
                except:
                    pass  # 正常，字段应该被删除
                
                # 检查employee_id字段存在
                try:
                    await conn.execute_query(f"SELECT employee_id FROM {table_name} LIMIT 1")
                    self.log(f"✅ 表 {table_name} employee_id字段正常")
                except:
                    self.log(f"⚠️  警告: 表 {table_name} 缺少employee_id字段!")
                    return False
                
            except Exception as e:
                self.log(f"验证表 {table_name} 失败: {str(e)}")
        
        self.log("✅ 回滚验证通过")
        return True
    
    async def run_rollback(self):
        """执行完整回滚流程"""
        self.log("=== 开始Personnel迁移回滚 ===")
        
        try:
            # 初始化数据库连接
            await Tortoise.init(
                db_url="mysql://root:123456@127.0.0.1:3306/easywork_hr",
                modules={"models": ["app.models"]}
            )
            
            async with in_transaction():
                # 1. 加载备份数据
                backup_data = await self.load_backup_data()
                
                # 2. 恢复Employee表
                await self.restore_employee_table(backup_data)
                
                # 3. 恢复外键引用
                await self.restore_foreign_keys()
                
                # 4. 删除Personnel表
                await self.remove_personnel_table()
                
                # 5. 验证回滚结果
                if await self.verify_rollback():
                    self.log("✅ 回滚成功完成!")
                else:
                    self.log("❌ 回滚验证失败，请检查数据")
                    raise Exception("Rollback verification failed")
            
        except Exception as e:
            self.log(f"❌ 回滚失败: {str(e)}")
            raise e
        
        finally:
            await Tortoise.close_connections()
            
            # 保存回滚日志
            log_file = f"rollback_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.rollback_log))
            
            self.log(f"回滚日志保存至: {log_file}")


async def main():
    """主函数"""
    backup_file = sys.argv[1] if len(sys.argv) > 1 else None
    rollback = PersonnelRollback(backup_file)
    await rollback.run_rollback()


if __name__ == "__main__":
    print("Personnel迁移回滚脚本")
    print("⚠️  警告: 此操作将回滚Personnel迁移，恢复到Employee模型!")
    
    confirm = input("确定要继续回滚吗? (yes/no): ")
    if confirm.lower() == 'yes':
        asyncio.run(main())
    else:
        print("回滚已取消")