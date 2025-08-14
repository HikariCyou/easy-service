from fastapi import APIRouter

from .bp import router
from .employee import router as employee_router

bp_router = APIRouter()
bp_router.include_router(router, tags=["bp"])
bp_router.include_router(employee_router, prefix="/employee", tags=["employee"])

__all__ = ["bp_router"]
