<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const loading = ref(true)
const activeTab = ref('smtp')

// SMTP
const smtp = ref({ host: '', port: 465, ssl: true, user: '', password: '', alert_email_to: '' })
const smtpSaving = ref(false)
const smtpTesting = ref(false)

// General
const general = ref({ log_paths: '', cors_origins: '', jwt_expire_minutes: 480 })
const generalSaving = ref(false)

// Info
const info = ref({})

// Usuarios
const users = ref([])
const newUser = ref({ username: '', password: '', is_admin: false })
const creatingUser = ref(false)

// Password
const passwordForm = ref({ current: '', new: '', confirm: '' })
const changingPw = ref(false)

onMounted(async () => {
  try {
    const [settingsRes, usersRes] = await Promise.all([
      axios.get('/api/settings/current'),
      authStore.isAdmin ? axios.get('/api/auth/users') : Promise.resolve({ data: [] }),
    ])
    const s = settingsRes.data
    smtp.value = {
      host: s.smtp.host,
      port: s.smtp.port,
      ssl: s.smtp.ssl,
      user: s.smtp.user,
      password: '',
      alert_email_to: s.smtp.alert_email_to,
    }
    general.value = {
      log_paths: s.general.log_paths,
      cors_origins: s.general.cors_origins,
      jwt_expire_minutes: s.general.jwt_expire_minutes,
    }
    info.value = s.info
    users.value = usersRes.data
  } catch (err) {
    if (window.__vigia_notify) window.__vigia_notify('Error cargando configuracion')
  } finally {
    loading.value = false
  }
})

const saveSMTP = async () => {
  smtpSaving.value = true
  try {
    await axios.put('/api/settings/smtp', {
      smtp_host: smtp.value.host,
      smtp_port: smtp.value.port,
      smtp_ssl: smtp.value.ssl,
      smtp_user: smtp.value.user,
      smtp_password: smtp.value.password,
      alert_email_to: smtp.value.alert_email_to,
    })
    if (window.__vigia_notify) window.__vigia_notify('SMTP guardado', 'success')
  } catch (err) {
    if (window.__vigia_notify) window.__vigia_notify(err.response?.data?.detail || 'Error guardando SMTP')
  } finally {
    smtpSaving.value = false
  }
}

const testEmail = async () => {
  smtpTesting.value = true
  try {
    const { data } = await axios.post('/api/settings/test-email')
    if (window.__vigia_notify) window.__vigia_notify(data.message, 'success')
  } catch (err) {
    if (window.__vigia_notify) window.__vigia_notify(err.response?.data?.detail || 'Error enviando email')
  } finally {
    smtpTesting.value = false
  }
}

const saveGeneral = async () => {
  generalSaving.value = true
  try {
    await axios.put('/api/settings/general', general.value)
    if (window.__vigia_notify) window.__vigia_notify('Configuracion guardada', 'success')
  } catch (err) {
    if (window.__vigia_notify) window.__vigia_notify(err.response?.data?.detail || 'Error guardando')
  } finally {
    generalSaving.value = false
  }
}

const createUser = async () => {
  if (!newUser.value.username || !newUser.value.password) return
  creatingUser.value = true
  try {
    await axios.post('/api/auth/users', newUser.value)
    if (window.__vigia_notify) window.__vigia_notify(`Usuario ${newUser.value.username} creado`, 'success')
    newUser.value = { username: '', password: '', is_admin: false }
    const { data } = await axios.get('/api/auth/users')
    users.value = data
  } catch (err) {
    if (window.__vigia_notify) window.__vigia_notify(err.response?.data?.detail || 'Error creando usuario')
  } finally {
    creatingUser.value = false
  }
}

const deleteUser = async (username) => {
  if (!confirm(`Eliminar usuario ${username}?`)) return
  try {
    await axios.delete(`/api/auth/users/${username}`)
    users.value = users.value.filter(u => u.username !== username)
    if (window.__vigia_notify) window.__vigia_notify(`Usuario ${username} eliminado`, 'success')
  } catch (err) {
    if (window.__vigia_notify) window.__vigia_notify(err.response?.data?.detail || 'Error eliminando')
  }
}

