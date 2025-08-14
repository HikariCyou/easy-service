from fastapi import APIRouter

from .employee import router

employee_router = APIRouter()
employee_router.include_router(router, tags=["employee"])

__all__ = ["employee_router"]