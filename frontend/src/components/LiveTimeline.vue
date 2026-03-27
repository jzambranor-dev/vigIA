<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js'
import { onWsMessage } from '../services/websocket'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const MAX_POINTS = 30
const bucketSeconds = 10

let currentBucketEvents = 0
let currentBucketAnomalies = 0

// Datos NO reactivos (raw arrays) para evitar stack overflow
const rawLabels = []
const rawEvents = []
const rawAnomalies = []
for (let i = 0; i < MAX_POINTS; i++) {
  rawLabels.push('')
  rawEvents.push(0)
  rawAnomalies.push(0)
}

// chartData reactivo que se reemplaza completo cada tick
const chartData = ref(buildChartData())

function buildChartData() {
  return {
    labels: [...rawLabels],
    datasets: [
      {
        label: 'Eventos / 10s',
        data: [...rawEvents],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
      },
      {
        label: 'Anomalias / 10s',
        data: [...rawAnomalies],
        borderColor: '#e94560',
        backgroundColor: 'rgba(233, 69, 96, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
      },
    ],
  }
}

const unsub = onWsMessage('event', (data) => {
  currentBucketEvents++
  if (data.is_anomaly) currentBucketAnomalies++
})

let interval = null
onMounted(() => {
  interval = setInterval(() => {
    const now = new Date()
    const label = now.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

    rawLabels.push(label)
    rawEvents.push(currentBucketEvents)
    rawAnomalies.push(currentBucketAnomalies)

    if (rawLabels.length > MAX_POINTS) {
      rawLabels.shift()
      rawEvents.shift()
      rawAnomalies.shift()
    }

    currentBucketEvents = 0
    currentBucketAnomalies = 0

    // Reemplazar chartData completo (trigger reactivo limpio)
    chartData.value = buildChartData()
  }, bucketSeconds * 1000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
  unsub()
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 300 },
  plugins: {
    legend: {
      labels: { color: '#fff', usePointStyle: true, pointStyle: 'line', boxWidth: 20, font: { size: 11 } },
    },
  },
  scales: {
    x: {
      ticks: { color: '#6b7280', maxRotation: 0, maxTicksLimit: 6, font: { size: 10 } },
      grid: { color: '#1a1a2e' },
    },
    y: {
      beginAtZero: true,
      ticks: { color: '#6b7280', stepSize: 1, font: { size: 10 } },
      grid: { color: '#1a1a2e' },
    },
  },
}
</script>

<template>
  <div class="bg-secondary rounded-lg p-4 border border-accent">
    <h3 class="text-sm font-semibold mb-2">
      Actividad en Tiempo Real
      <span class="text-xs text-gray-500 font-normal ml-1">(cada 10s)</span>
    </h3>
    <div class="h-40">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>
