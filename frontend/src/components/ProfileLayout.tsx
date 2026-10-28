import type { ReactNode } from 'react'

// 마이페이지·내 문장·작가 화면이 함께 쓰는 틀 (6-7)
// 맨 위 줄은 44px 이상으로 띄우고, 맨 아래는 넉넉히 둠 — 화면 바닥·주소창에 버튼이 붙지 않게
export default function ProfileFrame({
  children,
  top,
  width = 'max-w-3xl',
}: {
  children: ReactNode
  top?: ReactNode
  width?: string
}) {
  return (
    <main className="min-h-screen bg-paper px-4 pt-4 pb-20 sm:px-6">
      <div className={`mx-auto ${width}`}>
        <div className="flex min-h-11 items-center justify-between gap-3">{top}</div>
        <div className="mt-3">{children}</div>
      </div>
    </main>
  )
}

export function Panel({
  title,
  children,
  danger = false,
  className = '',
}: {
  title?: string
  children: ReactNode
  danger?: boolean
  className?: string
}) {
  return (
    <section
      className={`flex flex-col rounded-lg bg-white p-4 shadow-paper ring-1 ${
        danger ? 'ring-down-600/25' : 'ring-stone-200/60'
      } ${className}`}
    >
      {title && (
        <h2 className={`mb-3 text-sm font-semibold ${danger ? 'text-down-600' : 'text-stone-700'}`}>
          {title}
        </h2>
      )}
      {children}
    </section>
  )
}
