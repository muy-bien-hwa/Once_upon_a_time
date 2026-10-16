import { useEffect, useRef, type ReactNode } from 'react'

type Props = {
  open: boolean
  title: string
  children?: ReactNode
  confirmLabel: string
  // 기본은 "취소" (고정 확인창처럼 "아니요"가 어울릴 때 바꿔 씀, D-91)
  cancelLabel?: string
  // 안내만 할 때는 취소 버튼을 숨기고 확인 버튼 하나만 (삭제할 수 없는 문장 안내 등)
  hideCancel?: boolean
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
  cancelLabel = '취소',
  hideCancel = false,
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
      // 확인창이 링크(문장 박스 등) 안에 들어 있을 수 있어, 클릭이 바깥으로 새지 않게 막음
      // 브라우저가 링크를 따라가는 기본 동작까지 막아야 해서 둘 다 호출 (stopPropagation만으론 부족)
      onClick={(event) => {
        event.preventDefault()
        event.stopPropagation()
      }}
      // Esc 키 = 취소 (등록 중에는 닫지 않음)
      onCancel={(event) => {
        event.preventDefault()
        if (!busy) onCancel()
      }}
      className="m-auto w-[min(26rem,90vw)] rounded-lg bg-white p-6 shadow-xl backdrop:bg-stone-900/40"
    >
      <h2 className="text-lg font-semibold text-stone-800">{title}</h2>
      {children && <div className="mt-3 text-sm text-stone-600">{children}</div>}
      <div className="mt-6 flex justify-end gap-2">
        {!hideCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="rounded-lg px-3 py-2 text-sm text-stone-600 hover:bg-stone-100 disabled:opacity-50"
          >
            {cancelLabel}
          </button>
        )}
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
