type Props = {
  page: number
  totalPages: number
  onChange: (page: number) => void
}

// 페이지 번호 버튼 (D-57): ‹ 1 2 3 4 5 ›
export default function Pagination({ page, totalPages, onChange }: Props) {
  if (totalPages <= 1) return null

  const base = 'min-w-9 rounded-lg px-2 py-1.5 text-sm'
  const arrow = `${base} text-stone-600 hover:bg-stone-200 disabled:opacity-30 disabled:hover:bg-transparent`

  return (
    <nav aria-label="페이지" className="mt-8 flex justify-center gap-1">
      <button
        type="button"
        className={arrow}
        disabled={page === 1}
        onClick={() => onChange(page - 1)}
        aria-label="이전 페이지"
      >
        ‹
      </button>
      {pageWindow(page, totalPages).map((number) => (
        <button
          key={number}
          type="button"
          onClick={() => onChange(number)}
          aria-current={number === page ? 'page' : undefined}
          className={
            number === page
              ? `${base} bg-brand-600 font-semibold text-white`
              : `${base} text-stone-600 hover:bg-stone-200`
          }
        >
          {number}
        </button>
      ))}
      <button
        type="button"
        className={arrow}
        disabled={page === totalPages}
        onClick={() => onChange(page + 1)}
        aria-label="다음 페이지"
      >
        ›
      </button>
    </nav>
  )
}

// 번호는 최대 5개, 지금 페이지가 가운데 오도록
function pageWindow(page: number, totalPages: number, count = 5): number[] {
  const start = Math.max(1, Math.min(page - Math.floor(count / 2), totalPages - count + 1))
  const end = Math.min(totalPages, start + count - 1)
  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
}
