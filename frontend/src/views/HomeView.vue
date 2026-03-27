<script setup>
import Dashboard from '../components/Dashboard.vue'
import AlertsPanel from '../components/AlertsPanel.vue'
import StatsChart from '../components/StatsChart.vue'
import SeverityChart from '../components/SeverityChart.vue'
import LiveTimeline from '../components/LiveTimeline.vue'
import TopIPsChart from '../components/TopIPsChart.vue'
import LiveFeed from '../components/LiveFeed.vue'
</script>

<template>
  <div class="space-y-6">
    <h2 class="text-2xl font-bold">Dashboard</h2>
    <Dashboard />

    <!-- Timeline en tiempo real -->
    <LiveTimeline />

    <!-- Graficos estáticos -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2">
        <StatsChart />
      </div>
      <SeverityChart />
    </div>

    <!-- Tiempo real: Top IPs + Feed -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <TopIPsChart />
      <LiveFeed />
    </div>

    <!-- Alertas recientes -->
    <div>
      <h3 class="text-lg font-semibold mb-4">Alertas Recientes</h3>
      <AlertsPanel />
    </div>
  </div>
</template>
