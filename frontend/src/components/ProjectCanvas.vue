<template>
  <section class="panel">
    <div class="panel-header">
      <div>
        <h2>Холст проекта</h2>
        <p v-if="linkMode.active" class="hint">
          Выберите целевой блок для связи с
          <strong>{{ activeNodeName(linkMode.fromId ?? 0) }}</strong>
          <button class="link-cancel" @click="cancelLinkMode">Отмена</button>
        </p>
      </div>
      <div class="actions">
        <div v-if="mindmapMode" class="mindmap-actions">
          <input
            v-model="mindmapPrompt"
            class="mindmap-input"
            placeholder="Опишите продукт для AI-схемы"
          />
          <button class="ghost" @click="buildAiMindmap">AI-схема</button>
          <button class="ghost" @click="addMindmapNode">Добавить узел</button>
          <button class="ghost" @click="addMindmapNote">Комментарий</button>
          <button
            class="ghost"
            title="Автоматически раскладывает узлы по уровням"
            @click="autoLayoutMindmap"
          >
            Авто-раскладка (XMind)
          </button>
          <input
            v-model="versionTitle"
            class="mindmap-input"
            placeholder="Название версии"
          />
          <button class="ghost" @click="saveMindmapVersion">Сохранить версию</button>
          <select v-model="selectedVersionId" class="mindmap-select">
            <option value="">История схем</option>
            <option v-for="version in store.mindmapVersions" :key="version.id" :value="String(version.id)">
              {{ formatVersion(version) }}
            </option>
          </select>
          <button class="ghost" :disabled="!selectedVersionId" @click="applyMindmapVersion">
            Применить версию
          </button>
          <button class="ghost" @click="exportMindmapPng">PNG</button>
          <button class="ghost" @click="exportMindmapPdf">PDF</button>
          <button class="ghost" @click="exportMindmapBundle">PNG + PDF</button>
          <input
            v-model="mindmapSearch"
            class="mindmap-input"
            placeholder="Поиск модулей/узлов"
          />
          <select v-model="compareVersionId" class="mindmap-select">
            <option value="">Сравнить с версией</option>
            <option v-for="version in store.mindmapVersions" :key="version.id" :value="String(version.id)">
              {{ formatVersion(version) }}
            </option>
          </select>
          <button class="ghost" :disabled="!compareVersionId" @click="compareWithVersion">
            Сравнить
          </button>
          <button class="ghost" :disabled="!compareActive" @click="clearComparison">
            Сбросить сравнение
          </button>
        </div>
        <div class="zoom-controls">
          <button class="ghost" @click="zoomOut">-</button>
          <span>{{ Math.round(zoom * 100) }}%</span>
          <button class="ghost" @click="zoomIn">+</button>
          <button class="ghost" @click="resetZoom">Сброс</button>
        </div>
        <button class="ghost" @click="toggleMindmap">
          {{ mindmapMode ? "Свободная раскладка" : "Режим XMind" }}
        </button>
        <button class="ghost" @click="clearConnections" :disabled="connections.length === 0">
          Очистить связи
        </button>
      </div>
    </div>
    <div
      class="canvas-surface"
      ref="canvasRef"
      @click="hideContextMenu"
      @dragover.prevent="handleCanvasDragOver"
      @drop.prevent="handleCanvasDrop"
    >
      <div
        class="canvas-zoom"
        :style="zoomStyle"
        @dragover.prevent="handleCanvasDragOver"
        @drop.prevent="handleCanvasDrop"
      >
        <svg v-if="lines.length" class="canvas-lines">
          <path
            v-for="(line, index) in lines"
            :key="index"
            :d="linePath(line)"
          />
        </svg>
        <template v-if="mindmapMode">
          <div class="mindmap-nodes">
            <div class="legend">
              <div class="legend-title">Модули</div>
              <div class="legend-items">
                <span
                  v-for="module in filteredLegendModules"
                  :key="module.id"
                  class="legend-item"
                  :style="moduleBadgeStyle(module.id)"
                  draggable="true"
                  @dragstart="startLegendDrag(module.id, $event)"
                  @dragend="finishLegendDrag"
                >
                  {{ module.name }}
                </span>
              </div>
              <div v-if="compareActive" class="legend-compare">
                <span class="legend-chip added">Добавлено</span>
                <span class="legend-chip changed">Изменено</span>
                <span class="legend-chip removed">Удалено: {{ compareSummary.removed }}</span>
              </div>
            </div>
            <div
              v-for="node in filteredMindmapNodes"
              :key="node.id"
              class="module-card absolute"
              :ref="(el) => setNodeRef(el, node.id)"
              :style="nodeCardStyle(node)"
              :class="compareClass(node)"
              @contextmenu="openContextMenu($event, node.id)"
              @click.stop="handleNodeClick(node.id)"
            >
              <header
                class="module-header drag-handle"
                @mousedown.stop.prevent="startNodeDrag($event, node.id)"
              >
                <div>
                  <strong>{{ node.title }}</strong>
                  <small
                    v-if="node.module_id"
                    class="module-badge"
                    :style="moduleBadgeStyle(node.module_id)"
                  >
                    {{ moduleName(node.module_id) }}
                  </small>
                </div>
                <span v-if="linkMode.fromId === node.id" class="link-badge">
                  Источник связи
                </span>
                <button class="ghost danger" @click="removeMindmapNode(node.id)">
                  Удалить
                </button>
              </header>
              <div class="module-body">
                <div class="grid">
                  <label class="wide">
                    Название
                    <input
                      :value="node.title"
                      @input="updateNodeField(node, 'title', $event)"
                    />
                  </label>
                  <label class="wide">
                    Описание
                    <input
                      :value="node.description"
                      @input="updateNodeField(node, 'description', $event)"
                    />
                  </label>
                  <label class="wide">
                    Модуль
                    <select
                      :value="node.module_id ?? ''"
                      @change="updateNodeModule(node, $event)"
                    >
                      <option value="">Без привязки</option>
                      <option v-for="module in store.modules" :key="module.id" :value="module.id">
                        {{ module.name }}
                      </option>
                    </select>
                  </label>
                </div>
                <div class="grid">
                  <label>
                    FE часы
                    <input
                      type="number"
                      :value="node.hours_frontend"
                      @change="updateNodeField(node, 'hours_frontend', $event)"
                    />
                  </label>
                  <label>
                    BE часы
                    <input
                      type="number"
                      :value="node.hours_backend"
                      @change="updateNodeField(node, 'hours_backend', $event)"
                    />
                  </label>
                  <label>
                    QA часы
                    <input
                      type="number"
                      :value="node.hours_qa"
                      @change="updateNodeField(node, 'hours_qa', $event)"
                    />
                  </label>
                </div>
                <div class="grid">
                  <label v-for="role in extraRoles" :key="role">
                    {{ role }} часы
                    <input
                      type="number"
                      :value="roleHoursValue(node, role)"
                      @change="updateNodeRoleHours(node, role, $event)"
                    />
                  </label>
                </div>
              </div>
            </div>
            <div
              v-for="note in store.mindmapNotes"
              :key="note.id"
              class="note"
              :style="noteStyle(note)"
              @mousedown.stop.prevent="startNoteDrag($event, note.id)"
            >
              <textarea
                :value="note.content"
                @input="updateNoteContent(note, $event)"
                @mousedown.stop
              ></textarea>
              <button class="note-remove" @click="removeMindmapNote(note.id)">×</button>
            </div>
            <div v-if="store.mindmapNodes.length === 0" class="empty">
              Сгенерируйте схему или добавьте узел вручную
            </div>
            <div v-else-if="filteredMindmapNodes.length === 0" class="empty">
              Ничего не найдено по поиску
            </div>
          </div>
        </template>
        <Draggable
          v-else
          class="canvas-nodes"
          :list="store.projectModules"
          :group="{ name: 'modules', pull: false, put: true }"
          item-key="id"
          :sort="true"
          :animation="160"
          @add="handleAdd"
          @end="handleDragEnd"
        >
          <template #item="{ element }">
            <div
              class="module-card"
              :ref="(el) => setNodeRef(el, element.id)"
              @contextmenu="openContextMenu($event, element.id)"
              @click.stop="handleNodeClick(element.id)"
            >
              <header class="module-header">
                <div>
                  <strong>{{ moduleName(element.module_id) }}</strong>
                  <small v-if="element.custom_name">{{ element.custom_name }}</small>
                </div>
                <span v-if="linkMode.fromId === element.id" class="link-badge">
                  Источник связи
                </span>
                <button class="ghost danger" @click="store.removeProjectModule(element.id)">
                  Удалить
                </button>
              </header>
              <div class="module-body">
                <div class="grid">
                  <label>
                    FE часы
                    <input
                      type="number"
                      :value="element.override_frontend ?? baseHours(element.module_id).hours_frontend"
                      @change="updateHours(element, 'override_frontend', $event)"
                    />
                  </label>
                  <label>
                    BE часы
                    <input
                      type="number"
                      :value="element.override_backend ?? baseHours(element.module_id).hours_backend"
                      @change="updateHours(element, 'override_backend', $event)"
                    />
                  </label>
                  <label>
                    QA часы
                    <input
                      type="number"
                      :value="element.override_qa ?? baseHours(element.module_id).hours_qa"
                      @change="updateHours(element, 'override_qa', $event)"
                    />
                  </label>
                </div>
                <div class="grid">
                  <label>
                    Неопределенность
                    <select
                      :value="element.uncertainty_level ?? store.project?.uncertainty_level"
                      @change="updateSelect(element, 'uncertainty_level', $event)"
                    >
                      <option value="known">Делали 100 раз</option>
                      <option value="new_tech">Новая технология</option>
                    </select>
                  </label>
                  <label>
                    UI/UX
                    <select
                      :value="element.uiux_level ?? store.project?.uiux_level"
                      @change="updateSelect(element, 'uiux_level', $event)"
                    >
                      <option value="mvp">MVP / Bootstrap</option>
                      <option value="award">Award Winning</option>
                    </select>
                  </label>
                  <label class="checkbox">
                    <input
                      type="checkbox"
                      :checked="element.legacy_code ?? store.project?.legacy_code"
                      @change="updateCheckbox(element, 'legacy_code', $event)"
                    />
                    Legacy code
                  </label>
                </div>
                <div class="grid">
                  <label>
                    FE роль
                    <select
                      :value="assignmentLevel(element.id, 'frontend')"
                      @change="assignRole(element.id, 'frontend', $event)"
                    >
                      <option value="junior">Junior</option>
                      <option value="middle">Middle</option>
                      <option value="senior">Senior</option>
                    </select>
                  </label>
                  <label>
                    BE роль
                    <select
                      :value="assignmentLevel(element.id, 'backend')"
                      @change="assignRole(element.id, 'backend', $event)"
                    >
                      <option value="junior">Junior</option>
                      <option value="middle">Middle</option>
                      <option value="senior">Senior</option>
                    </select>
                  </label>
                  <label>
                    QA роль
                    <select
                      :value="assignmentLevel(element.id, 'qa')"
                      @change="assignRole(element.id, 'qa', $event)"
                    >
                      <option value="junior">Junior</option>
                      <option value="middle">Middle</option>
                      <option value="senior">Senior</option>
                    </select>
                  </label>
                </div>
              </div>
            </div>
          </template>
          <template #footer>
            <div v-if="store.projectModules.length === 0" class="empty">
              Перетащите модули сюда
            </div>
          </template>
        </Draggable>
      </div>
      <div
        v-if="contextMenu.visible"
        class="context-menu"
        :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }"
        @click.stop
      >
        <button class="ghost" @click="startLinkMode">Связать с...</button>
        <button class="ghost" @click="removeConnections">Удалить связи</button>
        <button v-if="!mindmapMode" class="ghost" @click="resetModule">
          Сбросить настройки
        </button>
        <button class="danger" @click="removeActiveNode">
          {{ mindmapMode ? "Удалить узел" : "Удалить модуль" }}
        </button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { toPng } from "html-to-image";
