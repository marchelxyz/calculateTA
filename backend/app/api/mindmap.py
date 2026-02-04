from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
import json

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models import (
    Project,
    ProjectMindmapVersion,
    ProjectNode,
    ProjectNodeConnection,
    ProjectNodeRoleHours as ProjectNodeRoleHoursModel,
    ProjectNote,
)
from app.schemas import (
    MindmapSnapshot,
    MindmapVersionCreate,
    MindmapVersionDetailOut,
    MindmapVersionOut,
    ProjectNodeConnectionBase,
    ProjectNodeCreate,
    ProjectNodeOut,
    ProjectNodeRoleHours as ProjectNodeRoleHoursPayload,
    ProjectNoteBase,
    ProjectNoteOut,
)

router = APIRouter(prefix="/projects", tags=["mindmap"])


@router.get("/{project_id}/mindmap/nodes", response_model=list[ProjectNodeOut])
def list_nodes(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> list[ProjectNodeOut]:
    """Return mindmap nodes for a project."""

    _ensure_project(session, project_id)
    result = session.execute(
        select(ProjectNode).where(ProjectNode.project_id == project_id)
    )
    return [_serialize_node(node) for node in result.scalars()]


@router.post("/{project_id}/mindmap/nodes", response_model=ProjectNodeOut)
def create_node(
    project_id: int,
    payload: ProjectNodeCreate,
    session: Session = Depends(get_db_session),
) -> ProjectNodeOut:
    """Create a new mindmap node."""

    _ensure_project(session, project_id)
    node = ProjectNode(
        project_id=project_id,
        module_id=payload.module_id,
        title=payload.title,
        description=payload.description,
        is_ai=payload.is_ai,
        hours_frontend=payload.hours_frontend,
        hours_backend=payload.hours_backend,
        hours_qa=payload.hours_qa,
        uncertainty_level=payload.uncertainty_level,
        uiux_level=payload.uiux_level,
        legacy_code=payload.legacy_code,
        position_x=payload.position_x,
        position_y=payload.position_y,
    )
    session.add(node)
    session.flush()
    _replace_node_role_hours(session, node.id, payload.role_hours)
    session.commit()
    session.refresh(node)
    return _serialize_node(node)


@router.patch("/{project_id}/mindmap/nodes/{node_id}", response_model=ProjectNodeOut)
def update_node(
    project_id: int,
    node_id: int,
    payload: ProjectNodeCreate,
    session: Session = Depends(get_db_session),
) -> ProjectNodeOut:
    """Update a mindmap node."""

    _ensure_project(session, project_id)
    node = session.execute(
        select(ProjectNode).where(
            ProjectNode.project_id == project_id,
            ProjectNode.id == node_id,
        )
    ).scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    node.module_id = payload.module_id
    node.title = payload.title
    node.description = payload.description
    node.is_ai = payload.is_ai
    node.hours_frontend = payload.hours_frontend
    node.hours_backend = payload.hours_backend
    node.hours_qa = payload.hours_qa
    node.uncertainty_level = payload.uncertainty_level
    node.uiux_level = payload.uiux_level
    node.legacy_code = payload.legacy_code
    node.position_x = payload.position_x
    node.position_y = payload.position_y
    _replace_node_role_hours(session, node.id, payload.role_hours)
    session.commit()
    session.refresh(node)
    return _serialize_node(node)


@router.delete("/{project_id}/mindmap/nodes/{node_id}")
def delete_node(
    project_id: int,
    node_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    """Delete a mindmap node."""

    _ensure_project(session, project_id)
    node = session.execute(
        select(ProjectNode).where(
            ProjectNode.project_id == project_id,
            ProjectNode.id == node_id,
        )
    ).scalar_one_or_none()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    session.execute(
        delete(ProjectNodeConnection).where(
            ProjectNodeConnection.project_id == project_id,
            (ProjectNodeConnection.from_node_id == node_id)
            | (ProjectNodeConnection.to_node_id == node_id),
        )
    )
    session.delete(node)
    session.commit()
    return {"status": "ok"}


@router.get("/{project_id}/mindmap/connections", response_model=list[ProjectNodeConnectionBase])
def list_connections(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> list[ProjectNodeConnectionBase]:
    """Return mindmap connections."""

    _ensure_project(session, project_id)
    result = session.execute(
        select(ProjectNodeConnection).where(ProjectNodeConnection.project_id == project_id)
    )
    return [
        ProjectNodeConnectionBase(
            from_node_id=item.from_node_id,
            to_node_id=item.to_node_id,
        )
        for item in result.scalars()
    ]


@router.put("/{project_id}/mindmap/connections", response_model=list[ProjectNodeConnectionBase])
def replace_connections(
    project_id: int,
    payload: list[ProjectNodeConnectionBase],
    session: Session = Depends(get_db_session),
) -> list[ProjectNodeConnectionBase]:
    """Replace all mindmap connections."""

    _ensure_project(session, project_id)
    session.execute(
        delete(ProjectNodeConnection).where(ProjectNodeConnection.project_id == project_id)
    )
    for item in payload:
        session.add(
            ProjectNodeConnection(
                project_id=project_id,
                from_node_id=item.from_node_id,
                to_node_id=item.to_node_id,
            )
        )
    session.commit()
    return payload


@router.get("/{project_id}/mindmap/notes", response_model=list[ProjectNoteOut])
def list_notes(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> list[ProjectNoteOut]:
    """Return mindmap notes."""

    _ensure_project(session, project_id)
    result = session.execute(
        select(ProjectNote).where(ProjectNote.project_id == project_id)
    )
    return [
        ProjectNoteOut(
            id=item.id,
            content=item.content,
            position_x=item.position_x,
            position_y=item.position_y,
        )
        for item in result.scalars()
    ]


@router.post("/{project_id}/mindmap/notes", response_model=ProjectNoteOut)
def create_note(
    project_id: int,
    payload: ProjectNoteBase,
    session: Session = Depends(get_db_session),
) -> ProjectNoteOut:
    """Create a mindmap note."""

    _ensure_project(session, project_id)
    note = ProjectNote(
        project_id=project_id,
        content=payload.content,
        position_x=payload.position_x,
        position_y=payload.position_y,
    )
    session.add(note)
    session.commit()
    session.refresh(note)
    return ProjectNoteOut(
        id=note.id,
        content=note.content,
        position_x=note.position_x,
        position_y=note.position_y,
    )


@router.patch("/{project_id}/mindmap/notes/{note_id}", response_model=ProjectNoteOut)
def update_note(
    project_id: int,
    note_id: int,
    payload: ProjectNoteBase,
    session: Session = Depends(get_db_session),
) -> ProjectNoteOut:
    """Update a mindmap note."""

    _ensure_project(session, project_id)
    note = session.execute(
        select(ProjectNote).where(
            ProjectNote.project_id == project_id,
            ProjectNote.id == note_id,
        )
    ).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.content = payload.content
    note.position_x = payload.position_x
    note.position_y = payload.position_y
    session.commit()
    session.refresh(note)
    return ProjectNoteOut(
        id=note.id,
        content=note.content,
        position_x=note.position_x,
        position_y=note.position_y,
    )


@router.delete("/{project_id}/mindmap/notes/{note_id}")
def delete_note(
    project_id: int,
    note_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    """Delete a mindmap note."""

    _ensure_project(session, project_id)
    note = session.execute(
        select(ProjectNote).where(
            ProjectNote.project_id == project_id,
            ProjectNote.id == note_id,
        )
    ).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    session.delete(note)
    session.commit()
    return {"status": "ok"}


@router.get("/{project_id}/mindmap/versions", response_model=list[MindmapVersionOut])
def list_versions(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> list[MindmapVersionOut]:
    """Return mindmap versions."""

    _ensure_project(session, project_id)
    result = session.execute(
        select(ProjectMindmapVersion)
        .where(ProjectMindmapVersion.project_id == project_id)
        .order_by(ProjectMindmapVersion.created_at.desc())
    )
    return [_serialize_version(item) for item in result.scalars()]


@router.post("/{project_id}/mindmap/versions", response_model=MindmapVersionOut)
def create_version(
    project_id: int,
    payload: MindmapVersionCreate,
    session: Session = Depends(get_db_session),
) -> MindmapVersionOut:
    """Save mindmap snapshot as version."""

    _ensure_project(session, project_id)
    version = ProjectMindmapVersion(
        project_id=project_id,
        title=payload.title,
        payload=_snapshot_to_json(payload.snapshot),
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return _serialize_version(version)


@router.get("/{project_id}/mindmap/versions/{version_id}", response_model=MindmapVersionDetailOut)
def get_version(
    project_id: int,
    version_id: int,
    session: Session = Depends(get_db_session),
) -> MindmapVersionDetailOut:
    """Return version with snapshot."""

    _ensure_project(session, project_id)
    version = session.execute(
        select(ProjectMindmapVersion).where(
            ProjectMindmapVersion.project_id == project_id,
            ProjectMindmapVersion.id == version_id,
        )
    ).scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    snapshot = _snapshot_from_json(version.payload)
    return MindmapVersionDetailOut(
        id=version.id,
        title=version.title,
        created_at=version.created_at.isoformat(),
        snapshot=snapshot,
    )


@router.post("/{project_id}/mindmap/versions/{version_id}/apply")
def apply_version(
    project_id: int,
    version_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    """Replace current mindmap with stored snapshot."""

    _ensure_project(session, project_id)
    version = session.execute(
        select(ProjectMindmapVersion).where(
            ProjectMindmapVersion.project_id == project_id,
            ProjectMindmapVersion.id == version_id,
        )
    ).scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    snapshot = _snapshot_from_json(version.payload)
    _replace_mindmap(session, project_id, snapshot)
    session.commit()
    return {"status": "ok"}


def _ensure_project(session: Session, project_id: int) -> Project:
    project = session.execute(select(Project).where(Project.id == project_id)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _replace_node_role_hours(
    session: Session,
    node_id: int,
    role_hours: list[ProjectNodeRoleHoursPayload],
) -> None:
    session.execute(
        delete(ProjectNodeRoleHoursModel).where(ProjectNodeRoleHoursModel.node_id == node_id)
    )
    for item in role_hours:
        if item.hours <= 0:
            continue
        session.add(
            ProjectNodeRoleHoursModel(
                node_id=node_id,
                role=item.role,
                hours=item.hours,
            )
        )


def _serialize_node(node: ProjectNode) -> ProjectNodeOut:
    return ProjectNodeOut(
        id=node.id,
        title=node.title,
        description=node.description,
        module_id=node.module_id,
        is_ai=node.is_ai,
        hours_frontend=node.hours_frontend,
        hours_backend=node.hours_backend,
        hours_qa=node.hours_qa,
        uncertainty_level=node.uncertainty_level,
        uiux_level=node.uiux_level,
        legacy_code=node.legacy_code,
        position_x=node.position_x,
        position_y=node.position_y,
        role_hours=[{"role": item.role, "hours": item.hours} for item in node.role_hours],
    )


def _serialize_version(version: ProjectMindmapVersion) -> MindmapVersionOut:
    """Convert version model to response payload."""
    return MindmapVersionOut(
        id=version.id,
        title=version.title,
        created_at=version.created_at.isoformat(),
    )


def _snapshot_to_json(snapshot: MindmapSnapshot) -> str:
    """Serialize snapshot to JSON."""
    return snapshot.model_dump_json()


def _snapshot_from_json(payload: str) -> MindmapSnapshot:
    """Deserialize snapshot from JSON."""
    data = json.loads(payload)
    return MindmapSnapshot(**data)


def _replace_mindmap(
    session: Session,
    project_id: int,
    snapshot: MindmapSnapshot,
) -> None:
    """Replace mindmap data with snapshot."""
    session.execute(
        delete(ProjectNodeConnection).where(ProjectNodeConnection.project_id == project_id)
    )
    session.execute(
        delete(ProjectNodeRoleHoursModel).where(ProjectNodeRoleHoursModel.node_id.in_(
            select(ProjectNode.id).where(ProjectNode.project_id == project_id)
        ))
    )
    session.execute(delete(ProjectNode).where(ProjectNode.project_id == project_id))
    session.execute(delete(ProjectNote).where(ProjectNote.project_id == project_id))

    key_map: dict[str, int] = {}
    for node in snapshot.nodes:
        created = ProjectNode(
            project_id=project_id,
            module_id=node.module_id,
            title=node.title,
            description=node.description,
            is_ai=node.is_ai,
            hours_frontend=node.hours_frontend,
            hours_backend=node.hours_backend,
            hours_qa=node.hours_qa,
            uncertainty_level=node.uncertainty_level,
            uiux_level=node.uiux_level,
            legacy_code=node.legacy_code,
            position_x=node.position_x,
            position_y=node.position_y,
        )
        session.add(created)
        session.flush()
        key_map[node.key] = created.id
        for item in node.role_hours:
            if item.hours <= 0:
                continue
            session.add(
                ProjectNodeRoleHoursModel(
                    node_id=created.id,
                    role=item.role,
                    hours=item.hours,
                )
            )

    for connection in snapshot.connections:
        from_id = key_map.get(connection.from_key)
        to_id = key_map.get(connection.to_key)
        if not from_id or not to_id:
            continue
        session.add(
            ProjectNodeConnection(
                project_id=project_id,
                from_node_id=from_id,
                to_node_id=to_id,
            )
        )

    for note in snapshot.notes:
        session.add(
            ProjectNote(
                project_id=project_id,
                content=note.content,
                position_x=note.position_x,
                position_y=note.position_y,
            )
        )
