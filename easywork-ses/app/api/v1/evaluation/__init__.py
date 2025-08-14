from fastapi import APIRouter

from .person_evaluation import router

evaluation_router = APIRouter()

evaluation_router.include_router(router)

__all__ = ["evaluation_router"]