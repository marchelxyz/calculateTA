<template>
  <canvas ref="canvas"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import {
  Chart,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
} from "chart.js";

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

type Props = {
  workCost: number;
  infraCost: number;
};

const props = defineProps<Props>();
const canvas = ref<HTMLCanvasElement | null>(null);
let chart: Chart | null = null;

function buildChart() {
  if (!canvas.value) return;
  const labels = ["Работы", "Инфраструктура"];
  const data = [props.workCost, props.infraCost];
  const colors = ["#60a5fa", "#f59e0b"];
  chart = new Chart(canvas.value, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: colors,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });
}

function rebuildChart() {
  if (chart) {
    chart.destroy();
    chart = null;
  }
  buildChart();
}

onMounted(() => {
  buildChart();
});

onUnmounted(() => {
  if (chart) {
    chart.destroy();
  }
});

watch(
  () => [props.workCost, props.infraCost],
  () => {
    rebuildChart();
  }
);
</script>
