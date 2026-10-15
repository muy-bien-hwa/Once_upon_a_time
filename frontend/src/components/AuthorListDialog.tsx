import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import {
  appointManager,
  dismissManager,
  fetchAuthors,
  type StoryAuthor,
} from '../api/managers.ts'
import PenBadge from './PenBadge.tsx'

type Props = { storyId: number; open: boolean; onClose: () => void }

// 스토리 작가 목록 (D-91)
// 누구나 볼 수 있고, 스토리를 시작한 작가에게만 권한 주기·거두기 버튼이 보임
export default function AuthorListDialog({ storyId, open, onClose }: Props) {
  const dialog = useRef<HTMLDialogElement>(null)
  const queryClient = useQueryClient()

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['authors', storyId],
    queryFn: ({ signal }) => fetchAuthors(storyId, signal),
    enabled: open,
  })

  const change = useMutation({
    mutationFn: ({ userId, make }: { userId: number; make: boolean }) =>
      make ? appointManager(storyId, userId) : dismissManager(storyId, userId),
    onSuccess: (updated) => {
      queryClient.setQueryData(['authors', storyId], updated)
      // 고정 버튼이 보일지 말지가 바뀜
      queryClient.invalidateQueries({ queryKey: ['post'] })
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (open && !element.open) element.showModal()
    if (!open && element.open) element.close()
  }, [open])

  return (
    <dialog
      ref={dialog}
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
      className="m-auto w-[min(28rem,92vw)] rounded-lg bg-white p-6 shadow-xl backdrop:bg-stone-900/40"
    >
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold text-stone-800">스토리 작가</h2>
        <button
          type="button"
          onClick={onClose}
          className="ml-auto rounded-lg px-3 py-1.5 text-sm text-stone-600 hover:bg-stone-100"
        >
          닫기
        </button>
      </div>

      <p className="mt-1 text-[13px] text-stone-500">
        <PenBadge kind="creator" /> 스토리를 시작한 작가 · <PenBadge kind="manager" /> 글을 고정할
        수 있는 관리자
      </p>

      <div className="mt-4 max-h-[60vh] overflow-y-auto">
        {isPending ? (
          <div className="h-24 animate-pulse rounded-lg bg-stone-100" />
        ) : isError ? (
          <p className="py-6 text-center text-sm text-red-500">{error.message}</p>
        ) : (
          <ul className="divide-y divide-stone-200">
            {data.items.map((author) => (
              <li key={author.user_id} className="flex items-center gap-2 py-2.5">
                <Name author={author} />
                <span className="text-[13px] text-stone-500 tabular-nums">
                  {author.sentence_count}문장
                </span>
                {data.can_appoint && !author.is_creator && (
                  <button
                    type="button"
                    disabled={change.isPending}
                    onClick={() =>
                      change.mutate({ userId: author.user_id, make: !author.is_manager })
                    }
                    className="ml-auto rounded-lg border border-stone-300 px-3 py-1 text-[13px] text-stone-600 hover:border-brand-600 hover:text-brand-700 disabled:opacity-50"
                  >
                    {author.is_manager ? '권한 거두기' : '권한 주기'}
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
        {change.isError && <p className="mt-2 text-sm text-red-500">{change.error.message}</p>}
      </div>
    </dialog>
  )
}

function Name({ author }: { author: StoryAuthor }) {
  return (
    // 닉네임을 누르면 뜨는 유저 정보 창은 추후 제작 (D-91)
    <span className="flex min-w-0 items-center gap-1 font-medium text-stone-800">
      {author.is_creator ? (
        <PenBadge kind="creator" />
      ) : author.is_manager ? (
        <PenBadge kind="manager" />
      ) : null}
      <span className="truncate">{author.nickname}</span>
    </span>
  )
}
