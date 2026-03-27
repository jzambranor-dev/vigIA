<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { onWsMessage } from '../services/websocket'

const stats = ref(null)
const loading = ref(true)
const recentCount = ref(0)

const fetchStats = async () => {
  try {
    const { data } = await axios.get('/api/stats/summary')
    stats.value = data
  } catch (err) {
    console.error('Error cargando estadisticas:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStats()
})

// Actualizar contadores en tiempo real
const unsub1 = onWsMessage('event', (data) => {
  if (stats.value) {
    stats.value.total_events++
    if (data.is_anomaly) stats.value.total_anomalies++
    recentCount.value++
  }
})

const unsub2 = onWsMessage('alert', (data) => {
  if (stats.value) {
    stats.value.total_alerts++
    stats.value.unacknowledged_alerts++
    // Actualizar severidad
    if (data.severity) {
      if (!stats.value.alerts_by_severity) stats.value.alerts_by_severity = {}
      stats.value.alerts_by_severity[data.severity] = (stats.value.alerts_by_severity[data.severity] || 0) + 1
    }
  }
})

onUnmounted(() => { unsub1(); unsub2() })
</script>

<template>
  <div v-if="loading" class="text-center py-10">Cargando estadisticas...</div>
  <div v-else-if="stats" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    <div class="bg-secondary rounded-lg p-6 border border-accent">
      <p class="text-gray-400 text-sm">Total Eventos</p>
      <p class="text-3xl font-bold">{{ stats.total_events?.toLocaleString() }}</p>
      <p v-if="recentCount > 0" class="text-xs text-green-400 mt-1">+{{ recentCount }} nuevos</p>
    </div>
    <div class="bg-secondary rounded-lg p-6 border border-accent">
      <p class="text-gray-400 text-sm">Anomalias</p>
      <p class="text-3xl font-bold text-yellow-400">{{ stats.total_anomalies?.toLocaleString() }}</p>
    </div>
    <div class="bg-secondary rounded-lg p-6 border border-accent">
      <p class="text-gray-400 text-sm">Alertas</p>
      <p class="text-3xl font-bold text-danger">{{ stats.total_alerts?.toLocaleString() }}</p>
    </div>
    <div class="bg-secondary rounded-lg p-6 border border-accent">
      <p class="text-gray-400 text-sm">Sin Reconocer</p>
      <p class="text-3xl font-bold text-red-500">{{ stats.unacknowledged_alerts?.toLocaleString() }}</p>
    </div>
  </div>
</template>
