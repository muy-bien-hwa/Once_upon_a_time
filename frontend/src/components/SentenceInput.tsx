import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import { createChild, type Sentence } from '../api/sentences.ts'
import ConfirmDialog from './ConfirmDialog.tsx'

const MAX_LENGTH = 100

// 가운데 목록 맨 아래 "+ 여기에 이어 쓰기" → 입력칸 → 확인창 → 등록 (D-61·D-64)
export default function SentenceInput({ parent }: { parent: Sentence }) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState('')
  const [confirming, setConfirming] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const write = useMutation({
    mutationFn: (content: string) => createChild(parent.id, content),
    onSuccess: (created) => {
      // 이 문장의 이어진 문장 목록과 스토리 목록(작가 수·최장 문장 수)을 다시 받아오게 함
      queryClient.invalidateQueries({ queryKey: ['children', parent.id] })
      queryClient.invalidateQueries({ queryKey: ['stories'] })
      // 제목 아래 정보 칸의 작가 수·최장 문장 수도 바뀜
      queryClient.invalidateQueries({ queryKey: ['story'] })
      setConfirming(false)
      setOpen(false)
      setText('')
      // 방금 쓴 문장 화면으로 이동 (D-62)
      navigate(`/s/${created.id}`)
    },
  })

  // 접힌·삭제된 문장 뒤에는 이어 쓸 수 없음 (D-50·D-70)
  if (parent.status !== 'active') {
    return (
      <p className="mt-3 rounded-2xl border border-dashed border-stone-300 p-4 text-center text-sm text-stone-400">
        {parent.status === 'folded'
          ? '신고 처리된 문장 뒤에는 이어 쓸 수 없어요.'
          : '삭제된 문장 뒤에는 이어 쓸 수 없어요.'}
      </p>
    )
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-3 w-full rounded-2xl border border-dashed border-stone-300 p-4 text-stone-500 transition hover:border-stone-400 hover:text-stone-700"
      >
        + 여기에 이어 쓰기
      </button>
    )
  }

  // 글자 수는 [...text].length로 셈 (JS 기본 length는 이모지를 2로 셈)
  const trimmed = text.trim()
  const length = [...trimmed].length
  const canSubmit = length > 0 && length <= MAX_LENGTH && !write.isPending

  return (
    <div className="mt-3 rounded-2xl border border-stone-300 bg-white p-4">
      <input
        type="text"
        autoFocus
        value={text}
        onChange={(event) => setText(event.target.value)}
        // 줄바꿈 금지 → Enter는 등록 확인창 (D-61)
        onKeyDown={(event) => {
          if (event.key === 'Enter' && canSubmit) setConfirming(true)
        }}
        placeholder="다음 문장을 한 줄로 써 주세요"
        className="w-full text-stone-800 outline-none placeholder:text-stone-400"
      />

      <div className="mt-3 flex items-center gap-2 text-sm">
        <span className={length > MAX_LENGTH ? 'text-red-500' : 'text-stone-400'}>
          {[...text].length}/{MAX_LENGTH}
        </span>
        <button
          type="button"
          onClick={() => {
            setOpen(false)
            setText('')
            write.reset()
          }}
          className="ml-auto rounded-lg px-3 py-1.5 text-stone-600 hover:bg-stone-100"
        >
          취소
        </button>
        <button
          type="button"
          disabled={!canSubmit}
          onClick={() => setConfirming(true)}
          className="rounded-lg bg-brand-600 px-4 py-1.5 font-medium text-white hover:bg-brand-700 disabled:opacity-40"
        >
          등록
        </button>
      </div>

      {write.isError && <p className="mt-2 text-sm text-red-500">{write.error.message}</p>}

      <ConfirmDialog
        open={confirming}
        title="이 문장을 등록할까요?"
        confirmLabel="등록"
        busyLabel="등록 중…"
        busy={write.isPending}
        onConfirm={() => write.mutate(trimmed)}
        onCancel={() => setConfirming(false)}
      >
        <p className="rounded-xl bg-stone-100 p-3 text-stone-800">{trimmed}</p>
        <p className="mt-2 text-stone-500">등록한 문장은 나중에 고칠 수 없어요.</p>
      </ConfirmDialog>
    </div>
  )
}
