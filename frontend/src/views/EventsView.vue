<script setup>
import { ref } from 'vue'
import axios from 'axios'
import EventsTable from '../components/EventsTable.vue'

const exportingEvents = ref(false)
const exportingAlerts = ref(false)

const exportCSV = async (type) => {
  const isEvents = type === 'events'
  if (isEvents) exportingEvents.value = true
  else exportingAlerts.value = true

  try {
    const url = isEvents ? '/api/geo/export/events' : '/api/geo/export/alerts'
    const response = await axios.get(url, { responseType: 'blob' })
    const blobUrl = window.URL.createObjectURL(new Blob([response.data]))
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = isEvents ? 'vigia_events.csv' : 'vigia_alerts.csv'
    a.click()
    window.URL.revokeObjectURL(blobUrl)
    if (window.__vigia_notify) window.__vigia_notify(`${isEvents ? 'Eventos' : 'Alertas'} exportados`, 'success')
  } catch (err) {
    if (window.__vigia_notify) window.__vigia_notify('Error exportando CSV')
  } finally {
    exportingEvents.value = false
    exportingAlerts.value = false
  }
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-2xl font-bold">Eventos de Log</h2>
      <div class="flex gap-2">
        <button
          @click="exportCSV('events')"
          :disabled="exportingEvents"
          class="flex items-center gap-1.5 bg-accent hover:bg-accent/80 px-3 py-1.5 rounded text-sm transition-colors disabled:opacity-50"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ exportingEvents ? 'Exportando...' : 'Exportar Eventos CSV' }}
        </button>
        <button
          @click="exportCSV('alerts')"
          :disabled="exportingAlerts"
          class="flex items-center gap-1.5 bg-danger/80 hover:bg-danger px-3 py-1.5 rounded text-sm transition-colors disabled:opacity-50"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ exportingAlerts ? 'Exportando...' : 'Exportar Alertas CSV' }}
        </button>
      </div>
    </div>
    <EventsTable />
  </div>
</template>
