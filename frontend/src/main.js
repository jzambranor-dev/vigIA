import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'
import { useAuthStore } from './stores/auth'
import { connectWebSocket, disconnectWebSocket } from './services/websocket'
import axios from 'axios'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Inicializar autenticacion
const authStore = useAuthStore()
authStore.initAuth()

// Conectar WebSocket si autenticado
if (authStore.isAuthenticated) {
  connectWebSocket()
}

// Interceptor: redirigir a login si recibe 401
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      disconnectWebSocket()
      authStore.logout()
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

app.mount('#app')
