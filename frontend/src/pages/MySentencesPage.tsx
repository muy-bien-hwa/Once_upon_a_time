import { useInfiniteQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { fetchMySentences, type ProfileSort } from '../api/profile.ts'
import LoginButton from '../components/LoginButton.tsx'
import LogoutButton from '../components/LogoutButton.tsx'
import Notice from '../components/Notice.tsx'
import ProfileFrame, { Panel } from '../components/ProfileLayout.tsx'
import SentenceRow from '../components/SentenceRow.tsx'
import { useMe } from '../lib/useMe.ts'

const SORTS: { value: ProfileSort; label: string }[] = [
  { value: 'latest', label: '최신순' },
  { value: 'votes', label: '추천순' },
]

// 내가 쓴 문장 전부 (D-95) — 검색·정렬·더 보기
export default function MySentencesPage() {
  const { data: me, isPending } = useMe()
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const sort: ProfileSort = params.get('sort') === 'votes' ? 'votes' : 'latest'

  const list = useInfiniteQuery({
    queryKey: ['me', 'sentences', { sort, q }],
    queryFn: ({ pageParam, signal }) => fetchMySentences({ page: pageParam, sort, q }, signal),
    initialPageParam: 1,
    // 받은 만큼이 전체보다 적으면 다음 쪽이 있음
    getNextPageParam: (last) => (last.page * last.size < last.total ? last.page + 1 : undefined),
    enabled: Boolean(me),
  })

  const change = (next: { q?: string; sort?: ProfileSort }) => {
    const updated = new URLSearchParams(params)
    for (const [key, value] of Object.entries(next)) {
      if (value) updated.set(key, value)
      else updated.delete(key)
    }
    // 기본 정렬은 주소에 남기지 않음
    if (updated.get('sort') === 'latest') updated.delete('sort')
    setParams(updated)
    window.scrollTo({ top: 0 })
  }

  const top = (
    <>
      <Link
        to="/me"
        className="inline-flex min-h-11 items-center text-sm text-stone-500 transition hover:text-stone-800"
      >
        ‹ 마이페이지
      </Link>
      {me && <LogoutButton />}
    </>
  )

  if (isPending) {
    return (
      <ProfileFrame top={top}>
        <div className="h-64 animate-pulse rounded-lg bg-stone-200/70" />
      </ProfileFrame>
    )
  }

  if (!me) {
    return (
      <ProfileFrame top={top}>
        <Notice message="내 문장은 로그인한 뒤에 볼 수 있어요.">
          <LoginButton small />
        </Notice>
      </ProfileFrame>
    )
  }

  const items = list.data?.pages.flatMap((page) => page.items) ?? []
  const total = list.data?.pages[0].total ?? 0

  return (
    <ProfileFrame top={top}>
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="font-serif text-2xl font-semibold text-stone-900">내 문장</h1>
        {list.data && (
          <p className="text-sm text-stone-500">
            {q ? `찾은 문장 ${total}개` : `모두 ${total}개`}
          </p>
        )}
      </header>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <SearchBox value={q} onSearch={(text) => change({ q: text })} />
        <div className="flex gap-1.5">
          {SORTS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => change({ sort: option.value })}
              aria-current={sort === option.value}
              className={`min-h-11 rounded-full px-4 text-sm transition ${
                sort === option.value
                  ? 'bg-brand-600 font-medium text-white'
                  : 'border border-stone-200 bg-white text-stone-600 hover:bg-stone-100'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {q && (
        <p className="mt-2 text-xs text-stone-400">
          지운 문장·신고 처리된 문장은 내용이 남아 있지 않아 찾을 수 없어요.
        </p>
      )}

      <div className="mt-4">
        {list.isPending ? (
          <div className="h-64 animate-pulse rounded-lg bg-stone-200/70" />
        ) : list.isError ? (
          <Notice message={list.error.message} />
        ) : items.length === 0 ? (
          <Notice message={q ? `"${q}"가 들어간 문장이 없어요.` : '아직 쓴 문장이 없어요.'}>
            {q ? (
              <button
                type="button"
                onClick={() => change({ q: '' })}
                className="inline-flex min-h-11 items-center rounded-lg border border-stone-200 px-3 text-sm text-stone-700 transition hover:bg-stone-100"
              >
                검색 지우기
              </button>
            ) : (
              <Link
                to="/"
                className="inline-flex min-h-11 items-center rounded-lg bg-brand-600 px-4 text-sm font-medium text-white transition hover:bg-brand-700"
              >
                이야기 둘러보기
              </Link>
            )}
          </Notice>
        ) : (
          <>
            <Panel>
              <ul className="-mx-2 divide-y divide-stone-100">
                {items.map((sentence) => (
                  <SentenceRow key={sentence.id} sentence={sentence} />
                ))}
              </ul>
            </Panel>
            {list.hasNextPage && (
              <button
                type="button"
                onClick={() => list.fetchNextPage()}
                disabled={list.isFetchingNextPage}
                className="mt-3 flex min-h-11 w-full items-center justify-center rounded-lg bg-brand-50 text-sm font-medium text-brand-700 ring-1 ring-brand-600/15 transition hover:bg-brand-100 disabled:opacity-60"
              >
                {list.isFetchingNextPage ? '불러오는 중…' : `더 보기 (${items.length} / ${total})`}
              </button>
            )}
          </>
        )}
      </div>
    </ProfileFrame>
  )
}

function SearchBox({ value, onSearch }: { value: string; onSearch: (text: string) => void }) {
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
        id="my-sentence-search"
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        maxLength={100}
        placeholder="문장 속 낱말로 찾기"
        aria-label="문장 속 낱말로 찾기"
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