import { jsPDF } from "jspdf";
import { VueDraggableNext as Draggable } from "vue-draggable-next";
import { useProjectStore } from "../stores/project";
import type { ProjectConnection, ProjectModule, ProjectNode, ProjectNote } from "../types";

const store = useProjectStore();
const canvasRef = ref<HTMLElement | null>(null);
const lines = ref<{ x1: number; y1: number; x2: number; y2: number }[]>([]);
const nodeRefs = ref<Record<number, HTMLElement>>({});
const moduleConnections = ref<{ fromId: number; toId: number }[]>([]);
const mindmapConnections = ref<{ fromId: number; toId: number }[]>([]);
const linkMode = ref<{ active: boolean; fromId: number | null }>({
  active: false,
  fromId: null,
});
const mindmapMode = ref(false);
const mindmapPositions = ref<Record<number, { x: number; y: number }>>({});
const zoom = ref(1);
const mindmapPrompt = ref("");
const autoLayoutEnabled = ref(true);
const versionTitle = ref("");
const selectedVersionId = ref("");
const compareVersionId = ref("");
const mindmapSearch = ref("");
const compareActive = ref(false);
const compareDiff = ref<{ added: Set<number>; changed: Set<number>; removed: number }>({
  added: new Set(),
  changed: new Set(),
  removed: 0,
});
const draggingLegendModuleId = ref<number | null>(null);
const lastLegendDropPoint = ref<{ x: number; y: number } | null>(null);
const dropHandled = ref(false);
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  moduleId: null as number | null,
});
const draggingNode = ref<{ id: number; offsetX: number; offsetY: number } | null>(null);
const draggingNote = ref<{ id: number; offsetX: number; offsetY: number } | null>(null);
const nodeSaveTimers = new Map<number, number>();
const noteSaveTimers = new Map<number, number>();

