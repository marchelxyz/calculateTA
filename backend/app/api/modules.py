from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.db import get_db_session
from app.models import Module, ModuleRoleHours, ProjectModule
from app.schemas import (
    ModuleCreate,
    ModuleOut,
    ModuleRoleHours as ModuleRoleHoursPayload,
    ModuleUpdate,
)

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=list[ModuleOut])
def list_modules(session: Session = Depends(get_db_session)) -> list[ModuleOut]:
    """Return module catalog."""

    result = session.execute(select(Module).options(joinedload(Module.role_hours)))
    return [_serialize_module(module) for module in result.unique().scalars()]


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
    session.flush()
    _sync_role_hours(session, module.id, payload.role_hours)
    session.commit()
    session.refresh(module)
    session.refresh(module, attribute_names=["role_hours"])
    return _serialize_module(module)


@router.patch("/{module_id}", response_model=ModuleOut)
def update_module(
    module_id: int,
    payload: ModuleUpdate,
    session: Session = Depends(get_db_session),
) -> ModuleOut:
    """Update catalog module."""

    module = session.execute(
        select(Module).where(Module.id == module_id).options(joinedload(Module.role_hours))
    ).scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    if payload.name is not None:
        module.name = payload.name
    if payload.description is not None:
        module.description = payload.description
    if payload.hours_frontend is not None:
        module.hours_frontend = payload.hours_frontend
    if payload.hours_backend is not None:
        module.hours_backend = payload.hours_backend
    if payload.hours_qa is not None:
        module.hours_qa = payload.hours_qa
    if payload.role_hours is not None:
        _replace_role_hours(session, module.id, payload.role_hours)
    session.commit()
    session.refresh(module)
    session.refresh(module, attribute_names=["role_hours"])
    return _serialize_module(module)

@router.delete("/{module_id}")
def delete_module(
    module_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    """Delete module from catalog."""

    module = session.execute(select(Module).where(Module.id == module_id)).scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    used = session.execute(
        select(ProjectModule.id).where(ProjectModule.module_id == module_id)
    ).first()
    if used:
        raise HTTPException(status_code=409, detail="Module is used in projects")
    session.delete(module)
    session.commit()
    return {"status": "ok"}


def _sync_role_hours(
    session: Session,
    module_id: int,
    items: list[ModuleRoleHoursPayload],
) -> None:
    if not items:
        return
    for item in items:
        if item.hours <= 0:
            continue
        session.add(
            ModuleRoleHours(
                module_id=module_id,
                role=item.role,
                hours=item.hours,
            )
        )


def _replace_role_hours(
    session: Session,
    module_id: int,
    items: list[ModuleRoleHoursPayload],
) -> None:
    session.execute(
        delete(ModuleRoleHours).where(ModuleRoleHours.module_id == module_id)
    )
    _sync_role_hours(session, module_id, items)


def _serialize_module(module: Module) -> ModuleOut:
    return ModuleOut(
        id=module.id,
        code=module.code,
        name=module.name,
        description=module.description,
        hours_frontend=module.hours_frontend,
        hours_backend=module.hours_backend,
        hours_qa=module.hours_qa,
        role_hours=[{"role": item.role, "hours": item.hours} for item in module.role_hours],
    )
