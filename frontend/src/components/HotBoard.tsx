import { useEffect, useState } from 'react'
import HotRecord from './HotRecord.tsx'
import { HotTopSentences, HotTopStories } from './HotTop.tsx'

const PANES = [
  { id: 'stories', label: 'Best 스토리' },
  { id: 'sentences', label: 'Best 문장' },
  { id: 'record', label: '지금까지 기록' },
]
const INTERVAL = 5_000

// 홈 맨 위 Hot 영역: 창 3개가 5초마다 돌아가며 보임 (D-76)
export default function HotBoard() {
  const [index, setIndex] = useState(0)
  const [paused, setPaused] = useState(false)

  useEffect(() => {
    if (paused) return
    const timer = setInterval(() => setIndex((current) => (current + 1) % PANES.length), INTERVAL)
    return () => clearInterval(timer)
  }, [paused])

  return (
    <section
      aria-label="Hot"
      className="rounded-lg bg-white p-6 shadow-paper ring-1 ring-stone-200/60 sm:p-8"
      // 마우스를 올리거나 키보드로 들어오면 잠시 멈춤
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <div className="flex items-center gap-2">
        <h2 className="text-xl font-bold tracking-tight text-stone-800">{PANES[index].label}</h2>
        <div className="ml-auto flex gap-2">
          {PANES.map((pane, i) => (
            <button
              key={pane.id}
              type="button"
              aria-label={pane.label}
              aria-current={i === index}
              onClick={() => setIndex(i)}
              // 점은 작게 보이되 누를 수 있는 범위는 넓게 (-m-1.5 p-1.5)
              className="-m-1.5 rounded-full p-1.5"
            >
              <span
                className={`block h-2.5 w-2.5 rounded-full transition ${
                  i === index ? 'bg-brand-600' : 'bg-stone-300 hover:bg-stone-400'
                }`}
              />
            </button>
          ))}
        </div>
      </div>

      {/* 높이를 고정 → 창이 바뀌어도 아래 스토리 목록이 흔들리지 않음 */}
      {/* key가 바뀌면 다시 그려지면서 등장 애니메이션이 한 번 실행됨 */}
      <div key={index} className="hot-pane mt-5 flex min-h-[19rem] flex-col justify-center">
        {index === 0 && <HotTopStories />}
        {index === 1 && <HotTopSentences />}
        {index === 2 && <HotRecord />}
      </div>
    </section>
  )
}
