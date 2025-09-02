# 如何彻底避免Tortoise ORM表丢失问题

## 问题根源

当你修改`app/models/*.py`文件时，Tortoise ORM会：

1. **扫描所有模型定义**，如果某个表对应的模型类丢失或定义不完整
2. **自动生成迁移**，认为这些表"不再需要"
3. **执行DROP TABLE**，删除"多余"的表

## 彻底避免的5个关键措施

### 1. 🚫 **禁用自动迁移**

**立即执行以下操作：**

```python
# 在 app/settings/config.py 或数据库配置中设置：
TORTOISE_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "credentials": {
                "host": "127.0.0.1",
                "port": "3306",
                "user": "root", 
                "password": "123456",
                "database": "easywork_hr",
                "charset": "utf8mb4",
            }
        }
    },
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        }
    },
    # ⚠️ 关键设置 - 禁用自动迁移
    "use_tz": False,
    "timezone": "Asia/Tokyo"
}

# 在 Tortoise.init() 调用中添加：
await Tortoise.init(
    config=TORTOISE_CONFIG,
    # ❌ 绝对不要设置这个参数！
    # generate_schemas=True,  # 这会导致自动删除表
)
```

### 2. 📋 **手动管理迁移**

```bash
# 只在确认无误时才手动执行迁移
aerich init -t app.settings.TORTOISE_ORM --location migrations
aerich init-db

# 修改模型后，手动生成迁移（可选）
aerich migrate

# ⚠️ 执行迁移前务必备份数据库！
aerich upgrade
```

### 3. 🔒 **模型文件安全编辑原则**

#### ✅ 安全的操作：
- **添加新字段**（设置null=True或default值）
- **修改字段属性**（长度、类型兼容的变更）
- **添加索引**
- **修改字段描述**

#### ⚠️ 危险的操作：
- **删除模型类定义**
- **重命名模型类**  
- **删除字段**
- **修改主键**
- **修改外键关系**

#### 💡 正确做法：
```python
# ❌ 错误 - 直接删除会导致表丢失
# class OldModel(BaseModel):
#     pass

# ✅ 正确 - 先标记废弃，后续单独删除
class OldModel(BaseModel):
    """已废弃 - 待删除"""
    class Meta:
        table = "old_table"
        # 可以加上注释说明废弃原因
```

### 4. 📝 **建立检查清单**

修改模型前必须检查：

```bash
# 1. 备份数据库
mysqldump -u root -p easywork_hr > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 检查当前表结构
mysql -u root -p -e "SHOW TABLES FROM easywork_hr"

# 3. 确认所有模型类都完整定义
python -c "from app.models import *; print('所有模型导入成功')"

# 4. 生成迁移（不执行）
aerich migrate --name "describe_your_changes"

# 5. 检查生成的迁移文件内容
cat migrations/models/latest_migration_file.py

# 6. 确认无DROP TABLE操作后才执行
aerich upgrade
```

### 5. 🛡️ **模型完整性保护**

创建一个模型检查脚本：

```python
# check_models.py
import asyncio
from tortoise import Tortoise
from app.models import *

async def check_all_models():
    """检查所有模型是否完整定义"""
    
    required_models = [
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
    
    print("检查模型定义...")
    for model_name in required_models:
        try:
            model = globals()[model_name]
            print(f"✅ {model_name} - OK")
        except KeyError:
            print(f"❌ {model_name} - 缺失！")
            
    print("\\n检查数据库连接和表...")
    await Tortoise.init(
        db_url="mysql://root:123456@127.0.0.1:3306/easywork_hr",
        modules={"models": ["app.models"]}
    )
    
    conn = Tortoise.get_connection("default")
    tables = await conn.execute_query_dict("SHOW TABLES")
    
    existing_tables = [list(t.values())[0] for t in tables]
    
    expected_tables = [
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
    
    print("\\n数据库表检查:")
    for table in expected_tables:
        if table in existing_tables:
            print(f"✅ {table} - 存在")
        else:
            print(f"❌ {table} - 缺失！")
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(check_all_models())
```

## 🚨 紧急恢复指南

如果已经丢失了表：

### 1. 立即停止所有操作
```bash
# 停止应用服务
pkill -f "python.*run.py"
```

### 2. 检查备份
```bash
# 查找最近的数据库备份
ls -la *.sql | head -5
# 或查找自动备份
ls -la /path/to/backups/ | head -5
```

### 3. 恢复表结构
```sql
-- 手动重建丢失的表（以EmployeeResidentAddress为例）
CREATE TABLE hr_employee_resident_address (
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
    
    INDEX idx_personnel_id (personnel_id),
    FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 4. 重建所有丢失的表

你需要重建的表可能包括：
- `hr_employee_resident_address` 
- `hr_employee_address`
- `hr_employee_emergency_contact`
- `hr_employee_bank_account`
- `hr_employee_residence_status`
- `hr_employee_passport`
- `hr_employee_social_insurance`
- `hr_employee_employment_insurance`
- 其他相关表...

## 🔧 立即执行的保护措施

1. **马上备份当前数据库**
2. **禁用自动迁移功能**
3. **安装模型检查脚本**
4. **建立每日自动备份**

这样就能彻底避免表再次丢失！