const changePassword = async () => {
  if (passwordForm.value.new !== passwordForm.value.confirm) {
    if (window.__vigia_notify) window.__vigia_notify('Las contrasenas no coinciden', 'warning')
    return
  }
  changingPw.value = true
  try {
    await axios.put(`/api/auth/password?current_password=${encodeURIComponent(passwordForm.value.current)}&new_password=${encodeURIComponent(passwordForm.value.new)}`)
    if (window.__vigia_notify) window.__vigia_notify('Contrasena actualizada', 'success')
    passwordForm.value = { current: '', new: '', confirm: '' }
  } catch (err) {
    if (window.__vigia_notify) window.__vigia_notify(err.response?.data?.detail || 'Error cambiando contrasena')
  } finally {
    changingPw.value = false
  }
}

const inputClass = "w-full bg-primary border border-accent rounded-lg px-4 py-2.5 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-danger transition-colors"
</script>

<template>
  <div>
    <h2 class="text-2xl font-bold mb-6">Configuracion</h2>

    <div v-if="loading" class="text-center py-10">Cargando...</div>

    <div v-else>
      <!-- Tabs -->
      <div class="flex gap-1 mb-6 bg-secondary rounded-lg p-1 border border-accent w-fit">
        <button v-for="tab in ['smtp', 'general', 'usuarios', 'password', 'info']" :key="tab"
          @click="activeTab = tab"
          class="px-4 py-2 rounded-md text-sm capitalize transition-colors"
          :class="activeTab === tab ? 'bg-danger text-white' : 'text-gray-400 hover:text-white'"
        >{{ tab === 'smtp' ? 'Email SMTP' : tab === 'password' ? 'Contrasena' : tab }}</button>
      </div>

      <!-- SMTP -->
      <div v-if="activeTab === 'smtp'" class="bg-secondary rounded-lg p-6 border border-accent max-w-2xl space-y-4">
        <h3 class="text-lg font-semibold mb-2">Configuracion del Servidor de Correo</h3>
        <p class="text-gray-400 text-sm mb-4">Las alertas CRITICAL se envian automaticamente al correo configurado.</p>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs text-gray-400 mb-1">Host SMTP</label>
            <input v-model="smtp.host" :class="inputClass" placeholder="smtp.hostinger.com" />
          </div>
          <div>
            <label class="block text-xs text-gray-400 mb-1">Puerto</label>
            <input v-model.number="smtp.port" type="number" :class="inputClass" />
          </div>
        </div>
        <div class="flex items-center gap-3">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="smtp.ssl" class="accent-danger" />
            <span class="text-sm text-gray-300">SSL/TLS</span>
          </label>
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Usuario / Email</label>
          <input v-model="smtp.user" :class="inputClass" placeholder="info@devs-rick.com" />
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Contrasena</label>
          <input v-model="smtp.password" type="password" :class="inputClass" placeholder="Dejar vacio para no cambiar" />
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Enviar alertas a</label>
          <input v-model="smtp.alert_email_to" :class="inputClass" placeholder="admin@ejemplo.com" />
        </div>
        <div class="flex gap-3 pt-2">
          <button @click="saveSMTP" :disabled="smtpSaving"
            class="bg-danger hover:bg-danger/80 px-5 py-2 rounded text-sm font-semibold transition-colors disabled:opacity-50">
            {{ smtpSaving ? 'Guardando...' : 'Guardar SMTP' }}
          </button>
          <button @click="testEmail" :disabled="smtpTesting"
            class="bg-accent hover:bg-accent/80 px-5 py-2 rounded text-sm transition-colors disabled:opacity-50">
            {{ smtpTesting ? 'Enviando...' : 'Enviar Email de Prueba' }}
          </button>
        </div>
      </div>

      <!-- General -->
      <div v-if="activeTab === 'general'" class="bg-secondary rounded-lg p-6 border border-accent max-w-2xl space-y-4">
        <h3 class="text-lg font-semibold mb-2">Configuracion General</h3>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Rutas de logs a monitorear (separadas por coma)</label>
          <input v-model="general.log_paths" :class="inputClass" placeholder="/host/logs/auth.log,/host/logs/syslog" />
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Origenes CORS permitidos (separados por coma)</label>
          <input v-model="general.cors_origins" :class="inputClass" placeholder="https://vigia.devs-rick.com" />
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Duracion del token JWT (minutos)</label>
          <input v-model.number="general.jwt_expire_minutes" type="number" :class="inputClass" />
        </div>
        <button @click="saveGeneral" :disabled="generalSaving"
          class="bg-danger hover:bg-danger/80 px-5 py-2 rounded text-sm font-semibold transition-colors disabled:opacity-50">
          {{ generalSaving ? 'Guardando...' : 'Guardar' }}
        </button>
        <p class="text-xs text-gray-500">Algunos cambios requieren reiniciar el backend (docker compose restart backend).</p>
      </div>

      <!-- Usuarios -->
      <div v-if="activeTab === 'usuarios'" class="space-y-4 max-w-2xl">
        <div class="bg-secondary rounded-lg p-6 border border-accent">
          <h3 class="text-lg font-semibold mb-4">Usuarios del Sistema</h3>
          <div class="space-y-2">
            <div v-for="u in users" :key="u.id"
              class="flex items-center justify-between bg-primary rounded-lg px-4 py-3">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-full bg-accent flex items-center justify-center text-sm font-bold">
                  {{ u.username[0].toUpperCase() }}
                </div>
                <div>
                  <p class="text-sm font-semibold">{{ u.username }}</p>
                  <p class="text-xs text-gray-500">{{ u.is_admin ? 'Administrador' : 'Usuario' }} - {{ new Date(u.created_at).toLocaleDateString() }}</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span v-if="u.is_admin" class="text-xs bg-danger/20 text-danger px-2 py-0.5 rounded">admin</span>
                <button v-if="u.username !== authStore.username" @click="deleteUser(u.username)"
                  class="text-gray-500 hover:text-red-400 transition-colors text-xs">Eliminar</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Crear usuario -->
        <div class="bg-secondary rounded-lg p-6 border border-accent">
          <h3 class="text-sm font-semibold mb-3">Crear Nuevo Usuario</h3>
          <div class="grid grid-cols-2 gap-3">
            <input v-model="newUser.username" :class="inputClass" placeholder="Nombre de usuario" />
            <input v-model="newUser.password" type="password" :class="inputClass" placeholder="Contrasena" />
          </div>
          <div class="flex items-center justify-between mt-3">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="newUser.is_admin" class="accent-danger" />
              <span class="text-sm text-gray-300">Administrador</span>
            </label>
            <button @click="createUser" :disabled="creatingUser"
              class="bg-danger hover:bg-danger/80 px-4 py-2 rounded text-sm font-semibold transition-colors disabled:opacity-50">
              {{ creatingUser ? 'Creando...' : 'Crear Usuario' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Password -->
      <div v-if="activeTab === 'password'" class="bg-secondary rounded-lg p-6 border border-accent max-w-md space-y-4">
        <h3 class="text-lg font-semibold mb-2">Cambiar Contrasena</h3>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Contrasena actual</label>
          <input v-model="passwordForm.current" type="password" :class="inputClass" />
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Nueva contrasena</label>
          <input v-model="passwordForm.new" type="password" :class="inputClass" />
        </div>
        <div>
          <label class="block text-xs text-gray-400 mb-1">Confirmar nueva contrasena</label>
          <input v-model="passwordForm.confirm" type="password" :class="inputClass" />
        </div>
        <button @click="changePassword" :disabled="changingPw"
          class="bg-danger hover:bg-danger/80 px-5 py-2 rounded text-sm font-semibold transition-colors disabled:opacity-50">
          {{ changingPw ? 'Cambiando...' : 'Cambiar Contrasena' }}
        </button>
      </div>

      <!-- Info -->
      <div v-if="activeTab === 'info'" class="bg-secondary rounded-lg p-6 border border-accent max-w-md">
        <h3 class="text-lg font-semibold mb-4">Informacion del Sistema</h3>
        <div class="space-y-3 text-sm">
          <div class="flex justify-between">
            <span class="text-gray-400">Version</span>
            <span>{{ info.version }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">PostgreSQL</span>
            <span class="font-mono text-xs">{{ info.postgres_host }}:5432/{{ info.postgres_db }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Redis</span>
            <span class="font-mono text-xs">{{ info.redis_host }}:6379</span>
          </div>
          <hr class="border-accent">
          <div class="flex justify-between">
            <span class="text-gray-400">Proyecto</span>
            <span>vigIA - Log Analyzer AI</span>
          </div>
          <div class="flex justify-between">
            <span class="text-gray-400">Autor</span>
            <span>J. Zambrano R.</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
