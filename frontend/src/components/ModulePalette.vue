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
      <div class="creator-grid">
        <input v-model="draft.name" placeholder="Название" />
        <input v-model="draft.code" placeholder="Код (optional)" />
        <input v-model="draft.description" placeholder="Описание" />
        <input type="number" v-model.number="draft.hours_frontend" placeholder="FE часы" />
        <input type="number" v-model.number="draft.hours_backend" placeholder="BE часы" />
        <input type="number" v-model.number="draft.hours_qa" placeholder="QA часы" />
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
  background: white;
  padding: 16px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
.hint {
  margin-top: 0;
  color: #64748b;
  font-size: 14px;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.card strong {
  font-size: 14px;
}
.card span {
  font-size: 12px;
  color: #64748b;
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
.creator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
}
.creator-grid input {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.primary {
  margin-top: 10px;
  background: #2563eb;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
}
</style>
