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
            <div class="mindmap-content">
              <div class="mindmap-stage">
                <div ref="mindmapContainerRef" class="mindmap-container"></div>
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
              </div>
              <div class="mindmap-editor">
                <div v-if="selectedMindmapNode" class="module-card" :class="compareClass(selectedMindmapNode)">
                  <header class="module-header">
                    <div>
                      <strong>{{ selectedMindmapNode.title }}</strong>
                      <small
                        v-if="selectedMindmapNode.module_id"
                        class="module-badge"
                        :style="moduleBadgeStyle(selectedMindmapNode.module_id)"
                      >
                        {{ moduleName(selectedMindmapNode.module_id) }}
                      </small>
                    </div>
                    <button class="ghost danger" @click="removeMindmapNode(selectedMindmapNode.id)">
                      Удалить
                    </button>
                  </header>
                  <div class="module-body">
                    <div class="grid">
                      <label class="wide">
                        Название
                        <input
                          :value="selectedMindmapNode.title"
                          @input="updateNodeField(selectedMindmapNode, 'title', $event)"
                        />
                      </label>
                      <label class="wide">
                        Описание
                        <input
                          :value="selectedMindmapNode.description"
                          @input="updateNodeField(selectedMindmapNode, 'description', $event)"
                        />
                      </label>
                      <label class="wide">
                        Модуль
                        <select
                          :value="selectedMindmapNode.module_id ?? ''"
                          @change="updateNodeModule(selectedMindmapNode, $event)"
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
                          :value="selectedMindmapNode.hours_frontend"
                          @change="updateNodeField(selectedMindmapNode, 'hours_frontend', $event)"
                        />
                      </label>
                      <label>
                        BE часы
                        <input
                          type="number"
                          :value="selectedMindmapNode.hours_backend"
                          @change="updateNodeField(selectedMindmapNode, 'hours_backend', $event)"
                        />
                      </label>
                      <label>
                        QA часы
                        <input
                          type="number"
                          :value="selectedMindmapNode.hours_qa"
                          @change="updateNodeField(selectedMindmapNode, 'hours_qa', $event)"
                        />
                      </label>
                    </div>
                    <div class="grid">
                      <label v-for="role in extraRoles" :key="role">
                        {{ role }} часы
                        <input
                          type="number"
                          :value="roleHoursValue(selectedMindmapNode, role)"
                          @change="updateNodeRoleHours(selectedMindmapNode, role, $event)"
                        />
                      </label>
                    </div>
                  </div>
                </div>
                <div v-else class="empty">Выберите узел для редактирования</div>
              </div>
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
import MindMap from "simple-mind-map/full";
import "simple-mind-map/dist/simpleMindMap.esm.min.css";
import { VueDraggableNext as Draggable } from "vue-draggable-next";
import { useProjectStore } from "../stores/project";
import type { ProjectConnection, ProjectModule, ProjectNode, ProjectNote } from "../types";

type MindmapNodeData = {
  text: string;
  uid: string;
  customLeft?: number;
  customTop?: number;
};

type MindmapTreeNode = {
  data: MindmapNodeData;
  children: MindmapTreeNode[];
};

const store = useProjectStore();
const canvasRef = ref<HTMLElement | null>(null);
const mindmapContainerRef = ref<HTMLDivElement | null>(null);
const lines = ref<{ x1: number; y1: number; x2: number; y2: number }[]>([]);
const nodeRefs = ref<Record<number, HTMLElement>>({});
const moduleConnections = ref<{ fromId: number; toId: number }[]>([]);
const mindmapInstance = ref<InstanceType<typeof MindMap> | null>(null);
const linkMode = ref<{ active: boolean; fromId: number | null }>({
  active: false,
  fromId: null,
});
const mindmapMode = ref(false);
const useCustomPositions = ref(true);
const zoom = ref(1);
const freeZoomCache = ref(1);
const mindmapPrompt = ref("");
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
const selectedMindmapNodeId = ref<number | null>(null);
const lastDraggedMindmapNode = ref<any | null>(null);
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  moduleId: null as number | null,
});
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
  if (mindmapMode.value) {
    return store.mindmapConnections.map((item) => ({
      fromId: item.from_node_id,
      toId: item.to_node_id,
    }));
  }
  return moduleConnections.value;
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

