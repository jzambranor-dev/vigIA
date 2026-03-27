<script setup>
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'
import { ref } from 'vue'
import { isConnected } from './services/websocket'
import { isSoundEnabled, toggleSound } from './services/alertSound'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const showNotification = ref(false)
const notificationMsg = ref('')
const notificationType = ref('error')
const soundOn = ref(isSoundEnabled())

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const handleToggleSound = () => {
  soundOn.value = toggleSound()
}

window.__vigia_notify = (msg, type = 'error') => {
  notificationMsg.value = msg
  notificationType.value = type
  showNotification.value = true
  setTimeout(() => { showNotification.value = false }, 4000)
}
</script>

<template>
  <!-- Toast -->
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

  <!-- Login -->
  <div v-if="route.name === 'login'">
    <RouterView />
  </div>

  <!-- App -->
  <div v-else class="min-h-screen bg-primary">
    <nav class="bg-secondary border-b border-accent px-6 py-3">
      <div class="flex items-center justify-between max-w-7xl mx-auto">
        <RouterLink to="/" class="flex items-center gap-2.5 group">
          <img src="/logo.svg" alt="vigIA" class="w-8 h-8" />
          <span class="text-xl font-bold">
            <span class="text-white group-hover:text-gray-200 transition-colors">vig</span><span class="text-danger">IA</span>
          </span>
          <span
            class="w-2 h-2 rounded-full"
            :class="isConnected ? 'bg-green-500' : 'bg-red-500'"
            :title="isConnected ? 'Conectado en tiempo real' : 'Desconectado'"
          ></span>
        </RouterLink>
        <div class="flex items-center gap-5">
          <RouterLink to="/" class="text-sm hover:text-danger transition-colors"
            :class="{ 'text-danger': route.name === 'home' }">Dashboard</RouterLink>
          <RouterLink to="/events" class="text-sm hover:text-danger transition-colors"
            :class="{ 'text-danger': route.name === 'events' }">Eventos</RouterLink>
          <RouterLink to="/map" class="text-sm hover:text-danger transition-colors"
            :class="{ 'text-danger': route.name === 'map' }">Mapa</RouterLink>
          <RouterLink to="/reports" class="text-sm hover:text-danger transition-colors"
            :class="{ 'text-danger': route.name === 'reports' }">Reportes</RouterLink>
          <RouterLink to="/ml" class="text-sm hover:text-danger transition-colors"
            :class="{ 'text-danger': route.name === 'ml' }">ML</RouterLink>
          <div class="flex items-center gap-2 ml-3 pl-3 border-l border-accent">
            <!-- Sonido toggle -->
            <button
              @click="handleToggleSound"
              class="text-gray-400 hover:text-white transition-colors"
              :title="soundOn ? 'Desactivar sonido' : 'Activar sonido'"
            >
              <svg v-if="soundOn" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
              </svg>
            </button>
            <span class="text-sm text-gray-400">
              {{ authStore.username }}
              <span v-if="authStore.isAdmin" class="text-danger text-xs">(admin)</span>
            </span>
            <button
              @click="handleLogout"
              class="text-gray-400 hover:text-danger transition-colors"
              title="Cerrar sesion"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>

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
