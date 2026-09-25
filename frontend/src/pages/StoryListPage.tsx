import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { fetchStories, type StoryListQuery, type StorySort } from '../api/stories.ts'
import HotBoard from '../components/HotBoard.tsx'
import Notice from '../components/Notice.tsx'
import Pagination from '../components/Pagination.tsx'
import StoryCard from '../components/StoryCard.tsx'

const SORTS: { value: StorySort; label: string }[] = [
  { value: 'latest', label: '최신순' },
  { value: 'oldest', label: '오래된순' },
  { value: 'recommended', label: '추천순' },
  { value: 'deepest', label: '깊은순' },
  { value: 'shallowest', label: '얕은순' },
]
const SIZES = [20, 50]
const DEFAULT_QUERY: StoryListQuery = { sort: 'latest', page: 1, size: 20 }

// ① 스토리 목록 (첫 화면) — 정렬·페이지·개수는 주소(?sort=&page=&size=)에 담음
// → 새로고침·뒤로 가기·주소 공유 때도 같은 목록이 보임
export default function StoryListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const query = readQuery(searchParams)
  // 1열·2열 선택은 주소가 아니라 이 브라우저에 기억해 둠 (공유 주소는 그대로)
  const [columns, setColumns] = useState<1 | 2>(readColumns)

  // 서버에서 목록 받아오기 (TanStack Query가 로딩·에러·저장(캐시)을 관리)
  const { data, isPending, isError, error, refetch, isPlaceholderData } = useQuery({
    queryKey: ['stories', query],
    queryFn: ({ signal }) => fetchStories(query, signal),
    // 페이지를 넘기는 동안 이전 목록을 그대로 보여줌 (화면 깜빡임 방지)
    placeholderData: keepPreviousData,
  })

  function changeQuery(changes: Partial<StoryListQuery>) {
    const next = { ...query, ...changes }
    // 기본값은 주소에서 뺌 → 첫 화면 주소가 그냥 "/"
    const params = new URLSearchParams()
    for (const key of ['sort', 'page', 'size'] as const) {
      if (next[key] !== DEFAULT_QUERY[key]) params.set(key, String(next[key]))
    }
    setSearchParams(params)
    window.scrollTo({ top: 0 })
  }

  function changeColumns(value: 1 | 2) {
    setColumns(value)
    try {
      localStorage.setItem(COLUMNS_KEY, String(value))
    } catch {
      // 저장이 막혀 있어도(시크릿 창 등) 화면은 그대로 동작
    }
  }

  return (
    <main className="min-h-screen bg-stone-50 px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <header className="py-6 text-center sm:py-10">
          <h1 className="text-4xl font-bold tracking-tight text-stone-900 sm:text-5xl">
            옛날 옛적에
          </h1>
        </header>

        <HotBoard />

        <div className="mt-6 flex justify-center">
          <Link
            to="/stories/new"
            className="rounded-full bg-brand-600 px-6 py-3 font-medium text-white transition hover:bg-brand-700"
          >
            새 스토리
          </Link>
        </div>

        <div className="mt-8 flex items-center gap-2">
          <p className="mr-auto text-sm text-stone-500">{data ? `스토리 ${data.total}개` : ''}</p>
          <select
            aria-label="정렬"
            value={query.sort}
            onChange={(event) => changeQuery({ sort: event.target.value as StorySort, page: 1 })}
            className="rounded-lg border border-stone-300 bg-white px-2 py-1.5 text-sm text-stone-700"
          >
            {SORTS.map((sort) => (
              <option key={sort.value} value={sort.value}>
                {sort.label}
              </option>
            ))}
          </select>
          <div role="group" aria-label="보기 방식" className="flex rounded-lg bg-stone-200 p-0.5">
            {([1, 2] as const).map((value) => (
              <button
                key={value}
                type="button"
                aria-pressed={columns === value}
                onClick={() => changeColumns(value)}
                className={`rounded-md px-2.5 py-1 text-sm ${
                  columns === value
                    ? 'bg-white font-medium text-stone-800 shadow-sm'
                    : 'text-stone-500'
                }`}
              >
                {value}열
              </button>
            ))}
          </div>
          <div role="group" aria-label="한 페이지에 볼 개수" className="flex rounded-lg bg-stone-200 p-0.5">
            {SIZES.map((size) => (
              <button
                key={size}
                type="button"
                aria-pressed={query.size === size}
                onClick={() => changeQuery({ size, page: 1 })}
                className={`rounded-md px-2.5 py-1 text-sm ${
                  query.size === size ? 'bg-white font-medium text-stone-800 shadow-sm' : 'text-stone-500'
                }`}
              >
                {size}개
              </button>
            ))}
          </div>
        </div>

        <section className="mt-4">
          {isPending ? (
            <Skeleton />
          ) : isError && !data ? (
            <Notice message={error.message}>
              <button type="button" onClick={() => refetch()} className="underline">
                다시 시도
              </button>
            </Notice>
          ) : data.total === 0 ? (
            <Notice message="아직 스토리가 없어요.">
              <Link to="/stories/new" className="underline">
                첫 스토리 열기
              </Link>
            </Notice>
          ) : data.items.length === 0 ? (
            <Notice message="이 페이지에는 스토리가 없어요.">
              <button type="button" onClick={() => changeQuery({ page: 1 })} className="underline">
                첫 페이지로
              </button>
            </Notice>
          ) : (
            <>
              {/* 카드 배치: 1열 · 2열 선택 (좁은 화면에서는 항상 1열) */}
              <ul
                className={`grid gap-3 ${columns === 2 ? 'sm:grid-cols-2' : ''} ${
                  isPlaceholderData ? 'opacity-60' : ''
                } transition-opacity`}
              >
                {data.items.map((story) => (
                  <li key={story.id}>
                    <StoryCard story={story} />
                  </li>
                ))}
              </ul>
              <Pagination
                page={query.page}
                totalPages={Math.ceil(data.total / query.size)}
                onChange={(page) => changeQuery({ page })}
              />
            </>
          )}
        </section>
      </div>
    </main>
  )
}

const COLUMNS_KEY = 'story-list-columns'

// 브라우저에 저장해 둔 보기 방식 (없거나 읽지 못하면 2열)
function readColumns(): 1 | 2 {
  try {
    return localStorage.getItem(COLUMNS_KEY) === '1' ? 1 : 2
  } catch {
    return 2
  }
}

// 주소의 값이 이상하면(없는 정렬, 음수 페이지 등) 기본값으로
function readQuery(params: URLSearchParams): StoryListQuery {
  const sortParam = params.get('sort')
  const sort = SORTS.find((item) => item.value === sortParam)?.value ?? DEFAULT_QUERY.sort
  const page = Math.max(1, Math.floor(Number(params.get('page'))) || 1)
  const sizeParam = Number(params.get('size'))
  const size = SIZES.includes(sizeParam) ? sizeParam : DEFAULT_QUERY.size
  return { sort, page, size }
}

function Skeleton() {
  return (
    <ul className="space-y-3" aria-label="불러오는 중">
      {[0, 1, 2].map((i) => (
        <li key={i} className="h-32 animate-pulse rounded-2xl bg-stone-200/70" />
      ))}
    </ul>
  )
}
