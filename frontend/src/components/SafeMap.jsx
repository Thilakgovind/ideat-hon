import 'maplibre-gl/dist/maplibre-gl.css'

import * as maplibregl from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { useEffect, useRef, useState } from 'react'

// Point MapLibre at its worker explicitly (its relative worker path breaks under Vite).
maplibregl.setWorkerUrl(workerUrl)

const KEY = import.meta.env.VITE_MAPTILER_KEY
const STYLES = {
  light: `https://api.maptiler.com/maps/streets-v2/style.json?key=${KEY}`,
  dark: `https://api.maptiler.com/maps/streets-v2-dark/style.json?key=${KEY}`,
}

export const mapAvailable = () => Boolean(KEY)

const toLngLat = (p) => [p[1], p[0]] // our data is [lat, lng]

/**
 * MapLibre + MapTiler map. Renders `fallback` when there is no key or the map fails.
 * routes:  [{ id, coords: [[lat,lng]...], color, width, dashed, glow }]
 * pins:    [{ id, lat, lng, color, label, size, onClick, element }]
 * glows:   [{ lat, lng, level }]   anonymous crowd areas (never individuals)
 */
export default function SafeMap({ theme = 'light', center, zoom = 14, routes = [], pins = [], glows = [], fit, className, fallback }) {
  const box = useRef(null)
  const map = useRef(null)
  const markers = useRef([])
  const [failed, setFailed] = useState(!KEY)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (!KEY || !box.current) return undefined
    let m
    try {
      m = new maplibregl.Map({
        container: box.current,
        style: STYLES[theme],
        center: center ? toLngLat(center) : [80.2422, 13.0604],
        zoom,
        attributionControl: { compact: true },
      })
    } catch {
      setFailed(true)
      return undefined
    }
    map.current = m
    // If the style never finishes loading (slow 3G, tile/style error), show the illustrated fallback.
    const giveUp = setTimeout(() => { if (!m.loaded()) setFailed(true) }, 8000)
    m.on('load', () => { clearTimeout(giveUp); setReady(true) })
    m.on('error', (e) => {
      if (!m.loaded() && /style|401|403|Failed to fetch/i.test(String(e?.error?.message || e?.error?.status || ''))) setFailed(true)
    })
    return () => {
      clearTimeout(giveUp)
      markers.current.forEach((mk) => mk.remove())
      markers.current = []
      m.remove()
      map.current = null
      setReady(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [theme])

  // data layers
  useEffect(() => {
    const m = map.current
    if (!m || !ready) return
    const glowData = {
      type: 'FeatureCollection',
      features: glows.map((g) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [g.lng, g.lat] },
        properties: { w: { busy: 1, moderate: 0.65, quiet: 0.3, empty: 0 }[g.level] ?? 0.3 } })),
    }
    const routeData = {
      type: 'FeatureCollection',
      features: routes.map((r) => ({ type: 'Feature', geometry: { type: 'LineString', coordinates: r.coords.map(toLngLat) },
        properties: { id: r.id, color: r.color || '#2EE6A8', width: r.width || 5, dashed: r.dashed ? 1 : 0, glow: r.glow ? 1 : 0 } })),
    }
    const upsert = (id, dataObj, layers) => {
      if (m.getSource(id)) m.getSource(id).setData(dataObj)
      else {
        m.addSource(id, { type: 'geojson', data: dataObj })
        layers.forEach((l) => m.addLayer(l))
      }
    }
    upsert('crowd', glowData, [{
      id: 'crowd-heat', type: 'heatmap', source: 'crowd',
      paint: {
        'heatmap-weight': ['get', 'w'], 'heatmap-radius': 45, 'heatmap-intensity': 1, 'heatmap-opacity': 0.65,
        'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'], 0, 'rgba(255,181,46,0)', 0.4, 'rgba(255,181,46,0.35)', 1, 'rgba(255,181,46,0.75)'],
      },
    }])
    upsert('routes', routeData, [
      { id: 'routes-glow', type: 'line', source: 'routes', filter: ['==', ['get', 'glow'], 1],
        layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': ['get', 'color'], 'line-width': 16, 'line-opacity': 0.22 } },
      { id: 'routes-solid', type: 'line', source: 'routes', filter: ['==', ['get', 'dashed'], 0],
        layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': ['get', 'color'], 'line-width': ['get', 'width'] } },
      { id: 'routes-dashed', type: 'line', source: 'routes', filter: ['==', ['get', 'dashed'], 1],
        layout: { 'line-cap': 'round' }, paint: { 'line-color': ['get', 'color'], 'line-width': ['get', 'width'], 'line-dasharray': [0.5, 2] } },
    ])

    markers.current.forEach((mk) => mk.remove())
    markers.current = pins.map((p) => {
      let el = p.element
      if (!el) {
        el = document.createElement('button')
        el.type = 'button'
        el.title = p.label || ''
        el.setAttribute('aria-label', p.label || 'place')
        const s = p.size || 18
        el.style.cssText = `width:${s}px;height:${s}px;border-radius:50%;background:${p.color || '#2EE6A8'};border:3px solid ${theme === 'dark' ? '#120F19' : '#fff'};box-shadow:0 2px 6px rgba(0,0,0,.25);cursor:pointer;padding:0`
      }
      if (p.onClick) el.addEventListener('click', p.onClick)
      return new maplibregl.Marker({ element: el }).setLngLat([p.lng, p.lat]).addTo(m)
    })

    const pts = fit || routes.flatMap((r) => r.coords)
    if (pts.length > 1) {
      const b = pts.reduce((acc, p) => acc.extend(toLngLat(p)), new maplibregl.LngLatBounds(toLngLat(pts[0]), toLngLat(pts[0])))
      m.fitBounds(b, { padding: { top: 120, bottom: 60, left: 50, right: 50 }, maxZoom: 16, duration: 0 })
    }
  }, [ready, routes, pins, glows, fit, theme])

  if (failed) return fallback || null
  // MapLibre's CSS makes the map box position:relative, so position the wrapper instead.
  return (
    <div className={className} role="region" aria-label="Map">
      <div ref={box} className="h-full w-full" />
    </div>
  )
}
