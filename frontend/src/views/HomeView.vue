<script setup>
import Dashboard from '../components/Dashboard.vue'
import AlertsPanel from '../components/AlertsPanel.vue'
import StatsChart from '../components/StatsChart.vue'
</script>

<template>
  <div class="space-y-6">
    <h2 class="text-2xl font-bold">Dashboard</h2>
    <Dashboard />
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <StatsChart />
      <div>
        <h3 class="text-lg font-semibold mb-4">Alertas Recientes</h3>
        <AlertsPanel />
      </div>
    </div>
  </div>
</template>