const moduleMap = computed(() => {
  const map = new Map<number, { name: string; hours_frontend: number; hours_backend: number; hours_qa: number }>();
  store.modules.forEach((module) => {
    map.set(module.id, {
      name: module.name,
      hours_frontend: module.hours_frontend,
      hours_backend: module.hours_backend,
      hours_qa: module.hours_qa,
    });
  });
  return map;
});

const connections = computed(() => {
  return mindmapMode.value ? mindmapConnections.value : moduleConnections.value;
});

const extraRoles = computed(() => {
  const base = new Set(["фронтенд", "бекенд", "тестировщик", "qa", "backend", "frontend"]);
  const roles = new Set(store.rates.map((rate) => rate.role).filter((role) => role));
  return Array.from(roles).filter((role) => !base.has(role.toLowerCase()));
});

const modulePalette = [
  "#38bdf8",
  "#f472b6",
  "#a78bfa",
  "#34d399",
  "#fb923c",
  "#60a5fa",
  "#facc15",
  "#f87171",
  "#4ade80",
  "#22d3ee",
];

function moduleName(moduleId: number) {
  return moduleMap.value.get(moduleId)?.name ?? "Модуль";
}

function activeNodeName(nodeId: number) {
  if (mindmapMode.value) {
    const node = store.mindmapNodes.find((item) => item.id === nodeId);
    return node?.title ?? "Узел";
  }
  const moduleId = store.projectModules.find((item) => item.id === nodeId)?.module_id ?? 0;
  return moduleName(moduleId);
}

function roleHoursValue(node: ProjectNode, role: string) {
  const item = node.role_hours.find((entry) => entry.role === role);
  return item?.hours ?? 0;
}

function moduleColor(moduleId: number) {
  const index = Math.abs(moduleId) % modulePalette.length;
  return modulePalette[index];
}

function moduleBadgeStyle(moduleId: number) {
  const color = moduleColor(moduleId);
  return {
    backgroundColor: `${color}22`,
    color,
    borderColor: `${color}55`,
  };
}

function nodeCardStyle(node: ProjectNode) {
  const base = nodeStyle(node.id, node.position_x, node.position_y);
  if (!node.module_id) {
    return base;
  }
  const color = moduleColor(node.module_id);
  return {
    ...base,
    borderColor: color,
    boxShadow: `0 10px 20px ${color}22`,
    background: `linear-gradient(135deg, ${color}14 0%, var(--card-bg) 50%)`,
  };
}

function compareClass(node: ProjectNode) {
  if (!compareActive.value) return "";
  if (compareDiff.value.added.has(node.id)) return "node-added";
  if (compareDiff.value.changed.has(node.id)) return "node-changed";
  return "";
}

const compareSummary = computed(() => ({
  removed: compareDiff.value.removed,
}));

const filteredMindmapNodes = computed(() => {
  const query = mindmapSearch.value.trim().toLowerCase();
  if (!query) return store.mindmapNodes;
  return store.mindmapNodes.filter((node) => {
    const moduleNameValue = node.module_id ? moduleName(node.module_id) : "";
    return [node.title, node.description, moduleNameValue]
      .join(" ")
      .toLowerCase()
      .includes(query);
  });
});

const filteredLegendModules = computed(() => {
  const query = mindmapSearch.value.trim().toLowerCase();
  if (!query) return store.modules;
  return store.modules.filter((module) =>
    [module.name, module.code, module.description]
      .join(" ")
      .toLowerCase()
      .includes(query)
  );
});

function baseHours(moduleId: number) {
  return (
    moduleMap.value.get(moduleId) ?? {
      hours_frontend: 0,
      hours_backend: 0,
      hours_qa: 0,
    }
  );
}

function handleAdd(event: { clone?: { id?: number }; item?: HTMLElement }) {
  const moduleId = event.clone?.id;
  if (moduleId) {
    store.addModule(moduleId);
  }
  if (event.item) {
    event.item.remove();
  }
  scheduleLineUpdate();
}

async function buildAiMindmap() {
  if (!mindmapPrompt.value.trim()) return;
  await store.generateMindmap(mindmapPrompt.value.trim());
  mindmapPrompt.value = "";
  autoLayoutEnabled.value = true;
  nextTick(() => {
    buildMindmapLayout();
    updateLines();
  });
}

