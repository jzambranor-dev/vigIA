<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { Line } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js'
import { onWsMessage } from '../services/websocket'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const MAX_POINTS = 30
const bucketSeconds = 10

// Contadores por bucket de tiempo
const eventCounts = ref([])
const anomalyCounts = ref([])
const labels = ref([])

// Inicializar con ceros
for (let i = 0; i < MAX_POINTS; i++) {
  eventCounts.value.push(0)
  anomalyCounts.value.push(0)
  labels.value.push('')
}

let currentBucketEvents = 0
let currentBucketAnomalies = 0

const unsub = onWsMessage('event', (data) => {
  currentBucketEvents++
  if (data.is_anomaly) currentBucketAnomalies++
})

// Tick cada N segundos
let interval = null
onMounted(() => {
  interval = setInterval(() => {
    const now = new Date()
    const label = now.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

    eventCounts.value.push(currentBucketEvents)
    anomalyCounts.value.push(currentBucketAnomalies)
    labels.value.push(label)

    if (eventCounts.value.length > MAX_POINTS) {
      eventCounts.value.shift()
      anomalyCounts.value.shift()
      labels.value.shift()
    }

    currentBucketEvents = 0
    currentBucketAnomalies = 0
  }, bucketSeconds * 1000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
  unsub()
})

const chartData = computed(() => ({
  labels: labels.value,
  datasets: [
    {
      label: 'Eventos / 10s',
      data: eventCounts.value,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 0,
    },
    {
      label: 'Anomalias / 10s',
      data: anomalyCounts.value,
      borderColor: '#e94560',
      backgroundColor: 'rgba(233, 69, 96, 0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 0,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  animation: { duration: 300 },
  plugins: {
    legend: {
      labels: { color: '#fff', usePointStyle: true, pointStyle: 'line' },
    },
  },
  scales: {
    x: {
      ticks: { color: '#6b7280', maxRotation: 0, maxTicksLimit: 6 },
      grid: { color: '#1a1a2e' },
    },
    y: {
      beginAtZero: true,
      ticks: { color: '#6b7280', stepSize: 1 },
      grid: { color: '#1a1a2e' },
    },
  },
}
</script>

<template>
  <div class="bg-secondary rounded-lg p-6 border border-accent">
    <h3 class="text-lg font-semibold mb-4">
      Actividad en Tiempo Real
      <span class="text-xs text-gray-500 font-normal ml-2">(cada 10 segundos)</span>
    </h3>
    <Line :data="chartData" :options="chartOptions" :key="eventCounts.length" />
  </div>
</template>
