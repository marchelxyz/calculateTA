import { defineStore } from "pinia";
import client from "../api/client";
import type {
  AiMindmapResponse,
  AiParseResponse,
  Module,
  Project,
  ProjectConnection,
  ProjectList,
  ProjectModule,
  Assignment,
  Rate,
  RateDraft,
  Summary,
  ProjectCoefficient,
  InfrastructureItem,
  ProjectInfrastructure,
  ProjectNode,
  ProjectNodeConnection,
  ProjectNote,
  MindmapSnapshot,
  MindmapVersion,
  MindmapVersionDetail,
  User,
} from "../types";

type State = {
  currentUser: User | null;
  project: Project | null;
  projects: ProjectList[];
  activeProjectId: number | null;
  modules: Module[];
  projectModules: ProjectModule[];
  connections: ProjectConnection[];
  assignments: Assignment[];
  rates: Rate[];
  summary: Summary | null;
  aiResult: AiParseResponse | null;
  coefficients: ProjectCoefficient[];
  infrastructureCatalog: InfrastructureItem[];
  projectInfrastructure: ProjectInfrastructure[];
  mindmapNodes: ProjectNode[];
  mindmapConnections: ProjectNodeConnection[];
  mindmapNotes: ProjectNote[];
  mindmapVersions: MindmapVersion[];
  users: User[];
  loading: boolean;
};

