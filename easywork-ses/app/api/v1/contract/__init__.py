from fastapi import APIRouter

from .contract import router

contract_router = APIRouter()
contract_router.include_router(router, tags=["contract"])

__all__ = ["contract_router"]