import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import {
  DETAIL_MAX,
  REPORT_REASONS,
  sendReport,
  type ReportKind,
  type ReportReason,
} from '../api/reports.ts'
import { useMe } from '../lib/useMe.ts'
import ConfirmDialog from './ConfirmDialog.tsx'
import LoginButton from './LoginButton.tsx'

type Props = {
  kind: ReportKind
  id: number
  // 서버가 알려 주는 "내가 이미 신고했는지" → 한 번 신고하면 다시 못 누름 (D-93)
  reported: boolean
  // 댓글이면 어느 글의 댓글인지 (신고 뒤 그 글의 댓글을 다시 받아오려고)
  postId?: number
  // 쓴 사람 (내 글에는 버튼을 아예 보여주지 않음 — 서버도 막음, D-93)
  authorNickname?: string | null
  // pill = 문장 박스·글 아래 알약 버튼 / text = 댓글 줄의 작은 글자 버튼
  variant?: 'pill' | 'text'
  small?: boolean
}

const WHAT: Record<ReportKind, string> = {
  sentence: '문장',
  post: '글',
  comment: '댓글',
}

// 신고 버튼 + 신고 창 (F-10·D-93)
// 사유 7종 중 하나를 고르고, 설명은 500자까지 ("기타"는 설명 필수)
export default function ReportButton({
  kind,
  id,
  reported,
  postId,
  authorNickname,
  variant = 'pill',
  small = false,
}: Props) {
  const { data: me } = useMe()
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState<ReportReason | null>(null)
  const [detail, setDetail] = useState('')
  const [needLogin, setNeedLogin] = useState(false)
  // 보낸 뒤에는 목록을 다시 받아올 때까지 기다리지 않고 바로 "신고했어요"로 바꿈
  const [done, setDone] = useState(false)
  const queryClient = useQueryClient()

  const send = useMutation({
    mutationFn: () => sendReport(kind, id, reason!, detail.trim()),
    onSuccess: () => {
      setDone(true)
      if (kind === 'sentence') {
        queryClient.invalidateQueries({ queryKey: ['children'] })
        queryClient.invalidateQueries({ queryKey: ['path'] })
        queryClient.invalidateQueries({ queryKey: ['stories'] })
      } else if (kind === 'post') {
        queryClient.invalidateQueries({ queryKey: ['post', id] })
        queryClient.invalidateQueries({ queryKey: ['posts'] })
      } else {
        queryClient.invalidateQueries({ queryKey: ['comments', postId] })
      }
    },
  })

  // 닉네임은 중복이 없으므로(D-84) 이름이 같으면 내가 쓴 것 → 신고 버튼 없음
  if (me?.nickname != null && me.nickname === authorNickname) return null

  const already = reported || done
  const length = [...detail].length
  // "기타"는 무엇이 문제인지 알 수 없으므로 설명을 받음 (서버도 같은 규칙)
  const ready =
    reason !== null && length <= DETAIL_MAX && (reason !== 'other' || detail.trim() !== '')

  function press() {
    // 로그인 안 했으면 창을 열지 않고 안내만 (투표와 같은 방식, D-83)
    if (!me) {
      setNeedLogin(true)
      return
    }
    setNeedLogin(false)
    setOpen(true)
  }

  function close() {
    setOpen(false)
    send.reset()
  }

  return (
    <>
      <button
        type="button"
        disabled={already}
        // 문장 박스 전체가 링크라 그 위로 올리고(z-10) 이동은 막음
        onClick={(event) => {
          event.preventDefault()
          event.stopPropagation()
          press()
        }}
        className={
          variant === 'text'
            ? 'rounded px-1.5 py-0.5 hover:bg-stone-100 hover:text-stone-800 disabled:hover:bg-transparent'
            : `relative z-10 shrink-0 rounded-full border border-stone-200 text-stone-500 transition hover:border-stone-400 hover:text-stone-700 ${
                small ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-sm'
              }`
        }
      >
        {already ? '신고했어요' : '신고'}
      </button>

      {needLogin && (
        <span className="relative z-10 flex items-center gap-2 text-red-500">
          로그인이 필요해요.
          <LoginButton small />
        </span>
      )}

      {done ? (
        <ConfirmDialog
          open={open}
          title="신고했어요"
          confirmLabel="확인"
          hideCancel
          onConfirm={close}
          onCancel={close}
        >
          <p className="text-stone-600">
            살펴보고 처리할게요. 같은 {WHAT[kind]}을 다시 신고할 수는 없어요.
          </p>
        </ConfirmDialog>
      ) : (
        <ConfirmDialog
          open={open}
          title={`이 ${WHAT[kind]}을 신고할까요?`}
          confirmLabel="신고하기"
          cancelLabel="취소"
          busyLabel="보내는 중…"
          busy={send.isPending}
          confirmDisabled={!ready}
          danger
          onConfirm={() => send.mutate()}
          onCancel={close}
        >
          <fieldset>
            <legend className="mb-2 text-stone-600">무엇이 문제인가요? (하나만)</legend>
            <div className="flex flex-wrap gap-1.5">
              {REPORT_REASONS.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  aria-pressed={reason === item.value}
                  onClick={() => setReason(item.value)}
                  className={`rounded-full border px-3 py-1 transition ${
                    reason === item.value
                      ? 'border-down-600 bg-down-600/10 font-medium text-down-600'
                      : 'border-stone-200 text-stone-600 hover:border-stone-400'
                  }`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </fieldset>

          <label className="mt-4 block">
            <span className="text-stone-600">
              자세한 이유 {reason === 'other' ? '(기타는 꼭 적어 주세요)' : '(안 적어도 돼요)'}
            </span>
            <textarea
              value={detail}
              onChange={(event) => setDetail(event.target.value)}
              rows={3}
              placeholder="무슨 일이 있었는지 알려 주세요"
              className="mt-1 w-full rounded-lg border border-stone-200 p-3 text-[15px] text-stone-800 outline-none focus:border-brand-600"
            />
          </label>
          <div className="flex items-center gap-2">
            <span className={length > DETAIL_MAX ? 'text-red-500' : 'text-stone-400'}>
              {length}/{DETAIL_MAX}
            </span>
            {send.isError && <span className="text-red-500">{send.error.message}</span>}
          </div>
          <p className="mt-2 text-stone-400">신고 내용은 운영자만 봅니다.</p>
        </ConfirmDialog>
      )}
    </>
  )
}
