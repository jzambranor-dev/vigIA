<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { onWsMessage } from '../services/websocket'

const topIPs = ref(new Map())
const sortedIPs = ref([])
const MAX_IPS = 10

const updateSorted = () => {
  sortedIPs.value = [...topIPs.value.entries()]
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, MAX_IPS)
}

const unsub = onWsMessage('event', (data) => {
  if (!data.source_ip) return
  const entry = topIPs.value.get(data.source_ip) || { count: 0, anomalies: 0 }
  entry.count++
  if (data.is_anomaly) entry.anomalies++
  topIPs.value.set(data.source_ip, entry)
  updateSorted()
})

onUnmounted(() => unsub())

const maxCount = () => {
  if (sortedIPs.value.length === 0) return 1
  return sortedIPs.value[0]?.[1]?.count || 1
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
      <div v-for="[ip, info] in sortedIPs" :key="ip" class="flex items-center gap-3">
        <span class="font-mono text-xs text-gray-300 w-32 shrink-0">{{ ip }}</span>
        <div class="flex-1 bg-primary rounded-full h-4 overflow-hidden">
          <div
            class="h-full rounded-full transition-all duration-300"
            :class="info.anomalies > 0 ? 'bg-danger' : 'bg-blue-500'"
            :style="{ width: (info.count / maxCount() * 100) + '%' }"
          ></div>
        </div>
        <span class="text-xs text-gray-400 w-16 text-right">{{ info.count }}</span>
        <span v-if="info.anomalies > 0" class="text-xs text-danger w-8">{{ info.anomalies }}!</span>
      </div>
    </div>
  </div>
</template>
