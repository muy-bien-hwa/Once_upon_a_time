import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { withdraw } from '../api/profile.ts'
import ConfirmDialog from './ConfirmDialog.tsx'

// 계정 삭제 (마이페이지 맨 아래, D-95)
// 되돌릴 수 없는 일이라 **닉네임을 그대로 입력해야** 삭제 버튼이 눌림
export default function DeleteAccount({ nickname }: { nickname: string | null }) {
  const [open, setOpen] = useState(false)
  const [typed, setTyped] = useState('')
  const [done, setDone] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const remove = useMutation({
    mutationFn: withdraw,
    // 받아 둔 내용은 홈으로 갈 때 비움 — 지금 비우면 이 창까지 사라짐
    onSuccess: () => setDone(true),
  })

  const close = () => {
    setOpen(false)
    setTyped('')
    remove.reset()
  }

  const goHome = () => {
    queryClient.clear()
    navigate('/', { replace: true })
  }

  return (
    <>
      <p className="text-sm leading-relaxed text-stone-500">
        닉네임과 이메일이 지워지고 되돌릴 수 없어요. 이미 쓴 문장은 뒷이야기가 무너지지 않도록 남고,
        이름만 "탈퇴한 작가"로 바뀌어요.
      </p>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-3 inline-flex min-h-11 items-center self-start rounded-lg border border-down-600/40 px-3 text-sm text-down-600 transition hover:bg-down-600/5"
      >
        계정 삭제
      </button>

      <ConfirmDialog
        open={open && !done}
        title="정말 계정을 삭제할까요?"
        confirmLabel="삭제하기"
        busyLabel="삭제하는 중…"
        busy={remove.isPending}
        confirmDisabled={nickname !== null && typed.trim() !== nickname}
        danger
        onConfirm={() => remove.mutate()}
        onCancel={close}
      >
        <p>지우고 나면 같은 구글 계정으로 다시 와도 새 작가가 되고, 옛 기록과는 이어지지 않아요.</p>
        <p className="mt-2">삭제를 원하는 문장이 있다면 먼저 지워 주세요. 삭제한 뒤에는 지울 수 없어요.</p>
        {nickname !== null && (
          <label className="mt-4 block">
            <span className="text-stone-500">
              확인을 위해 <b className="text-stone-800">{nickname}</b>을(를) 그대로 적어 주세요
            </span>
            <input
              type="text"
              id="withdraw-confirm"
              value={typed}
              onChange={(event) => setTyped(event.target.value)}
              placeholder={nickname}
              className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-stone-800 outline-none placeholder:text-stone-300 focus:border-down-600"
            />
          </label>
        )}
        {remove.isError && <p className="mt-3 text-down-600">{remove.error.message}</p>}
      </ConfirmDialog>

      <ConfirmDialog
        open={done}
        title="계정을 삭제했어요"
        confirmLabel="홈으로"
        hideCancel
        onConfirm={goHome}
        onCancel={goHome}
      >
        <p>그동안 함께해 주셔서 고마웠어요. 남긴 문장은 "탈퇴한 작가"의 이름으로 남아 있어요.</p>
      </ConfirmDialog>
    </>
  )
}
