<script setup>
import { ref, onMounted, watch } from 'vue'
import { useEventsStore } from '../stores/events'

const store = useEventsStore()

const filters = ref({
  event_type: '',
  source_ip: '',
  is_anomaly: '',
  limit: 50,
  skip: 0,
})

const currentPage = ref(1)

const applyFilters = () => {
  currentPage.value = 1
  filters.value.skip = 0
  fetchWithFilters()
}

const fetchWithFilters = () => {
  const params = { limit: filters.value.limit, skip: filters.value.skip }
  if (filters.value.event_type) params.event_type = filters.value.event_type
  if (filters.value.source_ip) params.source_ip = filters.value.source_ip
  if (filters.value.is_anomaly !== '') params.is_anomaly = filters.value.is_anomaly === 'true'
  store.fetchEvents(params)
}

const clearFilters = () => {
  filters.value = { event_type: '', source_ip: '', is_anomaly: '', limit: 50, skip: 0 }
  currentPage.value = 1
  fetchWithFilters()
}

const totalPages = () => Math.ceil(store.total / filters.value.limit) || 1

const goToPage = (page) => {
  if (page < 1 || page > totalPages()) return
  currentPage.value = page
  filters.value.skip = (page - 1) * filters.value.limit
  fetchWithFilters()
}

onMounted(() => fetchWithFilters())
</script>

<template>
  <div>
    <!-- Filtros -->
    <div class="bg-secondary rounded-lg p-4 border border-accent mb-4">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div>
          <label class="block text-xs text-gray-400 mb-1">Tipo de Evento</label>
          <input
            v-model="filters.event_type"
            type="text"
            placeholder="ssh_login, apache_access..."
            class="w-full bg-primary border border-accent rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-danger"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">IP Origen</label>
          <input
            v-model="filters.source_ip"
            type="text"
            placeholder="192.168.1.1"
            class="w-full bg-primary border border-accent rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-danger"
          />
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Anomalia</label>
          <select
            v-model="filters.is_anomaly"
            class="w-full bg-primary border border-accent rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-danger"
          >
            <option value="">Todos</option>
            <option value="true">Solo anomalias</option>
            <option value="false">Solo normales</option>
          </select>
        </div>
        <div class="flex items-end gap-2">
          <button @click="applyFilters" class="bg-danger hover:bg-danger/80 px-4 py-2 rounded text-sm font-semibold transition-colors">
            Filtrar
          </button>
          <button @click="clearFilters" class="bg-accent hover:bg-accent/80 px-4 py-2 rounded text-sm transition-colors">
            Limpiar
          </button>
        </div>
      </div>
    </div>

    <!-- Tabla -->
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
            <th class="text-left py-3 px-4">Anomalia</th>
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

      <!-- Paginación -->
      <div class="flex items-center justify-between mt-4">
        <p class="text-gray-400 text-sm">Total: {{ store.total }} eventos</p>
        <div class="flex items-center gap-2">
          <button
            @click="goToPage(currentPage - 1)"
            :disabled="currentPage <= 1"
            class="px-3 py-1 rounded bg-accent hover:bg-accent/80 text-sm disabled:opacity-30 transition-colors"
          >Ant.</button>
          <span class="text-sm text-gray-400">{{ currentPage }} / {{ totalPages() }}</span>
          <button
            @click="goToPage(currentPage + 1)"
            :disabled="currentPage >= totalPages()"
            class="px-3 py-1 rounded bg-accent hover:bg-accent/80 text-sm disabled:opacity-30 transition-colors"
          >Sig.</button>
        </div>
      </div>
    </div>
  </div>
</template>
