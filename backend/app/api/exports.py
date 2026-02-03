from __future__ import annotations

import csv
import io
from collections import defaultdict
from dataclasses import dataclass

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.calculator import (
    ModuleHours,
    apply_project_coefficients,
    merge_module_overrides,
    resolve_effective_levels,
)
from app.db import get_db_session
from app.models import Assignment, Project, ProjectInfrastructure, ProjectModule, Rate

router = APIRouter(prefix="/projects", tags=["exports"])


ROLE_DEFAULT_LEVEL = {
    "frontend": "middle",
    "backend": "senior",
    "qa": "middle",
}


@dataclass(frozen=True)
class WorkRow:
    """Work row for export."""

    module_name: str
    role: str
    level: str
    hours: float
    rate: float
    cost: float


@dataclass(frozen=True)
class InfraRow:
    """Infrastructure row for export."""

    name: str
    quantity: int
    unit_cost: float
    total_cost: float


@router.get("/{project_id}/export.csv")
def export_project_csv(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> Response:
    """Export project data to CSV."""

    data = _collect_export_data(session, project_id)
    csv_text = _build_csv(data)
    filename = f"project-{project_id}-export.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=csv_text, media_type="text/csv; charset=utf-8", headers=headers)


@router.get("/{project_id}/export.pdf")
def export_project_pdf(
    project_id: int,
    session: Session = Depends(get_db_session),
) -> StreamingResponse:
    """Export project data to PDF."""

    data = _collect_export_data(session, project_id)
    buffer = io.BytesIO()
    _build_pdf(data, buffer)
    buffer.seek(0)
    filename = f"project-{project_id}-export.pdf"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(buffer, media_type="application/pdf", headers=headers)


def _collect_export_data(session: Session, project_id: int) -> dict[str, list]:
    project = _get_project(session, project_id)
    project_modules = _load_project_modules(session, project_id)
    assignments = _load_assignments(session, project_id)
    rates = _load_rates(session)
    infra = _load_project_infrastructure(session, project_id)

    work_rows = _build_work_rows(project, project_modules, assignments, rates)
    infra_rows = _build_infra_rows(infra)
    return {
        "project": project,
        "work": work_rows,
        "infra": infra_rows,
    }


def _build_csv(data: dict[str, list]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow(["Работы"])
    writer.writerow(["Модуль", "Роль", "Уровень", "Часы", "Ставка", "Стоимость"])
    for row in data["work"]:
        writer.writerow(
            [
                row.module_name,
                row.role,
                row.level,
                _format_number(row.hours),
                _format_number(row.rate),
                _format_number(row.cost),
            ]
        )

    writer.writerow([])
    writer.writerow(["Инфраструктура"])
    writer.writerow(["Элемент", "Количество", "Стоимость/ед.", "Итого"])
    for row in data["infra"]:
        writer.writerow(
            [
                row.name,
                row.quantity,
                _format_number(row.unit_cost),
                _format_number(row.total_cost),
            ]
        )

    return output.getvalue()


def _build_pdf(data: dict[str, list], buffer: io.BytesIO) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=24, leftMargin=24, topMargin=24, bottomMargin=24)
    elements = []

    elements.append(Paragraph("Экспорт оценки проекта", styles["Title"]))
    elements.append(Spacer(1, 12))

    work_table = _build_work_table(data["work"])
    elements.append(Paragraph("Работы", styles["Heading2"]))
    elements.append(work_table)
    elements.append(Spacer(1, 16))

    infra_table = _build_infra_table(data["infra"])
    elements.append(Paragraph("Инфраструктура", styles["Heading2"]))
    elements.append(infra_table)

    doc.build(elements)


def _build_work_table(rows: list[WorkRow]) -> Table:
    table_data = [["Модуль", "Роль", "Уровень", "Часы", "Ставка", "Стоимость"]]
    for row in rows:
        table_data.append(
            [
                row.module_name,
                row.role,
                row.level,
                _format_number(row.hours),
                _format_number(row.rate),
                _format_number(row.cost),
            ]
        )
    table = Table(table_data, colWidths=[160, 60, 70, 55, 65, 70])
    _apply_table_style(table)
    return table


def _build_infra_table(rows: list[InfraRow]) -> Table:
    table_data = [["Элемент", "Количество", "Стоимость/ед.", "Итого"]]
    for row in rows:
        table_data.append(
            [
                row.name,
                str(row.quantity),
                _format_number(row.unit_cost),
                _format_number(row.total_cost),
            ]
        )
    table = Table(table_data, colWidths=[210, 80, 100, 80])
    _apply_table_style(table)
    return table


def _apply_table_style(table: Table) -> None:
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )


