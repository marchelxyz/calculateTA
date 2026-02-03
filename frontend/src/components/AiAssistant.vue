<template>
  <section class="panel">
    <h2>AI ассистент</h2>
    <p class="hint">
      AI разбивает описание продукта на WBS-задачи и сопоставляет их с модулями.
      Нажмите «Добавить модули», чтобы быстро заполнить холст.
    </p>
    <textarea
      v-model="prompt"
      placeholder="Опишите проект одним предложением..."
    ></textarea>
    <div class="actions">
      <button class="primary" @click="runAi">Разобрать задачи</button>
      <button class="ghost" @click="addSuggested" :disabled="!canAdd">
        Добавить модули
      </button>
    </div>
    <div v-if="store.aiResult" class="results">
      <p class="rationale">{{ store.aiResult.rationale }}</p>
      <div class="section">
        <h3>WBS декомпозиция</h3>
        <div v-if="store.aiResult.tasks.length === 0" class="empty">
          AI не предложил задач.
        </div>
        <div v-for="task in store.aiResult.tasks" :key="task.title" class="item">
          <strong>{{ task.title }}</strong>
          <span>{{ moduleName(task.module_code) }}</span>
          <small>{{ task.details }}</small>
          <small>confidence: {{ task.confidence.toFixed(2) }}</small>
        </div>
      </div>
      <div class="section">
        <h3>Список модулей</h3>
        <div v-if="store.aiResult.suggestions.length === 0" class="empty">
          AI не предложил модулей.
        </div>
        <div
          v-for="item in store.aiResult.suggestions"
          :key="item.module_code"
          class="item"
        >
          <strong>{{ moduleName(item.module_code) }}</strong>
          <span>{{ item.module_code }}</span>
          <small>confidence: {{ item.confidence.toFixed(2) }}</small>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useProjectStore } from "../stores/project";

const store = useProjectStore();
const prompt = ref("");

const moduleCodeMap = computed(() => {
  const map = new Map<string, number>();
  store.modules.forEach((module) => {
    map.set(module.code, module.id);
  });
  return map;
});

const canAdd = computed(() => {
  if (!store.aiResult) return false;
  return store.aiResult.tasks.length > 0 || store.aiResult.suggestions.length > 0;
});

function moduleName(code: string) {
  const module = store.modules.find((item) => item.code === code);
  return module?.name ?? "Неизвестный модуль";
}

async function runAi() {
  if (!prompt.value.trim()) return;
  await store.parseAi(prompt.value);
}

async function addSuggested() {
  if (!store.aiResult) return;
  const moduleCodes = new Set<string>();
  store.aiResult.tasks.forEach((task) => {
    if (task.module_code) moduleCodes.add(task.module_code);
  });
  store.aiResult.suggestions.forEach((suggestion) => {
    if (suggestion.module_code) moduleCodes.add(suggestion.module_code);
  });
  for (const code of moduleCodes) {
    const moduleId = moduleCodeMap.value.get(code);
    if (moduleId) {
      await store.addModule(moduleId);
    }
  }
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
  margin: 0 0 10px;
  font-size: 12px;
  color: var(--muted);
}
textarea {
  width: 100%;
  min-height: 100px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
  padding: 10px;
  resize: vertical;
}
.actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}
.primary {
  background: var(--accent);
  color: var(--accent-contrast);
  border: none;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
}
.ghost {
  background: transparent;
  border: 1px solid var(--border);
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  color: var(--text);
}
.results {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.section h3 {
  margin: 0 0 6px;
  font-size: 13px;
  color: #0f172a;
}
.item {
  background: var(--card-bg);
  padding: 8px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
}
.rationale {
  font-size: 12px;
  color: var(--muted);
}
.empty {
  font-size: 12px;
  color: var(--muted-2);
}
</style>
