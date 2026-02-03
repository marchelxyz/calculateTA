<template>
  <section class="panel">
    <h2>Холст проекта</h2>
    <div class="canvas-surface" ref="canvasRef" @click="hideContextMenu">
      <svg v-if="lines.length" class="canvas-lines">
        <path
          v-for="(line, index) in lines"
          :key="index"
          :d="linePath(line)"
        />
      </svg>
      <Draggable
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
          >
            <header class="module-header">
              <div>
                <strong>{{ moduleName(element.module_id) }}</strong>
                <small v-if="element.custom_name">{{ element.custom_name }}</small>
              </div>
              <button class="ghost" @click="store.removeProjectModule(element.id)">
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
      <div
        v-if="contextMenu.visible"
        class="context-menu"
        :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }"
        @click.stop
      >
        <button class="ghost" @click="resetModule">Сбросить настройки</button>
        <button class="danger" @click="removeModule">Удалить модуль</button>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { VueDraggableNext as Draggable } from "vue-draggable-next";
import { useProjectStore } from "../stores/project";
import type { ProjectModule } from "../types";

const store = useProjectStore();
const canvasRef = ref<HTMLElement | null>(null);
const lines = ref<{ x1: number; y1: number; x2: number; y2: number }[]>([]);
const nodeRefs = ref<Record<number, HTMLElement>>({});
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  moduleId: null as number | null,
});

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

function moduleName(moduleId: number) {
  return moduleMap.value.get(moduleId)?.name ?? "Модуль";
}

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
  if (!canvasRef.value) return;
  const rect = canvasRef.value.getBoundingClientRect();
  const points = store.projectModules
    .map((module) => {
      const element = nodeRefs.value[module.id];
      if (!element) return null;
      const box = element.getBoundingClientRect();
      return {
        x: box.left - rect.left + box.width / 2,
        y: box.top - rect.top + box.height / 2,
      };
    })
    .filter((point): point is { x: number; y: number } => Boolean(point));

  const nextLines = [];
  for (let i = 0; i < points.length - 1; i += 1) {
    nextLines.push({
      x1: points[i].x,
      y1: points[i].y,
      x2: points[i + 1].x,
      y2: points[i + 1].y,
    });
  }
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

function hideContextMenu() {
  if (!contextMenu.value.visible) return;
  contextMenu.value.visible = false;
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
  hideContextMenu();
}

function handleResize() {
  updateLines();
}

watch(
  () => store.projectModules.map((module) => module.id),
  async () => {
    await nextTick();
    updateLines();
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
</script>

<style scoped>
.panel {
  background: white;
  padding: 16px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
.canvas-surface {
  min-height: 420px;
  padding: 16px;
  border-radius: 14px;
  border: 1px dashed #cbd5f5;
  background-image:
    linear-gradient(#eef2ff 1px, transparent 1px),
    linear-gradient(90deg, #eef2ff 1px, transparent 1px);
  background-size: 24px 24px;
  position: relative;
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
  stroke: #94a3b8;
  stroke-width: 2;
}
.canvas-nodes {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  min-height: 360px;
}
.module-card {
  width: min(420px, 100%);
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 12px;
  background: #f8fafc;
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
  color: #64748b;
  margin-top: 2px;
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
  color: #475569;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
input,
select {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.checkbox {
  flex-direction: row;
  align-items: center;
  gap: 6px;
}
.ghost {
  background: transparent;
  border: none;
  color: #ef4444;
  cursor: pointer;
}
.context-menu {
  position: absolute;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
  z-index: 5;
}
.context-menu button {
  text-align: left;
  background: transparent;
  border: none;
  padding: 6px 8px;
  border-radius: 8px;
  cursor: pointer;
}
.context-menu button:hover {
  background: #f1f5f9;
}
.context-menu .danger {
  color: #ef4444;
}
.empty {
  padding: 20px;
  text-align: center;
  color: #94a3b8;
}
</style>
