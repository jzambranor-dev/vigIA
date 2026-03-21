<script setup>
import { onMounted } from 'vue'
import { useAlertsStore } from '../stores/alerts'

const store = useAlertsStore()

onMounted(() => {
  store.fetchAlerts({ limit: 20 })
})

const severityColor = (severity) => {
  const colors = {
    CRITICAL: 'bg-red-600',
    HIGH: 'bg-orange-500',
    MEDIUM: 'bg-yellow-500',
    LOW: 'bg-blue-500',
  }
  return colors[severity] || 'bg-gray-500'
}
</script>

<template>
  <div>
    <div v-if="store.loading" class="text-center py-10">Cargando alertas...</div>
    <div v-else class="space-y-3">
      <div
        v-for="alert in store.alerts"
        :key="alert.id"
        class="bg-secondary rounded-lg p-4 border border-accent"
        :class="{ 'opacity-50': alert.acknowledged }"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span :class="[severityColor(alert.severity), 'px-2 py-1 rounded text-xs font-bold']">
              {{ alert.severity }}
            </span>
            <span class="text-sm font-mono">{{ alert.alert_type }}</span>
          </div>
          <button
            v-if="!alert.acknowledged"
            @click="store.acknowledgeAlert(alert.id)"
            class="text-xs bg-accent hover:bg-accent/80 px-3 py-1 rounded transition-colors"
          >
            Reconocer
          </button>
          <span v-else class="text-xs text-gray-500">Reconocida</span>
        </div>
        <p class="text-sm text-gray-300 mt-2">{{ alert.description }}</p>
        <div class="flex gap-4 mt-2 text-xs text-gray-500">
          <span v-if="alert.source_ip">IP: {{ alert.source_ip }}</span>
          <span>{{ new Date(alert.created_at).toLocaleString() }}</span>
        </div>
      </div>
      <p v-if="store.alerts.length === 0" class="text-gray-500 text-center py-6">
        Sin alertas activas
      </p>
    </div>
  </div>
</template>
