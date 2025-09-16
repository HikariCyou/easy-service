from fastapi import APIRouter
from .order import router

order_router = APIRouter()
order_router.include_router(router)

__all__ = ["order_router"]