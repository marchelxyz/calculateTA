<template>
  <section class="panel">
    <div class="panel-header">
      <div>
        <h2>Главная</h2>
        <p class="hint">Сводная таблица по работам и инфраструктуре.</p>
      </div>
      <div class="actions">
        <button class="ghost" @click="store.downloadExportCsv">Скачать CSV</button>
        <button class="ghost" @click="store.downloadExportPdf">Скачать PDF</button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr class="section">
            <th colspan="6">Работы</th>
          </tr>
          <tr>
            <th>Модуль</th>
            <th>Роль</th>
            <th>Уровень</th>
            <th>Часы</th>
            <th>Ставка</th>
            <th>Стоимость</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in workRows" :key="row.key">
            <td>{{ row.moduleName }}</td>
            <td>{{ row.roleLabel }}</td>
            <td>{{ row.levelLabel }}</td>
            <td>{{ formatNumber(row.hours) }}</td>
            <td>₽{{ formatNumber(row.rate) }}</td>
            <td>₽{{ formatNumber(row.cost) }}</td>
          </tr>
          <tr v-if="workRows.length === 0">
            <td colspan="6" class="empty">Нет данных по работам.</td>
          </tr>
          <tr class="total">
            <td colspan="5">Итого по работам</td>
            <td>₽{{ formatNumber(workTotalCost) }}</td>
          </tr>
        </tbody>
        <thead>
          <tr class="section">
            <th colspan="6">Инфраструктура</th>
          </tr>
          <tr>
            <th>Элемент</th>
            <th>Количество</th>
            <th>Стоимость/ед.</th>
            <th>Итого</th>
            <th colspan="2"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in infraRows" :key="row.id">
            <td>{{ row.name }}</td>
            <td>{{ row.quantity }}</td>
            <td>₽{{ formatNumber(row.unitCost) }}</td>
            <td>₽{{ formatNumber(row.totalCost) }}</td>
            <td colspan="2"></td>
          </tr>
          <tr v-if="infraRows.length === 0">
            <td colspan="6" class="empty">Нет данных по инфраструктуре.</td>
          </tr>
          <tr class="total">
            <td colspan="3">Итого по инфраструктуре</td>
            <td>₽{{ formatNumber(infraTotalCost) }}</td>
            <td colspan="2"></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="charts">
      <div class="chart-card">
        <h3>Сценарии стоимости</h3>
        <ScenarioChart v-if="store.summary" :scenarios="store.summary.scenarios" />
        <p v-else class="empty">Добавьте модули и инфраструктуру.</p>
      </div>
      <div class="chart-card">
        <h3>Работы vs Инфраструктура</h3>
        <CostSplitChart :work-cost="workTotalCost" :infra-cost="infraTotalCost" />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useProjectStore } from "../stores/project";
import ScenarioChart from "./ScenarioChart.vue";
import CostSplitChart from "./CostSplitChart.vue";

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

const assignmentMap = computed(() => {
  const map = new Map<string, string>();
  store.assignments.forEach((assignment) => {
    map.set(`${assignment.project_module_id}:${assignment.role}`, assignment.level);
  });
  return map;
});

const rateMap = computed(() => {
  const map = new Map<string, number>();
  store.rates.forEach((rate) => {
    map.set(`${rate.role}:${rate.level}`, rate.hourly_rate);
  });
  return map;
});

const infraCatalogMap = computed(() => {
  const map = new Map<number, { name: string; unit_cost: number }>();
  store.infrastructureCatalog.forEach((item) => {
    map.set(item.id, { name: item.name, unit_cost: item.unit_cost });
  });
  return map;
});

