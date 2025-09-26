from fastapi import APIRouter
from .finance import router as finance_router

router = APIRouter()
router.include_router(finance_router, tags=["finance"])

__all__ = ["router"]