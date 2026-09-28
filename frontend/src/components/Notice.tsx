import type { ReactNode } from 'react'

// 목록·내용 자리에 띄우는 안내 상자 (불러오기 실패, 비어 있음 등)
export default function Notice({ message, children }: { message: string; children?: ReactNode }) {
  return (
    <div className="rounded-lg bg-white p-10 text-center text-stone-500 shadow-paper ring-1 ring-stone-200/60">
      <p>{message}</p>
      {children && <div className="mt-3 text-sm text-stone-700">{children}</div>}
    </div>
  )
}
