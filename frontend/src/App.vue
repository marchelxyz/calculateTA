<template>
  <div class="app" :class="{ dark: isDark }">
    <header class="header">
      <div class="header-top">
        <div>
          <h1>Центр управления полетами</h1>
          <p>Интерактивный конструктор проекта с пересчетом денег и времени.</p>
        </div>
        <button class="theme-toggle" @click="toggleTheme">
          {{ isDark ? "Светлая тема" : "Темная тема" }}
        </button>
      </div>
    </header>
    <div class="main">
      <aside class="left">
        <ModulePalette />
        <AiAssistant />
      </aside>
      <section class="right">
        <div class="controls">
          <SlidersPanel />
          <RatesPanel />
        </div>
        <ProjectCanvas />
        <SummaryPanel />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useProjectStore } from "./stores/project";
import ModulePalette from "./components/ModulePalette.vue";
import ProjectCanvas from "./components/ProjectCanvas.vue";
import SlidersPanel from "./components/SlidersPanel.vue";
import RatesPanel from "./components/RatesPanel.vue";
import SummaryPanel from "./components/SummaryPanel.vue";
import AiAssistant from "./components/AiAssistant.vue";

const store = useProjectStore();
const isDark = ref(false);

onMounted(() => {
  loadTheme();
  store.bootstrap();
});

watch(isDark, (value) => {
  saveTheme(value);
});

function toggleTheme() {
  isDark.value = !isDark.value;
}

function loadTheme() {
  const stored = localStorage.getItem("theme");
  isDark.value = stored === "dark";
}

function saveTheme(value: boolean) {
  localStorage.setItem("theme", value ? "dark" : "light");
}
</script>

<style scoped>
.app {
  font-family: "Inter", system-ui, -apple-system, sans-serif;
  padding: 24px;
  color: var(--text);
  background: var(--bg);
  min-height: 100vh;
  --bg: #f8fafc;
  --text: #0f172a;
  --panel-bg: #ffffff;
  --panel-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
  --border: #e2e8f0;
  --muted: #64748b;
  --muted-2: #94a3b8;
  --card-bg: #f8fafc;
  --grid: #eef2ff;
  --grid-line: #cbd5f5;
  --accent: #2563eb;
  --accent-contrast: #ffffff;
  --danger: #ef4444;
  --success: #22c55e;
  --warning: #f59e0b;
  --input-bg: #ffffff;
  --canvas-line: #94a3b8;
}
.app.dark {
  --bg: #0b1120;
  --text: #e2e8f0;
  --panel-bg: #111827;
  --panel-shadow: 0 8px 24px rgba(2, 6, 23, 0.6);
  --border: #1f2937;
  --muted: #9ca3af;
  --muted-2: #6b7280;
  --card-bg: #0f172a;
  --grid: #111827;
  --grid-line: #1f2937;
  --accent: #60a5fa;
  --accent-contrast: #0b1120;
  --danger: #f87171;
  --success: #34d399;
  --warning: #fbbf24;
  --input-bg: #0b1220;
  --canvas-line: #64748b;
}
.header {
  margin-bottom: 24px;
}
.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.header h1 {
  margin: 0 0 4px;
}
.header p {
  color: var(--muted);
}
.theme-toggle {
  border: 1px solid var(--border);
  background: var(--panel-bg);
  color: var(--text);
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
}
.main {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 20px;
}
.left,
.right {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.controls {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}
</style>
