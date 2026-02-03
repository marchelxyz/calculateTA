from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import Assignment, Module, Project, ProjectCoefficient, ProjectModule
from app.schemas import (
    AssignmentOut,
    AssignmentUpsert,
    ProjectCreate,
    ProjectCoefficientCreate,
    ProjectCoefficientOut,
    ProjectModuleCreate,
    ProjectModuleOut,
    ProjectModuleUpdate,
    ProjectOut,
    ProjectSettings,
    SummaryOut,
)
from app.services.summary_service import build_project_summary

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut)
def create_project(
    payload: ProjectCreate,
    session: Session = Depends(get_db_session),
) -> ProjectOut:
    """Create new project."""

    project = Project(
        name=payload.name,
        description=payload.description,
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    _seed_project_coefficients(session, project.id)
    return ProjectOut(**project.__dict__)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> ProjectOut:
    """Get project by id."""

    project = _get_project(session, project_id)
    return ProjectOut(**project.__dict__)


@router.put("/{project_id}/settings", response_model=ProjectOut)
def update_settings(
    project_id: int,
    payload: ProjectSettings,
    session: Session = Depends(get_db_session),
) -> ProjectOut:
    """Update project settings."""

    project = _get_project(session, project_id)
    project.uncertainty_level = payload.uncertainty_level
    project.uiux_level = payload.uiux_level
    project.legacy_code = payload.legacy_code
    session.commit()
    session.refresh(project)
    return ProjectOut(**project.__dict__)


@router.get("/{project_id}/modules", response_model=list[ProjectModuleOut])
def list_project_modules(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> list[ProjectModuleOut]:
    """List project modules."""

    result = session.execute(
        select(ProjectModule).where(ProjectModule.project_id == project_id)
    )
    return [ProjectModuleOut(**module.__dict__) for module in result.scalars()]


@router.post("/{project_id}/modules", response_model=ProjectModuleOut)
def add_project_module(
    project_id: int,
    payload: ProjectModuleCreate,
    session: Session = Depends(get_db_session),
) -> ProjectModuleOut:
    """Add module to project."""

    _get_project(session, project_id)
    module = _get_module(session, payload.module_id)
    existing = _find_project_module(session, project_id, module.id)
    if existing:
        return ProjectModuleOut(**existing.__dict__)
    project_module = ProjectModule(
        project_id=project_id,
        module_id=module.id,
        custom_name=payload.custom_name,
    )
    session.add(project_module)
    session.commit()
    session.refresh(project_module)
    return ProjectModuleOut(**project_module.__dict__)


@router.patch("/{project_id}/modules/{project_module_id}", response_model=ProjectModuleOut)
def update_project_module(
    project_id: int,
    project_module_id: int,
    payload: ProjectModuleUpdate,
    session: Session = Depends(get_db_session),
) -> ProjectModuleOut:
    """Update module overrides."""

    project_module = _get_project_module(session, project_id, project_module_id)
    _apply_project_module_updates(project_module, payload)
    session.commit()
    session.refresh(project_module)
    return ProjectModuleOut(**project_module.__dict__)


@router.delete("/{project_id}/modules/{project_module_id}")
def delete_project_module(
    project_id: int,
    project_module_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    """Remove module from project."""

    project_module = _get_project_module(session, project_id, project_module_id)
    session.delete(project_module)
    session.commit()
    return {"status": "ok"}


@router.post("/{project_id}/assignments", response_model=list[AssignmentOut])
def upsert_assignments(
    project_id: int,
    payload: list[AssignmentUpsert],
    session: Session = Depends(get_db_session),
) -> list[AssignmentOut]:
    """Upsert role assignments."""

    _get_project(session, project_id)
    results = []
    for assignment in payload:
        db_assignment = _get_assignment(session, project_id, assignment)
        if db_assignment:
            db_assignment.level = assignment.level
        else:
            db_assignment = Assignment(
                project_id=project_id,
                project_module_id=assignment.project_module_id,
                role=assignment.role,
                level=assignment.level,
            )
            session.add(db_assignment)
        session.flush()
        results.append(AssignmentOut(**db_assignment.__dict__))
    session.commit()
    return results


@router.get("/{project_id}/assignments", response_model=list[AssignmentOut])
def list_assignments(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> list[AssignmentOut]:
    """List assignments for project."""

    _get_project(session, project_id)
    result = session.execute(
        select(Assignment).where(Assignment.project_id == project_id)
    )
    return [AssignmentOut(**assignment.__dict__) for assignment in result.scalars()]


@router.get("/{project_id}/summary", response_model=SummaryOut)
def get_summary(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> SummaryOut:
    """Return summary for project."""

    return build_project_summary(session, project_id)


@router.get("/{project_id}/coefficients", response_model=list[ProjectCoefficientOut])
def list_coefficients(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> list[ProjectCoefficientOut]:
    """List project coefficients."""

    _get_project(session, project_id)
    result = session.execute(
        select(ProjectCoefficient).where(ProjectCoefficient.project_id == project_id)
    )
    items = list(result.scalars())
    if not items:
        _seed_project_coefficients(session, project_id)
        result = session.execute(
            select(ProjectCoefficient).where(ProjectCoefficient.project_id == project_id)
        )
        items = list(result.scalars())
    return [ProjectCoefficientOut(**item.__dict__) for item in items]


@router.put("/{project_id}/coefficients", response_model=list[ProjectCoefficientOut])
def upsert_coefficients(
    project_id: int,
    payload: list[ProjectCoefficientCreate],
    session: Session = Depends(get_db_session),
) -> list[ProjectCoefficientOut]:
    """Upsert project coefficients."""

    _get_project(session, project_id)
    results: list[ProjectCoefficientOut] = []
    for item in payload:
        existing = _get_project_coefficient(session, project_id, item.name)
        if existing:
            existing.multiplier = item.multiplier
            record = existing
        else:
            record = ProjectCoefficient(
                project_id=project_id,
                name=item.name,
                multiplier=item.multiplier,
            )
            session.add(record)
        session.flush()
        results.append(ProjectCoefficientOut(**record.__dict__))
    session.commit()
    return results


def _get_project(session: Session, project_id: int) -> Project:
    result = session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _get_module(session: Session, module_id: int) -> Module:
    result = session.execute(select(Module).where(Module.id == module_id))
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


def _get_project_module(
    session: Session,
    project_id: int,
    project_module_id: int,
) -> ProjectModule:
    result = session.execute(
        select(ProjectModule)
        .where(ProjectModule.id == project_module_id)
        .where(ProjectModule.project_id == project_id)
    )
    project_module = result.scalar_one_or_none()
    if not project_module:
        raise HTTPException(status_code=404, detail="Project module not found")
    return project_module


def _find_project_module(
    session: Session,
    project_id: int,
    module_id: int,
) -> ProjectModule | None:
    result = session.execute(
        select(ProjectModule)
        .where(ProjectModule.project_id == project_id)
        .where(ProjectModule.module_id == module_id)
    )
    return result.scalar_one_or_none()


def _get_assignment(
    session: Session,
    project_id: int,
    payload: AssignmentUpsert,
) -> Assignment | None:
    result = session.execute(
        select(Assignment)
        .where(Assignment.project_id == project_id)
        .where(Assignment.project_module_id == payload.project_module_id)
        .where(Assignment.role == payload.role)
    )
    return result.scalar_one_or_none()


def _apply_project_module_updates(
    project_module: ProjectModule,
    payload: ProjectModuleUpdate,
) -> None:
    if payload.custom_name is not None:
        project_module.custom_name = payload.custom_name
    if payload.override_frontend is not None:
        project_module.override_frontend = payload.override_frontend
    if payload.override_backend is not None:
        project_module.override_backend = payload.override_backend
    if payload.override_qa is not None:
        project_module.override_qa = payload.override_qa
    if payload.uncertainty_level is not None:
        project_module.uncertainty_level = payload.uncertainty_level
    if payload.uiux_level is not None:
        project_module.uiux_level = payload.uiux_level
    if payload.legacy_code is not None:
        project_module.legacy_code = payload.legacy_code


def _get_project_coefficient(
    session: Session,
    project_id: int,
    name: str,
) -> ProjectCoefficient | None:
    result = session.execute(
        select(ProjectCoefficient)
        .where(ProjectCoefficient.project_id == project_id)
        .where(ProjectCoefficient.name == name)
    )
    return result.scalar_one_or_none()


def _seed_project_coefficients(session: Session, project_id: int) -> None:
    defaults = [
        ProjectCoefficient(project_id=project_id, name="Неопределенность", multiplier=1.0),
        ProjectCoefficient(project_id=project_id, name="UI/UX", multiplier=1.0),
        ProjectCoefficient(project_id=project_id, name="Legacy code", multiplier=1.0),
    ]
    session.add_all(defaults)
    session.commit()
