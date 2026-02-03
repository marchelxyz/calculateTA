<template>
  <section class="panel">
    <h2>Вход</h2>
    <p class="hint">Введите логин и пароль для доступа к проектам.</p>
    <div class="form">
      <label>
        Логин
        <input v-model="username" />
      </label>
      <label>
        Пароль
        <input v-model="password" type="password" />
      </label>
    </div>
    <button class="primary" @click="login">Войти</button>
    <p v-if="error" class="error">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useProjectStore } from "../stores/project";

const emit = defineEmits<{ (event: "authenticated"): void }>();
const store = useProjectStore();
const username = ref("");
const password = ref("");
const error = ref("");

async function login() {
  error.value = "";
  if (!username.value.trim() || !password.value.trim()) {
    error.value = "Введите логин и пароль.";
    return;
  }
  localStorage.setItem("auth_username", username.value.trim());
  localStorage.setItem("auth_password", password.value);
  try {
    await store.checkAuth();
    emit("authenticated");
  } catch {
    localStorage.removeItem("auth_username");
    localStorage.removeItem("auth_password");
    error.value = "Неверные учетные данные.";
  }
}
</script>

<style scoped>
.panel {
  background: var(--panel-bg);
  padding: 16px;
  border-radius: 16px;
  box-shadow: var(--panel-shadow);
  max-width: 360px;
  margin: 80px auto;
}
.hint {
  font-size: 12px;
  color: var(--muted);
  margin: 0 0 12px;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}
label {
  font-size: 12px;
  color: var(--muted);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
input {
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--input-bg);
  color: var(--text);
}
.primary {
  background: var(--accent);
  color: var(--accent-contrast);
  border: none;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
}
.error {
  margin-top: 8px;
  font-size: 12px;
  color: var(--danger);
}
</style>