function compareClass(node: ProjectNode) {
  if (!compareActive.value) return "";
  if (compareDiff.value.added.has(node.id)) return "node-added";
  if (compareDiff.value.changed.has(node.id)) return "node-changed";
  return "";
}

const compareSummary = computed(() => ({
  removed: compareDiff.value.removed,
}));

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

const selectedMindmapNode = computed(() => {
  if (!mindmapMode.value || selectedMindmapNodeId.value === null) return null;
  return store.mindmapNodes.find((node) => node.id === selectedMindmapNodeId.value) ?? null;
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
  useCustomPositions.value = false;
  await nextTick();
  refreshMindmapFromStore();
  autoLayoutMindmap();
}

async function addMindmapNode() {
  const point = getMindmapCenter();
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
    position_x: point.x - 120,
    position_y: point.y - 80,
    role_hours: [],
  });
  if (created) {
    selectedMindmapNodeId.value = created.id;
    refreshMindmapFromStore();
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
  lastLegendDropPoint.value = getDropPoint(event);
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
  const point = getDropPoint(event);
  useCustomPositions.value = true;
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
  useCustomPositions.value = true;
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
  const created = await store.createMindmapNode({
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
  if (created) {
    refreshMindmapFromStore();
  }
  return created;
}

function autoLayoutMindmap() {
  useCustomPositions.value = false;
  if (!mindmapInstance.value) return;
  mindmapInstance.value.execCommand("RESET_LAYOUT");
  mindmapInstance.value.view.fit();
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
  useCustomPositions.value = true;
  selectedVersionId.value = "";
  refreshMindmapFromStore();
}

function formatVersion(version: { title: string; created_at: string }) {
  const date = new Date(version.created_at);
  return `${version.title} · ${date.toLocaleString("ru-RU")}`;
}

async function exportMindmapPng() {
  if (mindmapMode.value && mindmapInstance.value) {
    await mindmapInstance.value.export("png", true, "mindmap");
    return;
  }
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
  if (mindmapMode.value && mindmapInstance.value) {
    await mindmapInstance.value.export("pdf", true, "mindmap");
    return;
  }
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
    updateLines();
  });
}

function updateLines() {
  if (!canvasRef.value || mindmapMode.value) {
    lines.value = [];
    return;
  }
  const rect = canvasRef.value.getBoundingClientRect();
  const positions: Record<number, { x: number; y: number }> = {};
  const nodeIds = store.projectModules.map((module) => module.id);
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
}

const zoomStyle = computed(() => {
  return {
    transform: mindmapMode.value ? "none" : `scale(${zoom.value})`,
  };
});

function zoomIn() {
  if (mindmapMode.value && mindmapInstance.value) {
    mindmapInstance.value.view.enlarge();
    return;
  }
  zoom.value = Math.min(1.6, Number((zoom.value + 0.1).toFixed(2)));
  scheduleLineUpdate();
}

function zoomOut() {
  if (mindmapMode.value && mindmapInstance.value) {
    mindmapInstance.value.view.narrow();
    return;
  }
  zoom.value = Math.max(0.6, Number((zoom.value - 0.1).toFixed(2)));
  scheduleLineUpdate();
}

function resetZoom() {
  if (mindmapMode.value && mindmapInstance.value) {
    mindmapInstance.value.view.reset();
    return;
  }
  zoom.value = 1;
  scheduleLineUpdate();
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
    if (mindmapMode.value) {
      refreshMindmapFromStore();
    } else {
      scheduleLineUpdate();
      saveConnections();
    }
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
  if (mindmapMode.value) {
    refreshMindmapFromStore();
  } else {
    scheduleLineUpdate();
    saveConnections();
  }
  hideContextMenu();
}

