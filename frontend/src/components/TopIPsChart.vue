<script setup>
import { ref, onUnmounted } from 'vue'
import { onWsMessage } from '../services/websocket'

const MAX_IPS = 10

// Datos no reactivos
const ipMap = {}
const sortedIPs = ref([])

let updateTimer = null

const unsub = onWsMessage('event', (data) => {
  if (!data.source_ip) return
  if (!ipMap[data.source_ip]) ipMap[data.source_ip] = { count: 0, anomalies: 0 }
  ipMap[data.source_ip].count++
  if (data.is_anomaly) ipMap[data.source_ip].anomalies++
})

// Actualizar la vista cada 3 segundos en vez de cada evento
updateTimer = setInterval(() => {
  const entries = Object.entries(ipMap)
    .map(([ip, info]) => ({ ip, ...info }))
    .sort((a, b) => b.count - a.count)
    .slice(0, MAX_IPS)
  sortedIPs.value = entries
}, 3000)

onUnmounted(() => {
  unsub()
  if (updateTimer) clearInterval(updateTimer)
})

const maxCount = () => {
  if (sortedIPs.value.length === 0) return 1
  return sortedIPs.value[0]?.count || 1
}
</script>

<template>
  <div class="bg-secondary rounded-lg p-6 border border-accent">
    <h3 class="text-lg font-semibold mb-4">
      Top IPs
      <span class="text-xs text-gray-500 font-normal ml-2">(sesion actual)</span>
    </h3>
    <div v-if="sortedIPs.length === 0" class="text-gray-500 text-sm text-center py-6">
      Esperando eventos con IP...
    </div>
    <div v-else class="space-y-2">
      <div v-for="item in sortedIPs" :key="item.ip" class="flex items-center gap-3">
        <span class="font-mono text-xs text-gray-300 w-32 shrink-0">{{ item.ip }}</span>
        <div class="flex-1 bg-primary rounded-full h-4 overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-300"
            :class="item.anomalies > 0 ? 'bg-danger' : 'bg-blue-500'"
            :style="{ width: (item.count / maxCount() * 100) + '%' }"
          ></div>
        </div>
        <span class="text-xs text-gray-400 w-16 text-right">{{ item.count }}</span>
        <span v-if="item.anomalies > 0" class="text-xs text-danger w-8">{{ item.anomalies }}!</span>
      </div>
    </div>
  </div>
</template>
