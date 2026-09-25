import { Link } from 'react-router'
import type { Sentence } from '../api/sentences.ts'
import { formatDate, formatTimeAgo } from '../lib/time.ts'
import SentenceText from './SentenceText.tsx'

// 가운데 목록의 문장 박스 하나. 누르면 그 문장으로 이동해서 한 칸 더 읽음
export default function SentenceBox({ sentence }: { sentence: Sentence }) {
  return (
    <Link to={`/s/${sentence.id}`} className="flex items-start gap-2">
      <article className="flex-1 rounded-2xl bg-white p-4 shadow-sm transition hover:shadow-md">
        <SentenceText sentence={sentence} />
        <div className="mt-3 flex items-center gap-2 text-xs text-stone-500">
          {sentence.author_nickname && <span>{sentence.author_nickname}</span>}
          <time dateTime={sentence.created_at} title={formatDate(sentence.created_at)}>
            {formatTimeAgo(sentence.created_at)}
          </time>
          {/* 투표·신고는 3·5단계 기능 → 지금은 흐리게 표시만 (D-64) */}
          <span className="ml-auto opacity-40">▲ {sentence.up_count}</span>
          <span className="opacity-40">▼ {sentence.down_count}</span>
          <span className="opacity-40">신고</span>
        </div>
      </article>
      <ChildCount count={sentence.child_count} />
    </Link>
  )
}

// 이어진 문장 수 = 겹친 회색 빈 박스 (D-59)
function ChildCount({ count }: { count: number }) {
  if (count === 0) return <span className="w-9 shrink-0" />

  return (
    <span
      className="flex w-9 shrink-0 flex-col items-center gap-1 pt-4 text-xs text-stone-400"
      aria-label={`이어진 문장 ${count}개`}
    >
      <span className="relative block h-7 w-7">
        {Array.from({ length: Math.min(count, 3) }, (_, i) => (
          <span
            key={i}
            className="absolute h-4 w-5 rounded-md border border-stone-300 bg-stone-100"
            style={{ top: i * 4, left: i * 4 }}
          />
        ))}
      </span>
      <span aria-hidden>{count}</span>
    </span>
  )
}
