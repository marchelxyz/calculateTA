<template>
  <section class="panel">
    <h2>Матрица команды</h2>
    <div class="table-wrap">
      <div class="table">
        <div class="row header">
          <span>Роль</span>
          <span>Уровень</span>
          <span>Ставка (₽/час)</span>
          <span></span>
        </div>
        <div v-for="rate in editableRates" :key="rateKey(rate)" class="row">
          <input v-model="rate.role" />
          <input v-model="rate.level" />
          <input type="number" v-model.number="rate.hourly_rate" />
          <button class="ghost danger" @click="removeRate(rate)">Удалить</button>
        </div>
        <div class="row add-row">
          <input v-model="newRate.role" placeholder="role" />
          <input v-model="newRate.level" placeholder="level" />
          <input type="number" v-model.number="newRate.hourly_rate" placeholder="₽/час" />
          <button class="ghost" @click="addRate">Добавить</button>
        </div>
      </div>
    </div>
    <button class="primary" @click="saveRates">Сохранить ставки</button>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useProjectStore } from "../stores/project";
import type { RateDraft } from "../types";

const store = useProjectStore();
const editableRates = ref<RateDraft[]>([]);
const newRate = ref<RateDraft>({
  role: "",
  level: "",
  hourly_rate: 0,
});

watch(
  () => store.rates,
  (rates) => {
    editableRates.value = rates.map((rate) => ({ ...rate }));
  },
  { immediate: true }
);

const hasChanges = computed(() => {
  if (editableRates.value.length !== store.rates.length) return true;
  return editableRates.value.some((rate) => {
    const original = store.rates.find((item) => item.id === rate.id);
    if (!original) return true;
    return (
      original.role !== rate.role ||
      original.level !== rate.level ||
      original.hourly_rate !== rate.hourly_rate
    );
  });
});

function addRate() {
  if (!newRate.value.role.trim() || !newRate.value.level.trim()) return;
  editableRates.value = [...editableRates.value, { ...newRate.value }];
  newRate.value = { role: "", level: "", hourly_rate: 0 };
}

function rateKey(rate: RateDraft) {
  if (rate.id) return `id-${rate.id}`;
  return `${rate.role}-${rate.level}`;
}

function removeRate(rate: RateDraft) {
  editableRates.value = editableRates.value.filter((item) => item !== rate);
}

function saveRates() {
  if (!hasChanges.value) return;
  store.updateRates(editableRates.value);
}
</script>

<style scoped>
.panel {
  background: white;
  padding: 16px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
.table-wrap {
  overflow-x: auto;
}
.table {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 560px;
}
.row {
  display: grid;
  grid-template-columns: 1fr 1fr 120px 110px;
  gap: 8px;
  align-items: center;
  font-size: 13px;
}
.add-row {
  grid-template-columns: 1fr 1fr 120px 120px;
}
.header {
  font-weight: 600;
  color: #0f172a;
}
input {
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
.ghost {
  background: transparent;
  border: 1px dashed #cbd5f5;
  color: #1d4ed8;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
}
.ghost.danger {
  border-style: solid;
  color: #ef4444;
}
</style>
