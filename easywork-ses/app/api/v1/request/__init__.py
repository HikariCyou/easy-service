from fastapi import APIRouter

from .request import router

request_router = APIRouter()
request_router.include_router(router)

__all__ = ["request_router"]
