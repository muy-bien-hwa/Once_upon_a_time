import type { ReactNode } from 'react'

// 화면에서 쓰는 아이콘 한 벌 (이모지·기호 글자 대신 직접 그림, PM 요청 2026-11-05)
// - 색은 글자색을 따라가고(currentColor), 크기는 className으로 정함
// - 선 굵기와 네모(24×24)를 똑같이 맞춰 어디에 놓아도 한 집안으로 보이게
// - 뜻은 옆의 글자나 aria-label이 전하므로 아이콘 자체는 읽지 않게 둠

type IconProps = { className?: string }

function Stroke({ className = 'h-4 w-4', children }: IconProps & { children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
      focusable="false"
    >
      {children}
    </svg>
  )
}

export function SearchIcon({ className }: IconProps) {
  return (
    <Stroke className={className}>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m15.5 15.5 4.5 4.5" />
    </Stroke>
  )
}

export function ChevronLeft({ className }: IconProps) {
  return (
    <Stroke className={className}>
      <path d="m14.5 5-7 7 7 7" />
    </Stroke>
  )
}

export function ChevronRight({ className }: IconProps) {
  return (
    <Stroke className={className}>
      <path d="m9.5 5 7 7-7 7" />
    </Stroke>
  )
}

// 표는 작게 놓이므로 속을 채운 쪽이 또렷함
function Solid({ className = 'h-3 w-3', children }: IconProps & { children: ReactNode }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden focusable="false">
      {children}
    </svg>
  )
}

export function CaretUp({ className }: IconProps) {
  return (
    <Solid className={className}>
      <path d="M12 6.5 21 18H3z" />
    </Solid>
  )
}

export function CaretDown({ className }: IconProps) {
  return (
    <Solid className={className}>
      <path d="M12 17.5 3 6h18z" />
    </Solid>
  )
}
