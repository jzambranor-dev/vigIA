<script setup>
import { onMounted } from 'vue'
import { useEventsStore } from '../stores/events'

const store = useEventsStore()

onMounted(() => {
  store.fetchEvents({ limit: 50 })
})
</script>

<template>
  <div class="overflow-x-auto">
    <div v-if="store.loading" class="text-center py-10">Cargando eventos...</div>
    <table v-else class="w-full text-sm">
      <thead>
        <tr class="border-b border-accent text-gray-400">
          <th class="text-left py-3 px-4">Timestamp</th>
          <th class="text-left py-3 px-4">Tipo</th>
          <th class="text-left py-3 px-4">IP Origen</th>
          <th class="text-left py-3 px-4">Usuario</th>
          <th class="text-left py-3 px-4">Nivel</th>
          <th class="text-left py-3 px-4">Score</th>
          <th class="text-left py-3 px-4">Anomalía</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="event in store.events"
          :key="event.id"
          class="border-b border-accent/30 hover:bg-accent/20 transition-colors"
          :class="{ 'bg-danger/10': event.is_anomaly }"
        >
          <td class="py-2 px-4 text-xs">{{ new Date(event.timestamp_utc).toLocaleString() }}</td>
          <td class="py-2 px-4">
            <span class="bg-accent/50 px-2 py-1 rounded text-xs">{{ event.event_type }}</span>
          </td>
          <td class="py-2 px-4 font-mono text-xs">{{ event.source_ip || '-' }}</td>
          <td class="py-2 px-4">{{ event.username || '-' }}</td>
          <td class="py-2 px-4">
            <span
              :class="{
                'text-green-400': event.log_level === 'INFO',
                'text-yellow-400': event.log_level === 'WARNING',
                'text-red-400': event.log_level === 'ERROR',
                'text-red-600': event.log_level === 'CRITICAL',
              }"
            >{{ event.log_level }}</span>
          </td>
          <td class="py-2 px-4">{{ event.severity_score.toFixed(2) }}</td>
          <td class="py-2 px-4">
            <span v-if="event.is_anomaly" class="text-danger font-bold">SI</span>
            <span v-else class="text-gray-500">no</span>
          </td>
        </tr>
      </tbody>
    </table>
    <p class="text-gray-400 text-sm mt-4">Total: {{ store.total }} eventos</p>
  </div>
</template>
