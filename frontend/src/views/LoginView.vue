<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')

const handleLogin = async () => {
  const success = await authStore.login(username.value, password.value)
  if (success) {
    router.push('/')
  }
}
</script>

<template>
  <div class="min-h-screen bg-primary flex items-center justify-center px-4">
    <div class="bg-secondary rounded-xl p-8 border border-accent w-full max-w-md shadow-2xl">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 bg-danger/20 rounded-full mb-4">
          <svg class="w-8 h-8 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-white">vigIA</h1>
        <p class="text-gray-400 text-sm mt-1">Sistema de Monitoreo de Seguridad</p>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleLogin" class="space-y-5">
        <div>
          <label class="block text-sm text-gray-400 mb-1.5">Usuario</label>
          <input
            v-model="username"
            type="text"
            required
            autocomplete="username"
            class="w-full bg-primary border border-accent rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-danger transition-colors"
            placeholder="Ingresa tu usuario"
          />
        </div>

        <div>
          <label class="block text-sm text-gray-400 mb-1.5">Contrasena</label>
          <input
            v-model="password"
            type="password"
            required
            autocomplete="current-password"
            class="w-full bg-primary border border-accent rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-danger transition-colors"
            placeholder="Ingresa tu contrasena"
          />
        </div>

        <!-- Error -->
        <div v-if="authStore.error" class="bg-danger/20 border border-danger/50 rounded-lg px-4 py-3 text-danger text-sm">
          {{ authStore.error }}
        </div>

        <button
          type="submit"
          :disabled="authStore.loading"
          class="w-full bg-danger hover:bg-danger/80 text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ authStore.loading ? 'Autenticando...' : 'Iniciar Sesion' }}
        </button>
      </form>

      <p class="text-gray-500 text-xs text-center mt-6">
        Log Analyzer AI v0.2.0
      </p>
    </div>
  </div>
</template>
