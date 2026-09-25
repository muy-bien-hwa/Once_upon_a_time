import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { fetchRecord } from '../api/stats.ts'

// 기네스 세계기록: 한 소설에 참여한 최다 작가 수 (PM 확인 2026-09-26)
const GUINNESS = {
  authors: 122,
  source:
    'https://www.guinnessworldrecords.com/world-records/628603-most-contributions-to-a-published-work-of-fiction',
}

// 3번 창: 기네스 기록과 우리 최다 작가 스토리를 글로 나란히 비교 (D-76)
export default function HotRecord() {
  const { data, isPending, isError } = useQuery({
    queryKey: ['stats', 'record'],
    queryFn: ({ signal }) => fetchRecord(signal),
  })

  if (isPending) return <div className="h-32 animate-pulse rounded-xl bg-stone-100" />
  if (isError || !data.most_authors_story) {
    return (
      <p className="flex h-32 items-center justify-center text-stone-400">아직 기록이 없어요.</p>
    )
  }

  const story = data.most_authors_story

  return (
    <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:justify-center">
      <div className="flex-1">
        <p className="text-stone-600">기네스 세계기록 · 한 소설에 참여한 최다 작가</p>
        <p className="mt-1 text-3xl font-bold text-stone-800">{GUINNESS.authors}명</p>
        <a
          href={GUINNESS.source}
          target="_blank"
          rel="noreferrer"
          className="mt-1 inline-block text-sm text-stone-400 underline hover:text-stone-600"
        >
          출처
        </a>
      </div>

      <span className="shrink-0 text-2xl font-bold text-stone-300">vs</span>

      <div className="flex-1">
        <p className="text-stone-600">지금 우리 기록</p>
        <p className="mt-1 text-3xl font-bold text-brand-700">{story.author_count}명</p>
        <Link
          to={`/s/${story.first_sentence_id}`}
          className="mt-1 inline-block text-sm text-stone-500 underline hover:text-stone-800"
        >
          {story.title}
        </Link>
      </div>
    </div>
  )
}
