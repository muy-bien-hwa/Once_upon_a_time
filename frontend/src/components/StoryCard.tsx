import { Link } from 'react-router'
import type { Story } from '../api/stories.ts'
import { formatDate, formatTimeAgo } from '../lib/time.ts'
import RecommendButton from './RecommendButton.tsx'

// 스토리 목록 카드 (D-67·D-73·D-79) — 책 표지 모양 (D-103)
// 안쪽에 가는 테두리 한 줄, 가운데 정렬 / 첫 문장은 3줄(휴대폰 2줄) 고정 → 카드 높이가 들쭉날쭉하지 않음
export default function StoryCard({ story }: { story: Story }) {
  return (
    <article className="group relative h-full rounded-lg bg-white p-2 shadow-paper ring-1 ring-stone-200/60 transition duration-150 hover:-translate-y-0.5 hover:shadow-paper-lift has-[a:focus-visible]:ring-2 has-[a:focus-visible]:ring-brand-600">
      <div className="flex h-full flex-col items-center rounded border border-stone-200 px-5 pt-6 pb-4 text-center">
        <h2 className="max-w-full font-serif text-[18.5px] font-semibold tracking-tight text-stone-900">
          {/* 카드 전체를 누를 수 있게 링크 영역을 카드 크기로 넓힘 (after:inset-0) */}
          <Link
            to={`/s/${story.first_sentence_id}`}
            className="line-clamp-1 after:absolute after:inset-0 after:rounded-lg focus-visible:outline-none"
          >
            {story.title}
          </Link>
        </h2>
        <span aria-hidden className="my-3 block h-px w-7 shrink-0 bg-stone-400" />

        {story.first_sentence_status === 'folded' ? (
          <p className="min-h-[3.7em] text-[15px] leading-[1.85] text-stone-500 sm:min-h-[5.55em]">
            신고 처리된 문장입니다.
          </p>
        ) : (
          <p className="line-clamp-2 min-h-[3.7em] font-serif text-[15.5px] leading-[1.85] text-stone-600 sm:line-clamp-3 sm:min-h-[5.55em]">
            {story.first_sentence}
          </p>
        )}

        <p className="mt-4 text-[13px] text-stone-500 tabular-nums">
          {/* 핵심 지표(작가 수)만 진하게 */}
          <span className="font-semibold text-stone-700">작가 {story.author_count}명</span>
          <span aria-hidden className="mx-1.5 text-stone-300">
            ·
          </span>
          최장 {story.max_depth + 1}문장
          <span aria-hidden className="mx-1.5 text-stone-300">
            ·
          </span>
          <time dateTime={story.created_at} title={formatDate(story.created_at)}>
            {formatTimeAgo(story.created_at)}
          </time>
        </p>
        <div className="mt-3 flex justify-center">
          <RecommendButton story={story} />
        </div>
      </div>
    </article>
  )
}
