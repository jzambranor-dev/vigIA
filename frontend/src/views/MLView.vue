<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'

const mlStatus = ref(null)
const stats = ref(null)
const loading = ref(true)
const retraining = ref(false)
const retrainResult = ref(null)

onMounted(async () => {
  try {
    const [mlRes, statsRes] = await Promise.all([
      axios.get('/api/ml/status'),
      axios.get('/api/stats/summary'),
    ])
    mlStatus.value = mlRes.data
    stats.value = statsRes.data
  } catch (err) {
    if (window.__vigia_notify) window.__vigia_notify('Error cargando estado ML')
  } finally {
    loading.value = false
  }
})

const anomalyRate = computed(() => {
  if (!stats.value || !stats.value.total_events) return 0
  return ((stats.value.total_anomalies / stats.value.total_events) * 100).toFixed(3)
})

const alertRate = computed(() => {
  if (!stats.value || !stats.value.total_events) return 0
  return ((stats.value.total_alerts / stats.value.total_events) * 100).toFixed(2)
})

const retrain = async () => {
  retraining.value = true
  retrainResult.value = null
  try {
    const { data } = await axios.post('/api/ml/retrain')
    retrainResult.value = data
    if (data.status === 'ok') {
      if (window.__vigia_notify) window.__vigia_notify('Modelos re-entrenados exitosamente', 'success')
      // Recargar estado
      const { data: updated } = await axios.get('/api/ml/status')
      mlStatus.value = updated
    } else {
      if (window.__vigia_notify) window.__vigia_notify(data.message, 'warning')
    }
  } catch (err) {
    const msg = err.response?.data?.detail || 'Error re-entrenando modelos'
    if (window.__vigia_notify) window.__vigia_notify(msg)
  } finally {
    retraining.value = false
  }
}

