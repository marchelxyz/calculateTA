<template>
  <section class="panel">
    <h2>Палитра модулей</h2>
    <p class="hint">Перетаскивайте кубики на холст или добавляйте по клику.</p>
    <Draggable
      class="list"
      :list="store.modules"
      :group="{ name: 'modules', pull: 'clone', put: false }"
      :clone="cloneModule"
      item-key="id"
    >
      <template #item="{ element }">
        <div class="card" @click="store.addModule(element.id)">
          <strong>{{ element.name }}</strong>
          <span>{{ element.description }}</span>
        </div>
      </template>
    </Draggable>
  </section>
</template>

<script setup lang="ts">
import { VueDraggableNext as Draggable } from "vue-draggable-next";
import { useProjectStore } from "../stores/project";
import type { Module } from "../types";

const store = useProjectStore();

function cloneModule(module: Module) {
  return module;
}
</script>

<style scoped>
.panel {
  background: white;
  padding: 16px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}
.hint {
  margin-top: 0;
  color: #64748b;
  font-size: 14px;
}
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.card {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.card strong {
  font-size: 14px;
}
.card span {
  font-size: 12px;
  color: #64748b;
}
</style>
