<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'
import { ref } from 'vue'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const showNotification = ref(false)
const notificationMsg = ref('')
const notificationType = ref('error')

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// Exponer notificación globalmente
window.__vigia_notify = (msg, type = 'error') => {
  notificationMsg.value = msg
  notificationType.value = type
  showNotification.value = true
  setTimeout(() => { showNotification.value = false }, 4000)
}
</script>

<template>
  <!-- Notificación toast global -->
  <Transition name="slide">
    <div
      v-if="showNotification"
      class="fixed top-4 right-4 z-50 px-5 py-3 rounded-lg shadow-lg text-sm font-medium max-w-sm"
      :class="{
        'bg-red-600/90 text-white': notificationType === 'error',
        'bg-green-600/90 text-white': notificationType === 'success',
        'bg-yellow-600/90 text-white': notificationType === 'warning',
      }"
    >
      {{ notificationMsg }}
    </div>
  </Transition>

  <!-- Login page: sin navbar -->
  <div v-if="route.name === 'login'">
    <RouterView />
  </div>

  <!-- App principal -->
  <div v-else class="min-h-screen bg-primary">
    <!-- Navbar -->
    <nav class="bg-secondary border-b border-accent px-6 py-4">
      <div class="flex items-center justify-between max-w-7xl mx-auto">
        <h1 class="text-xl font-bold text-danger">
          vigIA
        </h1>
        <div class="flex items-center gap-6">
          <RouterLink to="/" class="hover:text-danger transition-colors"
            :class="{ 'text-danger': route.name === 'home' }">Dashboard</RouterLink>
          <RouterLink to="/events" class="hover:text-danger transition-colors"
            :class="{ 'text-danger': route.name === 'events' }">Eventos</RouterLink>
          <RouterLink to="/reports" class="hover:text-danger transition-colors"
            :class="{ 'text-danger': route.name === 'reports' }">Reportes</RouterLink>
          <RouterLink to="/ml" class="hover:text-danger transition-colors"
            :class="{ 'text-danger': route.name === 'ml' }">ML</RouterLink>
          <div class="flex items-center gap-3 ml-4 pl-4 border-l border-accent">
            <span class="text-sm text-gray-400">
              {{ authStore.username }}
              <span v-if="authStore.isAdmin" class="text-danger text-xs">(admin)</span>
            </span>
            <button
              @click="handleLogout"
              class="text-sm text-gray-400 hover:text-danger transition-colors"
              title="Cerrar sesion"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Content -->
    <main class="max-w-7xl mx-auto p-6">
      <RouterView />
    </main>
  </div>
</template>

<style>
.slide-enter-active, .slide-leave-active {
  transition: all 0.3s ease;
}
.slide-enter-from, .slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
