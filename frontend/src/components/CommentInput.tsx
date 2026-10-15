import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { createComment } from '../api/forum.ts'
import { useMe } from '../lib/useMe.ts'
import LoginNotice from './LoginNotice.tsx'

const MAX = 1000

type Props = {
  postId: number
  // 답글이면 어느 댓글에 다는지 + 누구에게 하는 말인지 (D-91)
  parentId?: number
  replyTo?: string | null
  onDone?: () => void
}

// 댓글·답글 입력칸 (F-17·D-91)
export default function CommentInput({ postId, parentId, replyTo, onDone }: Props) {
  const [text, setText] = useState('')
  const { data: me } = useMe()
  const queryClient = useQueryClient()

  const write = useMutation({
    mutationFn: () => createComment(postId, text.trim(), parentId),
    onSuccess: () => {
      setText('')
      queryClient.invalidateQueries({ queryKey: ['comments', postId] })
      queryClient.invalidateQueries({ queryKey: ['post', postId] })
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      onDone?.()
    },
  })

  if (!me || !me.nickname) {
    return <LoginNotice me={me} what={parentId ? '답글을 쓰려면' : '댓글을 쓰려면'} />
  }

  const length = [...text.trim()].length
  const canSubmit = length > 0 && length <= MAX && !write.isPending

  return (
    <form
      className="mt-3"
      onSubmit={(event) => {
        event.preventDefault()
        if (canSubmit) write.mutate()
      }}
    >
      {replyTo && (
        <p className="mb-1 text-[13px] text-stone-500">
          <span className="font-semibold text-brand-700">@{replyTo}</span> 님에게 답글
        </p>
      )}
      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        rows={parentId ? 2 : 3}
        placeholder={parentId ? '답글을 써 주세요' : '댓글을 써 주세요'}
        className="w-full rounded-lg border border-stone-200 p-3 text-[15px] text-stone-800 outline-none focus:border-brand-600"
      />
      <div className="mt-2 flex items-center gap-2 text-sm">
        <span className={length > MAX ? 'text-red-500' : 'text-stone-400'}>
          {[...text].length}/{MAX}
        </span>
        {write.isError && <span className="text-red-500">{write.error.message}</span>}
        {onDone && (
          <button
            type="button"
            onClick={onDone}
            className="ml-auto rounded-lg px-3 py-1.5 text-stone-600 hover:bg-stone-100"
          >
            취소
          </button>
        )}
        <button
          type="submit"
          disabled={!canSubmit}
          className={`rounded-lg bg-brand-600 px-4 py-1.5 font-medium text-white hover:bg-brand-700 disabled:opacity-40 ${
            onDone ? '' : 'ml-auto'
          }`}
        >
          {write.isPending ? '등록 중…' : '등록'}
        </button>
      </div>
    </form>
  )
}