async function addMindmapNode() {
  if (!canvasRef.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  const scale = zoom.value || 1;
  const centerX = (canvasRef.value.scrollLeft + rect.width / 2) / scale;
  const centerY = (canvasRef.value.scrollTop + rect.height / 2) / scale;
  const created = await store.createMindmapNode({
    title: "Новый узел",
    description: "",
    module_id: null,
    is_ai: false,
    hours_frontend: 0,
    hours_backend: 0,
    hours_qa: 0,
    uncertainty_level: null,
    uiux_level: null,
    legacy_code: null,
    position_x: centerX - 120,
    position_y: centerY - 80,
    role_hours: [],
  });
  if (created) {
    scheduleLineUpdate();
  }
}

async function addMindmapNote() {
  if (!canvasRef.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  const scale = zoom.value || 1;
  const centerX = (canvasRef.value.scrollLeft + rect.width / 2) / scale;
  const centerY = (canvasRef.value.scrollTop + rect.height / 2) / scale;
  await store.createMindmapNote({
    content: "Комментарий",
    position_x: centerX - 80,
    position_y: centerY - 40,
  });
}

function startLegendDrag(moduleId: number, event: DragEvent) {
  if (!event.dataTransfer) return;
  event.dataTransfer.setData("text/plain", `module:${moduleId}`);
  event.dataTransfer.effectAllowed = "copy";
  draggingLegendModuleId.value = moduleId;
  lastLegendDropPoint.value = null;
  dropHandled.value = false;
}

async function handleCanvasDragOver(event: DragEvent) {
  if (!mindmapMode.value) return;
  event.preventDefault();
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = "copy";
  }
  lastLegendDropPoint.value = toCanvasPoint(event);
}

async function handleCanvasDrop(event: DragEvent) {
  if (!mindmapMode.value) return;
  event.preventDefault();
  const raw = event.dataTransfer?.getData("text/plain") ?? "";
  const moduleId =
    raw.startsWith("module:") ? Number(raw.replace("module:", "")) : draggingLegendModuleId.value;
  if (!moduleId) return;
  const module = store.modules.find((item) => item.id === moduleId);
  if (!module) return;
  const point = toCanvasPoint(event);
  autoLayoutEnabled.value = false;
  await createNodeFromModule(module, point.x, point.y);
  dropHandled.value = true;
  draggingLegendModuleId.value = null;
}

async function finishLegendDrag() {
  if (!mindmapMode.value) return;
  if (dropHandled.value) {
    dropHandled.value = false;
    return;
  }
  if (!draggingLegendModuleId.value || !lastLegendDropPoint.value) return;
  const module = store.modules.find((item) => item.id === draggingLegendModuleId.value);
  if (!module) return;
  autoLayoutEnabled.value = false;
  await createNodeFromModule(
    module,
    lastLegendDropPoint.value.x,
    lastLegendDropPoint.value.y
  );
  draggingLegendModuleId.value = null;
}

function toCanvasPoint(event: { clientX: number; clientY: number }) {
  if (!canvasRef.value) return { x: 0, y: 0 };
  const rect = canvasRef.value.getBoundingClientRect();
  const scale = zoom.value || 1;
  const x = (event.clientX - rect.left + canvasRef.value.scrollLeft) / scale;
  const y = (event.clientY - rect.top + canvasRef.value.scrollTop) / scale;
  return { x, y };
}

async function createNodeFromModule(
  module: {
    id: number;
    name: string;
    description: string;
    hours_frontend: number;
    hours_backend: number;
    hours_qa: number;
    role_hours?: Array<{ role: string; hours: number }>;
  },
  x: number,
  y: number
) {
  return store.createMindmapNode({
    title: module.name,
    description: module.description,
    module_id: module.id,
    is_ai: false,
    hours_frontend: module.hours_frontend,
    hours_backend: module.hours_backend,
    hours_qa: module.hours_qa,
    uncertainty_level: null,
    uiux_level: null,
    legacy_code: null,
    position_x: x - 120,
    position_y: y - 80,
    role_hours: module.role_hours ?? [],
  });
}

function autoLayoutMindmap() {
  autoLayoutEnabled.value = true;
  buildMindmapLayout();
  applyLayoutToNodes();
  updateLines();
}

async function saveMindmapVersion() {
  const title = versionTitle.value.trim();
  if (!title) return;
  await store.saveMindmapVersion(title);
  versionTitle.value = "";
}

async function applyMindmapVersion() {
  if (!selectedVersionId.value) return;
  await store.applyMindmapVersion(Number(selectedVersionId.value));
  autoLayoutEnabled.value = false;
  selectedVersionId.value = "";
  scheduleLineUpdate();
}

function formatVersion(version: { title: string; created_at: string }) {
  const date = new Date(version.created_at);
  return `${version.title} · ${date.toLocaleString("ru-RU")}`;
}

async function exportMindmapPng() {
  if (!canvasRef.value) return;
  const prevCompare = compareActive.value;
  compareActive.value = false;
  const prevZoom = zoom.value;
  zoom.value = 1;
  await nextTick();
  const node = canvasRef.value;
  const width = node.scrollWidth;
  const height = node.scrollHeight;
  const dataUrl = await toPng(node, {
    width,
    height,
    backgroundColor: getComputedStyle(node).backgroundColor,
    pixelRatio: 2,
  });
  downloadDataUrl(dataUrl, "mindmap.png");
  zoom.value = prevZoom;
  compareActive.value = prevCompare;
  scheduleLineUpdate();
}

async function exportMindmapPdf() {
  if (!canvasRef.value) return;
  const prevCompare = compareActive.value;
  compareActive.value = false;
  const prevZoom = zoom.value;
  zoom.value = 1;
  await nextTick();
  const node = canvasRef.value;
  const width = node.scrollWidth;
  const height = node.scrollHeight;
  const dataUrl = await toPng(node, {
    width,
    height,
    backgroundColor: getComputedStyle(node).backgroundColor,
    pixelRatio: 2,
  });
  const pdf = new jsPDF({
    orientation: width >= height ? "l" : "p",
    unit: "px",
    format: [width, height],
  });
  pdf.addImage(dataUrl, "PNG", 0, 0, width, height);
  pdf.save("mindmap.pdf");
  zoom.value = prevZoom;
  compareActive.value = prevCompare;
  scheduleLineUpdate();
}

async function exportMindmapBundle() {
  await exportMindmapPng();
  await exportMindmapPdf();
}

function nodeSignature(node: ProjectNode) {
  return `${node.title}::${node.module_id ?? "none"}`;
}

async function compareWithVersion() {
  if (!compareVersionId.value) return;
  const detail = await store.loadMindmapVersionDetail(Number(compareVersionId.value));
  if (!detail) return;
  const snapshot = detail.snapshot;
  const currentMap = new Map<string, ProjectNode>();
  store.mindmapNodes.forEach((node) => {
    currentMap.set(nodeSignature(node), node);
  });
  const snapshotMap = new Map<string, typeof snapshot.nodes[number]>();
  snapshot.nodes.forEach((node) => {
    snapshotMap.set(`${node.title}::${node.module_id ?? "none"}`, node);
  });
  const added = new Set<number>();
  const changed = new Set<number>();
  let removed = 0;

  snapshotMap.forEach((snapNode, key) => {
    const currentNode = currentMap.get(key);
    if (!currentNode) {
      removed += 1;
      return;
    }
    const changedFlag =
      currentNode.description !== snapNode.description ||
      currentNode.hours_frontend !== snapNode.hours_frontend ||
      currentNode.hours_backend !== snapNode.hours_backend ||
      currentNode.hours_qa !== snapNode.hours_qa;
    if (changedFlag) {
      changed.add(currentNode.id);
    }
  });

  currentMap.forEach((currentNode, key) => {
    if (!snapshotMap.has(key)) {
      added.add(currentNode.id);
    }
  });

  compareDiff.value = { added, changed, removed };
  compareActive.value = true;
}

function clearComparison() {
  compareActive.value = false;
  compareDiff.value = { added: new Set(), changed: new Set(), removed: 0 };
  compareVersionId.value = "";
}

function handleDragEnd() {
  scheduleLineUpdate();
}

function updateHours(
  projectModule: ProjectModule,
  field: "override_frontend" | "override_backend" | "override_qa",
  event: Event
) {
  const value = Number((event.target as HTMLInputElement).value);
  const updated = { ...projectModule, [field]: value };
  store.updateProjectModule(updated);
}

function updateSelect(
  projectModule: ProjectModule,
  field: "uncertainty_level" | "uiux_level",
  event: Event
) {
  const value = (event.target as HTMLSelectElement).value;
  const updated = { ...projectModule, [field]: value };
  store.updateProjectModule(updated);
}

function updateCheckbox(
  projectModule: ProjectModule,
  field: "legacy_code",
  event: Event
) {
  const value = (event.target as HTMLInputElement).checked;
  const updated = { ...projectModule, [field]: value };
  store.updateProjectModule(updated);
}

function assignmentLevel(projectModuleId: number, role: string) {
  const assignment = store.assignments.find(
    (item) => item.project_module_id === projectModuleId && item.role === role
  );
  if (assignment) {
    return assignment.level;
  }
  if (role === "backend") return "senior";
  return "middle";
}

function assignRole(projectModuleId: number, role: string, event: Event) {
  const level = (event.target as HTMLSelectElement).value;
  store.assignRole(projectModuleId, role, level);
}

function setNodeRef(el: Element | null, moduleId: number) {
  if (!el) {
    delete nodeRefs.value[moduleId];
    return;
  }
  nodeRefs.value[moduleId] = el as HTMLElement;
}

function scheduleLineUpdate() {
  requestAnimationFrame(() => {
    if (mindmapMode.value) {
      buildMindmapLayout();
    }
    updateLines();
  });
}

function updateLines() {
  if (!canvasRef.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  const positions: Record<number, { x: number; y: number }> = {};
  const nodeIds = mindmapMode.value
    ? store.mindmapNodes.map((node) => node.id)
    : store.projectModules.map((module) => module.id);
  nodeIds.forEach((nodeId) => {
    const element = nodeRefs.value[nodeId];
    if (!element) return;
    const box = element.getBoundingClientRect();
    positions[nodeId] = {
      x: box.left - rect.left + box.width / 2,
      y: box.top - rect.top + box.height / 2,
    };
  });

  const nextLines = connections.value
    .map((connection) => {
      const from = positions[connection.fromId];
      const to = positions[connection.toId];
      if (!from || !to) return null;
      return { x1: from.x, y1: from.y, x2: to.x, y2: to.y };
    })
    .filter(
      (line): line is { x1: number; y1: number; x2: number; y2: number } =>
        Boolean(line)
    );

  lines.value = nextLines;
}

function linePath(line: { x1: number; y1: number; x2: number; y2: number }) {
  const controlOffset = 60;
  const c1x = line.x1 + controlOffset;
  const c2x = line.x2 - controlOffset;
  return `M ${line.x1} ${line.y1} C ${c1x} ${line.y1} ${c2x} ${line.y2} ${line.x2} ${line.y2}`;
}

function openContextMenu(event: MouseEvent, moduleId: number) {
  if (!canvasRef.value) return;
  event.preventDefault();
  const rect = canvasRef.value.getBoundingClientRect();
  contextMenu.value = {
    visible: true,
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
    moduleId,
  };
}

function toggleMindmap() {
  mindmapMode.value = !mindmapMode.value;
  nextTick(() => {
    if (mindmapMode.value) {
      buildMindmapLayout();
    }
    updateLines();
  });
}

const zoomStyle = computed(() => {
  return {
    transform: `scale(${zoom.value})`,
  };
});

function zoomIn() {
  zoom.value = Math.min(1.6, Number((zoom.value + 0.1).toFixed(2)));
  scheduleLineUpdate();
}

function zoomOut() {
  zoom.value = Math.max(0.6, Number((zoom.value - 0.1).toFixed(2)));
  scheduleLineUpdate();
}

function resetZoom() {
  zoom.value = 1;
  scheduleLineUpdate();
}

function nodeStyle(moduleId: number, x?: number, y?: number) {
  if (!mindmapMode.value) return {};
  const position = autoLayoutEnabled.value
    ? mindmapPositions.value[moduleId] ?? { x: x ?? 40, y: y ?? 40 }
    : { x: x ?? 40, y: y ?? 40 };
  return {
    left: `${position.x}px`,
    top: `${position.y}px`,
  };
}

function buildMindmapLayout() {
  if (!canvasRef.value || !mindmapMode.value || !autoLayoutEnabled.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  const width = rect.width || 800;
  const centerX = width / 2;
  const levelGap = 260;
  const rowGap = 40;
  const nodeHeight = 170;
  const nodeWidth = 420;

  const nodes = store.mindmapNodes.map((node) => node.id);
  if (nodes.length === 0) {
    mindmapPositions.value = {};
    return;
  }

  const incoming = new Map<number, number>();
  const children = new Map<number, number[]>();
  nodes.forEach((id) => {
    incoming.set(id, 0);
    children.set(id, []);
  });
  connections.value.forEach((connection) => {
    if (!children.has(connection.fromId)) return;
    children.get(connection.fromId)?.push(connection.toId);
    incoming.set(connection.toId, (incoming.get(connection.toId) ?? 0) + 1);
  });

  const roots = nodes.filter((id) => (incoming.get(id) ?? 0) === 0);
  const root = roots[0] ?? nodes[0];

  const positions: Record<number, { x: number; y: number }> = {};
  const sizeCache = new Map<number, number>();

  function subtreeSize(nodeId: number, visiting = new Set<number>()) {
    if (sizeCache.has(nodeId)) return sizeCache.get(nodeId) ?? 1;
    if (visiting.has(nodeId)) return 1;
    visiting.add(nodeId);
    const childIds = children.get(nodeId) ?? [];
    const total = childIds.reduce(
      (sum, child) => sum + subtreeSize(child, visiting),
      1
    );
    sizeCache.set(nodeId, total);
    visiting.delete(nodeId);
    return total;
  }

  const rootChildren = (children.get(root) ?? []).slice();
  rootChildren.sort((a, b) => subtreeSize(b) - subtreeSize(a));
  const leftChildren: number[] = [];
  const rightChildren: number[] = [];
  rootChildren.forEach((child, index) => {
    if (index % 2 === 0) {
      rightChildren.push(child);
    } else {
      leftChildren.push(child);
    }
  });

  function layoutBranch(
    nodeId: number,
    side: number,
    depth: number,
    startY: number
  ): number {
    const childIds = children.get(nodeId) ?? [];
    if (childIds.length === 0) {
      positions[nodeId] = {
        x: centerX + side * depth * levelGap - nodeWidth / 2,
        y: startY,
      };
      return nodeHeight + rowGap;
    }
    let currentY = startY;
    childIds.forEach((childId) => {
      const height = layoutBranch(childId, side, depth + 1, currentY);
      currentY += height;
    });
    const totalHeight = Math.max(currentY - startY, nodeHeight + rowGap);
    const y = startY + totalHeight / 2 - nodeHeight / 2;
    positions[nodeId] = {
      x: centerX + side * depth * levelGap - nodeWidth / 2,
      y,
    };
    return totalHeight;
  }

  let leftHeight = 0;
  let rightHeight = 0;
  let leftY = 60;
  let rightY = 60;
  leftChildren.forEach((childId) => {
    const height = layoutBranch(childId, -1, 1, leftY);
    leftY += height;
    leftHeight += height;
  });
  rightChildren.forEach((childId) => {
    const height = layoutBranch(childId, 1, 1, rightY);
    rightY += height;
    rightHeight += height;
  });

  const rootY = Math.max(leftHeight, rightHeight) / 2;
  positions[root] = { x: centerX - nodeWidth / 2, y: Math.max(rootY, 60) };

  let orphanOffset = Object.keys(positions).length * 0.1;
  nodes.forEach((id, index) => {
    if (positions[id]) return;
    const x = 40 + (index % 3) * 280;
    const y = 300 + orphanOffset * rowGap;
    positions[id] = { x, y };
    orphanOffset += 1;
  });

  mindmapPositions.value = positions;
}

function applyLayoutToNodes() {
  const positions = mindmapPositions.value;
  store.mindmapNodes.forEach((node) => {
    const position = positions[node.id];
    if (!position) return;
    updateNodeLocal({
      ...node,
      position_x: position.x,
      position_y: position.y,
    });
    scheduleNodeSave({
      ...node,
      position_x: position.x,
      position_y: position.y,
    });
  });
}

function hideContextMenu() {
  if (!contextMenu.value.visible) return;
  contextMenu.value.visible = false;
}

function startLinkMode() {
  const moduleId = contextMenu.value.moduleId;
  if (!moduleId) return;
  linkMode.value = { active: true, fromId: moduleId };
  hideContextMenu();
}

function cancelLinkMode() {
  linkMode.value = { active: false, fromId: null };
}

function handleNodeClick(moduleId: number) {
  if (!linkMode.value.active || !linkMode.value.fromId) return;
  if (linkMode.value.fromId === moduleId) return;
  const exists = connections.value.some(
    (connection) =>
      connection.fromId === linkMode.value.fromId &&
      connection.toId === moduleId
  );
  if (!exists) {
    const nextConnections = [
      ...connections.value,
      { fromId: linkMode.value.fromId, toId: moduleId },
    ];
    updateConnections(nextConnections);
    scheduleLineUpdate();
    saveConnections();
  }
  cancelLinkMode();
}

function removeConnections() {
  const moduleId = contextMenu.value.moduleId;
  if (!moduleId) return;
  const nextConnections = connections.value.filter(
    (connection) => connection.fromId !== moduleId && connection.toId !== moduleId
  );
  updateConnections(nextConnections);
  scheduleLineUpdate();
  saveConnections();
  hideContextMenu();
}

function clearConnections() {
  updateConnections([]);
  scheduleLineUpdate();
  saveConnections();
}

function resetModule() {
  const moduleId = contextMenu.value.moduleId;
  if (!moduleId) return;
  const projectModule = store.projectModules.find((item) => item.id === moduleId);
  if (!projectModule) return;
  const updated: ProjectModule = {
    ...projectModule,
    override_frontend: null,
    override_backend: null,
    override_qa: null,
    uncertainty_level: null,
    uiux_level: null,
    legacy_code: null,
  };
  store.updateProjectModule(updated);
  hideContextMenu();
}

function removeModule() {
  const moduleId = contextMenu.value.moduleId;
  if (!moduleId) return;
  store.removeProjectModule(moduleId);
  const nextConnections = connections.value.filter(
    (connection) => connection.fromId !== moduleId && connection.toId !== moduleId
  );
  updateConnections(nextConnections);
  scheduleLineUpdate();
  saveConnections();
  hideContextMenu();
}

function removeActiveNode() {
  const nodeId = contextMenu.value.moduleId;
  if (!nodeId) return;
  if (mindmapMode.value) {
    removeMindmapNode(nodeId);
    hideContextMenu();
    return;
  }
  removeModule();
}

async function removeMindmapNode(nodeId: number) {
  await store.deleteMindmapNode(nodeId);
  const nextConnections = connections.value.filter(
    (connection) => connection.fromId !== nodeId && connection.toId !== nodeId
  );
  updateConnections(nextConnections);
  scheduleLineUpdate();
}

async function removeMindmapNote(noteId: number) {
  await store.deleteMindmapNote(noteId);
}

function handleResize() {
  if (mindmapMode.value) {
    buildMindmapLayout();
  }
  updateLines();
}

function updateConnections(nextConnections: { fromId: number; toId: number }[]) {
  if (mindmapMode.value) {
    mindmapConnections.value = nextConnections;
    store.updateMindmapConnections(
      nextConnections.map((item) => ({
        from_node_id: item.fromId,
        to_node_id: item.toId,
      }))
    );
    return;
  }
  moduleConnections.value = nextConnections;
}

function updateNodeLocal(updated: ProjectNode) {
  store.mindmapNodes = store.mindmapNodes.map((node) =>
    node.id === updated.id ? updated : node
  );
}

function updateNodeField(
  node: ProjectNode,
  field: "title" | "description" | "hours_frontend" | "hours_backend" | "hours_qa",
  event: Event
) {
  const target = event.target as HTMLInputElement;
  const value =
    field === "title" || field === "description"
      ? target.value
      : Number(target.value);
  const updated = { ...node, [field]: value };
  updateNodeLocal(updated);
  scheduleNodeSave(updated);
}

function updateNodeModule(node: ProjectNode, event: Event) {
  const value = (event.target as HTMLSelectElement).value;
  const moduleId = value ? Number(value) : null;
  const module = moduleId ? store.modules.find((item) => item.id === moduleId) : null;
  const updated: ProjectNode = {
    ...node,
    module_id: moduleId,
    hours_frontend: module?.hours_frontend ?? node.hours_frontend,
    hours_backend: module?.hours_backend ?? node.hours_backend,
    hours_qa: module?.hours_qa ?? node.hours_qa,
    role_hours: module?.role_hours ?? node.role_hours,
  };
  updateNodeLocal(updated);
  scheduleNodeSave(updated);
}

function updateNodeRoleHours(node: ProjectNode, role: string, event: Event) {
  const value = Number((event.target as HTMLInputElement).value);
  const next = node.role_hours.filter((item) => item.role !== role);
  if (value > 0) {
    next.push({ role, hours: value });
  }
  const updated = { ...node, role_hours: next };
  updateNodeLocal(updated);
  scheduleNodeSave(updated);
}

function scheduleNodeSave(node: ProjectNode) {
  const existing = nodeSaveTimers.get(node.id);
  if (existing) window.clearTimeout(existing);
  const timer = window.setTimeout(() => {
    store.updateMindmapNode(node.id, {
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
    });
  }, 400);
  nodeSaveTimers.set(node.id, timer);
}

function noteStyle(note: ProjectNote) {
  return {
    left: `${note.position_x}px`,
    top: `${note.position_y}px`,
  };
}

function updateNoteContent(note: ProjectNote, event: Event) {
  const value = (event.target as HTMLTextAreaElement).value;
  const updated = { ...note, content: value };
  store.mindmapNotes = store.mindmapNotes.map((item) =>
    item.id === note.id ? updated : item
  );
  scheduleNoteSave(updated);
}

function scheduleNoteSave(note: ProjectNote) {
  const existing = noteSaveTimers.get(note.id);
  if (existing) window.clearTimeout(existing);
  const timer = window.setTimeout(() => {
    store.updateMindmapNote(note.id, {
      content: note.content,
      position_x: note.position_x,
      position_y: note.position_y,
    });
  }, 400);
  noteSaveTimers.set(note.id, timer);
}

function startNodeDrag(event: MouseEvent, nodeId: number) {
  if (!canvasRef.value) return;
  const node = store.mindmapNodes.find((item) => item.id === nodeId);
  if (!node) return;
  autoLayoutEnabled.value = false;
  const point = toCanvasPoint(event);
  draggingNode.value = {
    id: nodeId,
    offsetX: point.x - node.position_x,
    offsetY: point.y - node.position_y,
  };
  window.addEventListener("mousemove", handleNodeDrag);
  window.addEventListener("mouseup", stopNodeDrag);
}

function handleNodeDrag(event: MouseEvent) {
  if (!draggingNode.value) return;
  const node = store.mindmapNodes.find((item) => item.id === draggingNode.value?.id);
  if (!node) return;
  const point = toCanvasPoint(event);
  const position_x = point.x - draggingNode.value.offsetX;
  const position_y = point.y - draggingNode.value.offsetY;
  const updated = { ...node, position_x, position_y };
  updateNodeLocal(updated);
  scheduleNodeSave(updated);
  scheduleLineUpdate();
}

function stopNodeDrag() {
  draggingNode.value = null;
  window.removeEventListener("mousemove", handleNodeDrag);
  window.removeEventListener("mouseup", stopNodeDrag);
}

function startNoteDrag(event: MouseEvent, noteId: number) {
  if (!canvasRef.value) return;
  const note = store.mindmapNotes.find((item) => item.id === noteId);
  if (!note) return;
  const point = toCanvasPoint(event);
  draggingNote.value = {
    id: noteId,
    offsetX: point.x - note.position_x,
    offsetY: point.y - note.position_y,
  };
  window.addEventListener("mousemove", handleNoteDrag);
  window.addEventListener("mouseup", stopNoteDrag);
}

function handleNoteDrag(event: MouseEvent) {
  if (!draggingNote.value) return;
  const note = store.mindmapNotes.find((item) => item.id === draggingNote.value?.id);
  if (!note) return;
  const point = toCanvasPoint(event);
  const position_x = point.x - draggingNote.value.offsetX;
  const position_y = point.y - draggingNote.value.offsetY;
  const updated = { ...note, position_x, position_y };
  store.mindmapNotes = store.mindmapNotes.map((item) =>
    item.id === note.id ? updated : item
  );
  scheduleNoteSave(updated);
  scheduleLineUpdate();
}

function stopNoteDrag() {
  draggingNote.value = null;
  window.removeEventListener("mousemove", handleNoteDrag);
  window.removeEventListener("mouseup", stopNoteDrag);
}

function downloadDataUrl(dataUrl: string, filename: string) {
  const link = document.createElement("a");
  link.href = dataUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

watch(
  () => store.projectModules.map((module) => module.id),
  async () => {
    await nextTick();
    if (!mindmapMode.value) {
      const nextConnections = moduleConnections.value.filter((connection) => {
        return (
          store.projectModules.some((module) => module.id === connection.fromId) &&
          store.projectModules.some((module) => module.id === connection.toId)
        );
      });
      moduleConnections.value = nextConnections;
    }
    if (mindmapMode.value) {
      buildMindmapLayout();
    }
    updateLines();
    saveConnections();
  }
);

watch(
  () => store.mindmapNodes.map((node) => node.id),
  async () => {
    if (!mindmapMode.value) return;
    await nextTick();
    const nextConnections = mindmapConnections.value.filter((connection) => {
      return (
        store.mindmapNodes.some((node) => node.id === connection.fromId) &&
        store.mindmapNodes.some((node) => node.id === connection.toId)
      );
    });
    mindmapConnections.value = nextConnections;
    buildMindmapLayout();
    updateLines();
  }
);

watch(
  () => store.mindmapConnections,
  (value) => {
    if (mindmapMode.value) {
      mindmapConnections.value = value.map((item) => ({
        fromId: item.from_node_id,
        toId: item.to_node_id,
      }));
      scheduleLineUpdate();
    }
  },
  { immediate: true }
);

watch(
  () => store.connections,
  (items) => {
    connections.value = items.map((item) => ({
      fromId: item.from_project_module_id,
      toId: item.to_project_module_id,
    }));
    scheduleLineUpdate();
  },
  { immediate: true }
);

watch(
  () => mindmapMode.value,
  (value) => {
    if (value) {
      mindmapConnections.value = store.mindmapConnections.map((item) => ({
        fromId: item.from_node_id,
        toId: item.to_node_id,
      }));
      buildMindmapLayout();
    }
    scheduleLineUpdate();
  }
);
onMounted(() => {
  window.addEventListener("resize", handleResize);
  nextTick(() => {
    updateLines();
  });
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
});

function saveConnections() {
  if (!store.project) return;
  const payload: ProjectConnection[] = connections.value.map((item) => ({
    id: 0,
    project_id: store.project?.id ?? 0,
    from_project_module_id: item.fromId,
    to_project_module_id: item.toId,
  }));
  store.updateConnections(payload);
}
</script>

<style scoped>
.panel {
  background: var(--panel-bg);
  padding: 16px;
  border-radius: 16px;
  box-shadow: var(--panel-shadow);
}
.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.mindmap-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.mindmap-input {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
  min-width: 240px;
}
.mindmap-select {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
  min-width: 200px;
}
.actions .ghost {
  border: 1px solid var(--border);
  padding: 6px 10px;
  border-radius: 8px;
  color: var(--text);
}
.zoom-controls {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px;
  border-radius: 10px;
  background: var(--card-bg);
}
.zoom-controls span {
  font-size: 12px;
  color: var(--muted);
  min-width: 44px;
  text-align: center;
}
.panel-header h2 {
  margin: 0;
}
.hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 8px;
}
.link-cancel {
  background: transparent;
  border: 1px solid var(--border);
  padding: 2px 6px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--text);
}
.canvas-surface {
  min-height: 420px;
  padding: 16px;
  border-radius: 14px;
  border: 1px dashed var(--grid-line);
  background-image:
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 24px 24px;
  position: relative;
  overflow: auto;
}
.legend {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 8px;
  margin-bottom: 10px;
  box-shadow: var(--panel-shadow);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.legend-title {
  font-size: 12px;
  color: var(--muted);
}
.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.legend-item {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid transparent;
  cursor: grab;
  user-select: none;
}
.legend-compare {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.legend-chip {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 999px;
  border: 1px solid transparent;
}
.legend-chip.added {
  background: var(--chip-added-bg);
  border-color: var(--chip-added-border);
  color: var(--chip-added-text);
}
.legend-chip.changed {
  background: var(--chip-changed-bg);
  border-color: var(--chip-changed-border);
  color: var(--chip-changed-text);
}
.legend-chip.removed {
  background: var(--chip-removed-bg);
  border-color: var(--chip-removed-border);
  color: var(--chip-removed-text);
}
.canvas-zoom {
  position: relative;
  transform-origin: top left;
  width: fit-content;
  min-width: 100%;
}
.canvas-lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.canvas-lines path {
  fill: none;
  stroke: var(--canvas-line);
  stroke-width: 2;
}
.canvas-nodes {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  min-height: 360px;
}
.mindmap-nodes {
  position: relative;
  min-height: 360px;
}
.module-card {
  width: min(420px, 100%);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px;
  background: var(--card-bg);
}
.module-card.node-added {
  outline: 2px solid #22c55e;
}
.module-card.node-changed {
  outline: 2px solid #eab308;
}
.module-card.absolute {
  position: absolute;
}
.drag-handle {
  cursor: grab;
}
.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.module-header strong {
  font-size: 15px;
}
.module-header small {
  display: block;
  color: var(--muted);
  margin-top: 2px;
}
.module-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 6px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid transparent;
  margin-top: 4px;
  width: fit-content;
}
.link-badge {
  font-size: 11px;
  color: var(--accent);
  background: var(--grid);
  padding: 2px 6px;
  border-radius: 999px;
  margin-left: auto;
  margin-right: 8px;
}
.module-body {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
}
label {
  font-size: 12px;
  color: var(--muted);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
input,
select {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
}
.checkbox {
  flex-direction: row;
  align-items: center;
  gap: 6px;
}
.ghost {
  background: transparent;
  border: none;
  color: var(--text);
  cursor: pointer;
}
.ghost.danger {
  color: var(--danger);
}
.context-menu {
  position: absolute;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: var(--panel-shadow);
  z-index: 5;
}
.context-menu button {
  text-align: left;
  background: transparent;
  border: none;
  padding: 6px 8px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text);
}
.context-menu button:hover {
  background: var(--card-bg);
}
.context-menu .danger {
  color: var(--danger);
}
.note {
  position: absolute;
  width: 160px;
  background: var(--note-bg);
  border: 1px solid var(--note-border);
  border-radius: 12px;
  padding: 8px;
  box-shadow: var(--panel-shadow);
}
.note textarea {
  width: 100%;
  min-height: 60px;
  background: transparent;
  border: none;
  resize: vertical;
  color: var(--note-text);
}
.note-remove {
  position: absolute;
  top: 4px;
  right: 6px;
  background: transparent;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: var(--note-action);
}
.empty {
  padding: 20px;
  text-align: center;
  color: var(--muted-2);
}
</style>
