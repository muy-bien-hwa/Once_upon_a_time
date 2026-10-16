import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { deleteSentence, type Sentence } from '../api/sentences.ts'
import { useMe } from '../lib/useMe.ts'
import ConfirmDialog from './ConfirmDialog.tsx'

type Props = {
  sentence: Sentence
  // 지운 뒤 어디로 갈지는 쓰는 쪽에서 정함 (목록에 남기 / 앞 문장으로 가기)
  onDeleted?: (status: string) => void
  // 문장 박스 안에서는 작게, 책 페이지 위에서는 보통 크기
  small?: boolean
}

// 내가 쓴 문장 지우기 (F-09·D-92)
// 뒤에 이어진 문장이 없으면 흔적 없이, 있으면 "삭제된 문장" 자리만 남음
// 이어진 문장이 있는 첫 문장은 지울 수 없고, 눌렀을 때 그 이유를 알려 줌
export default function DeleteSentenceButton({ sentence, onDeleted, small = false }: Props) {
  const { data: me } = useMe()
  const [open, setOpen] = useState(false)
  const queryClient = useQueryClient()

  const remove = useMutation({
    mutationFn: () => deleteSentence(sentence.id),
    onSuccess: ({ status }) => {
      setOpen(false)
      queryClient.invalidateQueries({ queryKey: ['children'] })
      queryClient.invalidateQueries({ queryKey: ['path'] })
      queryClient.invalidateQueries({ queryKey: ['stories'] })
      queryClient.invalidateQueries({ queryKey: ['story'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      onDeleted?.(status)
    },
    // 실패하면 창을 닫아야 안내 문구가 보임
    onError: () => setOpen(false),
  })

  // 닉네임은 중복이 없으므로(D-84) 이름이 같으면 내가 쓴 문장
  const mine = me?.nickname != null && me.nickname === sentence.author_nickname
  if (!mine || sentence.status !== 'active') return null

  const isRoot = sentence.parent_id === null
  const hasChildren = sentence.child_count > 0
  // 누가 이어 쓴 첫 문장은 지울 수 없음 → 버튼은 두되 눌렀을 때 이유를 알려 줌 (D-92)
  const blocked = isRoot && hasChildren

  return (
    <>
      <button
        type="button"
        // 문장 박스 전체가 링크라 그 위로 올리고 이동은 막음
        onClick={(event) => {
          event.preventDefault()
          event.stopPropagation()
          setOpen(true)
        }}
        className={`relative z-10 shrink-0 rounded-full border border-down-600/40 font-medium text-down-600 transition hover:border-down-600 hover:bg-down-600/10 ${
          small ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-sm'
        }`}
      >
        삭제
      </button>

      {blocked ? (
        <ConfirmDialog
          open={open}
          title="이 문장은 지울 수 없어요"
          confirmLabel="확인"
          hideCancel
          onConfirm={() => setOpen(false)}
          onCancel={() => setOpen(false)}
        >
          <p className="rounded-lg bg-stone-100 p-3 font-serif text-[17px] leading-relaxed text-stone-800">
            {sentence.content}
          </p>
          <p className="mt-2 text-stone-500">
            스토리의 첫 문장이고, 이미 뒤에 이어 쓴 문장이 {sentence.child_count}개 있어요. 첫
            문장을 지우면 스토리가 통째로 사라지기 때문에, 이어진 이야기가 있으면 지울 수
            없습니다.
          </p>
        </ConfirmDialog>
      ) : (
        <ConfirmDialog
          open={open}
          title={isRoot ? '이 문장을 지우면 스토리도 사라져요' : '이 문장을 지울까요?'}
          confirmLabel="네"
          cancelLabel="아니요"
          busyLabel="지우는 중…"
          busy={remove.isPending}
          onConfirm={() => remove.mutate()}
          onCancel={() => setOpen(false)}
        >
          <p className="rounded-lg bg-stone-100 p-3 font-serif text-[17px] leading-relaxed text-stone-800">
            {sentence.content}
          </p>
          <p className="mt-2 text-stone-500">
            {isRoot
              ? '스토리의 첫 문장이라, 지우면 스토리가 목록에서 사라집니다. 되돌릴 수 없어요.'
              : hasChildren
                ? '뒤에 이어진 이야기는 그대로 남고, 이 자리에는 "삭제된 문장"만 보입니다.'
                : '흔적 없이 사라집니다. 되돌릴 수 없어요.'}
          </p>
        </ConfirmDialog>
      )}

      {remove.isError && (
        <span className="relative z-10 text-xs text-red-500">{remove.error.message}</span>
      )}
    </>
  )
}
