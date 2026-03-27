<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const mapContainer = ref(null)
const loading = ref(true)
const markers = ref([])
const selectedIP = ref(null)
const ipDetail = ref(null)
let map = null

onMounted(async () => {
  // Inicializar mapa
  map = L.map(mapContainer.value, {
    center: [20, 0],
    zoom: 2,
    zoomControl: true,
    attributionControl: false,
  })

  // Tile layer oscuro
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 18,
  }).addTo(map)

  // Cargar datos
  try {
    const { data } = await axios.get('/api/geo/map?limit=100')
    markers.value = data.markers

    data.markers.forEach(m => {
      const color = m.alert_count >= 50 ? '#dc2626' : m.alert_count >= 10 ? '#f97316' : '#eab308'
      const radius = Math.min(Math.max(m.alert_count / 5, 4), 20)

      const circle = L.circleMarker([m.lat, m.lon], {
        radius: radius,
        fillColor: color,
        color: color,
        weight: 1,
        opacity: 0.8,
        fillOpacity: 0.5,
      }).addTo(map)

      circle.bindTooltip(
        `<b>${m.ip}</b><br>${m.city}, ${m.country}<br>${m.alert_count} alertas<br>${m.isp}`,
        { className: 'dark-tooltip' }
      )

      circle.on('click', () => loadIPDetail(m.ip))
    })
  } catch (err) {
    console.error('Error cargando mapa:', err)
  } finally {
    loading.value = false
  }
})

onUnmounted(() => {
  if (map) map.remove()
})

const loadIPDetail = async (ip) => {
  selectedIP.value = ip
  ipDetail.value = null
  try {
    const { data } = await axios.get(`/api/geo/ip/${ip}`)
    ipDetail.value = data
  } catch (err) {
    console.error('Error cargando detalle IP:', err)
  }
}

const closeDetail = () => {
  selectedIP.value = null
  ipDetail.value = null
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold mb-4">Mapa de Amenazas</h2>

    <div class="relative">
      <!-- Mapa -->
      <div
        ref="mapContainer"
        class="w-full rounded-lg border border-accent overflow-hidden"
        style="height: 500px;"
      ></div>

      <!-- Loading -->
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-primary/80 rounded-lg">
        <span class="text-gray-400">Cargando mapa de amenazas...</span>
      </div>

      <!-- Panel de detalle IP -->
      <Transition name="slide-panel">
        <div
          v-if="selectedIP"
          class="absolute top-2 right-2 w-80 bg-secondary/95 backdrop-blur border border-accent rounded-lg p-4 shadow-xl max-h-[480px] overflow-y-auto"
        >
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-bold font-mono text-danger">{{ selectedIP }}</h3>
            <button @click="closeDetail" class="text-gray-400 hover:text-white">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <div v-if="!ipDetail" class="text-gray-400 text-sm py-4 text-center">Cargando...</div>

          <div v-else class="space-y-3 text-sm">
            <!-- Geo -->
            <div v-if="ipDetail.geo" class="space-y-1">
              <p><span class="text-gray-400">Pais:</span> {{ ipDetail.geo.country }} ({{ ipDetail.geo.country_code }})</p>
              <p><span class="text-gray-400">Ciudad:</span> {{ ipDetail.geo.city || 'N/A' }}</p>
              <p><span class="text-gray-400">ISP:</span> {{ ipDetail.geo.isp }}</p>
              <p><span class="text-gray-400">Organizacion:</span> {{ ipDetail.geo.org }}</p>
            </div>

            <hr class="border-accent">

            <!-- Stats -->
            <div class="grid grid-cols-2 gap-2">
              <div class="bg-primary rounded p-2 text-center">
                <p class="text-lg font-bold">{{ ipDetail.total_events?.toLocaleString() }}</p>
                <p class="text-xs text-gray-400">Eventos</p>
              </div>
              <div class="bg-primary rounded p-2 text-center">
                <p class="text-lg font-bold text-danger">{{ ipDetail.total_alerts?.toLocaleString() }}</p>
                <p class="text-xs text-gray-400">Alertas</p>
              </div>
            </div>

            <!-- Event types -->
            <div v-if="Object.keys(ipDetail.event_types || {}).length">
              <p class="text-gray-400 text-xs mb-1">Tipos de evento:</p>
              <div v-for="(count, type) in ipDetail.event_types" :key="type"
                class="flex justify-between text-xs py-0.5">
                <span class="font-mono">{{ type }}</span>
                <span class="text-gray-400">{{ count }}</span>
              </div>
            </div>

            <!-- Alert types -->
            <div v-if="Object.keys(ipDetail.alert_types || {}).length">
              <p class="text-gray-400 text-xs mb-1">Tipos de alerta:</p>
              <div v-for="(count, type) in ipDetail.alert_types" :key="type"
                class="flex justify-between text-xs py-0.5">
                <span class="font-mono text-danger">{{ type }}</span>
                <span>{{ count }}</span>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Stats debajo del mapa -->
    <div class="mt-4 text-sm text-gray-400">
      {{ markers.length }} IPs geolocalizadas con alertas activas
    </div>
  </div>
</template>

<style>
.dark-tooltip {
  background-color: #16213e !important;
  color: #fff !important;
  border: 1px solid #0f3460 !important;
  border-radius: 8px !important;
  padding: 8px 12px !important;
  font-size: 12px !important;
  box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
}
.dark-tooltip::before {
  border-top-color: #0f3460 !important;
}
.slide-panel-enter-active, .slide-panel-leave-active {
  transition: all 0.2s ease;
}
.slide-panel-enter-from, .slide-panel-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
