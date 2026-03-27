<script setup>
import { ref, onMounted } from 'vue'
import { Doughnut } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import axios from 'axios'

ChartJS.register(ArcElement, Tooltip, Legend)

const chartData = ref(null)

const severityColors = {
  CRITICAL: '#dc2626',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#3b82f6',
}

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/stats/summary')
    const severity = data.alerts_by_severity || {}

    if (Object.keys(severity).length > 0) {
      chartData.value = {
        labels: Object.keys(severity),
        datasets: [
          {
            data: Object.values(severity),
            backgroundColor: Object.keys(severity).map(k => severityColors[k] || '#6b7280'),
            borderWidth: 0,
          },
        ],
      }
    }
  } catch (err) {
    console.error('Error cargando datos de severidad:', err)
  }
})

const chartOptions = {
  responsive: true,
  plugins: {
    legend: {
      position: 'bottom',
      labels: { color: '#fff', padding: 15 },
    },
  },
}
</script>

<template>
  <div class="bg-secondary rounded-lg p-6 border border-accent">
    <h3 class="text-lg font-semibold mb-4">Alertas por Severidad</h3>
    <div class="flex justify-center">
      <div v-if="chartData" class="w-64">
        <Doughnut :data="chartData" :options="chartOptions" />
      </div>
      <p v-else class="text-gray-500 py-10">Sin datos de alertas</p>
    </div>
  </div>
</template>
