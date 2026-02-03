export type Module = {
  id: number;
  code: string;
  name: string;
  description: string;
  hours_frontend: number;
  hours_backend: number;
  hours_qa: number;
  role_hours: Array<{ role: string; hours: number }>;
};

export type Project = {
  id: number;
  name: string;
  description: string;
  uncertainty_level: string;
  uiux_level: string;
  legacy_code: boolean;
};

export type ProjectModule = {
  id: number;
  module_id: number;
  custom_name: string;
  override_frontend: number | null;
  override_backend: number | null;
  override_qa: number | null;
  uncertainty_level: string | null;
  uiux_level: string | null;
  legacy_code: boolean | null;
};

export type ProjectNodeRoleHours = {
  role: string;
  hours: number;
};

export type ProjectNode = {
  id: number;
  title: string;
  description: string;
  module_id: number | null;
  is_ai: boolean;
  hours_frontend: number;
  hours_backend: number;
  hours_qa: number;
  uncertainty_level: string | null;
  uiux_level: string | null;
  legacy_code: boolean | null;
  position_x: number;
  position_y: number;
  role_hours: ProjectNodeRoleHours[];
};

export type ProjectNodeConnection = {
  from_node_id: number;
  to_node_id: number;
};

export type ProjectNote = {
  id: number;
  content: string;
  position_x: number;
  position_y: number;
};

export type MindmapSnapshotNode = {
  key: string;
  title: string;
  description: string;
  module_id: number | null;
  is_ai: boolean;
  hours_frontend: number;
  hours_backend: number;
  hours_qa: number;
  uncertainty_level: string | null;
  uiux_level: string | null;
  legacy_code: boolean | null;
  position_x: number;
  position_y: number;
  role_hours: ProjectNodeRoleHours[];
};

export type MindmapSnapshotConnection = {
  from_key: string;
  to_key: string;
};

export type MindmapSnapshot = {
  nodes: MindmapSnapshotNode[];
  connections: MindmapSnapshotConnection[];
  notes: Array<{ content: string; position_x: number; position_y: number }>;
};

export type MindmapVersion = {
  id: number;
  title: string;
  created_at: string;
};

export type MindmapVersionDetail = MindmapVersion & {
  snapshot: MindmapSnapshot;
};

export type Rate = {
  id: number;
  role: string;
  level: string;
  hourly_rate: number;
};

export type RateDraft = {
  id?: number;
  role: string;
  level: string;
  hourly_rate: number;
};

export type Assignment = {
  id: number;
  project_module_id: number;
  role: string;
  level: string;
};

export type SummaryTotals = {
  hours_frontend: number;
  hours_backend: number;
  hours_qa: number;
  hours_total: number;
  infra_cost: number;
  cost_total: number;
};

export type SummaryScenario = {
  label: string;
  total_hours: number;
  total_cost: number;
};

export type Summary = {
  totals: SummaryTotals;
  scenarios: SummaryScenario[];
};

export type ProjectCoefficient = {
  id: number;
  project_id: number;
  name: string;
  multiplier: number;
};

export type AiSuggestion = {
  module_code: string;
  confidence: number;
  notes: string;
};

export type AiWbsTask = {
  title: string;
  details: string;
  module_code: string;
  confidence: number;
};

export type AiParseResponse = {
  suggestions: AiSuggestion[];
  tasks: AiWbsTask[];
  rationale: string;
};

export type AiMindmapNode = {
  key: string;
  title: string;
  details: string;
  module_code: string;
  hours_frontend: number;
  hours_backend: number;
  hours_qa: number;
  role_hours: Array<{ role: string; hours: number }>;
};

export type AiMindmapConnection = {
  from_key: string;
  to_key: string;
};

export type AiMindmapResponse = {
  nodes: AiMindmapNode[];
  connections: AiMindmapConnection[];
  rationale: string;
};

export type InfrastructureItem = {
  id: number;
  code: string;
  name: string;
  description: string;
  unit_cost: number;
};

export type ProjectInfrastructure = {
  id: number;
  infrastructure_item_id: number;
  quantity: number;
};
