<script setup>
import { ref, onUnmounted } from 'vue'
import { onWsMessage } from '../services/websocket'

const MAX_ITEMS = 15
const events = ref([])

const unsub = onWsMessage('all', (msg) => {
  const item = {
    id: Date.now() + Math.random(),
    type: msg.type,
    data: msg.data,
    time: new Date().toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
  }
  events.value.unshift(item)
  if (events.value.length > MAX_ITEMS) events.value.pop()
})

onUnmounted(() => unsub())

const levelColor = (level) => {
  const colors = {
    INFO: 'text-green-400',
    WARNING: 'text-yellow-400',
    ERROR: 'text-red-400',
    CRITICAL: 'text-red-600',
  }
  return colors[level] || 'text-gray-400'
}

const severityColor = (severity) => {
  const colors = {
    CRITICAL: 'text-red-500',
    HIGH: 'text-orange-400',
    MEDIUM: 'text-yellow-400',
    LOW: 'text-blue-400',
  }
  return colors[severity] || 'text-gray-400'
}
</script>

<template>
  <div class="bg-secondary rounded-lg p-6 border border-accent">
    <h3 class="text-lg font-semibold mb-4">
      Feed en Vivo
      <span class="relative flex h-2 w-2 ml-2 inline-block align-middle">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
      </span>
    </h3>
    <div v-if="events.length === 0" class="text-gray-500 text-sm text-center py-6">
      Esperando eventos en tiempo real...
    </div>
    <div v-else class="space-y-1 max-h-96 overflow-y-auto">
      <div
        v-for="item in events"
        :key="item.id"
        class="flex items-start gap-2 text-xs py-1.5 border-b border-accent/20"
        :class="{ 'bg-danger/5': item.type === 'alert' }"
      >
        <span class="text-gray-500 shrink-0 w-16">{{ item.time }}</span>
        <!-- Evento -->
        <template v-if="item.type === 'event'">
          <span :class="levelColor(item.data.log_level)" class="shrink-0 w-16">{{ item.data.log_level }}</span>
          <span class="bg-accent/50 px-1.5 py-0.5 rounded shrink-0">{{ item.data.event_type }}</span>
          <span v-if="item.data.source_ip" class="font-mono text-gray-400">{{ item.data.source_ip }}</span>
          <span v-if="item.data.is_anomaly" class="text-danger font-bold ml-auto">ANOMALIA</span>
        </template>
        <!-- Alerta -->
        <template v-else-if="item.type === 'alert'">
          <span :class="severityColor(item.data.severity)" class="font-bold shrink-0 w-16">{{ item.data.severity }}</span>
          <span class="text-danger">{{ item.data.alert_type }}</span>
          <span v-if="item.data.source_ip" class="font-mono text-gray-400 ml-1">{{ item.data.source_ip }}</span>
        </template>
      </div>
    </div>
  </div>
</template>
