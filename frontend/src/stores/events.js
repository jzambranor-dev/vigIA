import { defineStore } from 'pinia'
import axios from 'axios'

export const useEventsStore = defineStore('events', {
  state: () => ({
    events: [],
    total: 0,
    loading: false,
    error: null,
  }),

  actions: {
    async fetchEvents(params = {}) {
      this.loading = true
      this.error = null
      try {
        const { data } = await axios.get('/api/events/', { params })
        this.events = data.items
        this.total = data.total
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
  },
})
