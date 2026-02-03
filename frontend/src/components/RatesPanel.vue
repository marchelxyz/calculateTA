<template>
  <section class="panel">
    <h2>Матрица команды</h2>
    <div class="table">
      <div class="row header">
        <span>Роль</span>
        <span>Уровень</span>
        <span>Ставка ($/час)</span>
      </div>
      <div v-for="rate in editableRates" :key="rate.id" class="row">
        <span>{{ rate.role }}</span>
        <span>{{ rate.level }}</span>
        <input type="number" v-model.number="rate.hourly_rate" />
      </div>
    </div>
    <button class="primary" @click="saveRates">Сохранить ставки</button>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useProjectStore } from "../stores/project";
import type { Rate } from "../types";

const store = useProjectStore();
const editableRates = ref<Rate[]>([]);

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
    return !original || original.hourly_rate !== rate.hourly_rate;
  });
});

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
.table {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.row {
  display: grid;
  grid-template-columns: 1fr 1fr 120px;
  gap: 8px;
  align-items: center;
  font-size: 13px;
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
</style>
