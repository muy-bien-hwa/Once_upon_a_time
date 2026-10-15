import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { cancelPostVote, votePost, type PostSummary } from '../api/forum.ts'
import { useMe } from '../lib/useMe.ts'

// 커뮤니티 글의 표 칸 (F-17·D-42)
// 문장 투표와 같은 방식: 다시 누르면 취소, 반대쪽은 바로 전환 / 추천 초록 · 비추천 빨강
export default function PostVote({ post }: { post: PostSummary }) {
  const { data: me } = useMe()
  const [notice, setNotice] = useState('')
  const queryClient = useQueryClient()

  const press = useMutation({
    mutationFn: (value: 1 | -1) =>
      post.my_vote === value ? cancelPostVote(post.id) : votePost(post.id, value),
    onSuccess: () => {
      setNotice('')
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      queryClient.invalidateQueries({ queryKey: ['post', post.id] })
    },
    onError: (error: Error) => setNotice(error.message),
  })

  function vote(value: 1 | -1) {
    // 로그인 안 했으면 누르지 않고 안내만 (D-83)
    if (!me) {
      setNotice('로그인이 필요해요.')
      return
    }
    press.mutate(value)
  }

  return (
    <div className="relative z-10 flex w-9 shrink-0 flex-col items-center">
      <Arrow mark="▲" label="추천" active={post.my_vote === 1} busy={press.isPending} onPress={() => vote(1)} />
      <span className="text-[13px] font-semibold text-stone-700 tabular-nums">
        {post.up_count - post.down_count}
      </span>
      <Arrow mark="▼" label="비추천" active={post.my_vote === -1} busy={press.isPending} onPress={() => vote(-1)} />

      {notice && (
        // 글 줄 전체가 링크라 안내는 위에 띄움 (줄 높이가 변하지 않게)
        <div className="absolute top-full left-0 z-20 mt-1 w-max max-w-[16rem] rounded-lg bg-white px-3 py-2 text-xs text-red-600 shadow-paper-lift ring-1 ring-stone-200">
          {notice}
        </div>
      )}
    </div>
  )
}

function Arrow({
  mark,
  label,
  active,
  busy,
  onPress,
}: {
  mark: string
  label: string
  active: boolean
  busy: boolean
  onPress: () => void
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      disabled={busy}
      // 글 줄 전체가 링크라 그 위로 올리고 이동은 막음
      onClick={(event) => {
        event.preventDefault()
        event.stopPropagation()
        onPress()
      }}
      className={`rounded px-1 text-[13px] transition hover:bg-stone-100 disabled:opacity-50 ${
        active ? (label === '추천' ? 'text-brand-600' : 'text-down-600') : 'text-stone-300'
      }`}
    >
      {mark}
    </button>
  )
}
