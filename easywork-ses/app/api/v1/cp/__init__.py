from fastapi import APIRouter

from .cp import router

cp_router = APIRouter()
cp_router.include_router(router)

__all__ = ["cp_router"]
