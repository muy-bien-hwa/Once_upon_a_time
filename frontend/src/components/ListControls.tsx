import { useState, type ReactNode } from 'react'

// 내 문장·작가 화면이 함께 쓰는 검색칸과 알약 버튼 (6-7)
// 누르는 것은 모두 세로 44px 이상 (손가락으로 눌러야 함)

export function SearchBox({
  value,
  onSearch,
  placeholder,
}: {
  value: string
  onSearch: (text: string) => void
  placeholder: string
}) {
  const [draft, setDraft] = useState(value)
  // 뒤로 가기로 주소의 검색어가 바뀌면 입력칸도 따라가게 (그릴 때 맞춤 — 효과로 하면 한 번 더 그려짐)
  const [shown, setShown] = useState(value)
  if (shown !== value) {
    setShown(value)
    setDraft(value)
  }

  return (
    <form
      className="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-stone-200 bg-white px-3 focus-within:border-brand-600"
      onSubmit={(event) => {
        event.preventDefault()
        onSearch(draft.trim())
      }}
    >
      <span aria-hidden className="text-stone-400">
        🔍
      </span>
      {/* type="search"의 X는 글자만 지우고 목록은 그대로라 헷갈림 → 우리 "지우기"만 둠 */}
      <input
        type="text"
        enterKeyHint="search"
        id="sentence-search"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        maxLength={100}
        placeholder={placeholder}
        aria-label={placeholder}
        className="min-h-11 min-w-0 flex-1 text-sm text-stone-800 outline-none placeholder:text-stone-400"
      />
      {value && (
        <button
          type="button"
          onClick={() => onSearch('')}
          className="shrink-0 text-sm text-stone-400 transition hover:text-stone-700"
        >
          지우기
        </button>
      )}
    </form>
  )
}

export function PillButton({
  active,
  onClick,
  children,
  // 정렬은 초록, 상태 거르개는 회색 — 나란히 있어도 다른 묶음으로 보이게
  tone = 'brand',
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
  tone?: 'brand' | 'stone'
}) {
  const on = tone === 'brand' ? 'bg-brand-600' : 'bg-stone-700'

  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active}
      className={`min-h-11 rounded-full px-3.5 text-sm transition ${
        active
          ? `${on} font-medium text-white`
          : 'border border-stone-200 bg-white text-stone-600 hover:bg-stone-100'
      }`}
    >
      {children}
    </button>
  )
}
