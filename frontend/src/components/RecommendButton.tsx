import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { cancelRecommendation, recommendStory, type Story } from '../api/stories.ts'
import { useMe } from '../lib/useMe.ts'
import LoginButton from './LoginButton.tsx'

// 목록 카드의 추천 버튼 (F-13). 다시 누르면 취소
// 자기 스토리·첫 문장이 접힌 스토리에는 누를 수 없고 추천 수만 보여줌 (D-54)
export default function RecommendButton({ story }: { story: Story }) {
  const { data: me } = useMe()
  const [notice, setNotice] = useState('')
  const queryClient = useQueryClient()

  const press = useMutation({
    mutationFn: () =>
      story.my_recommendation ? cancelRecommendation(story.id) : recommendStory(story.id),
    onSuccess: () => {
      setNotice('')
      // 목록의 추천 수·추천순 정렬과 읽기 화면 정보 칸, 홈 Hot 영역을 다시 받아옴
      queryClient.invalidateQueries({ queryKey: ['stories'] })
      queryClient.invalidateQueries({ queryKey: ['story', story.id] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
    onError: (error: Error) => setNotice(error.message),
  })

  // 닉네임은 중복이 없으므로(D-84) 이름이 같으면 내가 시작한 스토리
  const mine = me?.nickname != null && me.nickname === story.creator_nickname
  if (mine || story.first_sentence_status !== 'active') {
    return <Count count={story.recommend_count} />
  }

  return (
    <div className="relative z-10 ml-auto shrink-0">
      <button
        type="button"
        aria-pressed={story.my_recommendation}
        disabled={press.isPending}
        // 카드 전체가 링크라 그 위로 올리고(z-10) 이동은 막음
        onClick={(event) => {
          event.preventDefault()
          event.stopPropagation()
          // 로그인 안 했으면 누르지 않고 안내만 (D-83)
          if (!me) {
            setNotice('로그인이 필요해요.')
            return
          }
          press.mutate()
        }}
        className={`rounded-full border px-3 py-1 tabular-nums transition ${
          story.my_recommendation
            ? 'border-brand-600 bg-brand-600 font-medium text-white'
            : 'border-stone-200 hover:border-stone-300 hover:bg-stone-50'
        } disabled:opacity-50`}
      >
        추천 {story.recommend_count}
      </button>

      {notice && (
        // 카드 높이가 변하지 않도록 버튼 위에 띄움
        <div className="absolute right-0 bottom-full mb-2 flex items-center gap-2 whitespace-nowrap rounded-lg bg-white px-3 py-2 text-xs text-red-600 shadow-paper-lift ring-1 ring-stone-200">
          {notice}
          {!me && <LoginButton small />}
        </div>
      )}
    </div>
  )
}

function Count({ count }: { count: number }) {
  // 누를 수 없게 두어 이 자리를 눌러도 카드 링크가 그대로 동작
  return (
    <span className="pointer-events-none ml-auto shrink-0 rounded-full border border-stone-200 px-3 py-1 text-stone-400 tabular-nums">
      추천 {count}
    </span>
  )
}
