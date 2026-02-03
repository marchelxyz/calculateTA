<template>
  <div class="app">
    <header class="header">
      <h1>Центр управления полетами</h1>
      <p>Интерактивный конструктор проекта с пересчетом денег и времени.</p>
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
import { onMounted } from "vue";
import { useProjectStore } from "./stores/project";
import ModulePalette from "./components/ModulePalette.vue";
import ProjectCanvas from "./components/ProjectCanvas.vue";
import SlidersPanel from "./components/SlidersPanel.vue";
import RatesPanel from "./components/RatesPanel.vue";
import SummaryPanel from "./components/SummaryPanel.vue";
import AiAssistant from "./components/AiAssistant.vue";

const store = useProjectStore();

onMounted(() => {
  store.bootstrap();
});
</script>

<style scoped>
.app {
  font-family: "Inter", system-ui, -apple-system, sans-serif;
  padding: 24px;
  color: #0f172a;
  background: #f8fafc;
  min-height: 100vh;
}
.header {
  margin-bottom: 24px;
}
.header h1 {
  margin: 0 0 4px;
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
