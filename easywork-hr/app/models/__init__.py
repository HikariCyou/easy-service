# 新増model需要在这里导入
from .admin import *
from .employee import *
from .storage import *

# 为了向后兼容，保留Employee别名
from .employee import Personnel, Employee, EmployeeDetail