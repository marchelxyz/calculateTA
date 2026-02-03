<template>
  <canvas ref="canvas"></canvas>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from "chart.js";
import type { SummaryScenario } from "../types";

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

type Props = {
  scenarios: SummaryScenario[];
};

const props = defineProps<Props>();
const canvas = ref<HTMLCanvasElement | null>(null);
let chart: Chart | null = null;

function buildChart() {
  if (!canvas.value) return;
  const labels = props.scenarios.map((item) => item.label);
  const data = props.scenarios.map((item) => item.total_cost);
  const colors = ["#22c55e", "#f59e0b", "#ef4444"];

  chart = new Chart(canvas.value, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Стоимость",
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
  () => props.scenarios,
  () => {
    rebuildChart();
  }
);
</script>
