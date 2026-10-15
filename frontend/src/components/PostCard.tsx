import { Link } from 'react-router'
import type { PostSummary } from '../api/forum.ts'
import { formatDate, formatTimeAgo } from '../lib/time.ts'

// 커뮤니티 글 목록의 한 줄 (D-42·D-91)
// 왼쪽 표 칸 · 가운데 제목과 인용 · 아래 작성자와 댓글 수
export default function PostCard({ post }: { post: PostSummary }) {
  return (
    <article className="relative flex gap-4 rounded-lg bg-white p-4 shadow-paper ring-1 ring-stone-200/60 transition hover:shadow-paper-lift has-[a:focus-visible]:ring-2 has-[a:focus-visible]:ring-brand-600 sm:p-5">
      <PostScore up={post.up_count} down={post.down_count} />

      <div className="min-w-0 flex-1">
        <h3 className="font-semibold tracking-tight text-stone-900">
          {post.pin_slot && (
            <span className="mr-1.5 rounded-sm bg-brand-50 px-1.5 py-0.5 align-middle text-[11px] font-bold text-brand-700">
              고정
            </span>
          )}
          {/* 줄 전체를 누를 수 있게 링크 영역을 넓힘 */}
          <Link
            to={`/forum/posts/${post.id}`}
            className="after:absolute after:inset-0 after:rounded-lg focus-visible:outline-none"
          >
            {post.title}
          </Link>
        </h3>

        {post.quoted_sentence && (
          <p className="mt-2 line-clamp-2 border-l-2 border-brand-600 pl-3 font-serif text-[15px] text-stone-500">
            “{post.quoted_sentence.content}”
          </p>
        )}

        <p className="mt-2 flex flex-wrap items-center gap-1.5 text-[13px] text-stone-500">
          <span className="font-medium text-stone-600">{post.author_nickname}</span>
          <span aria-hidden className="text-stone-300">
            ·
          </span>
          <time dateTime={post.created_at} title={formatDate(post.created_at)}>
            {formatTimeAgo(post.created_at)}
          </time>
          <span aria-hidden className="text-stone-300">
            ·
          </span>
          <span className="tabular-nums">댓글 {post.comment_count}</span>
        </p>
      </div>
    </article>
  )
}

// 표 칸 (누르는 기능은 4-5에서)
export function PostScore({ up, down }: { up: number; down: number }) {
  return (
    <div className="flex w-9 shrink-0 flex-col items-center text-[13px] text-stone-400">
      <span aria-hidden>▲</span>
      <span className="font-semibold text-stone-700 tabular-nums" aria-label="추천에서 비추천을 뺀 수">
        {up - down}
      </span>
      <span aria-hidden>▼</span>
    </div>
  )
}
