from fastapi import APIRouter

from .freelancer import router as freelancer_router

router = APIRouter()
router.include_router(freelancer_router,)