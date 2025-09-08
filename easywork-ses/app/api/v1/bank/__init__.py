from fastapi import APIRouter
from .bank import router

bank_router = APIRouter()

bank_router.include_router(router)

__all__ = ["bank_router"]