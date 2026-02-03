from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.auth import require_user, router as auth_router
from app.api.connections import router as connections_router
from app.api.ai import router as ai_router
from app.api.exports import router as exports_router
from app.api.infrastructure import router as infrastructure_router
from app.api.modules import router as modules_router
from app.api.projects import router as projects_router
from app.api.rates import router as rates_router
from app.api.users import router as users_router


def get_api_router() -> APIRouter:
    """Build main API router."""

    router = APIRouter(dependencies=[Depends(require_user)])
    router.include_router(auth_router)
    router.include_router(modules_router)
    router.include_router(projects_router)
    router.include_router(connections_router)
    router.include_router(rates_router)
    router.include_router(ai_router)
    router.include_router(infrastructure_router)
    router.include_router(exports_router)
    router.include_router(users_router)
    return router
