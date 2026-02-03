from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import Module
from app.schemas import ModuleCreate, ModuleOut

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=list[ModuleOut])
def list_modules(session: Session = Depends(get_db_session)) -> list[ModuleOut]:
    """Return module catalog."""

    result = session.execute(select(Module))
    return [ModuleOut(**module.__dict__) for module in result.scalars()]


@router.post("", response_model=ModuleOut)
def create_module(
    payload: ModuleCreate,
    session: Session = Depends(get_db_session),
) -> ModuleOut:
    """Create catalog module."""

    existing = session.execute(
        select(Module).where(Module.code == payload.code)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Module code already exists")

    module = Module(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        hours_frontend=payload.hours_frontend,
        hours_backend=payload.hours_backend,
        hours_qa=payload.hours_qa,
    )
    session.add(module)
    session.commit()
    session.refresh(module)
    return ModuleOut(**module.__dict__)
