<template>
  <div class="app" :class="{ dark: isDark }">
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
            <button class="ghost" @click="saveAndClear">Сохранить и очистить</button>
            <button class="ghost" @click="toggleTheme">
              {{ isDark ? "Светлая тема" : "Темная тема" }}
            </button>
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
        <button :class="{ active: activeTab === 'modules' }" @click="activeTab = 'modules'">
          Модули
        </button>
        <button :class="{ active: activeTab === 'team' }" @click="activeTab = 'team'">
          Команда
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
          </div>
          <ProjectCanvas />
          <SummaryPanel />
        </section>
      </div>
      <InfrastructurePanel v-else-if="activeTab === 'infra'" />
      <ModulesPanel v-else-if="activeTab === 'modules'" />
      <RatesPanel v-else-if="activeTab === 'team'" />
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
import ModulesPanel from "./components/ModulesPanel.vue";

const store = useProjectStore();
const activeTab = ref<"main" | "work" | "infra" | "modules" | "team" | "admin">("main");
const ready = ref(false);
const selectedProjectId = ref<number | null>(null);
const isAdmin = computed(() => store.currentUser?.role === "admin");
const isDark = ref(false);

onMounted(() => {
  init();
});

async function init() {
  isDark.value = localStorage.getItem("theme") === "dark";
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

async function saveAndClear() {
  await createProject();
}

async function logout() {
  await store.logout();
  ready.value = false;
  await init();
}

function toggleTheme() {
  isDark.value = !isDark.value;
  localStorage.setItem("theme", isDark.value ? "dark" : "light");
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
  --note-bg: #fde68a;
  --note-border: #f59e0b;
  --note-text: #111827;
  --note-action: #b45309;
  --chip-added-bg: #dcfce7;
  --chip-added-border: #22c55e;
  --chip-added-text: #15803d;
  --chip-changed-bg: #fef9c3;
  --chip-changed-border: #eab308;
  --chip-changed-text: #854d0e;
  --chip-removed-bg: #fee2e2;
  --chip-removed-border: #ef4444;
  --chip-removed-text: #991b1b;
}
.app.dark {
  --bg: #0b1120;
  --text: #e2e8f0;
  --panel-bg: #0f172a;
  --panel-shadow: 0 8px 24px rgba(15, 23, 42, 0.35);
  --border: #1e293b;
  --muted: #94a3b8;
  --muted-2: #64748b;
  --card-bg: #111827;
  --grid: #111827;
  --grid-line: #1e293b;
  --accent: #38bdf8;
  --accent-contrast: #0b1120;
  --danger: #f87171;
  --success: #22c55e;
  --warning: #f59e0b;
  --input-bg: #0b1220;
  --canvas-line: #94a3b8;
  --note-bg: #3f2f00;
  --note-border: #a16207;
  --note-text: #fde68a;
  --note-action: #fbbf24;
  --chip-added-bg: #064e3b;
  --chip-added-border: #22c55e;
  --chip-added-text: #a7f3d0;
  --chip-changed-bg: #3f2f00;
  --chip-changed-border: #eab308;
  --chip-changed-text: #fef08a;
  --chip-removed-bg: #450a0a;
  --chip-removed-border: #ef4444;
  --chip-removed-text: #fecaca;
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
  flex-wrap: wrap;
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
