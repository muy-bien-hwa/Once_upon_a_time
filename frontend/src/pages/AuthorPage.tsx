import { useInfiniteQuery, useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router'
import { ApiError } from '../api/client.ts'
import { fetchAuthor, fetchAuthorSentences, type ProfileSort } from '../api/profile.ts'
import AccountBar from '../components/AccountBar.tsx'
import { PillButton, SearchBox } from '../components/ListControls.tsx'
import { ChevronLeft } from '../components/icons.tsx'
import Notice from '../components/Notice.tsx'
import ProfileFrame, { Panel } from '../components/ProfileLayout.tsx'
import SentenceRow from '../components/SentenceRow.tsx'

const SORTS: { value: ProfileSort; label: string }[] = [
  { value: 'latest', label: '최신순' },
  { value: 'votes', label: '추천순' },
]

// 작가 화면 (D-95) — 누구나 볼 수 있고, 지금 보이는 문장만 나옴
export default function AuthorPage() {
  const { nickname = '' } = useParams()
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const sort: ProfileSort = params.get('sort') === 'votes' ? 'votes' : 'latest'

  const author = useQuery({
    queryKey: ['author', nickname],
    queryFn: ({ signal }) => fetchAuthor(nickname, signal),
    retry: false,
  })
  const list = useInfiniteQuery({
    queryKey: ['author', nickname, 'sentences', { sort, q }],
    queryFn: ({ pageParam, signal }) =>
      fetchAuthorSentences(nickname, { page: pageParam, sort, q }, signal),
    initialPageParam: 1,
    getNextPageParam: (last) => (last.page * last.size < last.total ? last.page + 1 : undefined),
    enabled: author.isSuccess,
  })

  const change = (next: { q?: string; sort?: ProfileSort }) => {
    const updated = new URLSearchParams(params)
    for (const [key, value] of Object.entries(next)) {
      if (value) updated.set(key, value)
      else updated.delete(key)
    }
    if (updated.get('sort') === 'latest') updated.delete('sort')
    setParams(updated)
    window.scrollTo({ top: 0 })
  }

  const top = (
    <>
      <Link
        to="/"
        className="inline-flex min-h-11 items-center gap-1 text-sm text-stone-500 transition hover:text-stone-800"
      >
        <ChevronLeft className="h-4 w-4" /> 홈
      </Link>
      <AccountBar />
    </>
  )

  if (author.isPending) {
    return (
      <ProfileFrame top={top}>
        <div className="h-64 animate-pulse rounded-lg bg-stone-200/70" />
      </ProfileFrame>
    )
  }

  // 없는 닉네임도 탈퇴한 작가도 똑같이 404 (탈퇴 사실을 알려 주지 않음)
  if (author.isError) {
    const gone = author.error instanceof ApiError && author.error.status === 404
    return (
      <ProfileFrame top={top}>
        <Notice message={gone ? '없는 작가예요.' : author.error.message}>
          <Link to="/" className="text-stone-700 underline">
            목록으로
          </Link>
        </Notice>
      </ProfileFrame>
    )
  }

  const items = list.data?.pages.flatMap((page) => page.items) ?? []
  const total = list.data?.pages[0].total ?? 0
  const [year, month] = author.data.joined_month.split('-')

  return (
    <ProfileFrame top={top}>
      <Panel>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-serif text-2xl font-semibold text-stone-900">
              {author.data.nickname}
            </h1>
            {/* 날짜까지는 공개하지 않기로 함 (D-95) */}
            <p className="mt-1 text-sm text-stone-500">
              {year}년 {Number(month)}월부터 함께
            </p>
          </div>
          <div className="grid w-full grid-cols-3 gap-2 border-t border-stone-100 pt-3 text-center sm:w-auto sm:min-w-64 sm:border-t-0 sm:pt-0">
            <Count label="쓴 문장" value={author.data.sentence_count} />
            <Count label="참여한 이야기" value={author.data.story_count} />
            <Count label="받은 추천" value={author.data.received_up_count} />
          </div>
        </div>
      </Panel>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
        <SearchBox
          value={q}
          onSearch={(text) => change({ q: text })}
          placeholder="이 작가의 문장 찾기"
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

      <div className="mt-4">
        {list.isPending ? (
          <div className="h-64 animate-pulse rounded-lg bg-stone-200/70" />
        ) : list.isError ? (
          <Notice message={list.error.message} />
        ) : items.length === 0 ? (
          <Notice message={q ? '찾은 문장이 없어요.' : '아직 보이는 문장이 없어요.'}>
            {q && (
              <button
                type="button"
                onClick={() => change({ q: '' })}
                className="inline-flex min-h-11 items-center rounded-lg border border-stone-200 px-3 text-sm text-stone-700 transition hover:bg-stone-100"
              >
                검색 지우기
              </button>
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

function Count({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <b className="block text-xl font-semibold text-brand-700 tabular-nums">
        {value.toLocaleString('ko-KR')}
      </b>
      <span className="text-xs text-stone-500">{label}</span>
    </div>
  )
}
