from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class ModuleHours:
    """Normalized hours for a module."""

    frontend: float
    backend: float
    qa: float

    @property
    def total(self) -> float:
        """Return total hours."""

        return self.frontend + self.backend + self.qa


def apply_project_coefficients(
    hours: ModuleHours,
    uncertainty_level: str,
    uiux_level: str,
    legacy_code: bool,
) -> ModuleHours:
    """Apply project-level coefficients to module hours."""

    uncertainty = settings.uncertainty_coefficients.get(uncertainty_level, 1.0)
    uiux = settings.uiux_coefficients.get(uiux_level, 1.0)
    legacy = settings.legacy_multiplier if legacy_code else 1.0

    adjusted_frontend = hours.frontend * uncertainty * uiux * legacy
    adjusted_backend = hours.backend * uncertainty * legacy
    adjusted_qa = hours.qa * uncertainty * legacy

    return ModuleHours(
        frontend=adjusted_frontend,
        backend=adjusted_backend,
        qa=adjusted_qa,
    )


def apply_extra_multiplier(hours: ModuleHours, multiplier: float) -> ModuleHours:
    """Apply additional multiplier to all role hours."""

    if multiplier == 1.0:
        return hours
    return ModuleHours(
        frontend=hours.frontend * multiplier,
        backend=hours.backend * multiplier,
        qa=hours.qa * multiplier,
    )


def merge_module_overrides(
    base_hours: ModuleHours,
    override_frontend: float | None,
    override_backend: float | None,
    override_qa: float | None,
) -> ModuleHours:
    """Return module hours after applying overrides."""

    return ModuleHours(
        frontend=override_frontend if override_frontend is not None else base_hours.frontend,
        backend=override_backend if override_backend is not None else base_hours.backend,
        qa=override_qa if override_qa is not None else base_hours.qa,
    )


def resolve_effective_levels(
    project_level: str,
    module_level: str | None,
) -> str:
    """Resolve per-module level override with fallback."""

    if module_level:
        return module_level
    return project_level
