<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const stats = ref(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const { data } = await axios.get('/api/stats/summary')
    stats.value = data
  } catch (err) {
    console.error('Error cargando estadísticas:', err)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="loading" class="text-center py-10">Cargando estadísticas...</div>
  <div v-else-if="stats" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="bg-secondary rounded-lg p-6 border border-accent">
      <p class="text-gray-400 text-sm">Total Eventos</p>
      <p class="text-3xl font-bold">{{ stats.total_events }}</p>
    </div>
    <div class="bg-secondary rounded-lg p-6 border border-accent">
      <p class="text-gray-400 text-sm">Anomalías</p>
      <p class="text-3xl font-bold text-yellow-400">{{ stats.total_anomalies }}</p>
    </div>
    <div class="bg-secondary rounded-lg p-6 border border-accent">
      <p class="text-gray-400 text-sm">Alertas</p>
      <p class="text-3xl font-bold text-danger">{{ stats.total_alerts }}</p>
    </div>
    <div class="bg-secondary rounded-lg p-6 border border-accent">
      <p class="text-gray-400 text-sm">Sin Reconocer</p>
      <p class="text-3xl font-bold text-red-500">{{ stats.unacknowledged_alerts }}</p>
    </div>
  </div>
</template>
