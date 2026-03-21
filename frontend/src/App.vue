<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-primary">
    <!-- Navbar -->
    <nav class="bg-secondary border-b border-accent px-6 py-4">
      <div class="flex items-center justify-between max-w-7xl mx-auto">
        <h1 class="text-xl font-bold text-danger">
          🛡️ Log Analyzer AI
        </h1>
        <div class="flex gap-6">
          <RouterLink to="/" class="hover:text-danger transition-colors">Dashboard</RouterLink>
          <RouterLink to="/events" class="hover:text-danger transition-colors">Eventos</RouterLink>
          <RouterLink to="/reports" class="hover:text-danger transition-colors">Reportes</RouterLink>
        </div>
      </div>
    </nav>

    <!-- Content -->
    <main class="max-w-7xl mx-auto p-6">
      <RouterView />
    </main>
  </div>
</template>
