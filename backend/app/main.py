from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import get_api_router
from app.core.config import settings
from app.db_init import init_and_verify_db
from app.services.seed_service import seed_defaults
from app.db import SessionLocal


def create_app() -> FastAPI:
    """Create FastAPI application."""

    app = FastAPI(title=settings.app_name)
    _configure_cors(app)
    app.include_router(get_api_router(), prefix=settings.api_prefix)
    _mount_frontend(app)
    _register_startup(app)
    return app


def _configure_cors(app: FastAPI) -> None:
    origins = [str(origin) for origin in settings.cors_allowed_origins]
    if not origins:
        origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _mount_frontend(app: FastAPI) -> None:
    dist_path = Path(settings.frontend_dist_path)
    if dist_path.exists():
        app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(dist_path / "index.html")


def _register_startup(app: FastAPI) -> None:
    @app.on_event("startup")
    def _startup() -> None:
        init_and_verify_db()
        session = SessionLocal()
        try:
            seed_defaults(session)
        finally:
            session.close()


app = create_app()
