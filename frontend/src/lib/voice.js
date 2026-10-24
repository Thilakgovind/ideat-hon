import { useRef, useState } from 'react'

/** Hold-to-talk recorder. Resolves with an audio Blob, or null if the mic is unavailable. */
export function useRecorder() {
  const rec = useRef(null)
  const chunks = useRef([])
  const started = useRef(0)
  const [recording, setRecording] = useState(false)

  async function start() {
    started.current = Date.now()
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setRecording(true)
      return
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      chunks.current = []
      const r = new MediaRecorder(stream)
      r.ondataavailable = (e) => e.data.size && chunks.current.push(e.data)
      r.start()
      rec.current = r
    } catch {
      rec.current = null // permission denied: we still run the demo flow without audio
    }
    setRecording(true)
  }

  function stop() {
    setRecording(false)
    const seconds = Math.max(1, Math.round((Date.now() - started.current) / 1000))
    const r = rec.current
    rec.current = null
    if (!r) return Promise.resolve({ blob: null, seconds })
    return new Promise((resolve) => {
      r.onstop = () => {
        r.stream.getTracks().forEach((tr) => tr.stop())
        resolve({ blob: chunks.current.length ? new Blob(chunks.current, { type: r.mimeType }) : null, seconds })
      }
      r.stop()
    })
  }

  return { recording, start, stop }
}

/** Play Sarvam audio if we got it; otherwise speak with the device voice. Resolves when done. */
export function speak({ audioBase64, format = 'wav', text, lang }) {
  return new Promise((resolve) => {
    if (audioBase64) {
      const audio = new Audio(`data:audio/${format};base64,${audioBase64}`)
      audio.onended = resolve
      audio.onerror = resolve
      audio.play().catch(resolve)
      return
    }
    if (!('speechSynthesis' in window) || !text) return resolve()
    const u = new SpeechSynthesisUtterance(text)
    u.lang = lang === 'ta' ? 'ta-IN' : 'en-IN'
    u.onend = resolve
    u.onerror = resolve
    window.speechSynthesis.cancel()
    window.speechSynthesis.speak(u)
    setTimeout(resolve, 20000) // never hang the UI (voice replies are short)
  })
}
