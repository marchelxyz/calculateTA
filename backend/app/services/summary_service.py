from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.calculator import ModuleHours, apply_project_coefficients, merge_module_overrides, resolve_effective_levels
from app.core.scenarios import optimistic_value, pessimistic_value
from app.models import Assignment, Module, Project, ProjectInfrastructure, ProjectModule, Rate
from app.schemas import SummaryOut, SummaryScenario, SummaryTotals


ROLE_DEFAULT_LEVEL = {
    "frontend": "middle",
    "backend": "senior",
    "qa": "middle",
}


def build_project_summary(session: Session, project_id: int) -> SummaryOut:
    """Build a summary for project estimation."""

    project = _get_project(session, project_id)
    project_modules = _load_project_modules(session, project_id)
    assignments = _load_assignments(session, project_id)
    rates = _load_rates(session)
    infra_items = _load_project_infrastructure(session, project_id)

    totals = _calculate_totals(
        project=project,
        project_modules=project_modules,
        assignments=assignments,
        rates=rates,
        infra_items=infra_items,
    )
    scenarios = _calculate_scenarios(totals)

    return SummaryOut(totals=totals, scenarios=scenarios)


def _get_project(session: Session, project_id: int) -> Project:
    result = session.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one()
    return project


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
    result = session.execute(
        select(Assignment).where(Assignment.project_id == project_id)
    )
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


def _calculate_totals(
    project: Project,
    project_modules: list[ProjectModule],
    assignments: dict[tuple[int, str], str],
    rates: dict[tuple[str, str], float],
    infra_items: list[ProjectInfrastructure],
) -> SummaryTotals:
    totals = defaultdict(float)
    work_cost_total = 0.0

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
        legacy_code = project_module.legacy_code if project_module.legacy_code is not None else project.legacy_code

        adjusted = apply_project_coefficients(
            hours=merged,
            uncertainty_level=uncertainty_level,
            uiux_level=uiux_level,
            legacy_code=legacy_code,
        )

        totals["frontend"] += adjusted.frontend
        totals["backend"] += adjusted.backend
        totals["qa"] += adjusted.qa

        work_cost_total += _calculate_module_cost(
            project_module_id=project_module.id,
            adjusted=adjusted,
            assignments=assignments,
            rates=rates,
        )

    infra_cost = _calculate_infra_cost(infra_items)
    hours_total = totals["frontend"] + totals["backend"] + totals["qa"]
    cost_total = work_cost_total + infra_cost

    return SummaryTotals(
        hours_frontend=totals["frontend"],
        hours_backend=totals["backend"],
        hours_qa=totals["qa"],
        hours_total=hours_total,
        infra_cost=infra_cost,
        cost_total=cost_total,
    )


def _calculate_module_cost(
    project_module_id: int,
    adjusted: ModuleHours,
    assignments: dict[tuple[int, str], str],
    rates: dict[tuple[str, str], float],
) -> float:
    cost = 0.0
    role_hours = {
        "frontend": adjusted.frontend,
        "backend": adjusted.backend,
        "qa": adjusted.qa,
    }
    for role, hours in role_hours.items():
        level = assignments.get((project_module_id, role), ROLE_DEFAULT_LEVEL.get(role, "middle"))
        rate = rates.get((role, level), 0.0)
        cost += hours * rate
    return cost


def _calculate_scenarios(totals: SummaryTotals) -> list[SummaryScenario]:
    optimistic = SummaryScenario(
        label="Оптимистичный",
        total_hours=optimistic_value(totals.hours_total),
        total_cost=optimistic_value(totals.cost_total),
    )
    realistic = SummaryScenario(
        label="Реалистичный",
        total_hours=totals.hours_total,
        total_cost=totals.cost_total,
    )
    pessimistic = SummaryScenario(
        label="Пессимистичный",
        total_hours=pessimistic_value(totals.hours_total),
        total_cost=pessimistic_value(totals.cost_total),
    )
    return [optimistic, realistic, pessimistic]


def _calculate_infra_cost(infra_items: list[ProjectInfrastructure]) -> float:
    cost = 0.0
    for item in infra_items:
        unit_cost = item.infrastructure_item.unit_cost if item.infrastructure_item else 0.0
        cost += unit_cost * item.quantity
    return cost
