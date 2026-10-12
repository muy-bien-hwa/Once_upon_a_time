import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import {
  fetchTopSentences,
  fetchTopStories,
  type ByPeriod,
  type HotSentence,
  type HotStory,
} from '../api/stats.ts'

const PERIODS = [
  { key: 'day', label: '일간' },
  { key: 'week', label: '주간' },
  { key: 'month', label: '월간' },
] as const

// 1번 창: 추천 많은 스토리 Top 5 (일간·주간·월간)
export function HotTopStories() {
  const { data, isPending } = useQuery({
    queryKey: ['stats', 'top-stories'],
    queryFn: ({ signal }) => fetchTopStories(signal),
  })

  return (
    <Columns data={data} isPending={isPending} empty="아직 추천받은 스토리가 없어요">
      {(item: HotStory, rank: number) => {
        const top = rank <= MEDALS.length
        return (
          <li key={item.story.id}>
            <Link
              to={`/s/${item.story.first_sentence_id}`}
              className={`flex items-baseline gap-2 ${top ? 'py-1' : 'py-0.5'}`}
            >
              <Rank rank={rank} />
              <span
                className={`min-w-0 flex-1 truncate ${
                  top ? 'font-semibold text-stone-800' : 'text-[13px] text-stone-600'
                }`}
              >
                {item.story.title}
              </span>
              <span
                className={`shrink-0 tabular-nums ${
                  top ? 'text-[13px] font-semibold text-brand-700' : 'text-xs text-stone-500'
                }`}
              >
                추천 {item.recommend_count}
              </span>
            </Link>
            {/* 1·2·3등만 한 줄 더 (4·5등은 제목만) */}
            {top && (
              <p className="ml-6 truncate text-[13px] text-stone-500">
                작가 {authors(item.story.creator_nickname, item.story.author_count)} · 최장{' '}
                {item.story.max_depth + 1}문장
              </p>
            )}
          </li>
        )
      }}
    </Columns>
  )
}

// 2번 창: 추천 많은 문장 Top 5 (일간·주간·월간)
export function HotTopSentences() {
  const { data, isPending } = useQuery({
    queryKey: ['stats', 'top-sentences'],
    queryFn: ({ signal }) => fetchTopSentences(signal),
  })

  return (
    <Columns data={data} isPending={isPending} empty="아직 추천받은 문장이 없어요">
      {(item: HotSentence, rank: number) => {
        const top = rank <= MEDALS.length
        return (
          <li key={item.sentence.id}>
            <Link to={`/s/${item.sentence.id}`} className={`flex gap-2 ${top ? 'py-1' : 'py-0.5'}`}>
              <Rank rank={rank} className="pt-0.5" />
              <span className="min-w-0 flex-1">
                <span
                  className={`block truncate font-serif leading-6 ${
                    top ? 'text-[15px] text-stone-900' : 'text-[13px] text-stone-600'
                  }`}
                >
                  “{item.sentence.content}”
                </span>
                {top ? (
                  <>
                    <span className="block truncate text-[13px] text-stone-400">
                      {item.story.title}
                    </span>
                    <span className="block text-[13px] text-stone-500">
                      <span className="font-semibold text-brand-700 tabular-nums">
                        추천 {item.vote_count}
                      </span>{' '}
                      · {item.sentence.author_nickname}
                    </span>
                  </>
                ) : (
                  <span className="block text-xs text-stone-500 tabular-nums">
                    추천 {item.vote_count}
                  </span>
                )}
              </span>
            </Link>
          </li>
        )
      }}
    </Columns>
  )
}

// 1·2·3등은 금·은·동으로 조금 크게, 4·5등은 작은 숫자만 (PM 결정 2026-10-12)
const MEDALS = ['text-medal-gold', 'text-medal-silver', 'text-medal-bronze']

function Rank({ rank, className = '' }: { rank: number; className?: string }) {
  const medal = MEDALS[rank - 1]
  return (
    <span
      className={`w-4 shrink-0 tabular-nums ${className} ${
        medal ? `text-base font-bold ${medal}` : 'text-xs text-stone-400'
      }`}
    >
      {rank}
    </span>
  )
}

// 처음 만든 작가 + 나머지 인원 수
function authors(creator: string, count: number) {
  return count > 1 ? `${creator} 외 ${count - 1}명` : creator
}

// 일간·주간·월간 3열 (좁은 화면에서는 가로로 밀어 보기)
function Columns<T>({
  data,
  isPending,
  empty,
  children,
}: {
  data?: ByPeriod<T>
  isPending: boolean
  empty: string
  children: (item: T, rank: number) => ReactNode
}) {
  return (
    <div className="flex gap-5 overflow-x-auto sm:grid sm:grid-cols-3 sm:overflow-visible">
      {PERIODS.map((period) => (
        <div key={period.key} className="min-w-[80%] sm:min-w-0">
          <h3 className="mb-2 border-b border-stone-200 pb-1 text-sm font-semibold text-stone-600">
            {period.label}
          </h3>
          {isPending ? (
            <div className="h-40 animate-pulse rounded-lg bg-stone-100" />
          ) : data && data[period.key].length > 0 ? (
            <ol className="space-y-1.5">
              {data[period.key].map((item, index) => children(item, index + 1))}
            </ol>
          ) : (
            <p className="py-6 text-center text-[15px] text-stone-500">{empty}</p>
          )}
        </div>
      ))}
    </div>
  )
}
