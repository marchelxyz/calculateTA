<template>
  <div class="app">
    <AuthGate v-if="!ready || !store.currentUser" @authenticated="onAuthenticated" />
    <template v-else>
      <header class="header">
        <div class="header-top">
          <div>
            <h1>Центр управления полетами</h1>
            <p>Интерактивный конструктор проекта с пересчетом денег и времени.</p>
          </div>
          <div class="header-actions">
            <select v-model.number="selectedProjectId" @change="changeProject">
              <option v-for="project in store.projects" :key="project.id" :value="project.id">
                {{ project.name }}
              </option>
            </select>
            <button class="ghost" @click="createProject">Новый проект</button>
            <button class="ghost" @click="logout">Выйти</button>
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
        <button
          v-if="isAdmin"
          :class="{ active: activeTab === 'admin' }"
          @click="activeTab = 'admin'"
        >
          Админ
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
      <InfrastructurePanel v-else-if="activeTab === 'infra'" />
      <AdminPanel v-else />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useProjectStore } from "./stores/project";
import AdminPanel from "./components/AdminPanel.vue";
import AuthGate from "./components/AuthGate.vue";
import ModulePalette from "./components/ModulePalette.vue";
import ProjectCanvas from "./components/ProjectCanvas.vue";
import SlidersPanel from "./components/SlidersPanel.vue";
import RatesPanel from "./components/RatesPanel.vue";
import SummaryPanel from "./components/SummaryPanel.vue";
import AiAssistant from "./components/AiAssistant.vue";
import InfrastructurePanel from "./components/InfrastructurePanel.vue";
import MainDashboard from "./components/MainDashboard.vue";

const store = useProjectStore();
const activeTab = ref<"main" | "work" | "infra" | "admin">("main");
const ready = ref(false);
const selectedProjectId = ref<number | null>(null);
const isAdmin = computed(() => store.currentUser?.role === "admin");

onMounted(() => {
  init();
});

async function init() {
  const username = localStorage.getItem("auth_username");
  const password = localStorage.getItem("auth_password");
  if (username && password) {
    try {
      await store.checkAuth();
      await store.bootstrap();
      selectedProjectId.value = store.activeProjectId;
    } catch {
      await store.logout();
    }
  }
  ready.value = true;
}

async function onAuthenticated() {
  await store.bootstrap();
  selectedProjectId.value = store.activeProjectId;
}

async function changeProject() {
  if (!selectedProjectId.value) return;
  await store.setActiveProject(selectedProjectId.value);
}

async function createProject() {
  const name = window.prompt("Название проекта");
  if (!name) return;
  const project = await store.createProject(name);
  selectedProjectId.value = project.id;
  await store.setActiveProject(project.id);
}

async function logout() {
  await store.logout();
  ready.value = false;
  await init();
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
.header {
  margin-bottom: 24px;
}
.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-actions select {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
}
.ghost {
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text);
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
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
