import { useEffect, useState } from 'react'

// 0 → target 숫자 올리기 (D-90)
// 앞 구간은 성큼성큼, 마지막 몇 명 구간에서 천천히 멈춤 (슬롯머신이 멎듯)
export function useCountUp(target: number | undefined, duration = 1800): number {
  const [animated, setAnimated] = useState(0)
  // 움직임 줄이기를 켠 사람에게는 애니메이션 없이 최종 숫자만 (D-90)
  const [reduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  const skip = target === undefined || target <= 0 || reduced

  useEffect(() => {
    if (skip || target === undefined) return

    // 창이 가려져 화면 그리기가 멈추면 애니메이션도 멈춤 → 최종 숫자는 반드시 보이게
    const fallback = window.setTimeout(() => setAnimated(target), duration + 400)
    const start = performance.now()
    let frame = 0

    const tick = (now: number) => {
      const passed = Math.min((now - start) / duration, 1)
      // easeOutExpo: 절반 시점에 이미 97%까지 올라가고 끝에서 느려짐
      const eased = passed === 1 ? 1 : 1 - 2 ** (-10 * passed)
      setAnimated(Math.round(target * eased))
      if (passed < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)

    return () => {
      cancelAnimationFrame(frame)
      window.clearTimeout(fallback)
    }
  }, [skip, target, duration])

  return skip ? (target ?? 0) : animated
}
