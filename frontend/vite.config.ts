import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // 개발 중 /api, /auth 요청은 FastAPI(8000)로 넘김
    // → 브라우저 입장에서는 같은 주소(5173)라 CORS 설정이 필요 없음 (D-35)
    // localhost 대신 127.0.0.1: Node가 localhost를 IPv6(::1)로 먼저 찾아 연결에 실패하는 문제 방지
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/auth': 'http://127.0.0.1:8000',
    },
  },
})