const featureDescriptions = {
  severity_score: 'Score de severidad del evento (0.0 - 1.0)',
  is_high_risk_event: 'Evento de alto riesgo (SSH fallido, invalid user)',
  is_medium_risk_event: 'Evento de riesgo medio (sudo, SSH cerrado)',
  is_error_level: 'Nivel ERROR o CRITICAL',
  is_warning_level: 'Nivel WARNING',
  has_source_ip: 'Tiene IP de origen',
  hour_sin: 'Componente seno de la hora (patron temporal)',
  hour_cos: 'Componente coseno de la hora (patron temporal)',
  is_night: 'Evento nocturno (22:00 - 06:00)',
  is_weekend: 'Evento en fin de semana',
  http_status_normalized: 'Codigo HTTP normalizado (0-1)',
  url_length_normalized: 'Longitud de URL normalizada',
  url_suspicious_score: 'Score de sospecha en URL (traversal, SQLi)',
  message_entropy: 'Entropia del mensaje (complejidad)',
  has_username: 'Tiene nombre de usuario',
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold mb-6">Machine Learning</h2>

    <div v-if="loading" class="text-center py-10">Cargando estado de modelos...</div>

    <div v-else class="space-y-6">
      <!-- Stats de deteccion -->
      <div v-if="stats" class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-secondary rounded-lg p-5 border border-accent">
          <p class="text-gray-400 text-sm">Eventos Analizados</p>
          <p class="text-2xl font-bold">{{ stats.total_events?.toLocaleString() }}</p>
        </div>
        <div class="bg-secondary rounded-lg p-5 border border-accent">
          <p class="text-gray-400 text-sm">Anomalias Detectadas</p>
          <p class="text-2xl font-bold text-yellow-400">{{ stats.total_anomalies?.toLocaleString() }}</p>
          <p class="text-xs text-gray-500 mt-1">{{ anomalyRate }}% del total</p>
        </div>
        <div class="bg-secondary rounded-lg p-5 border border-accent">
          <p class="text-gray-400 text-sm">Alertas Generadas</p>
          <p class="text-2xl font-bold text-danger">{{ stats.total_alerts?.toLocaleString() }}</p>
          <p class="text-xs text-gray-500 mt-1">{{ alertRate }}% del total</p>
        </div>
        <div class="bg-secondary rounded-lg p-5 border border-accent">
          <p class="text-gray-400 text-sm">Tipos de Evento</p>
          <p class="text-2xl font-bold">{{ Object.keys(stats.events_by_type || {}).length }}</p>
        </div>
      </div>

      <!-- Modelos -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Isolation Forest -->
        <div class="bg-secondary rounded-lg p-6 border border-accent">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold">Isolation Forest</h3>
            <span
              v-if="mlStatus?.anomaly_model?.loaded"
              class="bg-green-600/20 text-green-400 px-3 py-1 rounded-full text-xs font-semibold"
            >Activo</span>
            <span v-else class="bg-red-600/20 text-red-400 px-3 py-1 rounded-full text-xs font-semibold">Inactivo</span>
          </div>
          <p class="text-gray-400 text-sm mb-3">
            Modelo no supervisado para deteccion de anomalias. Identifica eventos que se desvian del comportamiento normal del sistema.
          </p>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-400">Algoritmo</span>
              <span>Isolation Forest (scikit-learn)</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Archivo</span>
              <span class="font-mono text-xs">
                {{ mlStatus?.anomaly_model?.file_exists ? 'isolation_forest.pkl' : 'No encontrado' }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Tamano</span>
              <span>{{ mlStatus?.anomaly_model?.file_size_kb || 0 }} KB</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Estado</span>
              <span :class="mlStatus?.anomaly_model?.loaded ? 'text-green-400' : 'text-red-400'">
                {{ mlStatus?.anomaly_model?.loaded ? 'Cargado en memoria' : 'No cargado' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Random Forest Classifier -->
        <div class="bg-secondary rounded-lg p-6 border border-accent">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-lg font-semibold">Random Forest Classifier</h3>
            <span
              v-if="mlStatus?.classifier_model?.loaded"
              class="bg-green-600/20 text-green-400 px-3 py-1 rounded-full text-xs font-semibold"
            >Activo</span>
            <span v-else class="bg-red-600/20 text-red-400 px-3 py-1 rounded-full text-xs font-semibold">Inactivo</span>
          </div>
          <p class="text-gray-400 text-sm mb-3">
            Modelo supervisado para clasificacion de ataques. Categoriza eventos en tipos como fuerza bruta, SQL injection, directory traversal, etc.
          </p>
          <div class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-400">Algoritmo</span>
              <span>Random Forest (scikit-learn)</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Archivo</span>
              <span class="font-mono text-xs">
                {{ mlStatus?.classifier_model?.file_exists ? 'attack_classifier.pkl' : 'No encontrado' }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Tamano</span>
              <span>{{ mlStatus?.classifier_model?.file_size_kb || 0 }} KB</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Estado</span>
              <span :class="mlStatus?.classifier_model?.loaded ? 'text-green-400' : 'text-red-400'">
                {{ mlStatus?.classifier_model?.loaded ? 'Cargado en memoria' : 'No cargado' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Feature Engineering -->
      <div class="bg-secondary rounded-lg p-6 border border-accent">
        <h3 class="text-lg font-semibold mb-4">
          Feature Engineering
          <span class="text-sm text-gray-400 font-normal ml-2">{{ mlStatus?.feature_count || 0 }} dimensiones</span>
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            v-for="(feature, index) in (mlStatus?.feature_names || [])"
            :key="feature"
            class="bg-primary rounded px-4 py-3 border border-accent/50"
          >
            <div class="flex items-center gap-2">
              <span class="text-danger font-mono text-xs">{{ index + 1 }}</span>
              <span class="text-sm font-semibold">{{ feature }}</span>
            </div>
            <p class="text-xs text-gray-500 mt-1">{{ featureDescriptions[feature] || '' }}</p>
          </div>
        </div>
      </div>

      <!-- Eventos por tipo (lo que alimenta el ML) -->
      <div v-if="stats?.events_by_type" class="bg-secondary rounded-lg p-6 border border-accent">
        <h3 class="text-lg font-semibold mb-4">Distribucion de Eventos (datos de entrenamiento)</h3>
        <div class="space-y-2">
          <div v-for="(count, type) in stats.events_by_type" :key="type" class="flex items-center gap-3">
            <span class="text-sm font-mono w-44 text-gray-300">{{ type }}</span>
            <div class="flex-1 bg-primary rounded-full h-5 overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :class="{
                  'bg-danger': type.includes('failed') || type.includes('invalid'),
                  'bg-yellow-500': type.includes('sudo'),
                  'bg-blue-500': type.includes('syslog'),
                  'bg-green-500': type.includes('accepted'),
                  'bg-accent': !type.includes('failed') && !type.includes('sudo') && !type.includes('syslog') && !type.includes('accepted'),
                }"
                :style="{ width: Math.max((count / stats.total_events * 100), 1) + '%' }"
              ></div>
            </div>
            <span class="text-sm text-gray-400 w-24 text-right">{{ count.toLocaleString() }}</span>
          </div>
        </div>
      </div>

      <!-- Alertas por severidad -->
      <div v-if="stats?.alerts_by_severity" class="bg-secondary rounded-lg p-6 border border-accent">
        <h3 class="text-lg font-semibold mb-4">Alertas por Severidad (generadas por ML + reglas)</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div
            v-for="(count, severity) in stats.alerts_by_severity"
            :key="severity"
            class="text-center p-4 rounded-lg"
            :class="{
              'bg-red-600/20 border border-red-600/50': severity === 'CRITICAL',
              'bg-orange-500/20 border border-orange-500/50': severity === 'HIGH',
              'bg-yellow-500/20 border border-yellow-500/50': severity === 'MEDIUM',
              'bg-blue-500/20 border border-blue-500/50': severity === 'LOW',
            }"
          >
            <p class="text-2xl font-bold">{{ count.toLocaleString() }}</p>
            <p class="text-sm mt-1"
              :class="{
                'text-red-400': severity === 'CRITICAL',
                'text-orange-400': severity === 'HIGH',
                'text-yellow-400': severity === 'MEDIUM',
                'text-blue-400': severity === 'LOW',
              }"
            >{{ severity }}</p>
          </div>
        </div>
      </div>

      <!-- Acciones -->
      <div class="bg-secondary rounded-lg p-6 border border-accent">
        <h3 class="text-lg font-semibold mb-3">Re-entrenar Modelos</h3>
        <p class="text-gray-400 text-sm mb-4">
          Re-entrena Isolation Forest y Random Forest con los eventos mas recientes de la base de datos.
          Esto mejora la precision de deteccion basandose en el trafico real del servidor.
        </p>
        <button
          @click="retrain"
          :disabled="retraining"
          class="bg-danger hover:bg-danger/80 px-6 py-2 rounded font-semibold transition-colors disabled:opacity-50"
        >
          {{ retraining ? 'Re-entrenando...' : 'Re-entrenar Modelos' }}
        </button>

        <!-- Resultado del retrain -->
        <div v-if="retrainResult" class="mt-4 p-4 rounded-lg text-sm"
          :class="retrainResult.status === 'ok' ? 'bg-green-600/10 border border-green-600/30' : 'bg-yellow-600/10 border border-yellow-600/30'"
        >
          <p class="font-semibold mb-2">{{ retrainResult.message }}</p>
          <div v-if="retrainResult.events_used" class="space-y-1 text-gray-400">
            <p>Eventos usados: {{ retrainResult.events_used?.toLocaleString() }}</p>
            <p v-if="retrainResult.isolation_forest">
              Isolation Forest: {{ retrainResult.isolation_forest.status }}
              <span v-if="retrainResult.isolation_forest.samples"> ({{ retrainResult.isolation_forest.samples }} muestras)</span>
            </p>
            <p v-if="retrainResult.classifier">
              Classifier: {{ retrainResult.classifier.status }}
              <span v-if="retrainResult.classifier.accuracy"> — Accuracy: {{ (retrainResult.classifier.accuracy * 100).toFixed(1) }}%</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
