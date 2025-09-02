# 安全的模型修改工作流程

## 📋 修改前检查清单

### 1. 环境准备
```bash
# ✅ 必须执行的步骤
□ 备份数据库: mysqldump -u root -p easywork_hr > backup_$(date +%Y%m%d_%H%M%S).sql
□ 检查当前表: mysql -u root -p -e "SHOW TABLES FROM easywork_hr" 
□ 记录当前状态: python check_models.py > status_before.txt
□ 确认git状态干净: git status
```

### 2. 安全原则
- ✅ **只能新增**，不要删除模型类
- ✅ **先标记废弃**，后续单独处理
- ✅ **保持向后兼容**
- ❌ **绝不删除模型定义**

## 🔧 修改模型的安全步骤

### Step 1: 分析影响
```bash
# 1. 确认要修改的模型
echo "要修改的模型: [ModelName]"

# 2. 检查模型关联
python -c "
from app.models import [ModelName]
print('表名:', [ModelName].Meta.table)
print('关联字段:', [列出外键关联])
"
```

### Step 2: 安全修改
```python
# ✅ 正确做法 - 添加字段
class Personnel(BaseModel, TimestampMixin):
    # 原有字段保持不变
    existing_field = fields.CharField(max_length=100)
    
    # 新增字段 - 必须可空或有默认值
    new_field = fields.CharField(max_length=50, null=True, description="新增字段")

# ✅ 正确做法 - 修改字段属性（兼容性变更）
class Personnel(BaseModel, TimestampMixin):
    # 扩大长度是安全的
    name = fields.CharField(max_length=200, description="扩大长度")  # 原来是100

# ❌ 危险做法 - 删除模型
# class OldModel(BaseModel):  # 不要直接删除！
#     pass

# ✅ 正确做法 - 标记废弃
class OldModel(BaseModel, TimestampMixin):
    """🚨 已废弃 - 2025-01-15 - 原因: 合并到NewModel
    TODO: 数据迁移完成后删除此模型
    """
    old_field = fields.CharField(max_length=100)
    
    class Meta:
        table = "old_table"  # 保持表名不变
```

### Step 3: 验证修改
```bash
# 1. 语法检查
python -m py_compile app/models/employee.py

# 2. 导入检查
python -c "from app.models import *; print('导入成功')"

# 3. 完整性检查
python check_models.py

# 4. 如果检查通过，提交代码
git add app/models/
git commit -m "feat: 安全添加Personnel新字段"
```

### Step 4: 数据库迁移（可选）
```bash
# ⚠️ 只在确认安全时执行
aerich migrate --name "add_new_field_to_personnel"

# 检查生成的迁移文件
cat migrations/models/latest_file.py

# 确认无DROP操作后执行
aerich upgrade
```

## 🚨 紧急回滚程序

如果修改后发现表丢失：

### 1. 立即停止服务
```bash
pkill -f "python.*run.py"
```

### 2. 检查损失
```bash
mysql -u root -p -e "SHOW TABLES FROM easywork_hr"
```

### 3. 恢复表结构
```bash
# 使用预备的恢复脚本
mysql -u root -p easywork_hr < restore_missing_tables.sql
```

### 4. 回滚代码
```bash
git checkout HEAD~1 app/models/
```

### 5. 验证恢复
```bash
python check_models.py
```

## 📝 日常维护检查

### 每天执行
```bash
# 添加到crontab或CI/CD
0 9 * * * cd /path/to/project && python check_models.py
```

### 每周执行
```bash
# 检查数据库表结构变化
mysqldump -u root -p --no-data easywork_hr > schema_$(date +%Y%m%d).sql
```

## 🛡️ 预防配置

### 1. 数据库配置
```python
# app/settings/config.py
TORTOISE_CONFIG = {
    # ... 其他配置
    
    # ⚠️ 关键设置 - 禁用自动生成
    "use_tz": False,
    "timezone": "Asia/Tokyo",
    
    # 🚫 绝不设置此项！
    # "generate_schemas": True,  # 这会删除表！
}
```

### 2. 启动脚本保护
```python
# run.py 或启动文件中
await Tortoise.init(
    config=TORTOISE_CONFIG,
    # ❌ 绝对不要设置！
    # generate_schemas=True
)
```

### 3. 自动化检查
```bash
# 添加到Makefile
check-models:
    @echo "检查模型完整性..."
    @python check_models.py

# 修改start命令
start: check-models
    @echo "启动前检查通过"
    @python run.py
```

## 📚 最佳实践总结

### ✅ 安全操作
1. **添加新字段**（null=True或默认值）
2. **扩大字段长度** 
3. **添加索引**
4. **修改描述和注释**
5. **添加新的模型类**

### ⚠️ 需谨慎
1. **修改字段类型**（确保兼容）
2. **重命名字段**（需要迁移）
3. **修改外键关系**
4. **更改表名**

### ❌ 禁止操作
1. **删除模型类定义**
2. **删除字段定义** 
3. **直接修改主键**
4. **在生产环境直接ALTER TABLE**

## 🔍 问题诊断

### 如果表还是丢失了：

1. **检查模型文件**
   ```bash
   grep -n "class.*Model" app/models/*.py
   ```

2. **检查导入路径**
   ```bash
   python -c "from app.models import *"
   ```

3. **检查Meta定义**
   ```bash
   python -c "
   from app.models import EmployeeAddress
   print(EmployeeAddress.Meta.table)
   "
   ```

4. **查看迁移历史**
   ```bash
   aerich history
   ```

5. **检查数据库连接**
   ```bash
   mysql -u root -p -e "SELECT VERSION()"
   ```

遵循这个工作流程，就能彻底避免表丢失问题！