function clearConnections() {
  updateConnections([]);
  if (mindmapMode.value) {
    refreshMindmapFromStore();
  } else {
    scheduleLineUpdate();
    saveConnections();
  }
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
  if (selectedMindmapNodeId.value === nodeId) {
    selectedMindmapNodeId.value = null;
  }
  const nextConnections = connections.value.filter(
    (connection) => connection.fromId !== nodeId && connection.toId !== nodeId
  );
  updateConnections(nextConnections);
  refreshMindmapFromStore();
}

async function removeMindmapNote(noteId: number) {
  await store.deleteMindmapNote(noteId);
}

function handleResize() {
  if (mindmapMode.value) {
    mindmapInstance.value?.resize();
    return;
  }
  updateLines();
}

function updateConnections(nextConnections: { fromId: number; toId: number }[]) {
  if (mindmapMode.value) {
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
  if (mindmapMode.value && field === "title") {
    refreshMindmapFromStore();
  }
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

/** Инициализирует SimpleMindMap и подписки. */
function initializeMindmap() {
  if (!mindmapContainerRef.value) return;
  destroyMindmap();
  const instance = new MindMap({
    el: mindmapContainerRef.value,
    data: buildMindmapData(),
    layout: "mindMap",
    enableFreeDrag: true,
    mousewheelAction: "zoom",
    minZoomRatio: 60,
    maxZoomRatio: 160,
    scaleRatio: 10,
    fit: true,
  });
  instance.on("node_click", (node: any) => {
    handleMindmapNodeClick(node);
  });
  instance.on("node_contextmenu", (event: MouseEvent, node: any) => {
    const nodeId = parseMindmapNodeId(node?.getData?.("uid"));
    if (!nodeId) return;
    selectedMindmapNodeId.value = nodeId;
    openContextMenu(event, nodeId);
  });
  instance.on("node_text_edit_change", (payload: { node: any; text: string }) => {
    handleMindmapTextEdit(payload);
  });
  instance.on("node_dragging", (node: any) => {
    handleMindmapNodeDragging(node);
  });
  instance.on("node_dragend", () => {
    handleMindmapNodeDragEnd();
  });
  instance.on("scale", (scale: number) => {
    zoom.value = Number(scale.toFixed(2));
  });
  mindmapInstance.value = instance;
  zoom.value = Number(instance.view.scale.toFixed(2));
  applyMindmapSearch(mindmapSearch.value);
}

function destroyMindmap() {
  if (!mindmapInstance.value) return;
  mindmapInstance.value.destroy();
  mindmapInstance.value = null;
}

/** Перерисовывает карту по данным стора. */
function refreshMindmapFromStore() {
  if (!mindmapInstance.value) return;
  mindmapInstance.value.setData(buildMindmapData());
  applyMindmapSearch(mindmapSearch.value);
}

function applyMindmapSearch(query: string) {
  const search = (mindmapInstance.value as any)?.search as
    | { search: (text: string) => void; endSearch: () => void }
    | undefined;
  if (!search) return;
  const normalized = query.trim();
  if (!normalized) {
    search.endSearch();
    return;
  }
  search.search(normalized);
}

function handleMindmapNodeClick(node: any) {
  const nodeId = parseMindmapNodeId(node?.getData?.("uid"));
  if (!nodeId) return;
  selectedMindmapNodeId.value = nodeId;
  if (linkMode.value.active) {
    handleNodeClick(nodeId);
  }
}

function handleMindmapTextEdit(payload: { node: any; text: string }) {
  const nodeId = parseMindmapNodeId(payload.node?.getData?.("uid"));
  if (!nodeId) return;
  const target = store.mindmapNodes.find((node) => node.id === nodeId);
  if (!target) return;
  const updated = { ...target, title: payload.text };
  updateNodeLocal(updated);
  scheduleNodeSave(updated);
}

function handleMindmapNodeDragging(node: any) {
  lastDraggedMindmapNode.value = node;
}

function handleMindmapNodeDragEnd() {
  if (!lastDraggedMindmapNode.value) return;
  const node = lastDraggedMindmapNode.value;
  lastDraggedMindmapNode.value = null;
  const nodeId = parseMindmapNodeId(node?.getData?.("uid"));
  if (!nodeId) return;
  const target = store.mindmapNodes.find((item) => item.id === nodeId);
  if (!target) return;
  useCustomPositions.value = true;
  const updated = {
    ...target,
    position_x: Math.round(node.left ?? 0),
    position_y: Math.round(node.top ?? 0),
  };
  updateNodeLocal(updated);
  scheduleNodeSave(updated);
  syncMindmapConnections();
}

/** Синхронизирует связи из структуры mindmap в стор. */
function syncMindmapConnections() {
  if (!mindmapInstance.value) return;
  const data = mindmapInstance.value.getData() as MindmapTreeNode;
  const nextConnections = buildConnectionsFromMindmapData(data);
  if (nextConnections.length === 0 && store.mindmapConnections.length === 0) return;
  updateConnections(nextConnections);
}

function getDropPoint(event: { clientX: number; clientY: number }) {
  if (!mindmapMode.value) return toCanvasPoint(event);
  return getMindmapPoint(event);
}

function getMindmapCenter() {
  if (!mindmapContainerRef.value || !mindmapInstance.value) {
    return { x: 0, y: 0 };
  }
  const rect = mindmapContainerRef.value.getBoundingClientRect();
  return getMindmapPoint({
    clientX: rect.left + rect.width / 2,
    clientY: rect.top + rect.height / 2,
  });
}

function getMindmapPoint(event: { clientX: number; clientY: number }) {
  if (!mindmapInstance.value) return { x: 0, y: 0 };
  const raw = mindmapInstance.value.toPos(event.clientX, event.clientY);
  const transform = mindmapInstance.value.draw.transform();
  return {
    x: (raw.x - transform.translateX) / transform.scaleX,
    y: (raw.y - transform.translateY) / transform.scaleY,
  };
}

/** Строит дерево узлов для SimpleMindMap из текущего стора. */
function buildMindmapData() {
  if (store.mindmapNodes.length === 0) {
    return createRootNode("Схема проекта");
  }
  const nodeMap = new Map<number, MindmapTreeNode>();
  const childrenMap = new Map<number, number[]>();
  const incoming = new Map<number, number>();
  store.mindmapNodes.forEach((node) => {
    nodeMap.set(node.id, createMindmapNode(node));
    childrenMap.set(node.id, []);
    incoming.set(node.id, 0);
  });
  store.mindmapConnections.forEach((connection) => {
    if (!childrenMap.has(connection.from_node_id)) return;
    childrenMap.get(connection.from_node_id)?.push(connection.to_node_id);
    incoming.set(
      connection.to_node_id,
      (incoming.get(connection.to_node_id) ?? 0) + 1
    );
  });
  const roots = store.mindmapNodes
    .map((node) => node.id)
    .filter((id) => (incoming.get(id) ?? 0) === 0);
  const visited = new Set<number>();
  const rootChildren = roots.map((id) => buildMindmapBranch(id, nodeMap, childrenMap, visited));
  const orphans = store.mindmapNodes
    .map((node) => node.id)
    .filter((id) => !visited.has(id))
    .map((id) => buildMindmapBranch(id, nodeMap, childrenMap, visited));
  if (rootChildren.length === 1 && orphans.length === 0) {
    return rootChildren[0];
  }
  return createRootNode("Схема проекта", [...rootChildren, ...orphans]);
}

function buildMindmapBranch(
  nodeId: number,
  nodeMap: Map<number, MindmapTreeNode>,
  childrenMap: Map<number, number[]>,
  visited: Set<number>
) {
  if (visited.has(nodeId)) {
    return nodeMap.get(nodeId) ?? createRootNode("Цикл");
  }
  visited.add(nodeId);
  const base = nodeMap.get(nodeId) ?? createRootNode("Узел");
  const children = (childrenMap.get(nodeId) ?? [])
    .map((childId) => buildMindmapBranch(childId, nodeMap, childrenMap, visited))
    .filter(Boolean);
  return {
    data: { ...base.data },
    children,
  };
}

function buildConnectionsFromMindmapData(root: MindmapTreeNode) {
  const connections: { fromId: number; toId: number }[] = [];
  function walk(node: MindmapTreeNode) {
    const parentId = parseMindmapNodeId(node.data?.uid);
    node.children?.forEach((child) => {
      const childId = parseMindmapNodeId(child.data?.uid);
      if (parentId && childId) {
        connections.push({ fromId: parentId, toId: childId });
      }
      walk(child);
    });
  }
  walk(root);
  return connections;
}

function createMindmapNode(node: ProjectNode): MindmapTreeNode {
  const data: MindmapNodeData = {
    text: node.title || "Узел",
    uid: String(node.id),
  };
  if (useCustomPositions.value) {
    const left = normalizePosition(node.position_x);
    const top = normalizePosition(node.position_y);
    if (left !== null && top !== null) {
      data.customLeft = left;
      data.customTop = top;
    }
  }
  return { data, children: [] };
}

function createRootNode(title: string, children: MindmapTreeNode[] = []) {
  return {
    data: {
      text: title,
      uid: `root-${store.project?.id ?? "local"}`,
    },
    children,
  };
}

function normalizePosition(value: number) {
  if (!Number.isFinite(value)) return null;
  return Math.round(value);
}

function parseMindmapNodeId(uid: unknown) {
  const value = Number(uid);
  if (!Number.isFinite(value) || value <= 0) return null;
  return value;
}

watch(
  () => store.projectModules.map((module) => module.id),
  async () => {
    await nextTick();
    if (mindmapMode.value) return;
    const nextConnections = moduleConnections.value.filter((connection) => {
      return (
        store.projectModules.some((module) => module.id === connection.fromId) &&
        store.projectModules.some((module) => module.id === connection.toId)
      );
    });
    moduleConnections.value = nextConnections;
    updateLines();
    saveConnections();
  }
);

watch(
  () => store.mindmapNodes.map((node) => node.id),
  async () => {
    if (!mindmapMode.value) return;
    await nextTick();
    refreshMindmapFromStore();
  }
);

watch(
  () => store.mindmapConnections,
  () => {
    if (!mindmapMode.value) return;
    refreshMindmapFromStore();
  },
  { immediate: true }
);

watch(
  () => store.connections,
  (items) => {
    if (mindmapMode.value) return;
    moduleConnections.value = items.map((item) => ({
      fromId: item.from_project_module_id,
      toId: item.to_project_module_id,
    }));
    scheduleLineUpdate();
  },
  { immediate: true }
);

watch(
  () => mindmapMode.value,
  async (value) => {
    if (value) {
      freeZoomCache.value = zoom.value;
      await nextTick();
      initializeMindmap();
    } else {
      destroyMindmap();
      selectedMindmapNodeId.value = null;
      zoom.value = freeZoomCache.value;
    }
    scheduleLineUpdate();
  }
);

watch(
  () => mindmapSearch.value,
  (value) => {
    if (!mindmapMode.value) return;
    applyMindmapSearch(value);
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
  destroyMindmap();
});

function saveConnections() {
  if (!store.project) return;
  if (mindmapMode.value) {
    store.updateMindmapConnections(
      connections.value.map((item) => ({
        from_node_id: item.fromId,
        to_node_id: item.toId,
      }))
    );
    return;
  }
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
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.mindmap-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 12px;
  align-items: start;
}
.mindmap-stage {
  position: relative;
  min-height: 420px;
  border-radius: 14px;
  border: 1px solid var(--border);
  background: var(--card-bg);
  overflow: hidden;
}
.mindmap-container {
  width: 100%;
  height: 100%;
  min-height: 420px;
}
.mindmap-editor {
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
