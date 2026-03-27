import { defineStore } from 'pinia'
import axios from 'axios'
import { connectWebSocket, disconnectWebSocket } from '../services/websocket'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('vigia_token') || null,
    username: localStorage.getItem('vigia_username') || null,
    isAdmin: localStorage.getItem('vigia_is_admin') === 'true',
    loading: false,
    error: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
  },

  actions: {
    async login(username, password) {
      this.loading = true
      this.error = null
      try {
        const { data } = await axios.post('/api/auth/login', { username, password })
        this.token = data.access_token
        this.username = data.username
        this.isAdmin = data.is_admin

        localStorage.setItem('vigia_token', data.access_token)
        localStorage.setItem('vigia_username', data.username)
        localStorage.setItem('vigia_is_admin', data.is_admin)

        axios.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

        // Conectar WebSocket
        connectWebSocket()

        return true
      } catch (err) {
        this.error = err.response?.data?.detail || 'Error de conexion'
        return false
      } finally {
        this.loading = false
      }
    },

    logout() {
      disconnectWebSocket()

      this.token = null
      this.username = null
      this.isAdmin = false

      localStorage.removeItem('vigia_token')
      localStorage.removeItem('vigia_username')
      localStorage.removeItem('vigia_is_admin')

      delete axios.defaults.headers.common['Authorization']
    },

    initAuth() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
      }
    },
  },
})
