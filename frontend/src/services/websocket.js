import { ref } from 'vue'

const isConnected = ref(false)
let ws = null
let reconnectTimer = null
const listeners = new Map()

function getWsUrl() {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}/ws/events`
}

export function connectWebSocket() {
  const token = localStorage.getItem('vigia_token')
  if (!token || ws?.readyState === WebSocket.OPEN) return

  const url = `${getWsUrl()}?token=${token}`
  ws = new WebSocket(url)

  ws.onopen = () => {
    isConnected.value = true
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    // Ping cada 30s para mantener conexion viva
    ws._pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping')
      }
    }, 30000)
  }

  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      const type = msg.type // "event" o "alert"
      const callbacks = listeners.get(type) || []
      callbacks.forEach(cb => cb(msg.data))

      // Notificar a listeners "all" tambien
      const allCallbacks = listeners.get('all') || []
      allCallbacks.forEach(cb => cb(msg))
    } catch (e) {
      // Ignorar mensajes no-JSON (pongs)
    }
  }

  ws.onclose = () => {
    isConnected.value = false
    if (ws?._pingInterval) clearInterval(ws._pingInterval)
    // Reconectar en 3 segundos
    reconnectTimer = setTimeout(() => {
      connectWebSocket()
    }, 3000)
  }

  ws.onerror = () => {
    ws?.close()
  }
}

export function disconnectWebSocket() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (ws) {
    if (ws._pingInterval) clearInterval(ws._pingInterval)
    ws.onclose = null // Evitar reconexion
    ws.close()
    ws = null
  }
  isConnected.value = false
}

export function onWsMessage(type, callback) {
  if (!listeners.has(type)) listeners.set(type, [])
  listeners.get(type).push(callback)

  // Retorna funcion para desuscribirse
  return () => {
    const cbs = listeners.get(type)
    if (cbs) {
      const idx = cbs.indexOf(callback)
      if (idx > -1) cbs.splice(idx, 1)
    }
  }
}

export { isConnected }
