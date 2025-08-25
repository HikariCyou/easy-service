from fastapi import APIRouter

from .employee import router as employee_router
from .employee_evaluation import router as evaluation_router

router = APIRouter()
router.include_router(employee_router, prefix="/employee")
router.include_router(evaluation_router, prefix="/evaluations")