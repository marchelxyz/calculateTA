<template>
  <section class="panel">
    <h2>Палитра модулей</h2>
    <p class="hint">Перетаскивайте кубики на холст или добавляйте по клику.</p>
    <Draggable
      class="list"
      :list="store.modules"
      :group="{ name: 'modules', pull: 'clone', put: false }"
      :clone="cloneModule"
      item-key="id"
    >
      <template #item="{ element }">
        <div class="card" @click="store.addModule(element.id)">
          <strong>{{ element.name }}</strong>
          <span>{{ element.description }}</span>
        </div>
      </template>
    </Draggable>
    <div class="creator">
      <h3>Новый модуль</h3>
      <p class="creator-hint">
        Часы — это базовая оценка трудозатрат по ролям (FE/BE/QA).
        Эти значения участвуют в расчете стоимости и сроков.
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
      </div>
      <button class="primary" @click="createModule">Добавить модуль</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { VueDraggableNext as Draggable } from "vue-draggable-next";
import { useProjectStore } from "../stores/project";
import type { Module } from "../types";

const store = useProjectStore();
const draft = ref({
  code: "",
  name: "",
  description: "",
  hours_frontend: 0,
  hours_backend: 0,
  hours_qa: 0,
});

function cloneModule(module: Module) {
  return module;
}

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
  });
  draft.value = {
    code: "",
    name: "",
    description: "",
    hours_frontend: 0,
    hours_backend: 0,
    hours_qa: 0,
  };
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9а-яё]+/gi, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 32);
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
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  background: var(--card-bg);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.card strong {
  font-size: 14px;
}
.card span {
  font-size: 12px;
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
