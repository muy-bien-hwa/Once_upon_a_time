import { useEffect, useRef, useState } from 'react'
import { copyText } from '../lib/copyText.ts'
import { chromeIntentUrl, isAndroid } from '../lib/inAppBrowser.ts'

type Props = { app: string; open: boolean; onClose: () => void }

// 앱 안의 브라우저에서 로그인을 누르면 뜨는 안내 (F-24·D-45·D-90)
// 구글이 앱 안의 브라우저에서는 로그인을 막아서, 밖의 브라우저로 옮겨 가야 함
export default function InAppBrowserDialog({ app, open, onClose }: Props) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [message, setMessage] = useState('')
  const url = window.location.href

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
      className="m-auto w-[min(26rem,90vw)] rounded-lg bg-white p-6 text-left shadow-xl backdrop:bg-stone-900/40"
    >
      <h2 className="text-lg font-semibold text-stone-800">
        {app} 안에서는 구글 로그인이 안 돼요
      </h2>
      <p className="mt-3 text-sm text-stone-600">
        구글이 앱 안의 브라우저에서는 로그인을 막고 있어요. 아래 주소를 크롬·사파리 같은 브라우저에서
        열면 로그인할 수 있어요. 읽기만 한다면 여기서 그대로 보셔도 괜찮아요.
      </p>

      <p className="mt-4 rounded-lg bg-stone-100 p-3 text-xs break-all text-stone-700 select-all">
        {url}
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={async () => {
            setMessage((await copyText(url)) ? '복사했어요' : '복사하지 못했어요. 주소를 길게 눌러 복사해 주세요')
          }}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
        >
          주소 복사
        </button>
        {isAndroid() && (
          <a
            href={chromeIntentUrl(url)}
            className="rounded-lg border border-stone-300 px-4 py-2 text-sm text-stone-700 hover:border-brand-600 hover:text-brand-700"
          >
            크롬으로 열기
          </a>
        )}
        <button
          type="button"
          onClick={onClose}
          className="ml-auto rounded-lg px-3 py-2 text-sm text-stone-600 hover:bg-stone-100"
        >
          닫기
        </button>
      </div>

      {message && <p className="mt-3 text-sm text-stone-500">{message}</p>}

      {!isAndroid() && (
        <p className="mt-3 text-xs text-stone-500">
          아이폰은 화면 오른쪽 아래 ⋯ 또는 공유 버튼 → “Safari로 열기”를 눌러도 됩니다.
        </p>
      )}
    </dialog>
  )
}
