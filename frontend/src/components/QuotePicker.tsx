import { keepPreviousData, useInfiniteQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { searchSentences, type QuoteCandidate } from '../api/stories.ts'
import { SearchIcon } from './icons.tsx'

type Props = {
  storyId: number
  // 지금 고른 문장 (없으면 인용 없이 올라감)
  value: QuoteCandidate | null
  onChange: (quote: QuoteCandidate | null) => void
}

// 커뮤니티 글쓰기에서 인용할 문장 고르기 (D-102)
// 낱말을 치면 그 스토리의 문장을 찾아 주고, 하나를 누르면 인용으로 붙음 / 인용은 안 해도 됨
export default function QuotePicker({ storyId, value, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  // 글자를 칠 때마다 서버에 묻지 않도록, 잠깐 멈췄을 때만 찾음
  const word = useDelayed(text.trim(), 300)

  // 10개씩 받아 오고 [더 보기]로 이어 붙임 (내 문장·작가 화면과 같은 방식)
  const search = useInfiniteQuery({
    queryKey: ['quote-search', storyId, word],
    queryFn: ({ pageParam, signal }) => searchSentences(storyId, word, pageParam, signal),
    initialPageParam: 1,
    // 받은 만큼이 전체보다 적으면 다음 쪽이 있음
    getNextPageParam: (last) => (last.page * last.size < last.total ? last.page + 1 : undefined),
    enabled: open && word.length > 0,
    // 낱말을 고치는 동안 앞의 결과를 그대로 두어 목록이 깜빡이지 않게
    placeholderData: keepPreviousData,
  })

  function close() {
    setOpen(false)
    setText('')
  }

  // ① 이미 골랐을 때: 고른 문장 + 빼기
  if (value) {
    return (
      <div className="mb-5 border-l-2 border-brand-600 bg-brand-50/60 py-2 pr-2 pl-4">
        <p className="font-serif text-[15px] text-stone-700">“{value.content}”</p>
        <p className="mt-1 flex items-center gap-2 text-[13px] text-stone-500">
          이 문장을 인용해서 씁니다
          <button
            type="button"
            onClick={() => onChange(null)}
            className="btn btn-tag btn-sm ml-auto"
          >
            인용 빼기
          </button>
        </p>
      </div>
    )
  }

  // ② 아직 안 열었을 때: 여는 버튼
  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mb-5 w-full rounded-lg border border-dashed border-stone-300 px-4 py-3 text-left text-sm text-stone-500 transition hover:border-stone-400 hover:text-stone-700"
      >
        + 문장 인용하기 <span className="text-stone-400">(안 해도 돼요)</span>
      </button>
    )
  }

  // ③ 찾는 중
  const pages = word.length > 0 ? (search.data?.pages ?? []) : []
  const items = pages.flatMap((page) => page.items)
  const total = pages[0]?.total ?? 0
  // 치던 낱말로 찾기가 끝났는지 (끝났는데 없을 때만 "없어요"라고 말함)
  const settled = word.length > 0 && word === text.trim() && search.isSuccess

  return (
    <div className="mb-5 rounded-lg border border-stone-300 p-3">
      <div className="flex items-center gap-2">
        <SearchIcon className="h-4 w-4 shrink-0 text-stone-400" />
        <input
          type="text"
          autoFocus
          aria-label="인용할 문장 찾기"
          value={text}
          maxLength={100}
          onChange={(event) => setText(event.target.value)}
          // 이 칸은 글쓰기 양식 안에 있음 → Enter가 글을 올려 버리지 않게 막음
          onKeyDown={(event) => {
            if (event.key === 'Enter') event.preventDefault()
            if (event.key === 'Escape') close()
          }}
          placeholder="인용할 문장에 들어 있는 낱말 (예: 고양이)"
          className="min-w-0 flex-1 text-[15px] text-stone-800 outline-none placeholder:text-stone-300"
        />
        <button
          type="button"
          onClick={close}
          className="btn btn-tag btn-sm"
        >
          닫기
        </button>
      </div>

      {search.isError ? (
        <p className="mt-3 text-sm text-red-500">{search.error.message}</p>
      ) : items.length > 0 ? (
        // 더 보기로 목록이 길어져도 제목·내용 칸이 화면 밖으로 밀려나지 않게, 이 안에서만 굴림
        <div className="mt-3 max-h-96 overflow-y-auto border-t border-stone-100">
          <ul
            className={`divide-y divide-stone-100 transition-opacity ${
              search.isPlaceholderData ? 'opacity-60' : ''
            }`}
          >
            {items.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => {
                    onChange(item)
                    close()
                  }}
                  className="block w-full px-1 py-2.5 text-left hover:bg-stone-50"
                >
                  <span className="block font-serif text-[15px] leading-relaxed text-stone-800">
                    {item.content}
                  </span>
                  <span className="mt-0.5 block text-xs text-stone-500">
                    {item.author_nickname ?? '탈퇴한 작가'}
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {search.hasNextPage && (
            <div className="border-t border-stone-100 py-2 text-center">
              <button
                type="button"
                disabled={search.isFetchingNextPage}
                onClick={() => search.fetchNextPage()}
                className="btn btn-tag btn-sm"
              >
                {search.isFetchingNextPage
                  ? '불러오는 중…'
                  : `더 보기 (${items.length} / ${total})`}
              </button>
            </div>
          )}
        </div>
      ) : (
        <p className="mt-3 text-sm text-stone-400">
          {settled
            ? '그 낱말이 들어간 문장이 없어요.'
            : '이 스토리의 문장 가운데 하나를 골라 인용할 수 있어요.'}
        </p>
      )}
    </div>
  )
}

// 값이 바뀐 뒤 잠깐(ms) 기다렸다가 따라오는 값
function useDelayed<T>(value: T, ms: number): T {
  const [delayed, setDelayed] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDelayed(value), ms)
    return () => clearTimeout(timer)
  }, [value, ms])
  return delayed
}