export const useProjectStore = defineStore("project", {
  state: (): State => ({
    currentUser: null,
    project: null,
    projects: [],
    activeProjectId: null,
    modules: [],
    projectModules: [],
    connections: [],
    assignments: [],
    rates: [],
    summary: null,
    aiResult: null,
    coefficients: [],
    infrastructureCatalog: [],
    projectInfrastructure: [],
    mindmapNodes: [],
    mindmapConnections: [],
    mindmapNotes: [],
    mindmapVersions: [],
    users: [],
    loading: false,
  }),
  actions: {
    async checkAuth() {
      const response = await client.get<User>("/auth/me");
      this.currentUser = response.data;
      return response.data;
    },
    async logout() {
      localStorage.removeItem("auth_username");
      localStorage.removeItem("auth_password");
      this.currentUser = null;
    },
    async bootstrap() {
      this.loading = true;
      try {
        await this.loadModules();
        await this.loadRates();
        await this.loadInfrastructureCatalog();
        await this.loadProjects();
        await this.ensureActiveProject();
      } finally {
        this.loading = false;
      }
    },
    async loadProjects() {
      const response = await client.get<ProjectList[]>("/projects");
      this.projects = response.data;
    },
    async ensureActiveProject() {
      if (this.projects.length === 0) {
        const created = await this.createProject("Новый проект");
        await this.setActiveProject(created.id);
        return;
      }
      const stored = _getStoredProjectId();
      const selected =
        this.projects.find((project) => project.id === stored) ?? this.projects[0];
      await this.setActiveProject(selected.id);
    },
    async setActiveProject(projectId: number) {
      this.activeProjectId = projectId;
      localStorage.setItem("active_project_id", String(projectId));
      await this.loadProject(projectId);
      await this.loadProjectModules();
      await this.loadAssignments();
      await this.loadConnections();
      await this.loadCoefficients();
      await this.loadProjectInfrastructure();
      await this.loadMindmapNodes();
      await this.loadMindmapConnections();
      await this.loadMindmapNotes();
      await this.loadMindmapVersions();
      await this.loadSummary();
    },
    async createProject(name: string) {
      const response = await client.post<Project>("/projects", { name });
      const project = response.data;
      this.projects = [...this.projects, project];
      return project;
    },
    async updateProject(projectId: number, payload: { name: string; description: string }) {
      const response = await client.put<Project>(`/projects/${projectId}`, payload);
      this.project = response.data;
      await this.loadProjects();
    },
    async loadProject(projectId: number) {
      const response = await client.get<Project>(`/projects/${projectId}`);
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
      role_hours: Array<{ role: string; hours: number }>;
    }) {
      const response = await client.post<Module>("/modules", payload);
      this.modules = [...this.modules, response.data];
    },
    async deleteModule(moduleId: number) {
      await client.delete(`/modules/${moduleId}`);
      this.modules = this.modules.filter((module) => module.id !== moduleId);
    },
    async updateModule(moduleId: number, payload: Partial<Module>) {
      const response = await client.patch<Module>(`/modules/${moduleId}`, payload);
      this.modules = this.modules.map((module) =>
        module.id === moduleId ? response.data : module
      );
      return response.data;
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
    async loadConnections() {
      if (!this.project) return;
      const response = await client.get<ProjectConnection[]>(
        `/projects/${this.project.id}/connections`
      );
      this.connections = response.data;
    },
    async updateConnections(payload: ProjectConnection[]) {
      if (!this.project) return;
      const data = payload.map((item) => ({
        from_project_module_id: item.from_project_module_id,
        to_project_module_id: item.to_project_module_id,
      }));
      const response = await client.put<ProjectConnection[]>(
        `/projects/${this.project.id}/connections`,
        data
      );
      this.connections = response.data;
    },
    async loadUsers() {
      const response = await client.get<User[]>("/users");
      this.users = response.data;
    },
    async createUser(payload: { username: string; password: string; role: string }) {
      const response = await client.post<User>("/users", payload);
      this.users = [...this.users, response.data];
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
    async generateMindmap(prompt: string) {
      if (!this.project) return;
      const response = await client.post<AiMindmapResponse>("/ai/mindmap", {
        prompt,
      });
      await this._replaceMindmapWithAi(response.data);
    },
    async loadMindmapNodes() {
      if (!this.project) return;
      const response = await client.get<ProjectNode[]>(
        `/projects/${this.project.id}/mindmap/nodes`
      );
      this.mindmapNodes = response.data;
    },
    async createMindmapNode(payload: Omit<ProjectNode, "id">) {
      if (!this.project) return null;
      const response = await client.post<ProjectNode>(
        `/projects/${this.project.id}/mindmap/nodes`,
        payload
      );
      this.mindmapNodes = [...this.mindmapNodes, response.data];
      return response.data;
    },
    async updateMindmapNode(nodeId: number, payload: Omit<ProjectNode, "id">) {
      if (!this.project) return;
      const response = await client.patch<ProjectNode>(
        `/projects/${this.project.id}/mindmap/nodes/${nodeId}`,
        payload
      );
      this.mindmapNodes = this.mindmapNodes.map((node) =>
        node.id === nodeId ? response.data : node
      );
    },
    async deleteMindmapNode(nodeId: number) {
      if (!this.project) return;
      await client.delete(`/projects/${this.project.id}/mindmap/nodes/${nodeId}`);
      this.mindmapNodes = this.mindmapNodes.filter((node) => node.id !== nodeId);
    },
    async loadMindmapConnections() {
      if (!this.project) return;
      const response = await client.get<ProjectNodeConnection[]>(
        `/projects/${this.project.id}/mindmap/connections`
      );
      this.mindmapConnections = response.data;
    },
    async updateMindmapConnections(payload: ProjectNodeConnection[]) {
      if (!this.project) return;
      const response = await client.put<ProjectNodeConnection[]>(
        `/projects/${this.project.id}/mindmap/connections`,
        payload
      );
      this.mindmapConnections = response.data;
    },
    async loadMindmapNotes() {
      if (!this.project) return;
      const response = await client.get<ProjectNote[]>(
        `/projects/${this.project.id}/mindmap/notes`
      );
      this.mindmapNotes = response.data;
    },
    async loadMindmapVersions() {
      if (!this.project) return;
      const response = await client.get<MindmapVersion[]>(
        `/projects/${this.project.id}/mindmap/versions`
      );
      this.mindmapVersions = response.data;
    },
    async saveMindmapVersion(title: string) {
      if (!this.project) return;
      const snapshot = this._buildMindmapSnapshot();
      const response = await client.post<MindmapVersion>(
        `/projects/${this.project.id}/mindmap/versions`,
        {
          title,
          snapshot,
        }
      );
      this.mindmapVersions = [response.data, ...this.mindmapVersions];
    },
    async applyMindmapVersion(versionId: number) {
      if (!this.project) return;
      await client.post(
        `/projects/${this.project.id}/mindmap/versions/${versionId}/apply`
      );
      await this.loadMindmapNodes();
      await this.loadMindmapConnections();
      await this.loadMindmapNotes();
      await this.loadSummary();
    },
    async loadMindmapVersionDetail(versionId: number) {
      if (!this.project) return null;
      const response = await client.get<MindmapVersionDetail>(
        `/projects/${this.project.id}/mindmap/versions/${versionId}`
      );
      return response.data;
    },
    async createMindmapNote(payload: Omit<ProjectNote, "id">) {
      if (!this.project) return null;
      const response = await client.post<ProjectNote>(
        `/projects/${this.project.id}/mindmap/notes`,
        payload
      );
      this.mindmapNotes = [...this.mindmapNotes, response.data];
      return response.data;
    },
    async updateMindmapNote(noteId: number, payload: Omit<ProjectNote, "id">) {
      if (!this.project) return;
      const response = await client.patch<ProjectNote>(
        `/projects/${this.project.id}/mindmap/notes/${noteId}`,
        payload
      );
      this.mindmapNotes = this.mindmapNotes.map((note) =>
        note.id === noteId ? response.data : note
      );
    },
    async deleteMindmapNote(noteId: number) {
      if (!this.project) return;
      await client.delete(`/projects/${this.project.id}/mindmap/notes/${noteId}`);
      this.mindmapNotes = this.mindmapNotes.filter((note) => note.id !== noteId);
    },
    async _replaceMindmapWithAi(data: AiMindmapResponse) {
      if (!this.project) return;
      const moduleMap = new Map(this.modules.map((module) => [module.code, module]));
      await this.updateMindmapConnections([]);
      for (const node of this.mindmapNodes) {
        await this.deleteMindmapNode(node.id);
      }
      for (const note of this.mindmapNotes) {
        await this.deleteMindmapNote(note.id);
      }
      const keyToId = new Map<string, number>();
      for (const node of data.nodes) {
        const module = moduleMap.get(node.module_code);
        const created = await this.createMindmapNode({
          title: node.title,
          description: node.details,
          module_id: module?.id ?? null,
          is_ai: true,
          hours_frontend: node.hours_frontend || module?.hours_frontend || 0,
          hours_backend: node.hours_backend || module?.hours_backend || 0,
          hours_qa: node.hours_qa || module?.hours_qa || 0,
          uncertainty_level: null,
          uiux_level: null,
          legacy_code: null,
          position_x: 40,
          position_y: 40,
          role_hours: node.role_hours ?? [],
        });
        if (created) {
          keyToId.set(node.key, created.id);
        }
      }
      const connections = data.connections
        .map((connection) => {
          const fromId = keyToId.get(connection.from_key);
          const toId = keyToId.get(connection.to_key);
          if (!fromId || !toId) return null;
          return { from_node_id: fromId, to_node_id: toId };
        })
        .filter((item): item is ProjectNodeConnection => Boolean(item));
      await this.updateMindmapConnections(connections);
      await this.loadMindmapNodes();
      await this.loadMindmapNotes();
      await this.loadSummary();
    },
    _buildMindmapSnapshot(): MindmapSnapshot {
      return {
        nodes: this.mindmapNodes.map((node) => ({
          key: String(node.id),
          title: node.title,
          description: node.description,
          module_id: node.module_id,
          is_ai: node.is_ai,
          hours_frontend: node.hours_frontend,
          hours_backend: node.hours_backend,
          hours_qa: node.hours_qa,
          uncertainty_level: node.uncertainty_level,
          uiux_level: node.uiux_level,
          legacy_code: node.legacy_code,
          position_x: node.position_x,
          position_y: node.position_y,
          role_hours: node.role_hours,
        })),
        connections: this.mindmapConnections.map((item) => ({
          from_key: String(item.from_node_id),
          to_key: String(item.to_node_id),
        })),
        notes: this.mindmapNotes.map((note) => ({
          content: note.content,
          position_x: note.position_x,
          position_y: note.position_y,
        })),
      };
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

function _getStoredProjectId(): number | null {
  const raw = localStorage.getItem("active_project_id");
  if (!raw) return null;
  const value = Number(raw);
  return Number.isNaN(value) ? null : value;
}

function _getFilenameFromHeaders(headers: Record<string, string>): string | null {
  const contentDisposition = headers["content-disposition"];
  if (!contentDisposition) return null;
  const match = contentDisposition.match(/filename=\"?([^\"]+)\"?/i);
  if (!match) return null;
  return match[1];
}
