export type Module = {
  id: number;
  code: string;
  name: string;
  description: string;
  hours_frontend: number;
  hours_backend: number;
  hours_qa: number;
};

export type Project = {
  id: number;
  name: string;
  description: string;
  uncertainty_level: string;
  uiux_level: string;
  legacy_code: boolean;
};

export type ProjectList = Project;

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

export type ProjectConnection = {
  id: number;
  project_id: number;
  from_project_module_id: number;
  to_project_module_id: number;
};

export type User = {
  id: number;
  username: string;
  role: string;
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
