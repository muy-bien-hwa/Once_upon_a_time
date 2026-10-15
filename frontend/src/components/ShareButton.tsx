import { useEffect, useState } from 'react'
import { copyText } from '../lib/copyText.ts'

// 지금 보고 있는 문장 주소를 공유 (F-05)
// 휴대폰: 기본 공유 창 / PC: 주소 복사 (D-64)
export default function ShareButton({ title }: { title: string }) {
  const [message, setMessage] = useState('')

  // 안내 문구는 2초 뒤 사라짐
  useEffect(() => {
    if (!message) return
    const timer = setTimeout(() => setMessage(''), 2000)
    return () => clearTimeout(timer)
  }, [message])

  async function share() {
    const url = window.location.href
    // 손가락으로 쓰는 기기(휴대폰·태블릿)에서만 기본 공유 창 → PC는 주소 복사 (D-64)
    // PC 크롬에도 공유 기능이 있지만 윈도우 공유 창이 떠서 번거로움
    const isTouch = window.matchMedia('(pointer: coarse)').matches

    if (isTouch && navigator.share) {
      try {
        await navigator.share({ title, url })
      } catch {
        // 사용자가 공유 창을 닫은 경우 → 아무것도 하지 않음
      }
      return
    }

    setMessage((await copyText(url)) ? '주소를 복사했어요' : '주소를 복사하지 못했어요')
  }

  return (
    <div className="flex shrink-0 items-center gap-2">
      {message && <span className="text-sm text-stone-500">{message}</span>}
      <button
        type="button"
        onClick={share}
        className="rounded-full border border-stone-300 px-3 py-1.5 text-sm text-stone-600 hover:border-brand-600 hover:text-brand-700"
      >
        공유
      </button>
    </div>
  )
}
