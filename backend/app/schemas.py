from __future__ import annotations

from pydantic import BaseModel, Field


class ModuleRoleHours(BaseModel):
    """Module role hours."""

    role: str
    hours: float = Field(ge=0)


class ModuleBase(BaseModel):
    """Module base schema."""

    code: str
    name: str
    description: str = ""
    hours_frontend: float
    hours_backend: float
    hours_qa: float
    role_hours: list[ModuleRoleHours] = []


class ModuleCreate(ModuleBase):
    """Module creation schema."""


class ModuleOut(ModuleBase):
    """Module response schema."""

    id: int


class ProjectNodeRoleHours(BaseModel):
    """Mindmap node role hours."""

    role: str
    hours: float = Field(ge=0)


class ProjectNodeBase(BaseModel):
    """Mindmap node base schema."""

    title: str
    description: str = ""
    module_id: int | None = None
    is_ai: bool = False
    hours_frontend: float = 0
    hours_backend: float = 0
    hours_qa: float = 0
    uncertainty_level: str | None = None
    uiux_level: str | None = None
    legacy_code: bool | None = None
    position_x: float = 0
    position_y: float = 0
    role_hours: list[ProjectNodeRoleHours] = []


class ProjectNodeCreate(ProjectNodeBase):
    """Mindmap node create payload."""


class ProjectNodeOut(ProjectNodeBase):
    """Mindmap node response."""

    id: int


class ProjectNodeConnectionBase(BaseModel):
    """Connection between mindmap nodes."""

    from_node_id: int
    to_node_id: int


class ProjectNodeConnectionOut(ProjectNodeConnectionBase):
    """Mindmap connection response."""

    id: int


class ProjectNoteBase(BaseModel):
    """Mindmap note payload."""

    content: str = ""
    position_x: float = 0
    position_y: float = 0


class ProjectNoteOut(ProjectNoteBase):
    """Mindmap note response."""

    id: int


class MindmapSnapshotNode(BaseModel):
    """Mindmap snapshot node."""

    key: str
    title: str
    description: str = ""
    module_id: int | None = None
    is_ai: bool = False
    hours_frontend: float = 0
    hours_backend: float = 0
    hours_qa: float = 0
    uncertainty_level: str | None = None
    uiux_level: str | None = None
    legacy_code: bool | None = None
    position_x: float = 0
    position_y: float = 0
    role_hours: list[ProjectNodeRoleHours] = []


class MindmapSnapshotConnection(BaseModel):
    """Mindmap snapshot connection."""

    from_key: str
    to_key: str


class MindmapSnapshot(BaseModel):
    """Mindmap snapshot payload."""

    nodes: list[MindmapSnapshotNode]
    connections: list[MindmapSnapshotConnection]
    notes: list[ProjectNoteBase]


class MindmapVersionCreate(BaseModel):
    """Mindmap version create payload."""

    title: str
    snapshot: MindmapSnapshot


class MindmapVersionOut(BaseModel):
    """Mindmap version response."""

    id: int
    title: str
    created_at: str


class MindmapVersionDetailOut(MindmapVersionOut):
    """Mindmap version with snapshot."""

    snapshot: MindmapSnapshot


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


class ProjectCoefficientBase(BaseModel):
    """Project coefficient base schema."""

    name: str
    multiplier: float = Field(ge=0)


class ProjectCoefficientCreate(ProjectCoefficientBase):
    """Project coefficient creation schema."""


class ProjectCoefficientOut(ProjectCoefficientBase):
    """Project coefficient response schema."""

    id: int
    project_id: int


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


class AiMindmapNode(BaseModel):
    """AI mindmap node."""

    key: str
    title: str
    details: str = ""
    module_code: str = ""
    hours_frontend: float = 0
    hours_backend: float = 0
    hours_qa: float = 0
    role_hours: list[ModuleRoleHours] = []


class AiMindmapConnection(BaseModel):
    """AI mindmap connection."""

    from_key: str
    to_key: str


class AiMindmapRequest(BaseModel):
    """AI mindmap request."""

    prompt: str


class AiMindmapResponse(BaseModel):
    """AI mindmap response."""

    nodes: list[AiMindmapNode]
    connections: list[AiMindmapConnection]
    rationale: str
