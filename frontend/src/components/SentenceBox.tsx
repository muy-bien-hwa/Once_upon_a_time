import { Link } from 'react-router'
import type { Sentence } from '../api/sentences.ts'
import { formatDate, formatTimeAgo } from '../lib/time.ts'
import DeleteSentenceButton from './DeleteSentenceButton.tsx'
import SentenceText from './SentenceText.tsx'
import VoteButtons from './VoteButtons.tsx'

// 가운데 목록의 문장 박스 하나. 누르면 그 문장으로 이동해서 한 칸 더 읽음
export default function SentenceBox({ sentence }: { sentence: Sentence }) {
  return (
    <Link to={`/s/${sentence.id}`} className="flex items-start gap-2">
      <article className="flex-1 rounded-lg bg-white p-4 shadow-paper ring-1 ring-stone-200/60 transition hover:shadow-paper-lift">
        <SentenceText sentence={sentence} />
        <div className="mt-3 flex items-center gap-2 text-xs text-stone-500">
          {sentence.author_nickname && <span>{sentence.author_nickname}</span>}
          <time dateTime={sentence.created_at} title={formatDate(sentence.created_at)}>
            {formatTimeAgo(sentence.created_at)}
          </time>
          <span className="ml-auto flex items-center gap-1">
            {sentence.status === 'active' ? (
              <VoteButtons sentence={sentence} />
            ) : (
              // 접힘·삭제된 문장에는 투표할 수 없음 (D-82)
              <>
                <span className="opacity-40">▲ {sentence.up_count}</span>
                <span className="opacity-40">▼ {sentence.down_count}</span>
              </>
            )}
            {/* 내가 쓴 문장만 지울 수 있음 (F-09) */}
            <DeleteSentenceButton sentence={sentence} small />
            {/* 이 문장을 인용해 커뮤니티 글쓰기 (D-91) */}
            {sentence.status === 'active' && (
              <Link
                to={`/stories/${sentence.story_id}/forum/new?quote=${sentence.id}`}
                // 문장 박스 전체가 링크라 그 위로 올림
                onClick={(event) => event.stopPropagation()}
                className="relative z-10 rounded px-1.5 py-0.5 text-stone-500 hover:bg-stone-100 hover:text-brand-700"
              >
                글쓰기
              </Link>
            )}
            {/* 신고는 5단계 기능 → 지금은 흐리게 표시만 (D-64) */}
            <span className="opacity-40">신고</span>
          </span>
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
