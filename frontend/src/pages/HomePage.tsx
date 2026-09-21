import { useEffect, useState } from 'react'

// 백엔드 /api/health 응답 모양
type Health = {
  status: string
  db: string
}

export default function HomePage() {
  const [health, setHealth] = useState<Health | null>(null)  // <...> = TypeScript 표시. 이 state 에는 Health 모양의 값 또는 null 만 들어간다는 뜻.
  const [failed, setFailed] = useState(false)

  // 화면이 처음 나타날 때 한 번 서버 상태를 물어봄
  useEffect(() => {
    const controller = new AbortController()

    fetch('/api/health', { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json() as Promise<Health>
      })
      .then(setHealth)
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true)
      })

    // 화면이 사라지면 요청을 취소
    return () => controller.abort()
  }, [])

  return (
    <main className="flex min-h-screen items-center justify-center bg-stone-50 px-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-sm">
        <h1 className="text-3xl font-bold text-stone-800">옛날 옛적에</h1>
        <p className="mt-2 text-stone-500">한 문장씩 이어 쓰는 릴레이 스토리</p>
        <p className="mt-8 text-sm text-stone-700">{statusText(health, failed)}</p>
      </div>
    </main>
  )
}

function statusText(health: Health | null, failed: boolean) {
  if (failed) return '❌ 서버 연결 실패'
  if (!health) return '서버 연결 확인 중…'
  return health.db === 'ok' ? '✅ 서버 연결됨 · DB 연결됨' : '⚠️ 서버 연결됨 · DB 연결 실패'
}
