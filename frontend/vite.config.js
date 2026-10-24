import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const API = process.env.SAFEPATH_API || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@design': path.resolve(__dirname, '../design'),
    },
  },
  server: {
    port: 5173,
    fs: { allow: ['..'] },
    proxy: { '/api': API, '/health': API },
  },
})
