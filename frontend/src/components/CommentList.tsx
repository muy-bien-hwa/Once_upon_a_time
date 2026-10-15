import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { deleteComment, type Comment } from '../api/forum.ts'
import { useMe } from '../lib/useMe.ts'
import { formatDate, formatTimeAgo } from '../lib/time.ts'
import CommentInput from './CommentInput.tsx'

// 댓글 2단 (D-91)
// 맨 위 댓글 아래에 답글이 한 칸 들어가서 쌓임 — 답글의 답글도 더 들어가지 않고 같은 칸
export default function CommentList({ postId, items }: { postId: number; items: Comment[] }) {
  // 지금 답글을 쓰고 있는 댓글 (한 번에 하나만 열림)
  const [replyTo, setReplyTo] = useState<Comment | null>(null)

  if (items.length === 0) {
    return <p className="py-8 text-center text-stone-400">아직 댓글이 없어요.</p>
  }

  const roots = items.filter((item) => item.parent_id === null)
  const repliesOf = (rootId: number) => items.filter((item) => item.parent_id === rootId)

  return (
    <ul className="divide-y divide-stone-200">
      {roots.map((root) => (
        <li key={root.id} className="py-4">
          <CommentRow comment={root} postId={postId} replyTo={replyTo} onReply={setReplyTo} />

          {repliesOf(root.id).map((reply) => (
            <div key={reply.id} className="mt-3 flex gap-2 pl-3 sm:pl-6">
              <span aria-hidden className="text-stone-300">
                ㄴ
              </span>
              <div className="min-w-0 flex-1">
                <CommentRow
                  comment={reply}
                  postId={postId}
                  replyTo={replyTo}
                  onReply={setReplyTo}
                />
              </div>
            </div>
          ))}
        </li>
      ))}
    </ul>
  )
}

function CommentRow({
  comment,
  postId,
  replyTo,
  onReply,
}: {
  comment: Comment
  postId: number
  replyTo: Comment | null
  onReply: (comment: Comment | null) => void
}) {
  const { data: me } = useMe()
  const queryClient = useQueryClient()
  const remove = useMutation({
    mutationFn: () => deleteComment(comment.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', postId] })
      queryClient.invalidateQueries({ queryKey: ['post', postId] })
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  if (comment.status === 'folded') {
    return <p className="text-[15px] text-stone-400">신고 처리된 댓글입니다.</p>
  }

  // 닉네임은 중복이 없으므로(D-84) 이름이 같으면 내가 쓴 댓글
  const mine = me?.nickname != null && me.nickname === comment.author_nickname
  const open = replyTo?.id === comment.id

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
        <button
          type="button"
          onClick={() => onReply(open ? null : comment)}
          className="rounded px-1.5 py-0.5 hover:bg-stone-100 hover:text-stone-800"
        >
          답글
        </button>
        {mine && (
          <button
            type="button"
            disabled={remove.isPending}
            onClick={() => remove.mutate()}
            className="rounded px-1.5 py-0.5 hover:bg-stone-100 hover:text-down-600 disabled:opacity-50"
          >
            삭제
          </button>
        )}
      </p>

      {remove.isError && <p className="mt-1 text-[13px] text-red-500">{remove.error.message}</p>}

      {open && (
        <CommentInput
          postId={postId}
          parentId={comment.id}
          replyTo={comment.author_nickname}
          onDone={() => onReply(null)}
        />
      )}
    </>
  )
}
