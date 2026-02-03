<template>
  <div class="app">
    <header class="header">
      <div class="header-top">
        <div>
          <h1>Центр управления полетами</h1>
          <p>Интерактивный конструктор проекта с пересчетом денег и времени.</p>
        </div>
      </div>
    </header>
    <nav class="tabs">
      <button :class="{ active: activeTab === 'main' }" @click="activeTab = 'main'">
        Главная
      </button>
      <button :class="{ active: activeTab === 'work' }" @click="activeTab = 'work'">
        Работы
      </button>
      <button :class="{ active: activeTab === 'infra' }" @click="activeTab = 'infra'">
        Инфраструктура
      </button>
    </nav>
    <MainDashboard v-if="activeTab === 'main'" />
    <div v-else-if="activeTab === 'work'" class="main">
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
    <InfrastructurePanel v-else />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useProjectStore } from "./stores/project";
import ModulePalette from "./components/ModulePalette.vue";
import ProjectCanvas from "./components/ProjectCanvas.vue";
import SlidersPanel from "./components/SlidersPanel.vue";
import RatesPanel from "./components/RatesPanel.vue";
import SummaryPanel from "./components/SummaryPanel.vue";
import AiAssistant from "./components/AiAssistant.vue";
import InfrastructurePanel from "./components/InfrastructurePanel.vue";
import MainDashboard from "./components/MainDashboard.vue";

const store = useProjectStore();
const activeTab = ref<"main" | "work" | "infra">("main");

onMounted(() => {
  store.bootstrap();
});
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
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.tabs button {
  border: 1px solid var(--border);
  background: var(--panel-bg);
  color: var(--text);
  padding: 6px 12px;
  border-radius: 10px;
  cursor: pointer;
}
.tabs button.active {
  background: var(--accent);
  color: var(--accent-contrast);
  border-color: var(--accent);
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
