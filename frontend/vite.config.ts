import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 把所有 API 请求转发到 FastAPI 后端
      '/auth': 'http://localhost:8000',
      '/jobs': 'http://localhost:8000',
      '/applications': 'http://localhost:8000',
      '/resumes': 'http://localhost:8000',
      '/stats': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
})
