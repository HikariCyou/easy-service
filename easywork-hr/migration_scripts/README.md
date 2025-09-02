# Personnel统一模型迁移指南

## 概述

本迁移将easywork-hr系统的Employee模型升级为与easywork-ses系统统一的Personnel模型，解决两个服务间数据不一致的问题。

## 问题背景

- **easywork-ses**: 已使用统一的Personnel模型管理所有人员类型（员工、BP员工、自由职业者）
- **easywork-hr**: 仍使用独立的Employee模型，导致数据不同步
- **严重影响**: HR录入员工时，没有在SES系统创建对应Personnel记录，两个系统数据完全隔离

## 迁移方案

### 核心策略
- **统一数据模型**: 使用Personnel替代Employee
- **保留HR特化功能**: 所有HR特化模型（地址、银行账户等）保持不变，仅调整关联关系
- **向后兼容**: 保持现有API接口不变
- **安全迁移**: 完整备份+验证+回滚机制

### 模型变化

#### 新Personnel模型包含
```python
# === 基础信息 (原Employee字段) ===
user_id, code, joining_time, position, employment_type, 
business_content, salary_payment_type, salary, process_instance_id

# === SES统一字段 (新增) ===  
name, age, sex, birthday, phone, email, nationality,
visa_status, visa_expire_date, japanese_level, 
it_experience_years, standard_unit_price, employment_status
```

#### HR特化模型关联变化
```python
# 修改前
class EmployeeAddress:
    employee = fields.ForeignKeyField("Employee")

# 修改后  
class EmployeeAddress:
    personnel = fields.ForeignKeyField("Personnel")
```

## 迁移步骤

### 1. 执行迁移

```bash
cd /path/to/easywork-hr/migration_scripts

# 执行迁移 (需要确认)
python migrate_to_personnel_unified.py
```

### 2. 验证结果

迁移脚本会自动验证：
- Personnel表记录数 = Employee表记录数
- 所有HR特化表外键正确更新
- 数据完整性检查

### 3. 回滚 (如有问题)

```bash
# 使用自动备份回滚
python rollback_personnel_migration.py

# 或指定备份文件回滚
python rollback_personnel_migration.py backup_employee_data_20250901_120000.json
```

## 迁移内容详解

### 数据库结构变化

#### 1. 新建表
```sql
CREATE TABLE hr_personnel (
  -- 基础字段
  id BIGINT PRIMARY KEY,
  user_id BIGINT,
  person_type VARCHAR(20) DEFAULT 'employee',
  
  -- 原Employee字段
  code VARCHAR(50),
  joining_time DATE,
  position VARCHAR(255),
  employment_type VARCHAR(255),
  salary INT,
  
  -- SES统一字段  
  name VARCHAR(100),
  age INT,
  nationality VARCHAR(50),
  visa_expire_date DATE,
  it_experience_years FLOAT,
  -- ... 更多字段
);
```

#### 2. 更新关联表
所有HR特化表添加`personnel_id`字段，并建立外键约束：

```sql
-- 示例：员工地址表
ALTER TABLE hr_employee_address 
ADD COLUMN personnel_id BIGINT;

UPDATE hr_employee_address 
SET personnel_id = employee_id;

ALTER TABLE hr_employee_address
ADD CONSTRAINT fk_hr_employee_address_personnel_id 
FOREIGN KEY (personnel_id) REFERENCES hr_personnel(id);
```

### 应用代码变化

#### 1. 模型层
```python
# 新Personnel模型 (app/models/employee.py)
class Personnel(BaseModel, TimestampMixin):
    """统一人员管理模型"""
    user_id = fields.BigIntField()
    person_type = fields.CharEnumField(PersonType, default=PersonType.EMPLOYEE)
    name = fields.CharField(max_length=100)
    # ... 完整字段定义

# 保持兼容性
Employee = Personnel  # 别名
```

#### 2. 控制器层
```python
# 查询条件更新
async def get_employee_by_user_id(self, user_id: int):
    return await Personnel.get_or_none(
        user_id=user_id, 
        person_type=PersonType.EMPLOYEE  # 新增过滤条件
    )
```

#### 3. API层
接口保持不变，内部使用Personnel模型处理

## 安全措施

### 1. 自动备份
迁移前自动备份所有相关表数据到JSON文件：
```
backup_employee_data_20250901_120000.json
```

### 2. 事务性迁移
所有迁移操作在单一数据库事务中执行，失败自动回滚

### 3. 完整性验证
- 记录数量匹配验证
- 外键约束验证  
- 数据一致性验证

### 4. 回滚机制
提供完整回滚脚本，可恢复到迁移前状态

## 迁移后验证

### 1. 功能验证
- [ ] 员工注册功能正常
- [ ] 员工信息查询正常
- [ ] 员工详细信息（地址、银行账户等）正常
- [ ] HR流程（入职流程）正常

### 2. 数据验证
```sql
-- 检查Personnel数据
SELECT COUNT(*) FROM hr_personnel WHERE person_type = 'employee';

-- 检查关联表外键
SELECT COUNT(*) FROM hr_employee_address WHERE personnel_id IS NULL;

-- 验证数据一致性
SELECT p.user_id, p.name, a.address 
FROM hr_personnel p 
LEFT JOIN hr_employee_address a ON p.id = a.personnel_id 
LIMIT 10;
```

### 3. API验证
```bash
# 测试员工列表API
curl -X GET "http://localhost:8090/api/v1/employee/list"

# 测试员工详情API
curl -X GET "http://localhost:8090/api/v1/employee/get?employee_id=1"
```

## 注意事项

### 1. 服务间同步
迁移完成后，需要实现HR和SES系统的数据同步机制：
- HR录入员工时，同步创建SES的Personnel记录
- 基本信息变更时，双向同步

### 2. 前端影响
API接口保持兼容，前端无需修改

### 3. 性能考虑
Personnel表增加了很多字段，但大部分可为NULL，对性能影响有限

### 4. 维护建议
- 定期检查两个系统数据一致性
- 考虑后续统一为共享数据库或微服务同步机制

## 故障排除

### 常见问题

1. **迁移失败：外键约束错误**
   ```
   解决：检查是否有孤儿数据，清理后重试
   ```

2. **API调用失败：字段不存在**
   ```
   解决：确认模型文件已更新，重启服务
   ```

3. **数据查询为空**
   ```
   解决：检查person_type过滤条件是否正确
   ```

### 紧急回滚
如果迁移后发现严重问题：
```bash
# 立即回滚
python rollback_personnel_migration.py

# 重启服务
cd ../
make start
```

## 联系支持

如遇到迁移相关问题，请联系开发团队并提供：
- 迁移日志文件
- 错误信息截图  
- 数据库状态信息