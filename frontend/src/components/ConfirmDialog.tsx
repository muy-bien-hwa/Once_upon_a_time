import { useEffect, useRef, type ReactNode } from 'react'

type Props = {
  open: boolean
  title: string
  children?: ReactNode
  confirmLabel: string
  busyLabel?: string
  busy?: boolean
  onConfirm: () => void
  onCancel: () => void
}

// 직접 만든 확인창 (브라우저 기본 확인창 대신, 2026-09-25 PM 선택)
// <dialog>를 쓰면 화면 가운데 띄우기·뒤 가리기·Esc 닫기를 브라우저가 처리해 줌
export default function ConfirmDialog({
  open,
  title,
  children,
  confirmLabel,
  busyLabel,
  busy = false,
  onConfirm,
  onCancel,
}: Props) {
  const dialog = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const element = dialog.current
    if (!element) return
    if (open && !element.open) element.showModal()
    if (!open && element.open) element.close()
  }, [open])

  return (
    <dialog
      ref={dialog}
      // Esc 키 = 취소 (등록 중에는 닫지 않음)
      onCancel={(event) => {
        event.preventDefault()
        if (!busy) onCancel()
      }}
      className="m-auto w-[min(26rem,90vw)] rounded-2xl bg-white p-6 shadow-xl backdrop:bg-stone-900/40"
    >
      <h2 className="text-lg font-semibold text-stone-800">{title}</h2>
      {children && <div className="mt-3 text-sm text-stone-600">{children}</div>}
      <div className="mt-6 flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          disabled={busy}
          className="rounded-lg px-3 py-2 text-sm text-stone-600 hover:bg-stone-100 disabled:opacity-50"
        >
          취소
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={busy}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {busy ? (busyLabel ?? '처리 중…') : confirmLabel}
        </button>
      </div>
    </dialog>
  )
}
