from fastapi import APIRouter

from app.core.dependency import DependPermisson, DependAuth

from .apis import apis_router
from .employee import employee_router
v1_router = APIRouter()

v1_router.include_router(employee_router, prefix="/employee", tags=["従業員管理"], dependencies=[DependAuth])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermisson])