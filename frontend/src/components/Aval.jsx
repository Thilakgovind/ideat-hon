import { useMemo } from 'react'

import * as art from '@/aval/art'
import { cn } from '@/lib/utils'

/**
 * AVAL rendered live from design/aval/code (trusted local SVG strings).
 * state: idle | wave | listening | thinking | talking | alert
 * pose:  front (default) | cheer | guide | booking | face
 */
const MOOD_FOR_STATE = { idle: 'smile', wave: 'happy', listening: 'smile', thinking: 'thinking', talking: 'talking', alert: 'alert' }

export default function Aval({ state = 'idle', mood, pose = 'front', className, label }) {
  const svg = useMemo(() => {
    const m = mood || MOOD_FOR_STATE[state] || 'smile'
    switch (pose) {
      case 'cheer': return art.cheer()
      case 'guide': return art.guide()
      case 'booking': return art.booking()
      case 'face': return art.faceOnly(m)
      default: return art.front(m, state)
    }
  }, [state, mood, pose])
  return (
    <div
      className={cn('aval [&>svg]:block [&>svg]:h-full [&>svg]:w-full', className)}
      role="img"
      aria-label={label || `AVAL ${state}`}
      // Static SVG strings from our own design files, no user input.
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  )
}

export function AvalStatus({ state }) {
  if (state !== 'thinking') return null
  return (
    <span className="dots inline-flex gap-1" aria-label="AVAL is thinking">
      <span className="size-2 rounded-full bg-plum" />
      <span className="size-2 rounded-full bg-plum" />
      <span className="size-2 rounded-full bg-plum" />
    </span>
  )
}
