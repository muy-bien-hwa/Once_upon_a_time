import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { pinPost, unpinPost, type Post } from '../api/forum.ts'
import ConfirmDialog from './ConfirmDialog.tsx'

// 글 고정·해제 (D-91)
// 스토리를 시작한 작가와 관리자에게만 보임 (서버가 can_pin으로 알려 줌)
export default function PinButton({ post }: { post: Post }) {
  const [confirming, setConfirming] = useState(false)
  const queryClient = useQueryClient()
  const pinned = post.pin_slot !== null

  const press = useMutation({
    mutationFn: () => (pinned ? unpinPost(post.id) : pinPost(post.id)),
    onSuccess: () => {
      setConfirming(false)
      queryClient.invalidateQueries({ queryKey: ['post', post.id] })
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
    // 실패하면 확인창을 닫아야 안내 문구가 보임 (고정 2개 초과 등)
    onError: () => setConfirming(false),
  })

  if (!post.can_pin) return null

  return (
    <>
      <button
        type="button"
        onClick={() => setConfirming(true)}
        className="rounded-lg border border-stone-300 px-3 py-1.5 text-sm text-stone-600 hover:border-brand-600 hover:text-brand-700"
      >
        {pinned ? '고정 해제' : '고정하기'}
      </button>

      <ConfirmDialog
        open={confirming}
        title={pinned ? '이 글을 고정 해제할까요?' : '이 글을 고정할까요?'}
        confirmLabel="네"
        cancelLabel="아니요"
        busyLabel="처리 중…"
        busy={press.isPending}
        onConfirm={() => press.mutate()}
        onCancel={() => setConfirming(false)}
      >
        <p className="text-stone-600">
          {pinned
            ? '목록 맨 위에서 내려오고, 보통 글처럼 정렬됩니다.'
            : '커뮤니티 목록 맨 위에 올라갑니다. 고정은 스토리당 2개까지예요.'}
        </p>
      </ConfirmDialog>

      {press.isError && <span className="text-sm text-red-500">{press.error.message}</span>}
    </>
  )
}
