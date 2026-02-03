<template>
  <section class="panel">
    <h2>Итоги и сценарии</h2>
    <div v-if="store.summary" class="summary">
      <div class="totals">
        <div>
          <span>Frontend</span>
          <strong>{{ formatNumber(store.summary.totals.hours_frontend) }} ч</strong>
        </div>
        <div>
          <span>Backend</span>
          <strong>{{ formatNumber(store.summary.totals.hours_backend) }} ч</strong>
        </div>
        <div>
          <span>QA</span>
          <strong>{{ formatNumber(store.summary.totals.hours_qa) }} ч</strong>
        </div>
        <div>
          <span>Всего</span>
          <strong>{{ formatNumber(store.summary.totals.hours_total) }} ч</strong>
        </div>
        <div>
          <span>Стоимость</span>
          <strong>${{ formatNumber(store.summary.totals.cost_total) }}</strong>
        </div>
      </div>
      <ScenarioChart :scenarios="store.summary.scenarios" />
      <div class="scenario-list">
        <div v-for="scenario in store.summary.scenarios" :key="scenario.label" class="scenario">
          <strong>{{ scenario.label }}</strong>
          <span>{{ formatNumber(scenario.total_hours) }} ч</span>
          <span>${{ formatNumber(scenario.total_cost) }}</span>
        </div>
      </div>
    </div>
    <div v-else class="empty">Сценарии появятся после добавления модулей.</div>
  </section>
</template>

<script setup lang="ts">
import { useProjectStore } from "../stores/project";
import ScenarioChart from "./ScenarioChart.vue";

const store = useProjectStore();

function formatNumber(value: number) {
  return Math.round(value).toLocaleString("ru-RU");
}
</script>

<style scoped>
.panel {
  background: white;
  padding: 16px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
.summary {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.totals {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
}
.totals div {
  background: #f8fafc;
  padding: 10px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}
.scenario-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px;
}
.scenario {
  background: #f8fafc;
  padding: 10px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}
.empty {
  color: #94a3b8;
  font-size: 12px;
}
</style>
