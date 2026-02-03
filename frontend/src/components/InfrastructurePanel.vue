<template>
  <section class="panel">
    <div class="panel-header">
      <div>
        <h2>Инфраструктура</h2>
        <p class="hint">Выберите элементы инфраструктуры и укажите количество.</p>
      </div>
      <button class="primary" @click="save">Сохранить</button>
    </div>
    <div class="table-wrap">
      <div class="table">
        <div class="row header">
          <span>Элемент</span>
          <span>Описание</span>
          <span>Стоимость/ед.</span>
          <span>Кол-во</span>
          <span>Итого</span>
        </div>
        <div v-for="item in store.infrastructureCatalog" :key="item.id" class="row">
          <strong>{{ item.name }}</strong>
          <span class="muted">{{ item.description || "—" }}</span>
          <span>₽{{ formatNumber(item.unit_cost) }}</span>
          <input type="number" min="0" v-model.number="drafts[item.id]" />
          <span>₽{{ formatNumber(item.unit_cost * (drafts[item.id] ?? 0)) }}</span>
        </div>
      </div>
    </div>

    <div class="creator">
      <h3>Новый элемент</h3>
      <div class="creator-grid">
        <label>
          Название
          <input v-model="newItem.name" placeholder="Например: Kubernetes кластер" />
        </label>
        <label>
          Код
          <input v-model="newItem.code" placeholder="autofill если пусто" />
        </label>
        <label class="wide">
          Описание
          <input v-model="newItem.description" placeholder="Кратко: состав/назначение" />
        </label>
        <label>
          Стоимость/ед.
          <input type="number" v-model.number="newItem.unit_cost" placeholder="₽" />
        </label>
      </div>
      <button class="ghost" @click="createItem">Добавить элемент</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useProjectStore } from "../stores/project";
import type { InfrastructureItem, ProjectInfrastructure } from "../types";

const store = useProjectStore();
const drafts = ref<Record<number, number>>({});
const newItem = ref({
  code: "",
  name: "",
  description: "",
  unit_cost: 0,
});

const existingMap = computed(() => {
  const map = new Map<number, ProjectInfrastructure>();
  store.projectInfrastructure.forEach((item) => {
    map.set(item.infrastructure_item_id, item);
  });
  return map;
});

watch(
  () => [store.infrastructureCatalog, store.projectInfrastructure],
  () => {
    const next: Record<number, number> = {};
    store.infrastructureCatalog.forEach((item) => {
      next[item.id] = existingMap.value.get(item.id)?.quantity ?? 0;
    });
    drafts.value = next;
  },
  { immediate: true, deep: true }
);

async function save() {
  const payload = store.infrastructureCatalog.map((item) => ({
    id: existingMap.value.get(item.id)?.id ?? 0,
    infrastructure_item_id: item.id,
    quantity: Math.max(0, Number(drafts.value[item.id] ?? 0)),
  }));
  await store.updateProjectInfrastructure(payload);
}

async function createItem() {
  if (!newItem.value.name.trim()) return;
  const code = newItem.value.code.trim() || slugify(newItem.value.name);
  await store.createInfrastructureItem({
    code,
    name: newItem.value.name.trim(),
    description: newItem.value.description.trim(),
    unit_cost: Number(newItem.value.unit_cost) || 0,
  });
  newItem.value = { code: "", name: "", description: "", unit_cost: 0 };
}

function formatNumber(value: number) {
  return Math.round(value).toLocaleString("ru-RU");
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
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.hint {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--muted);
}
.table-wrap {
  overflow-x: auto;
}
.table {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 680px;
}
.row {
  display: grid;
  grid-template-columns: 1.2fr 1.6fr 140px 100px 140px;
  gap: 8px;
  align-items: center;
  font-size: 13px;
}
.header {
  font-weight: 600;
}
.muted {
  color: var(--muted);
}
input {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
}
.primary {
  background: var(--accent);
  color: var(--accent-contrast);
  border: none;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
}
.creator {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}
.creator h3 {
  margin: 0 0 8px;
  font-size: 14px;
}
.creator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
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
.ghost {
  margin-top: 10px;
  background: transparent;
  border: 1px dashed var(--border);
  color: var(--accent);
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
}
</style>
