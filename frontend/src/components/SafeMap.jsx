import 'maplibre-gl/dist/maplibre-gl.css'

import * as maplibregl from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { useEffect, useRef, useState } from 'react'

// Point MapLibre at its worker explicitly (its relative worker path breaks under Vite).
maplibregl.setWorkerUrl(workerUrl)

const KEY = import.meta.env.VITE_MAPTILER_KEY
const STYLES = {
  light: `https://api.maptiler.com/maps/streets-v2-pastel/style.json?key=${KEY}`,
  dark: `https://api.maptiler.com/maps/streets-v2-dark/style.json?key=${KEY}`,
}

// Brand tint over the light base map: cream land, lilac water, soft green parks.
const TINT = [
  [/^background$/, 'background', 'background-color', '#FFF7EC'],
  [/water/, 'fill', 'fill-color', '#DCD3F0'],
  [/park|grass|wood/, 'fill', 'fill-color', '#E3F1E4'],
]

// Place-type colours for the clustered dots (neutral signals only, never people).
export const TYPE_COLORS = {
  pharmacy: '#0E7C74', hospital: '#E3263F', police_booth: '#1F4FB8', shg_kiosk: '#E0457B',
  tea_shop: '#E8960F', bakery: '#E8960F', grocery: '#6B2FA0', atm: '#0B7F74',
  bus_shelter: '#4A1D6E', metro: '#4A1D6E', petrol_bunk: '#C2410C',
}

export const mapAvailable = () => Boolean(KEY)

const toLngLat = (p) => [p[1], p[0]] // our data is [lat, lng]

/**
 * MapLibre + MapTiler map. Renders `fallback` when there is no key or the map fails.
 * routes:  [{ id, coords: [[lat,lng]...], color, width, dashed, glow }]
 * pins:    [{ id, lat, lng, color, label, size, onClick, element }]   a few HTML markers
 * glows:   [{ lat, lng, level }]   anonymous crowd areas (never individuals)
 * places:  [{ id, lat, lng, type, open_now, women_run, name }]   clustered dots, scales to hundreds
 * me:      [lat, lng]   her own position; drawn on this screen only, never sent anywhere
 */
