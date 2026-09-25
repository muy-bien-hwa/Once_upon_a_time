import { useEffect, useState } from 'react'

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

    setMessage((await copy(url)) ? '주소를 복사했어요' : '주소를 복사하지 못했어요')
  }

  async function copy(url: string) {
    try {
      await navigator.clipboard.writeText(url)
      return true
    } catch {
      // 복사 권한이 막힌 브라우저 → 예전 방식으로 한 번 더 시도
      return copyByTextarea(url)
    }
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

// 화면 밖에 입력칸을 잠깐 만들어 복사 (오래된 방식이지만 대부분의 브라우저에서 동작)
function copyByTextarea(text: string) {
  const area = document.createElement('textarea')
  area.value = text
  area.readOnly = true
  area.style.position = 'fixed'
  area.style.opacity = '0'
  document.body.append(area)
  area.select()
  const copied = document.execCommand('copy')
  area.remove()
  return copied
}