const workRows = computed(() => {
  if (!store.project) return [];
  const rows: Array<{
    key: string;
    moduleName: string;
    roleLabel: string;
    levelLabel: string;
    hours: number;
    rate: number;
    cost: number;
  }> = [];
  store.projectModules.forEach((projectModule) => {
    const base = moduleMap.value.get(projectModule.module_id);
    if (!base) return;
    const merged = mergeOverrides(base, projectModule);
    const adjusted = applyCoefficients(store.project!, projectModule, merged);
    const roleHours = {
      frontend: adjusted.frontend,
      backend: adjusted.backend,
      qa: adjusted.qa,
    };
    Object.entries(roleHours).forEach(([role, hours]) => {
      const level = resolveLevel(projectModule.id, role);
      const rate = rateMap.value.get(`${role}:${level}`) ?? 0;
      rows.push({
        key: `${projectModule.id}-${role}`,
        moduleName: base.name,
        roleLabel: role.toUpperCase(),
        levelLabel: level,
        hours,
        rate,
        cost: hours * rate,
      });
    });
  });
  return rows;
});

const infraRows = computed(() => {
  return store.projectInfrastructure.map((item) => {
    const catalog = infraCatalogMap.value.get(item.infrastructure_item_id);
    const unitCost = catalog?.unit_cost ?? 0;
    return {
      id: item.id,
      name: catalog?.name ?? "Инфраструктура",
      quantity: item.quantity,
      unitCost,
      totalCost: unitCost * item.quantity,
    };
  });
});

const workTotalCost = computed(() =>
  workRows.value.reduce((sum, row) => sum + row.cost, 0)
);

const infraTotalCost = computed(() =>
  infraRows.value.reduce((sum, row) => sum + row.totalCost, 0)
);

function resolveLevel(projectModuleId: number, role: string) {
  const key = `${projectModuleId}:${role}`;
  const assigned = assignmentMap.value.get(key);
  if (assigned) return assigned;
  if (role === "backend") return "senior";
  return "middle";
}

function mergeOverrides(
  base: { hours_frontend: number; hours_backend: number; hours_qa: number },
  module: { override_frontend: number | null; override_backend: number | null; override_qa: number | null }
) {
  return {
    frontend: module.override_frontend ?? base.hours_frontend,
    backend: module.override_backend ?? base.hours_backend,
    qa: module.override_qa ?? base.hours_qa,
  };
}

function applyCoefficients(
  project: { uncertainty_level: string; uiux_level: string; legacy_code: boolean },
  module: { uncertainty_level: string | null; uiux_level: string | null; legacy_code: boolean | null },
  hours: { frontend: number; backend: number; qa: number }
) {
  const uncertainty = module.uncertainty_level ?? project.uncertainty_level;
  const uiux = module.uiux_level ?? project.uiux_level;
  const legacy = module.legacy_code ?? project.legacy_code;

  const uncertaintyCoeff = uncertainty === "new_tech" ? 1.5 : 1.0;
  const uiuxCoeff = uiux === "award" ? 2.5 : 1.0;
  const legacyCoeff = legacy ? 1.3 : 1.0;

  return {
    frontend: hours.frontend * uncertaintyCoeff * uiuxCoeff * legacyCoeff,
    backend: hours.backend * uncertaintyCoeff * legacyCoeff,
    qa: hours.qa * uncertaintyCoeff * legacyCoeff,
  };
}

function formatNumber(value: number) {
  return Math.round(value).toLocaleString("ru-RU");
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
.actions {
  display: flex;
  gap: 8px;
}
.ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
}
.table-wrap {
  overflow-x: auto;
}
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  min-width: 760px;
}
th,
td {
  padding: 8px;
  border-bottom: 1px solid var(--border);
  text-align: left;
}
thead tr.section th {
  background: var(--card-bg);
  color: var(--text);
  font-weight: 600;
}
.total td {
  font-weight: 600;
}
.empty {
  text-align: center;
  color: var(--muted-2);
}
.charts {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}
.chart-card {
  background: var(--card-bg);
  padding: 12px;
  border-radius: 12px;
}
.chart-card h3 {
  margin: 0 0 8px;
  font-size: 13px;
}
</style>