export default function SafeMap({ theme = 'light', center, zoom = 14, routes = [], pins = [], glows = [], places, me, onPlace,
  fit, className, fallback }) {
  const box = useRef(null)
  const map = useRef(null)
  const markers = useRef([])
  const onPlaceRef = useRef(onPlace)
  const [failed, setFailed] = useState(!KEY)
  const [ready, setReady] = useState(false)

  useEffect(() => { onPlaceRef.current = onPlace }, [onPlace])

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
    const giveUp = setTimeout(() => { if (!m.loaded()) setFailed(true) }, 12000)
    m.on('load', () => {
      clearTimeout(giveUp)
      if (theme === 'light') {
        for (const layer of m.getStyle().layers) {
          for (const [re, type, prop, color] of TINT) {
            if (layer.type === type && re.test(layer.id)) {
              try { m.setPaintProperty(layer.id, prop, color) } catch { /* layer without that property */ }
            }
          }
        }
      }
      setReady(true)
    })
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
    const upsert = (id, dataObj, layers, opts = {}) => {
      if (m.getSource(id)) m.getSource(id).setData(dataObj)
      else {
        m.addSource(id, { type: 'geojson', data: dataObj, ...opts })
        layers.forEach((l) => m.addLayer(l))
      }
    }

    upsert('crowd', {
      type: 'FeatureCollection',
      features: glows.map((g) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [g.lng, g.lat] },
        properties: { w: { busy: 1, moderate: 0.65, quiet: 0.3, empty: 0 }[g.level] ?? 0.3 } })),
    }, [{
      id: 'crowd-heat', type: 'heatmap', source: 'crowd',
      paint: {
        'heatmap-weight': ['get', 'w'], 'heatmap-radius': 45, 'heatmap-intensity': 1, 'heatmap-opacity': 0.65,
        'heatmap-color': ['interpolate', ['linear'], ['heatmap-density'], 0, 'rgba(255,181,46,0)', 0.4, 'rgba(255,181,46,0.35)', 1, 'rgba(255,181,46,0.75)'],
      },
    }])

    upsert('routes', {
      type: 'FeatureCollection',
      features: routes.map((r) => ({ type: 'Feature', geometry: { type: 'LineString', coordinates: r.coords.map(toLngLat) },
        properties: { id: r.id, color: r.color || '#2EE6A8', width: r.width || 5, dashed: r.dashed ? 1 : 0, glow: r.glow ? 1 : 0 } })),
    }, [
      { id: 'routes-glow', type: 'line', source: 'routes', filter: ['==', ['get', 'glow'], 1],
        layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': ['get', 'color'], 'line-width': 16, 'line-opacity': 0.22 } },
      { id: 'routes-solid', type: 'line', source: 'routes', filter: ['==', ['get', 'dashed'], 0],
        layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': ['get', 'color'], 'line-width': ['get', 'width'] } },
      { id: 'routes-dashed', type: 'line', source: 'routes', filter: ['==', ['get', 'dashed'], 1],
        layout: { 'line-cap': 'round' }, paint: { 'line-color': ['get', 'color'], 'line-width': ['get', 'width'], 'line-dasharray': [0.5, 2] } },
    ])

    if (places) {
      const isPoint = ['!', ['has', 'point_count']]
      const isCluster = ['has', 'point_count']
      const firstTime = !m.getSource('places')
      upsert('places', {
        type: 'FeatureCollection',
        features: places.map((p) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: [p.lng, p.lat] },
          properties: { id: p.id, name: (p.name || '').replace(/ \(.*\)$/, ''), color: TYPE_COLORS[p.type] || '#6B2FA0',
            open: p.open_now ? 1 : 0, women: p.women_run ? 1 : 0 } })),
      }, [
        { id: 'cluster-halo', type: 'circle', source: 'places', filter: isCluster,
          paint: { 'circle-color': '#E0457B', 'circle-opacity': 0.2, 'circle-radius': ['step', ['get', 'point_count'], 25, 10, 31, 30, 38] } },
        { id: 'clusters', type: 'circle', source: 'places', filter: isCluster,
          paint: { 'circle-color': '#4A1D6E', 'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': 3,
            'circle-radius': ['step', ['get', 'point_count'], 17, 10, 21, 30, 26] } },
        { id: 'cluster-count', type: 'symbol', source: 'places', filter: isCluster,
          layout: { 'text-field': ['get', 'point_count_abbreviated'], 'text-font': ['Noto Sans Bold'], 'text-size': 14, 'text-allow-overlap': true },
          paint: { 'text-color': '#FFFFFF' } },
        { id: 'place-women', type: 'circle', source: 'places', filter: ['all', isPoint, ['==', ['get', 'women'], 1]],
          paint: { 'circle-radius': 15, 'circle-color': 'rgba(224,69,123,0.16)', 'circle-stroke-color': '#E0457B', 'circle-stroke-width': 2 } },
        { id: 'place-dot', type: 'circle', source: 'places', filter: isPoint,
          paint: { 'circle-radius': 9, 'circle-color': ['case', ['==', ['get', 'open'], 1], ['get', 'color'], '#B9B0C4'],
            'circle-stroke-color': '#FFFFFF', 'circle-stroke-width': 3 } },
        { id: 'place-name', type: 'symbol', source: 'places', filter: isPoint, minzoom: 15,
          layout: { 'text-field': ['get', 'name'], 'text-font': ['Noto Sans Bold'], 'text-size': 12, 'text-offset': [0, 1.4],
            'text-anchor': 'top', 'text-max-width': 9, 'text-optional': true },
          paint: { 'text-color': '#24132F', 'text-halo-color': '#FFFFFF', 'text-halo-width': 1.8 } },
      ], { cluster: true, clusterRadius: 44, clusterMaxZoom: 15 })
      if (firstTime) {
        m.on('click', 'clusters', async (e) => {
          const f = e.features[0]
          const z = await m.getSource('places').getClusterExpansionZoom(f.properties.cluster_id)
          m.easeTo({ center: f.geometry.coordinates, zoom: z + 0.3, duration: 500 })
        })
        m.on('click', 'place-dot', (e) => onPlaceRef.current?.(e.features[0].properties.id))
        for (const id of ['clusters', 'place-dot']) {
          m.on('mouseenter', id, () => { m.getCanvas().style.cursor = 'pointer' })
          m.on('mouseleave', id, () => { m.getCanvas().style.cursor = '' })
        }
      }
    }

    markers.current.forEach((mk) => mk.remove())
    markers.current = []
    if (me) {
      const el = document.createElement('div')
      el.className = 'sp-me'
      el.setAttribute('role', 'img')
      el.setAttribute('aria-label', 'You are here')
      el.innerHTML = '<span class="sp-me-pulse"></span><span class="sp-me-dot"></span>'
      markers.current.push(new maplibregl.Marker({ element: el }).setLngLat(toLngLat(me)).addTo(m))
    }
    for (const p of pins) {
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
      markers.current.push(new maplibregl.Marker({ element: el }).setLngLat([p.lng, p.lat]).addTo(m))
    }

    const pts = fit || routes.flatMap((r) => r.coords)
    if (pts.length > 1) {
      const b = pts.reduce((acc, p) => acc.extend(toLngLat(p)), new maplibregl.LngLatBounds(toLngLat(pts[0]), toLngLat(pts[0])))
      m.fitBounds(b, { padding: { top: 120, bottom: 60, left: 50, right: 50 }, maxZoom: 16, duration: 0 })
    }
  }, [ready, routes, pins, glows, places, me, fit, theme])

  // re-centre when the caller moves the focus (e.g. "near me")
  useEffect(() => {
    if (map.current && ready && center && !fit) map.current.easeTo({ center: toLngLat(center), zoom, duration: 600 })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, center?.[0], center?.[1], zoom])

  if (failed) return fallback || null
  // MapLibre's CSS makes the map box position:relative, so position the wrapper instead.
  return (
    <div className={className} role="region" aria-label="Map">
      <div ref={box} className="h-full w-full" />
    </div>
  )
}
