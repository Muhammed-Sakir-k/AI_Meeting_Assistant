import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        main: 'vite_index.html'
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/upload': 'http://localhost:8000',
      '/status': 'http://localhost:8000',
      '/transcript': 'http://localhost:8000',
      '/summary': 'http://localhost:8000',
      '/actions': 'http://localhost:8000',
      '/report': 'http://localhost:8000',
      '/search': 'http://localhost:8000',
      '/translate': 'http://localhost:8000',
      '/languages': 'http://localhost:8000',
      '/sentiment': 'http://localhost:8000',
      '/questions': 'http://localhost:8000',
      '/reminders': 'http://localhost:8000',
      '/email': 'http://localhost:8000',
      '/voice-command': 'http://localhost:8000',
      '/analytics': 'http://localhost:8000',
      '/live': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
