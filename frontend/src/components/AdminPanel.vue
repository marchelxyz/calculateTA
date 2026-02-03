<template>
  <section class="panel">
    <div class="panel-header">
      <div>
        <h2>Админ‑панель</h2>
        <p class="hint">Управление пользователями.</p>
      </div>
      <button class="ghost" @click="loadUsers">Обновить</button>
    </div>
    <div class="table-wrap">
      <div class="table">
        <div class="row header">
          <span>Логин</span>
          <span>Роль</span>
        </div>
        <div v-for="user in store.users" :key="user.id" class="row">
          <span>{{ user.username }}</span>
          <span>{{ user.role }}</span>
        </div>
      </div>
    </div>

    <div class="creator">
      <h3>Добавить пользователя</h3>
      <div class="creator-grid">
        <label>
          Логин
          <input v-model="draft.username" />
        </label>
        <label>
          Пароль
          <input v-model="draft.password" type="password" />
        </label>
        <label>
          Роль
          <select v-model="draft.role">
            <option value="participant">participant</option>
            <option value="admin">admin</option>
          </select>
        </label>
      </div>
      <button class="primary" @click="createUser">Создать</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useProjectStore } from "../stores/project";

const store = useProjectStore();
const draft = ref({
  username: "",
  password: "",
  role: "participant",
});

onMounted(() => {
  loadUsers();
});

async function loadUsers() {
  await store.loadUsers();
}

async function createUser() {
  if (!draft.value.username.trim() || !draft.value.password.trim()) return;
  await store.createUser({
    username: draft.value.username.trim(),
    password: draft.value.password,
    role: draft.value.role,
  });
  draft.value = { username: "", password: "", role: "participant" };
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
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.hint {
  font-size: 12px;
  color: var(--muted);
  margin: 4px 0 0;
}
.ghost {
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text);
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
}
.table-wrap {
  overflow-x: auto;
}
.table {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 320px;
}
.row {
  display: grid;
  grid-template-columns: 1fr 120px;
  gap: 8px;
  font-size: 13px;
}
.header {
  font-weight: 600;
}
.creator {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}
.creator-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px;
}
label {
  font-size: 12px;
  color: var(--muted);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
input,
select {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
}
.primary {
  margin-top: 8px;
  background: var(--accent);
  color: var(--accent-contrast);
  border: none;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
}
</style>
