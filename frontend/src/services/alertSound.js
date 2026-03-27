/**
 * Servicio de alertas sonoras para eventos CRITICAL.
 * Genera un tono de alerta usando Web Audio API (no necesita archivos de sonido).
 */

let audioCtx = null
let soundEnabled = localStorage.getItem('vigia_sound') !== 'false'

export function isSoundEnabled() {
  return soundEnabled
}

export function toggleSound() {
  soundEnabled = !soundEnabled
  localStorage.setItem('vigia_sound', soundEnabled)
  return soundEnabled
}

export function playAlertSound(severity = 'CRITICAL') {
  if (!soundEnabled) return

  try {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    }

    const now = audioCtx.currentTime

    if (severity === 'CRITICAL') {
      // Tono de alerta urgente: dos tonos descendentes
      playTone(880, now, 0.15)
      playTone(660, now + 0.18, 0.15)
      playTone(880, now + 0.4, 0.15)
      playTone(660, now + 0.58, 0.15)
    } else if (severity === 'HIGH') {
      // Tono simple
      playTone(740, now, 0.2)
    }
  } catch (e) {
    // Audio API no disponible
  }
}

function playTone(freq, startTime, duration) {
  const osc = audioCtx.createOscillator()
  const gain = audioCtx.createGain()

  osc.connect(gain)
  gain.connect(audioCtx.destination)

  osc.type = 'sine'
  osc.frequency.setValueAtTime(freq, startTime)

  gain.gain.setValueAtTime(0.3, startTime)
  gain.gain.exponentialRampToValueAtTime(0.01, startTime + duration)

  osc.start(startTime)
  osc.stop(startTime + duration)
}
