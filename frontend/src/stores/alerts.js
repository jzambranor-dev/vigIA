import { defineStore } from 'pinia'
import axios from 'axios'

export const useAlertsStore = defineStore('alerts', {
  state: () => ({
    alerts: [],
    total: 0,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchAlerts(params = {}) {
      this.loading = true
      this.error = null
      try {
        const { data } = await axios.get('/api/alerts/', { params })
        this.alerts = data.items
        this.total = data.total
      } catch (err) {
        this.error = err.response?.data?.detail || err.message
        if (window.__vigia_notify) window.__vigia_notify(this.error)
      } finally {
        this.loading = false
      }
    },

    async acknowledgeAlert(alertId) {
      try {
        await axios.patch(`/api/alerts/${alertId}/acknowledge`, { acknowledged: true })
        if (window.__vigia_notify) window.__vigia_notify('Alerta reconocida', 'success')
        await this.fetchAlerts()
      } catch (err) {
        this.error = err.response?.data?.detail || err.message
        if (window.__vigia_notify) window.__vigia_notify(this.error)
      }
    },
  },
})
