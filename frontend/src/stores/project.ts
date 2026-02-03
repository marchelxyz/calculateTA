import { defineStore } from "pinia";
import client from "../api/client";
import type {
  AiParseResponse,
  Module,
  Project,
  ProjectModule,
  Assignment,
  Rate,
  RateDraft,
  Summary,
  ProjectCoefficient,
  InfrastructureItem,
  ProjectInfrastructure,
} from "../types";

type State = {
  project: Project | null;
  modules: Module[];
  projectModules: ProjectModule[];
  assignments: Assignment[];
  rates: Rate[];
  summary: Summary | null;
  aiResult: AiParseResponse | null;
  coefficients: ProjectCoefficient[];
  infrastructureCatalog: InfrastructureItem[];
  projectInfrastructure: ProjectInfrastructure[];
  loading: boolean;
};

export const useProjectStore = defineStore("project", {
  state: (): State => ({
    project: null,
    modules: [],
    projectModules: [],
    assignments: [],
    rates: [],
    summary: null,
    aiResult: null,
    coefficients: [],
    infrastructureCatalog: [],
    projectInfrastructure: [],
    loading: false,
  }),
  actions: {
    async bootstrap() {
      this.loading = true;
      try {
        await this.loadModules();
        await this.loadRates();
        if (!this.project) {
          await this.createProject("Новый проект");
        }
        await this.loadProjectModules();
        await this.loadAssignments();
        await this.loadCoefficients();
        await this.loadInfrastructureCatalog();
        await this.loadProjectInfrastructure();
        await this.loadSummary();
      } finally {
        this.loading = false;
      }
    },
    async createProject(name: string) {
      const response = await client.post<Project>("/projects", { name });
      this.project = response.data;
    },
    async loadModules() {
      const response = await client.get<Module[]>("/modules");
      this.modules = response.data;
    },
    async createModule(payload: {
      code: string;
      name: string;
      description: string;
      hours_frontend: number;
      hours_backend: number;
      hours_qa: number;
    }) {
      const response = await client.post<Module>("/modules", payload);
      this.modules = [...this.modules, response.data];
    },
    async loadProjectModules() {
      if (!this.project) return;
      const response = await client.get<ProjectModule[]>(
        `/projects/${this.project.id}/modules`
      );
      this.projectModules = response.data;
    },
    async loadAssignments() {
      if (!this.project) return;
      const response = await client.get<Assignment[]>(
        `/projects/${this.project.id}/assignments`
      );
      this.assignments = response.data;
    },
    async addModule(moduleId: number) {
      if (!this.project) return;
      await client.post<ProjectModule>(`/projects/${this.project.id}/modules`, {
        module_id: moduleId,
      });
      await this.loadProjectModules();
      await this.loadSummary();
    },
    async updateProjectModule(projectModule: ProjectModule) {
      if (!this.project) return;
      await client.patch<ProjectModule>(
        `/projects/${this.project.id}/modules/${projectModule.id}`,
        projectModule
      );
      await this.loadProjectModules();
      await this.loadSummary();
    },
    async removeProjectModule(projectModuleId: number) {
      if (!this.project) return;
      await client.delete(
        `/projects/${this.project.id}/modules/${projectModuleId}`
      );
      await this.loadProjectModules();
      await this.loadSummary();
    },
    async updateSettings(payload: {
      uncertainty_level: string;
      uiux_level: string;
      legacy_code: boolean;
    }) {
      if (!this.project) return;
      const response = await client.put<Project>(
        `/projects/${this.project.id}/settings`,
        payload
      );
      this.project = response.data;
      await this.loadSummary();
    },
    async loadRates() {
      const response = await client.get<Rate[]>("/rates");
      this.rates = response.data;
    },
    async updateRates(rates: RateDraft[]) {
      const payload = rates.map((rate) => ({
        role: rate.role,
        level: rate.level,
        hourly_rate: rate.hourly_rate,
      }));
      const response = await client.put<Rate[]>("/rates", payload);
      this.rates = response.data;
      await this.loadSummary();
    },
    async assignRole(projectModuleId: number, role: string, level: string) {
      if (!this.project) return;
      await client.post(`/projects/${this.project.id}/assignments`, [
        {
          project_module_id: projectModuleId,
          role,
          level,
        },
      ]);
      await this.loadAssignments();
      await this.loadSummary();
    },
    async loadSummary() {
      if (!this.project) return;
      const response = await client.get<Summary>(
        `/projects/${this.project.id}/summary`
      );
      this.summary = response.data;
    },
    async loadCoefficients() {
      if (!this.project) return;
      const response = await client.get<ProjectCoefficient[]>(
        `/projects/${this.project.id}/coefficients`
      );
      this.coefficients = response.data;
    },
    async updateCoefficients(payload: ProjectCoefficient[]) {
      if (!this.project) return;
      const data = payload.map((item) => ({
        name: item.name,
        multiplier: item.multiplier,
      }));
      const response = await client.put<ProjectCoefficient[]>(
        `/projects/${this.project.id}/coefficients`,
        data
      );
      this.coefficients = response.data;
      await this.loadSummary();
    },
    async loadInfrastructureCatalog() {
      const response = await client.get<InfrastructureItem[]>("/infrastructure");
      this.infrastructureCatalog = response.data;
    },
    async createInfrastructureItem(payload: {
      code: string;
      name: string;
      description: string;
      unit_cost: number;
    }) {
      const response = await client.post<InfrastructureItem>("/infrastructure", payload);
      this.infrastructureCatalog = [...this.infrastructureCatalog, response.data];
    },
    async loadProjectInfrastructure() {
      if (!this.project) return;
      const response = await client.get<ProjectInfrastructure[]>(
        `/projects/${this.project.id}/infrastructure`
      );
      this.projectInfrastructure = response.data;
    },
    async updateProjectInfrastructure(payload: ProjectInfrastructure[]) {
      if (!this.project) return;
      const data = payload.map((item) => ({
        infrastructure_item_id: item.infrastructure_item_id,
        quantity: item.quantity,
      }));
      const response = await client.put<ProjectInfrastructure[]>(
        `/projects/${this.project.id}/infrastructure`,
        data
      );
      this.projectInfrastructure = response.data;
      await this.loadSummary();
    },
    async downloadExportCsv() {
      if (!this.project) return;
      await this.downloadFile(`/projects/${this.project.id}/export.csv`);
    },
    async downloadExportPdf() {
      if (!this.project) return;
      await this.downloadFile(`/projects/${this.project.id}/export.pdf`);
    },
    async parseAi(prompt: string) {
      const response = await client.post<AiParseResponse>("/ai/parse", {
        prompt,
      });
      this.aiResult = response.data;
      return response.data;
    },
    async downloadFile(url: string) {
      const response = await client.get<Blob>(url, { responseType: "blob" });
      const contentType = response.headers["content-type"] ?? "";
      const blob = new Blob([response.data], { type: contentType });
      const link = document.createElement("a");
      const objectUrl = URL.createObjectURL(blob);
      link.href = objectUrl;
      link.download = _getFilenameFromHeaders(response.headers) ?? "export";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
    },
  },
});

function _getFilenameFromHeaders(headers: Record<string, string>): string | null {
  const contentDisposition = headers["content-disposition"];
  if (!contentDisposition) return null;
  const match = contentDisposition.match(/filename=\"?([^\"]+)\"?/i);
  if (!match) return null;
  return match[1];
}
