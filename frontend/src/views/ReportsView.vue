<script setup>
import { ref } from 'vue'

const downloading = ref(false)

const downloadReport = async () => {
  downloading.value = true
  try {
    const response = await fetch('/api/reports/pdf')
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'reporte_seguridad.pdf'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Error descargando reporte:', err)
  } finally {
    downloading.value = false
  }
}
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold mb-6">Reportes</h2>
    <div class="bg-secondary rounded-lg p-6 border border-accent">
      <h3 class="text-lg font-semibold mb-2">Reporte Ejecutivo PDF</h3>
      <p class="text-gray-400 mb-4">
        Genera un reporte PDF con el resumen de seguridad, alertas por severidad y estadísticas.
      </p>
      <button
        @click="downloadReport"
        :disabled="downloading"
        class="bg-danger hover:bg-danger/80 px-6 py-2 rounded font-semibold transition-colors disabled:opacity-50"
      >
        {{ downloading ? 'Generando...' : 'Descargar Reporte PDF' }}
      </button>
    </div>
  </div>
</template>
