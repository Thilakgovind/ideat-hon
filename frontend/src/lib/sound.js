let audio
let currentMood

export function stopMood() {
  if (!currentMood) return
  currentMood.stop()
  currentMood = null
}

export function playMood(mood) {
  stopMood()
  if (localStorage.getItem('avvai_sound') !== 'on') return
  try {
    const Context = window.AudioContext || window.webkitAudioContext
    audio ||= new Context()
    void audio.resume().catch(stopMood)
    const seconds = 2.4
    const buffer = audio.createBuffer(1, Math.ceil(audio.sampleRate * seconds), audio.sampleRate)
    const samples = buffer.getChannelData(0)
    for (let i = 0; i < samples.length; i++) samples[i] = Math.random() * 2 - 1
    const source = audio.createBufferSource()
    const filter = audio.createBiquadFilter()
    const gain = audio.createGain()
    filter.type = 'lowpass'
    filter.frequency.value = ({ stressed: 340, low: 520, steady: 880, rest: 380, okay: 940 })[mood] || 650
    source.buffer = buffer
    source.connect(filter).connect(gain).connect(audio.destination)
    gain.gain.setValueAtTime(0, audio.currentTime)
    gain.gain.linearRampToValueAtTime(.065, audio.currentTime + .5)
    gain.gain.linearRampToValueAtTime(0, audio.currentTime + seconds)
    source.onended = () => {
      if (currentMood === source) currentMood = null
      source.disconnect(); filter.disconnect(); gain.disconnect()
    }
    source.start()
    currentMood = source
  } catch { /* Check-ins also work without Web Audio. */ }
}
export function playCue() {
  if (localStorage.getItem('avvai_sound') !== 'on') return
  try {
    const Audio = window.AudioContext || window.webkitAudioContext
    audio ||= new Audio()
    audio.resume().then(() => {
      const oscillator = audio.createOscillator(), gain = audio.createGain()
      oscillator.connect(gain); gain.connect(audio.destination)
      oscillator.frequency.setValueAtTime(660, audio.currentTime)
      oscillator.frequency.exponentialRampToValueAtTime(880, audio.currentTime + .12)
      gain.gain.setValueAtTime(.035, audio.currentTime)
      gain.gain.exponentialRampToValueAtTime(.001, audio.currentTime + .2)
      oscillator.start(); oscillator.stop(audio.currentTime + .2)
    }).catch(() => {})
  } catch { /* Sound is optional; navigation must still work. */ }
}

