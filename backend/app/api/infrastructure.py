from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import InfrastructureItem, Project, ProjectInfrastructure
from app.schemas import (
    InfrastructureItemCreate,
    InfrastructureItemOut,
    ProjectInfrastructureOut,
    ProjectInfrastructureUpsert,
)

router = APIRouter(tags=["infrastructure"])


@router.get("/infrastructure", response_model=list[InfrastructureItemOut])
def list_infrastructure_items(
    session: Session = Depends(get_db_session),
) -> list[InfrastructureItemOut]:
    """List infrastructure catalog items."""

    result = session.execute(select(InfrastructureItem))
    return [InfrastructureItemOut(**item.__dict__) for item in result.scalars()]


@router.post("/infrastructure", response_model=InfrastructureItemOut)
def create_infrastructure_item(
    payload: InfrastructureItemCreate,
    session: Session = Depends(get_db_session),
) -> InfrastructureItemOut:
    """Create infrastructure catalog item."""

    existing = _find_infrastructure_item(session, payload.code)
    if existing:
        raise HTTPException(status_code=400, detail="Infrastructure item code already exists")
    item = InfrastructureItem(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        unit_cost=payload.unit_cost,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return InfrastructureItemOut(**item.__dict__)


@router.get("/projects/{project_id}/infrastructure", response_model=list[ProjectInfrastructureOut])
def list_project_infrastructure(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> list[ProjectInfrastructureOut]:
    """List infrastructure items for project."""

    _get_project(session, project_id)
    result = session.execute(
        select(ProjectInfrastructure).where(ProjectInfrastructure.project_id == project_id)
    )
    return [ProjectInfrastructureOut(**item.__dict__) for item in result.scalars()]


@router.put("/projects/{project_id}/infrastructure", response_model=list[ProjectInfrastructureOut])
def upsert_project_infrastructure(
    project_id: int,
    payload: list[ProjectInfrastructureUpsert],
    session: Session = Depends(get_db_session),
) -> list[ProjectInfrastructureOut]:
    """Upsert infrastructure items for project."""

    _get_project(session, project_id)
    results: list[ProjectInfrastructureOut] = []
    for entry in payload:
        _get_infrastructure_item(session, entry.infrastructure_item_id)
        record = _get_project_infrastructure(session, project_id, entry.infrastructure_item_id)
        if record:
            record.quantity = entry.quantity
        else:
            record = ProjectInfrastructure(
                project_id=project_id,
                infrastructure_item_id=entry.infrastructure_item_id,
                quantity=entry.quantity,
            )
            session.add(record)
        session.flush()
        results.append(ProjectInfrastructureOut(**record.__dict__))
    session.commit()
    return results


def _get_project(session: Session, project_id: int) -> Project:
    result = session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_infrastructure_item(
    session: Session,
    item_id: int,
) -> InfrastructureItem:
    result = session.execute(select(InfrastructureItem).where(InfrastructureItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Infrastructure item not found")
    return item


def _find_infrastructure_item(
    session: Session,
    code: str,
) -> InfrastructureItem | None:
    result = session.execute(select(InfrastructureItem).where(InfrastructureItem.code == code))
    return result.scalar_one_or_none()


def _get_project_infrastructure(
    session: Session,
    project_id: int,
    item_id: int,
) -> ProjectInfrastructure | None:
    result = session.execute(
        select(ProjectInfrastructure)
        .where(ProjectInfrastructure.project_id == project_id)
        .where(ProjectInfrastructure.infrastructure_item_id == item_id)
    )
    return result.scalar_one_or_none()
