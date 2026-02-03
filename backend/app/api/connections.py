from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import Project, ProjectConnection
from app.schemas import ProjectConnectionOut, ProjectConnectionUpsert

router = APIRouter(tags=["connections"])


@router.get("/projects/{project_id}/connections", response_model=list[ProjectConnectionOut])
def list_connections(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> list[ProjectConnectionOut]:
    """List project connections."""

    _get_project(session, project_id)
    result = session.execute(
        select(ProjectConnection).where(ProjectConnection.project_id == project_id)
    )
    return [ProjectConnectionOut(**item.__dict__) for item in result.scalars()]


@router.put("/projects/{project_id}/connections", response_model=list[ProjectConnectionOut])
def replace_connections(
    project_id: int,
    payload: list[ProjectConnectionUpsert],
    session: Session = Depends(get_db_session),
) -> list[ProjectConnectionOut]:
    """Replace project connections."""

    _get_project(session, project_id)
    session.execute(
        delete(ProjectConnection).where(ProjectConnection.project_id == project_id)
    )
    session.flush()
    records: list[ProjectConnectionOut] = []
    for item in payload:
        record = ProjectConnection(
            project_id=project_id,
            from_project_module_id=item.from_project_module_id,
            to_project_module_id=item.to_project_module_id,
        )
        session.add(record)
        session.flush()
        records.append(ProjectConnectionOut(**record.__dict__))
    session.commit()
    return records


def _get_project(session: Session, project_id: int) -> Project:
    result = session.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one()
