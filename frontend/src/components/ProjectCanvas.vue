<template>
  <section class="panel">
    <h2>Холст проекта</h2>
    <Draggable
      class="canvas"
      :list="store.projectModules"
      :group="{ name: 'modules', pull: false, put: true }"
      item-key="id"
      :sort="false"
      @add="handleAdd"
    >
      <template #item="{ element }">
        <div class="module-card">
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
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { VueDraggableNext as Draggable } from "vue-draggable-next";
import { useProjectStore } from "../stores/project";
import type { ProjectModule } from "../types";

const store = useProjectStore();

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
</script>

<style scoped>
.panel {
  background: white;
  padding: 16px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
.canvas {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.module-card {
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
.empty {
  padding: 20px;
  text-align: center;
  color: #94a3b8;
}
</style>
