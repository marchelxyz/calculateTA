<template>
  <section class="panel">
    <h2>Слайдеры сложности</h2>
    <div v-if="store.project" class="content">
      <label>
        Уровень неопределенности
        <select :value="store.project.uncertainty_level" @change="updateUncertainty">
          <option value="known">Делали 100 раз (x1.0)</option>
          <option value="new_tech">Новая технология (x1.5)</option>
        </select>
      </label>
      <label>
        Требования к UI/UX
        <select :value="store.project.uiux_level" @change="updateUiux">
          <option value="mvp">MVP / Bootstrap (x1.0)</option>
          <option value="award">Award Winning (x2.5 к фронтенду)</option>
        </select>
      </label>
      <label class="checkbox">
        <input
          type="checkbox"
          :checked="store.project.legacy_code"
          @change="updateLegacy"
        />
        Legacy Code (+30%)
      </label>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useProjectStore } from "../stores/project";

const store = useProjectStore();

function updateUncertainty(event: Event) {
  const uncertainty_level = (event.target as HTMLSelectElement).value;
  if (!store.project) return;
  store.updateSettings({
    uncertainty_level,
    uiux_level: store.project.uiux_level,
    legacy_code: store.project.legacy_code,
  });
}

function updateUiux(event: Event) {
  const uiux_level = (event.target as HTMLSelectElement).value;
  if (!store.project) return;
  store.updateSettings({
    uncertainty_level: store.project.uncertainty_level,
    uiux_level,
    legacy_code: store.project.legacy_code,
  });
}

function updateLegacy(event: Event) {
  const legacy_code = (event.target as HTMLInputElement).checked;
  if (!store.project) return;
  store.updateSettings({
    uncertainty_level: store.project.uncertainty_level,
    uiux_level: store.project.uiux_level,
    legacy_code,
  });
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
label {
  font-size: 12px;
  color: var(--muted);
  display: flex;
  flex-direction: column;
  gap: 6px;
}
select {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
}
.checkbox {
  flex-direction: row;
  align-items: center;
  gap: 6px;
}
</style>
