<script setup>
import { ref, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import axios from 'axios'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const chartData = ref(null)

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/stats/summary')
    const eventTypes = data.events_by_type || {}

    chartData.value = {
      labels: Object.keys(eventTypes),
      datasets: [
        {
          label: 'Eventos por tipo',
          backgroundColor: '#e94560',
          data: Object.values(eventTypes),
        },
      ],
    }
  } catch (err) {
    console.error('Error cargando datos del gráfico:', err)
  }
})

const chartOptions = {
  responsive: true,
  plugins: {
    legend: {
      labels: { color: '#fff' },
    },
  },
  scales: {
    x: {
      ticks: { color: '#9ca3af' },
      grid: { color: '#1a1a2e' },
    },
    y: {
      ticks: { color: '#9ca3af' },
      grid: { color: '#1a1a2e' },
    },
  },
}
</script>

<template>
  <div class="bg-secondary rounded-lg p-6 border border-accent">
    <h3 class="text-lg font-semibold mb-4">Eventos por Tipo</h3>
    <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
    <p v-else class="text-gray-500">Cargando gráfico...</p>
  </div>
</template>