def _build_work_rows(
    project: Project,
    project_modules: list[ProjectModule],
    assignments: dict[tuple[int, str], str],
    rates: dict[tuple[str, str], float],
) -> list[WorkRow]:
    rows: list[WorkRow] = []
    for project_module in project_modules:
        base_hours = ModuleHours(
            frontend=project_module.module.hours_frontend,
            backend=project_module.module.hours_backend,
            qa=project_module.module.hours_qa,
        )
        merged = merge_module_overrides(
            base_hours=base_hours,
            override_frontend=project_module.override_frontend,
            override_backend=project_module.override_backend,
            override_qa=project_module.override_qa,
        )
        uncertainty_level = resolve_effective_levels(
            project.uncertainty_level,
            project_module.uncertainty_level,
        )
        uiux_level = resolve_effective_levels(
            project.uiux_level,
            project_module.uiux_level,
        )
        legacy_code = (
            project_module.legacy_code if project_module.legacy_code is not None else project.legacy_code
        )
        adjusted = apply_project_coefficients(
            hours=merged,
            uncertainty_level=uncertainty_level,
            uiux_level=uiux_level,
            legacy_code=legacy_code,
        )
        role_hours = {
            "frontend": adjusted.frontend,
            "backend": adjusted.backend,
            "qa": adjusted.qa,
        }
        for role, hours in role_hours.items():
            level = _resolve_level(assignments, project_module.id, role)
            rate = rates.get((role, level), 0.0)
            rows.append(
                WorkRow(
                    module_name=project_module.module.name,
                    role=role,
                    level=level,
                    hours=hours,
                    rate=rate,
                    cost=hours * rate,
                )
            )
    return rows


def _build_infra_rows(items: list[ProjectInfrastructure]) -> list[InfraRow]:
    rows: list[InfraRow] = []
    for item in items:
        unit_cost = item.infrastructure_item.unit_cost if item.infrastructure_item else 0.0
        rows.append(
            InfraRow(
                name=item.infrastructure_item.name if item.infrastructure_item else "Инфраструктура",
                quantity=item.quantity,
                unit_cost=unit_cost,
                total_cost=unit_cost * item.quantity,
            )
        )
    return rows


def _load_project_modules(session: Session, project_id: int) -> list[ProjectModule]:
    result = session.execute(
        select(ProjectModule)
        .where(ProjectModule.project_id == project_id)
        .join(ProjectModule.module)
    )
    return list(result.scalars())


def _load_project_infrastructure(
    session: Session,
    project_id: int,
) -> list[ProjectInfrastructure]:
    result = session.execute(
        select(ProjectInfrastructure)
        .where(ProjectInfrastructure.project_id == project_id)
        .join(ProjectInfrastructure.infrastructure_item)
    )
    return list(result.scalars())


def _load_assignments(session: Session, project_id: int) -> dict[tuple[int, str], str]:
    result = session.execute(select(Assignment).where(Assignment.project_id == project_id))
    assignments: dict[tuple[int, str], str] = {}
    for assignment in result.scalars():
        assignments[(assignment.project_module_id, assignment.role)] = assignment.level
    return assignments


def _load_rates(session: Session) -> dict[tuple[str, str], float]:
    result = session.execute(select(Rate))
    rates: dict[tuple[str, str], float] = {}
    for rate in result.scalars():
        rates[(rate.role, rate.level)] = rate.hourly_rate
    return rates


def _get_project(session: Session, project_id: int) -> Project:
    result = session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _resolve_level(
    assignments: dict[tuple[int, str], str],
    project_module_id: int,
    role: str,
) -> str:
    return assignments.get((project_module_id, role), ROLE_DEFAULT_LEVEL.get(role, "middle"))


def _format_number(value: float) -> str:
    return f"{value:.2f}"
