#!/usr/bin/env python3
"""
模型完整性检查脚本
用于确保所有必要的模型都正确定义，避免表丢失问题

使用方法:
python check_models.py
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from tortoise import Tortoise
    from app.models import *
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)


class ModelIntegrityChecker:
    """模型完整性检查器"""
    
    def __init__(self):
        self.required_models = [
            'Personnel',
            'EmployeeAddress', 
            'EmployeeResidentAddress',
            'EmployeeEmergencyContact',
            'EmployeeBankAccount',
            'EmployeeResidenceStatus',
            'EmployeePassport',
            'EmployeeSocialInsurance',
            'EmployeeEmploymentInsurance',
            'EmployeeSalaryRecord',
            'EmployeeDocument',
            'EmployeeHistory'
        ]
        
        self.expected_tables = [
            'hr_personnel',
            'hr_employee_address',
            'hr_employee_resident_address', 
            'hr_employee_emergency_contact',
            'hr_employee_bank_account',
            'hr_employee_residence_status',
            'hr_employee_passport',
            'hr_employee_social_insurance',
            'hr_employee_employment_insurance',
            'hr_employee_salary_record',
            'hr_employee_document',
            'hr_employee_history'
        ]
    
    def check_model_definitions(self):
        """检查模型定义是否完整"""
        print("=" * 50)
        print("🔍 检查模型定义...")
        print("=" * 50)
        
        missing_models = []
        
        for model_name in self.required_models:
            try:
                model = globals().get(model_name)
                if model:
                    # 检查模型是否有Meta类和table属性
                    if hasattr(model, 'Meta') and hasattr(model.Meta, 'table'):
                        print(f"✅ {model_name} -> {model.Meta.table}")
                    else:
                        print(f"⚠️  {model_name} - 缺少Meta.table定义")
                else:
                    print(f"❌ {model_name} - 模型未定义!")
                    missing_models.append(model_name)
                    
            except Exception as e:
                print(f"❌ {model_name} - 错误: {str(e)}")
                missing_models.append(model_name)
        
        if missing_models:
            print(f"\\n❌ 发现 {len(missing_models)} 个缺失的模型:")
            for model in missing_models:
                print(f"   - {model}")
            return False
        else:
            print(f"\\n✅ 所有 {len(self.required_models)} 个模型定义完整!")
            return True
    
    async def check_database_tables(self):
        """检查数据库表是否存在"""
        print("\\n" + "=" * 50)
        print("🗄️  检查数据库表...")
        print("=" * 50)
        
        try:
            # 尝试多种数据库连接配置
            db_configs = [
                "mysql://root:123456@127.0.0.1:3306/easywork_hr",
                "mysql://root:@127.0.0.1:3306/easywork_hr",
                "mysql://root:password@127.0.0.1:3306/easywork_hr"
            ]
            
            conn = None
            for db_url in db_configs:
                try:
                    await Tortoise.init(
                        db_url=db_url,
                        modules={"models": ["app.models"]}
                    )
                    conn = Tortoise.get_connection("default")
                    print(f"✅ 数据库连接成功: {db_url.split('@')[1]}")
                    break
                except Exception as e:
                    print(f"⚠️  尝试连接 {db_url.split('@')[1]} 失败")
                    continue
            
            if not conn:
                print("❌ 无法连接到数据库，跳过表检查")
                return False
            
            # 获取所有表
            tables = await conn.execute_query_dict("SHOW TABLES")
            existing_tables = [list(t.values())[0] for t in tables]
            
            print(f"\\n数据库中共有 {len(existing_tables)} 个表:")
            for table in sorted(existing_tables):
                print(f"   📋 {table}")
            
            print(f"\\n检查必需表是否存在:")
            missing_tables = []
            
            for table in self.expected_tables:
                if table in existing_tables:
                    print(f"✅ {table}")
                else:
                    print(f"❌ {table} - 表不存在!")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"\\n❌ 发现 {len(missing_tables)} 个缺失的表:")
                for table in missing_tables:
                    print(f"   - {table}")
                
                print("\\n💡 恢复建议:")
                print("   1. 执行: mysql -u root -p easywork_hr < restore_missing_tables.sql")
                print("   2. 或运行迁移脚本重新创建表")
                return False
            else:
                print(f"\\n✅ 所有 {len(self.expected_tables)} 个必需表都存在!")
                return True
                
        except Exception as e:
            print(f"❌ 数据库检查失败: {str(e)}")
            return False
        
        finally:
            try:
                await Tortoise.close_connections()
            except:
                pass
    
    def check_import_integrity(self):
        """检查导入完整性"""
        print("\\n" + "=" * 50)
        print("📦 检查导入完整性...")
        print("=" * 50)
        
        try:
            # 检查关键导入
            from app.models.employee import Personnel, EmployeeAddress, EmployeeResidentAddress
            from app.models.enums import PersonType, EmploymentStatus, MarriageStatus
            
            print("✅ 核心模型导入成功")
            
            # 检查模型别名
            from app.models import Employee
            if Employee == Personnel:
                print("✅ Employee别名正确指向Personnel")
            else:
                print("⚠️  Employee别名可能有问题")
            
            return True
            
        except ImportError as e:
            print(f"❌ 导入失败: {str(e)}")
            return False
    
    def generate_recovery_commands(self):
        """生成恢复命令"""
        print("\\n" + "=" * 50)
        print("🛠️  恢复命令参考:")
        print("=" * 50)
        
        print("""
# 1. 立即备份当前数据库
mysqldump -u root -p easywork_hr > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 恢复缺失的表结构
mysql -u root -p easywork_hr < restore_missing_tables.sql

# 3. 检查表是否恢复
mysql -u root -p -e "SHOW TABLES FROM easywork_hr"

# 4. 重新检查模型
python check_models.py

# 5. 重启应用服务
make start
""")
    
    async def run_full_check(self):
        """运行完整检查"""
        print("🔍 Personnel模型完整性检查")
        print("=" * 50)
        
        results = []
        
        # 1. 检查模型定义
        results.append(self.check_model_definitions())
        
        # 2. 检查导入完整性
        results.append(self.check_import_integrity())
        
        # 3. 检查数据库表
        db_result = await self.check_database_tables()
        results.append(db_result)
        
        # 4. 总结
        print("\\n" + "=" * 50)
        print("📊 检查结果总结:")
        print("=" * 50)
        
        checks = [
            ("模型定义", results[0]),
            ("导入完整性", results[1]), 
            ("数据库表", results[2])
        ]
        
        all_passed = True
        for check_name, passed in checks:
            status = "✅ 通过" if passed else "❌ 失败"
            print(f"   {check_name}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\\n🎉 所有检查都通过! 模型完整性正常。")
        else:
            print("\\n⚠️  发现问题，需要修复！")
            self.generate_recovery_commands()
        
        return all_passed


async def main():
    """主函数"""
    checker = ModelIntegrityChecker()
    success = await checker.run_full_check()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n检查被用户中断")
    except Exception as e:
        print(f"\\n检查过程中发生错误: {str(e)}")
        sys.exit(1)