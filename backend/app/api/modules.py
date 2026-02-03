from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import Module
from app.schemas import ModuleOut

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=list[ModuleOut])
def list_modules(session: Session = Depends(get_db_session)) -> list[ModuleOut]:
    """Return module catalog."""

    result = session.execute(select(Module))
    return [ModuleOut(**module.__dict__) for module in result.scalars()]
