from fastapi import APIRouter

from app.core.dependency import DependAuth, DependPermisson

from .attendance import router as attendance_router
from .bank import bank_router
from .bp import bp_router
from .case import case_router
from .contract import contract_router
from .cp import cp_router
from .dashboard import router as dashboard_router
from .employee import router as employee_router
from .evaluation import router as evaluation_router
from .freelancer import router as freelancer_router
from .ip import ip_router
from .order import order_router
from .request import request_router

v1_router = APIRouter()

v1_router.include_router(attendance_router, prefix="/attendance", tags=["勤怠管理"], dependencies=[DependAuth])
v1_router.include_router(bp_router, prefix="/bp", tags=["ビジネスパートナー"], dependencies=[DependAuth])
v1_router.include_router(case_router, prefix="/case", tags=["案件管理"], dependencies=[DependAuth])
v1_router.include_router(cp_router, prefix="/cp", tags=["取り先会社"], dependencies=[DependAuth])
v1_router.include_router(contract_router, prefix="/contract", tags=["契約管理"], dependencies=[DependAuth])
v1_router.include_router(dashboard_router, prefix="/dashboard", tags=["ダッシュボード統計"], dependencies=[DependAuth])
v1_router.include_router(employee_router, prefix="/employee", tags=["自社員工管理"], dependencies=[DependAuth])
v1_router.include_router(evaluation_router, prefix="/evaluation", tags=["統一人材評価"], dependencies=[DependAuth])
v1_router.include_router(freelancer_router, prefix="/freelancer", tags=["フリーランサー管理"], dependencies=[DependAuth])
v1_router.include_router(ip_router, prefix="/ip", tags=["要員管理"], dependencies=[DependAuth])
v1_router.include_router(bank_router, prefix="/bank", tags=["銀行口座管理"], dependencies=[DependAuth])
v1_router.include_router(order_router, prefix="/order", tags=["注文書管理"], dependencies=[DependAuth])
v1_router.include_router(request_router, prefix="/request", tags=["請求書管理"], dependencies=[DependAuth])
