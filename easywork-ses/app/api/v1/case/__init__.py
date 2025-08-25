from fastapi import APIRouter

from .case import router
from .case_history import router as history_router

case_router = APIRouter()
case_router.include_router(router)
case_router.include_router(history_router, prefix="/history")

__all__ = ["case_router"]