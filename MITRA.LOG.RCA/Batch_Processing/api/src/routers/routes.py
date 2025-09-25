"""
API routes module
"""

from fastapi import APIRouter
from api.src.routers.job_routes import router as job_router
from api.src.routers.status_routes import router as status_router

# Create main router
router = APIRouter()

# Include sub-routers
router.include_router(job_router, prefix="/jobs", tags=["jobs"])
router.include_router(status_router, prefix="/system", tags=["system"])

__all__ = ["router", "job_router", "status_router"]
