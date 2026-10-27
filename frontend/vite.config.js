import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

const ROOT = path.resolve(import.meta.dirname, '..')

// Only these PUBLIC values ever reach the browser. Everything else in the root .env
// (service key, Razorpay secret, Twilio, textbee, Gemini, Sarvam) stays on the backend.
const PUBLIC_ENV = {
  VITE_MAPTILER_KEY: ['VITE_MAPTILER_KEY', 'MAPTILER_KEY'],
  VITE_SUPABASE_URL: ['VITE_SUPABASE_URL', 'SUPABASE_URL'],
  VITE_SUPABASE_ANON_KEY: ['VITE_SUPABASE_ANON_KEY', 'SUPABASE_ANON_KEY'],
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ROOT, '')
  const API = process.env.SAFEPATH_API || 'http://localhost:8000'
  const define = {}
  for (const [name, sources] of Object.entries(PUBLIC_ENV)) {
    const value = sources.map((s) => env[s]).find(Boolean) || ''
    define[`import.meta.env.${name}`] = JSON.stringify(value)
  }
  return {
    envDir: ROOT,
    envPrefix: 'VITE_PUBLIC_ONLY_', // nothing is exposed by prefix; only the `define` list above
    define,
    plugins: [react(), tailwindcss()],
    // MapLibre spawns its own web worker; pre-bundling breaks the worker URL in dev.
    optimizeDeps: { exclude: ['maplibre-gl'] },
    resolve: {
      alias: {
        '@': path.resolve(import.meta.dirname, './src'),
        '@design': path.resolve(import.meta.dirname, '../design'),
      },
    },
    server: {
      port: 5173,
      fs: { allow: ['..'] },
      proxy: { '/api': API, '/health': API },
    },
  }
})
