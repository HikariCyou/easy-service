from fastapi import APIRouter

from .case import router

case_router = APIRouter()
case_router.include_router(router, tags=["case"])

__all__ = ["case_router"]