from __future__ import annotations

from pydantic import BaseModel, Field


class ModuleBase(BaseModel):
    """Module base schema."""

    code: str
    name: str
    description: str = ""
    hours_frontend: float
    hours_backend: float
    hours_qa: float


class ModuleCreate(ModuleBase):
    """Module creation schema."""


class ModuleOut(ModuleBase):
    """Module response schema."""

    id: int


class InfrastructureItemBase(BaseModel):
    """Infrastructure item base schema."""

    code: str
    name: str
    description: str = ""
    unit_cost: float


class InfrastructureItemCreate(InfrastructureItemBase):
    """Infrastructure item creation schema."""


class InfrastructureItemOut(InfrastructureItemBase):
    """Infrastructure item response schema."""

    id: int


class ProjectCreate(BaseModel):
    """Project creation payload."""

    name: str
    description: str = ""


class ProjectSettings(BaseModel):
    """Project settings payload."""

    uncertainty_level: str
    uiux_level: str
    legacy_code: bool


class ProjectOut(BaseModel):
    """Project response."""

    id: int
    name: str
    description: str
    uncertainty_level: str
    uiux_level: str
    legacy_code: bool


class ProjectModuleCreate(BaseModel):
    """Add module to project payload."""

    module_id: int
    custom_name: str = ""


class ProjectModuleUpdate(BaseModel):
    """Update project module overrides."""

    custom_name: str | None = None
    override_frontend: float | None = None
    override_backend: float | None = None
    override_qa: float | None = None
    uncertainty_level: str | None = None
    uiux_level: str | None = None
    legacy_code: bool | None = None


class ProjectModuleOut(BaseModel):
    """Project module response."""

    id: int
    module_id: int
    custom_name: str
    override_frontend: float | None
    override_backend: float | None
    override_qa: float | None
    uncertainty_level: str | None
    uiux_level: str | None
    legacy_code: bool | None


class ProjectInfrastructureUpsert(BaseModel):
    """Upsert infrastructure item for a project."""

    infrastructure_item_id: int
    quantity: int = Field(ge=0)


class ProjectInfrastructureOut(BaseModel):
    """Project infrastructure response."""

    id: int
    infrastructure_item_id: int
    quantity: int


class RateUpsert(BaseModel):
    """Upsert hourly rate."""

    role: str
    level: str
    hourly_rate: float = Field(ge=0)


class RateOut(RateUpsert):
    """Rate response."""

    id: int


class AssignmentUpsert(BaseModel):
    """Upsert assignment."""

    project_module_id: int
    role: str
    level: str


class AssignmentOut(AssignmentUpsert):
    """Assignment response."""

    id: int


class SummaryScenario(BaseModel):
    """Scenario totals."""

    label: str
    total_hours: float
    total_cost: float


class SummaryTotals(BaseModel):
    """Summary totals."""

    hours_frontend: float
    hours_backend: float
    hours_qa: float
    hours_total: float
    infra_cost: float
    cost_total: float


class SummaryOut(BaseModel):
    """Project summary."""

    totals: SummaryTotals
    scenarios: list[SummaryScenario]


class AiParseRequest(BaseModel):
    """AI prompt input."""

    prompt: str


class AiModuleSuggestion(BaseModel):
    """AI module suggestion."""

    module_code: str
    confidence: float
    notes: str = ""


class AiWbsTask(BaseModel):
    """AI WBS task item."""

    title: str
    details: str
    module_code: str
    confidence: float


class AiParseResponse(BaseModel):
    """AI parsing response."""

    suggestions: list[AiModuleSuggestion]
    tasks: list[AiWbsTask]
    rationale: str
