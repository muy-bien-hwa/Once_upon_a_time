import { useInfiniteQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router'
import { fetchMySentences, type ProfileFilter, type ProfileSort } from '../api/profile.ts'
import { PillButton, SearchBox } from '../components/ListControls.tsx'
import { ChevronLeft } from '../components/icons.tsx'
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

// 상태 거르개 — 검색한 뒤 그 안에서 "삭제함"만 보는 식으로도 씀
const FILTERS: { value: ProfileFilter; label: string }[] = [
  { value: 'all', label: '전체' },
  { value: 'active', label: '보임' },
  { value: 'deleted', label: '삭제함' },
  { value: 'folded', label: '신고 처리됨' },
]

// 내가 쓴 문장 전부 (D-95) — 검색·정렬·더 보기
export default function MySentencesPage() {
  const { data: me, isPending } = useMe()
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const sort: ProfileSort = params.get('sort') === 'votes' ? 'votes' : 'latest'
  const status = (FILTERS.find((item) => item.value === params.get('status'))?.value ??
    'all') as ProfileFilter

  const list = useInfiniteQuery({
    queryKey: ['me', 'sentences', { sort, q, status }],
    queryFn: ({ pageParam, signal }) =>
      fetchMySentences({ page: pageParam, sort, q, status }, signal),
    initialPageParam: 1,
    // 받은 만큼이 전체보다 적으면 다음 쪽이 있음
    getNextPageParam: (last) => (last.page * last.size < last.total ? last.page + 1 : undefined),
    enabled: Boolean(me),
  })

  const change = (next: { q?: string; sort?: ProfileSort; status?: ProfileFilter }) => {
    const updated = new URLSearchParams(params)
    for (const [key, value] of Object.entries(next)) {
      if (value) updated.set(key, value)
      else updated.delete(key)
    }
    // 기본값은 주소에 남기지 않음
    if (updated.get('sort') === 'latest') updated.delete('sort')
    if (updated.get('status') === 'all') updated.delete('status')
    setParams(updated)
    window.scrollTo({ top: 0 })
  }

  const top = (
    <>
      <Link
        to="/me"
        className="inline-flex min-h-11 items-center gap-1 text-sm text-stone-500 transition hover:text-stone-800"
      >
        <ChevronLeft className="h-4 w-4" /> 마이페이지
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
  const counts = list.data?.pages[0].counts ?? null
  const chosen = FILTERS.find((item) => item.value === status)

  return (
    <ProfileFrame top={top}>
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="font-serif text-2xl font-semibold text-stone-900">내 문장</h1>
        {counts && (
          <p className="text-sm text-stone-500">
            {q ? `찾은 문장 ${counts.all}개` : `모두 ${counts.all}개`}
          </p>
        )}
      </header>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <SearchBox
          value={q}
          onSearch={(text) => change({ q: text })}
          placeholder="문장 속 낱말로 찾기"
        />
        <div className="flex gap-1.5">
          {SORTS.map((option) => (
            <PillButton
              key={option.value}
              active={sort === option.value}
              onClick={() => change({ sort: option.value })}
            >
              {option.label}
            </PillButton>
          ))}
        </div>
      </div>

      {counts && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {FILTERS.map((option) => (
            <PillButton
              key={option.value}
              active={status === option.value}
              onClick={() => change({ status: option.value })}
              tone="stone"
            >
              {option.label} <span className="tabular-nums opacity-70">{counts[option.value]}</span>
            </PillButton>
          ))}
        </div>
      )}

      <div className="mt-4">
        {list.isPending ? (
          <div className="h-64 animate-pulse rounded-lg bg-stone-200/70" />
        ) : list.isError ? (
          <Notice message={list.error.message} />
        ) : items.length === 0 ? (
          <Notice
            message={
              q
                ? status === 'all'
                  ? '찾은 문장이 없어요.'
                  : `찾은 문장 중에 "${chosen?.label}"은 없어요.`
                : status === 'all'
                  ? '아직 쓴 문장이 없어요.'
                  : `"${chosen?.label}"에 해당하는 문장이 없어요.`
            }
          >
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
