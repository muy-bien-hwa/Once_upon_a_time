import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import './index.css'
import App from './App.tsx'

// 서버 데이터 관리자 (TanStack Query): 받아온 데이터를 저장해 두고 로딩·에러 상태를 알려줌
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 실패하면 한 번만 다시 시도
      retry: 1,
      // 30초 안에 같은 목록을 다시 열면 서버에 다시 묻지 않고 저장된 것을 보여줌
      staleTime: 30 * 1000,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
