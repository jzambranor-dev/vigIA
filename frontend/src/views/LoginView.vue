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
        <img src="/logo.svg" alt="vigIA" class="w-20 h-20 mx-auto mb-3" />
        <h1 class="text-2xl font-bold">
          <span class="text-white">vig</span><span class="text-danger">IA</span>
        </h1>
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
