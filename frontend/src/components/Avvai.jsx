import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import './Avvai.css'

const FRAMES = { front: [0], back: [1], left: [2], right: [3], walk: [4, 5], run: [6, 7], jump: [9, 8, 8, 9], roll: [10], wave: [11, 0, 11, 8], dance: [11, 8, 0, 8] }

export function Avvai({ action = 'front', size = 112, label = 'Avvai, your sports companion' }) {
  const [step, setStep] = useState(0)
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    if (media.matches) return undefined
    const timer = setInterval(() => setStep(s => s + 1), action === 'run' ? 140 : 260)
    return () => clearInterval(timer)
  }, [action])
  const frames = FRAMES[action] || FRAMES.front
  const frame = frames[step % frames.length]
  return <span className={`avvai-sprite avvai-${action}`} role="img" aria-label={label} style={{ width: size, height: size, backgroundPosition: `${(frame % 4) * 100 / 3}% ${Math.floor(frame / 4) * 50}%` }} />
}

export function AvvaiCompanion() {
  const { pathname } = useLocation()
  const [hidden, setHidden] = useState(false)
  const [following, setFollowing] = useState(false)
  const [action, setAction] = useState('wave')
  const follower = useRef(null)
  const sensitive = pathname === '/veeramangai' || /sos|payment|private|aval/.test(pathname) || /\/(agent|voice|support|login)$/.test(pathname)
  useEffect(() => {
    if (!following || hidden || sensitive || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined
    let target = { x: window.innerWidth - 75, y: window.innerHeight - 170 }
    const current = { ...target }
    let raf, resting, jumping
    const fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches
    if (fine) document.documentElement.classList.add('avvai-cursor-mode')
    function move(e) {
      target = { x: Math.max(8, Math.min(window.innerWidth - 60, e.clientX)), y: Math.max(8, Math.min(window.innerHeight - 60, e.clientY)) }
      if (follower.current) follower.current.style.setProperty('--avvai-direction', target.x < current.x ? '-1' : '1')
      if (fine) document.documentElement.classList.add('avvai-cursor-mode')
      setAction('walk'); clearTimeout(resting)
      resting = setTimeout(() => setAction('front'), 280)
    }
    function tap(e) {
      if (e.target.closest('input,textarea,select,button,a,[contenteditable]')) return
      move(e); setAction('jump'); clearTimeout(jumping)
      jumping = setTimeout(() => setAction('front'), 850)
    }
    function keyboard(e) { if (e.key === 'Tab') document.documentElement.classList.remove('avvai-cursor-mode') }
    function tick() {
      current.x += (target.x - current.x) * .2
      current.y += (target.y - current.y) * .2
      if (follower.current) follower.current.style.transform = `translate3d(${current.x}px,${current.y}px,0)`
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    window.addEventListener('pointermove', move, { passive: true })
    window.addEventListener('pointerdown', tap, { passive: true })
    window.addEventListener('keydown', keyboard)
    return () => {
      cancelAnimationFrame(raf); clearTimeout(resting); clearTimeout(jumping)
      document.documentElement.classList.remove('avvai-cursor-mode')
      window.removeEventListener('pointermove', move); window.removeEventListener('pointerdown', tap); window.removeEventListener('keydown', keyboard)
    }
  }, [following, hidden, sensitive])
  if (sensitive) return null
  return <>
    <aside className="avvai-control" aria-label="Avvai companion controls">
      {hidden ? <button onClick={() => setHidden(false)}>Show Avvai</button> : <><button aria-pressed={following} onClick={() => setFollowing(!following)}>{following ? 'Avvai cursor: on' : 'Avvai cursor: off'}</button><button onClick={() => setHidden(true)} aria-label="Hide Avvai">×</button></>}
    </aside>
    {!hidden && <div ref={follower} className={following ? 'avvai-follower' : 'avvai-docked'} aria-hidden="true"><div className="avvai-facing"><Avvai action={action} size={following ? 56 : 88} /></div></div>}
  </>
}

export default function AvvaiStudio() {
  const [action, setAction] = useState('front')
  return <main className="avvai-studio">
    <p>VEERAMANGAI · CHARACTER STUDIO</p>
    <h1>Vanakkam. I’m Avvai.</h1>
    <p>Your sporty Tamil companion. Choose a view or movement.</p>
    <div className="avvai-stage"><Avvai action={action} size={240} /></div>
    <div className="avvai-actions">{Object.keys(FRAMES).map(name => <button key={name} aria-pressed={action === name} onClick={() => setAction(name)}>{name}</button>)}</div>
    <p>Walking and running use two illustrated poses; jumping, rolling and dancing add CSS motion. Reduced-motion preferences are respected.</p>
    <a href="/veeramangai">Back to the app →</a>
  </main>
}
