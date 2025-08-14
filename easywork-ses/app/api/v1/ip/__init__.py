from fastapi import APIRouter

from .import_person import router

ip_router = APIRouter()
ip_router.include_router(router)

__all__ = ["ip_router"]
