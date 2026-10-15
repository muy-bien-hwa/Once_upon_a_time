import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { cancelVote, voteSentence, type Sentence } from '../api/sentences.ts'
import { useMe } from '../lib/useMe.ts'
import LoginButton from './LoginButton.tsx'

// 문장 박스 안의 추천·비추천 버튼 (F-07)
// 같은 버튼을 다시 누르면 취소, 반대 버튼을 누르면 바로 바뀜 (PM 결정 2026-10-02)
export default function VoteButtons({ sentence }: { sentence: Sentence }) {
  const { data: me } = useMe()
  const [notice, setNotice] = useState('')
  const queryClient = useQueryClient()

  const press = useMutation({
    mutationFn: (value: 1 | -1) =>
      sentence.my_vote === value ? cancelVote(sentence.id) : voteSentence(sentence.id, value),
    onSuccess: () => {
      setNotice('')
      // 목록의 표 수와 순서를 다시 받아옴
      queryClient.invalidateQueries({ queryKey: ['children'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
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
    <>
      <VoteButton
        label="추천"
        mark="▲"
        tone="up"
        count={sentence.up_count}
        active={sentence.my_vote === 1}
        busy={press.isPending}
        onPress={() => vote(1)}
      />
      <VoteButton
        label="비추천"
        mark="▼"
        tone="down"
        count={sentence.down_count}
        active={sentence.my_vote === -1}
        busy={press.isPending}
        onPress={() => vote(-1)}
      />
      {notice && (
        <span className="flex items-center gap-2 text-red-500">
          {notice}
          {!me && <LoginButton small />}
        </span>
      )}
    </>
  )
}

// 누른 표만 색을 채움: 추천은 초록, 비추천은 빨강 (D-87, 색 구분은 PM 요청 2026-10-15)
const PRESSED = {
  up: 'bg-brand-600 font-medium text-white',
  down: 'bg-down-600 font-medium text-white',
}

function VoteButton({
  label,
  mark,
  tone,
  count,
  active,
  busy,
  onPress,
}: {
  label: string
  mark: string
  tone: 'up' | 'down'
  count: number
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
      // 문장 박스 전체가 링크라 그 위로 올리고(z-10) 이동은 막음
      onClick={(event) => {
        event.preventDefault()
        event.stopPropagation()
        onPress()
      }}
      className={`relative z-10 rounded-full px-2 py-0.5 tabular-nums transition ${
        active ? PRESSED[tone] : 'text-stone-500 hover:bg-stone-100'
      } disabled:opacity-50`}
    >
      {mark} {count}
    </button>
  )
}
