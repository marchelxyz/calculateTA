<template>
  <section class="panel">
    <h2>Каталог модулей</h2>
    <p class="hint">
      Модули общие для всех проектов — добавляйте и обновляйте их здесь.
    </p>
    <input v-model="search" class="search" placeholder="Поиск по модулям" type="search" />
    <div class="list">
      <div v-for="module in filteredModules" :key="module.id" class="card">
        <div class="card-body">
          <label>
            Название
            <input v-model="drafts[module.id].name" />
          </label>
          <label>
            Описание
            <input v-model="drafts[module.id].description" />
          </label>
        <div class="hours">
            <label>
              FE
              <input type="number" v-model.number="drafts[module.id].hours_frontend" />
            </label>
            <label>
              BE
              <input type="number" v-model.number="drafts[module.id].hours_backend" />
            </label>
            <label>
              QA
              <input type="number" v-model.number="drafts[module.id].hours_qa" />
            </label>
          <label v-for="role in extraRoles" :key="`${module.id}-${role}`">
            {{ role }}
            <input type="number" v-model.number="drafts[module.id].role_hours[role]" />
          </label>
          </div>
        </div>
        <div class="card-actions">
          <button class="ghost" @click="saveModule(module.id)">Сохранить</button>
          <button class="danger" @click="removeModule(module.id)">Удалить</button>
        </div>
      </div>
      <div v-if="!filteredModules.length" class="empty">Модули не найдены.</div>
    </div>
    <div class="creator">
      <h3>Новый модуль</h3>
      <p class="creator-hint">
        Часы — это базовая оценка трудозатрат по ролям и основа сметы.
      </p>
      <div class="creator-grid">
        <label>
          Название
          <input v-model="draft.name" placeholder="Например: Личный кабинет" />
        </label>
        <label>
          Код
          <input v-model="draft.code" placeholder="autofill если пусто" />
        </label>
        <label class="wide">
          Описание
          <input v-model="draft.description" placeholder="Кратко: что входит" />
        </label>
        <label>
          FE часы
          <input type="number" v-model.number="draft.hours_frontend" placeholder="8" />
        </label>
        <label>
          BE часы
          <input type="number" v-model.number="draft.hours_backend" placeholder="12" />
        </label>
        <label>
          QA часы
          <input type="number" v-model.number="draft.hours_qa" placeholder="4" />
        </label>
        <label v-for="role in extraRoles" :key="role">
          {{ role }} часы
          <input type="number" v-model.number="extraRoleHours[role]" placeholder="0" />
        </label>
      </div>
      <button class="primary" @click="createModule">Добавить модуль</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useProjectStore } from "../stores/project";

const store = useProjectStore();
const search = ref("");
const drafts = reactive<Record<number, {
  name: string;
  description: string;
  hours_frontend: number;
  hours_backend: number;
  hours_qa: number;
  role_hours: Record<string, number>;
}>>({});
const draft = ref({
  code: "",
  name: "",
  description: "",
  hours_frontend: 0,
  hours_backend: 0,
  hours_qa: 0,
});
const extraRoleHours = ref<Record<string, number>>({});

const filteredModules = computed(() => {
  const query = search.value.trim().toLowerCase();
  if (!query) return store.modules;
  return store.modules.filter((module) =>
    [module.name, module.code, module.description]
      .join(" ")
      .toLowerCase()
      .includes(query)
  );
});

watch(
  () => store.modules,
  (modules) => {
    modules.forEach((module) => {
      drafts[module.id] = {
        name: module.name,
        description: module.description,
        hours_frontend: module.hours_frontend,
        hours_backend: module.hours_backend,
        hours_qa: module.hours_qa,
        role_hours: buildRoleHoursDraft(module.role_hours),
      };
    });
  },
  { immediate: true }
);

