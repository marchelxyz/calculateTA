from __future__ import annotations

from fastapi import APIRouter

from app.api.ai import router as ai_router
from app.api.modules import router as modules_router
from app.api.projects import router as projects_router
from app.api.rates import router as rates_router


def get_api_router() -> APIRouter:
    """Build main API router."""

    router = APIRouter()
    router.include_router(modules_router)
    router.include_router(projects_router)
    router.include_router(rates_router)
    router.include_router(ai_router)
    return router
