import { Link } from 'react-router'
import type { Story } from '../api/stories.ts'
import { formatDate, formatTimeAgo } from '../lib/time.ts'

// 스토리 목록 카드 (D-67·D-73·D-79)
// 제목 = 고딕 굵게 / 첫 문장 = 명조 2줄 고정 → 카드 높이가 들쭉날쭉하지 않음
export default function StoryCard({ story }: { story: Story }) {
  return (
    <article
      className="group relative flex h-full flex-col rounded-lg bg-white p-5 shadow-paper ring-1 ring-stone-200/60 transition duration-150 hover:-translate-y-0.5 hover:shadow-paper-lift has-[a:focus-visible]:ring-2 has-[a:focus-visible]:ring-brand-600"
    >
      <h2 className="text-lg font-bold tracking-tight text-stone-900">
        {/* 카드 전체를 누를 수 있게 링크 영역을 카드 크기로 넓힘 (after:inset-0) */}
        <Link
          to={`/s/${story.first_sentence_id}`}
          className="line-clamp-1 after:absolute after:inset-0 after:rounded-lg focus-visible:outline-none"
        >
          {story.title}
        </Link>
      </h2>

      {story.first_sentence_status === 'folded' ? (
        <p className="mt-2 min-h-16 text-[15px] text-stone-500">신고 처리된 문장입니다.</p>
      ) : (
        <p className="mt-2 line-clamp-2 min-h-16 font-serif text-sentence text-stone-700">
          {story.first_sentence}
        </p>
      )}

      <div className="mt-4 flex items-center gap-1.5 text-[13px] text-stone-500">
        {/* 핵심 지표(작가 수)만 진하게 */}
        <span className="font-semibold text-stone-700 tabular-nums">
          작가 {story.author_count}명
        </span>
        <span aria-hidden className="text-stone-300">
          ·
        </span>
        <span className="tabular-nums">최장 {story.max_depth + 1}문장</span>
        <span aria-hidden className="text-stone-300">
          ·
        </span>
        <time
          dateTime={story.created_at}
          title={formatDate(story.created_at)}
          className="tabular-nums"
        >
          {formatTimeAgo(story.created_at)}
        </time>
        {/* 추천 기능(F-13, 3단계) 전까지 흐리게 표시만 (D-67)
            누를 수 없게 두어 이 자리를 눌러도 카드 링크가 그대로 동작 */}
        <span className="pointer-events-none ml-auto shrink-0 rounded-full border border-stone-200 px-3 py-1 tabular-nums">
          추천 {story.recommend_count}
        </span>
      </div>
    </article>
  )
}