watch(
  () => extraRoles.value,
  (roles) => {
    store.modules.forEach((module) => {
      const draft = drafts[module.id];
      if (!draft) return;
      roles.forEach((role) => {
        if (draft.role_hours[role] === undefined) {
          draft.role_hours[role] = 0;
        }
      });
    });
  },
  { immediate: true }
);

const extraRoles = computed(() => {
  const base = new Set(["фронтенд", "бекенд", "тестировщик", "qa", "backend", "frontend"]);
  const roles = new Set(
    store.rates.map((rate) => rate.role).filter((role) => role)
  );
  return Array.from(roles).filter((role) => !base.has(role.toLowerCase()));
});

async function createModule() {
  if (!draft.value.name.trim()) return;
  const code = draft.value.code.trim() || slugify(draft.value.name);
  await store.createModule({
    code,
    name: draft.value.name.trim(),
    description: draft.value.description.trim(),
    hours_frontend: Number(draft.value.hours_frontend) || 0,
    hours_backend: Number(draft.value.hours_backend) || 0,
    hours_qa: Number(draft.value.hours_qa) || 0,
    role_hours: extraRoles.value
      .map((role) => ({
        role,
        hours: Number(extraRoleHours.value[role]) || 0,
      }))
      .filter((item) => item.hours > 0),
  });
  draft.value = {
    code: "",
    name: "",
    description: "",
    hours_frontend: 0,
    hours_backend: 0,
    hours_qa: 0,
  };
  extraRoleHours.value = {};
}

async function removeModule(moduleId: number) {
  try {
    await store.deleteModule(moduleId);
  } catch (error) {
    console.error(error);
    alert("Нельзя удалить модуль, который используется в проектах.");
  }
}

async function saveModule(moduleId: number) {
  const draft = drafts[moduleId];
  if (!draft) return;
  await store.updateModule(moduleId, {
    name: draft.name.trim(),
    description: draft.description.trim(),
    hours_frontend: Number(draft.hours_frontend) || 0,
    hours_backend: Number(draft.hours_backend) || 0,
    hours_qa: Number(draft.hours_qa) || 0,
    role_hours: buildRoleHoursPayload(draft.role_hours),
  });
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9а-яё]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 32);
}

function buildRoleHoursDraft(
  roleHours: Array<{ role: string; hours: number }> | undefined
) {
  const draft: Record<string, number> = {};
  if (!roleHours) return draft;
  roleHours.forEach((item) => {
    draft[item.role] = item.hours;
  });
  return draft;
}

function buildRoleHoursPayload(roleHours: Record<string, number>) {
  return Object.entries(roleHours)
    .map(([role, hours]) => ({
      role,
      hours: Number(hours) || 0,
    }))
    .filter((item) => item.hours > 0);
}
</script>

<style scoped>
.panel {
  background: var(--panel-bg);
  padding: 16px;
  border-radius: 16px;
  box-shadow: var(--panel-shadow);
}
.hint {
  margin-top: 0;
  color: var(--muted);
  font-size: 14px;
}
.search {
  width: 100%;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
  margin: 8px 0 12px;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--card-bg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}
.card-body label {
  font-size: 12px;
  color: var(--muted);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.card-body input {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
}
.hours {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 8px;
}
.card-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 6px 10px;
  border-radius: 10px;
  cursor: pointer;
}
.danger {
  background: #ef4444;
  color: #fff;
  border: none;
  padding: 6px 10px;
  border-radius: 10px;
  cursor: pointer;
}
.empty {
  font-size: 13px;
  color: var(--muted);
}
.creator {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #e2e8f0;
}
.creator h3 {
  margin: 0 0 8px;
  font-size: 14px;
}
.creator-hint {
  margin: 0 0 10px;
  font-size: 12px;
  color: var(--muted);
}
.creator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
}
.creator-grid label {
  font-size: 12px;
  color: var(--muted);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.creator-grid .wide {
  grid-column: span 2;
}
.creator-grid input {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
}
.primary {
  margin-top: 10px;
  background: var(--accent);
  color: var(--accent-contrast);
  border: none;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
}
</style>
