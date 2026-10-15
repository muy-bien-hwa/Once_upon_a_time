// 작가 목록의 만년필 배지 (D-91)
// 금색 = 스토리를 시작한 작가 · 은색 = 그 작가가 임명한 관리자
export default function PenBadge({ kind }: { kind: 'creator' | 'manager' }) {
  const creator = kind === 'creator'
  return (
    <span
      title={creator ? '스토리를 시작한 작가' : '스토리 관리자'}
      aria-label={creator ? '스토리를 시작한 작가' : '스토리 관리자'}
      className={creator ? 'text-medal-gold' : 'text-medal-silver'}
    >
      {/* 만년필: 펜대 + 펜촉 */}
      <svg viewBox="0 0 16 16" className="inline-block h-4 w-4 align-text-bottom" fill="none" aria-hidden>
        <path
          d="M13.2 1.6 14.4 2.8 6.6 10.6 4.3 11.7 5.4 9.4z"
          fill="currentColor"
        />
        <path d="M4.3 11.7 1.8 14.2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      </svg>
    </span>
  )
}
