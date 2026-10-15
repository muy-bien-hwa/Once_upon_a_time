import type { Comment } from '../api/forum.ts'
import { formatDate, formatTimeAgo } from '../lib/time.ts'

// 댓글 2단 (D-91)
// 맨 위 댓글 아래에 답글이 한 칸 들어가서 쌓임 — 답글의 답글도 더 들어가지 않고 같은 칸
export default function CommentList({ items }: { items: Comment[] }) {
  if (items.length === 0) {
    return <p className="py-8 text-center text-stone-400">아직 댓글이 없어요.</p>
  }

  const roots = items.filter((item) => item.parent_id === null)
  const repliesOf = (rootId: number) => items.filter((item) => item.parent_id === rootId)

  return (
    <ul className="divide-y divide-stone-200">
      {roots.map((root) => (
        <li key={root.id} className="py-4">
          <CommentBody comment={root} />
          {repliesOf(root.id).map((reply) => (
            <div key={reply.id} className="mt-3 flex gap-2 pl-3 sm:pl-6">
              <span aria-hidden className="text-stone-300">
                ㄴ
              </span>
              <div className="min-w-0 flex-1">
                <CommentBody comment={reply} />
              </div>
            </div>
          ))}
        </li>
      ))}
    </ul>
  )
}

function CommentBody({ comment }: { comment: Comment }) {
  if (comment.status === 'folded') {
    return <p className="text-[15px] text-stone-400">신고 처리된 댓글입니다.</p>
  }

  return (
    <>
      <p className="text-[15px] whitespace-pre-wrap text-stone-800">
        {/* 누구에게 한 말인지 (닉네임이 바뀌면 여기도 따라 바뀜, D-91) */}
        {comment.reply_to_nickname && (
          <span className="mr-1 font-semibold text-brand-700">@{comment.reply_to_nickname}</span>
        )}
        {comment.body}
      </p>
      <p className="mt-1 flex flex-wrap items-center gap-1.5 text-[13px] text-stone-500">
        <span className="font-medium text-stone-600">{comment.author_nickname}</span>
        <span aria-hidden className="text-stone-300">
          ·
        </span>
        <time dateTime={comment.created_at} title={formatDate(comment.created_at)}>
          {formatTimeAgo(comment.created_at)}
        </time>
      </p>
    </>
  )
}
