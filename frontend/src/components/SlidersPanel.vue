<template>
  <section class="panel">
    <h2>Слайдеры сложности</h2>
    <div class="content">
      <div v-for="(item, index) in draft" :key="item.name + index" class="slider">
        <div class="slider-header">
          <strong>{{ item.name }}</strong>
          <span>x{{ item.multiplier.toFixed(2) }}</span>
        </div>
        <input
          type="range"
          min="0.5"
          max="3"
          step="0.05"
          v-model.number="item.multiplier"
        />
      </div>
      <button class="primary" @click="save">Сохранить коэффициенты</button>
    </div>
    <div class="creator">
      <h3>Новый коэффициент</h3>
      <div class="creator-grid">
        <label>
          Название
          <input v-model="newItem.name" placeholder="Например: Интеграции" />
        </label>
        <label>
          Множитель
          <input type="number" step="0.05" v-model.number="newItem.multiplier" />
        </label>
      </div>
      <button class="ghost" @click="add">Добавить ползунок</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useProjectStore } from "../stores/project";
import type { ProjectCoefficient } from "../types";

const store = useProjectStore();
const draft = ref<ProjectCoefficient[]>([]);
const newItem = ref({
  name: "",
  multiplier: 1,
});

watch(
  () => store.coefficients,
  (items) => {
    draft.value = items.map((item) => ({ ...item }));
  },
  { immediate: true }
);

function add() {
  if (!newItem.value.name.trim()) return;
  draft.value = [
    ...draft.value,
    {
      id: 0,
      project_id: store.project?.id ?? 0,
      name: newItem.value.name.trim(),
      multiplier: Number(newItem.value.multiplier) || 1,
    },
  ];
  newItem.value = { name: "", multiplier: 1 };
}

function save() {
  store.updateCoefficients(draft.value);
}
</script>

<style scoped>
.panel {
  background: var(--panel-bg);
  padding: 16px;
  border-radius: 16px;
  box-shadow: var(--panel-shadow);
}
.content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.slider {
  padding: 10px;
  border-radius: 12px;
  background: var(--card-bg);
}
.slider-header {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 6px;
}
input[type="range"] {
  width: 100%;
}
.primary {
  background: var(--accent);
  color: var(--accent-contrast);
  border: none;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
}
.creator {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}
.creator h3 {
  margin: 0 0 8px;
  font-size: 13px;
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
.creator-grid input {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
}
.ghost {
  margin-top: 8px;
  background: transparent;
  border: 1px dashed var(--border);
  color: var(--accent);
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
}
</style>
