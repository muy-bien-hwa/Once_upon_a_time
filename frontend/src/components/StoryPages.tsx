import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router'
import type { Sentence } from '../api/sentences.ts'

// 한 줄 높이(px) × 한 쪽 줄 수 = 쪽 높이. 줄 높이의 배수라 글줄이 반쯤 잘리지 않음
const LINE = 32
const LINES = 10
const PAGE_HEIGHT = LINE * LINES
// 쪽과 쪽 사이 간격
const GAP = 40

// 지금까지의 이야기를 책처럼 보여줌: 한 쪽이 차면 옆 쪽으로 이어지고, ◀▶로 좌우로 넘김 (D-80)
export default function StoryPages({ items }: { items: Sentence[] }) {
  const content = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(0)
  const [pageCount, setPageCount] = useState(1)
  const [page, setPage] = useState(0)

  // 한 쪽 너비 = 글이 놓이는 칸의 너비 (여백 제외, 창 크기가 바뀌면 다시 잼)
  useEffect(() => {
    const element = content.current
    if (!element) return

    const update = () => setWidth(element.clientWidth)
    update()
    const observer = new ResizeObserver(update)
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  // 글이 늘거나 폭이 바뀌면 쪽수를 다시 세고, 마지막 쪽(지금 읽는 문장)을 펼침
  useEffect(() => {
    const element = content.current
    if (!element || !width) return
    const count = Math.max(1, Math.round((element.scrollWidth + GAP) / (width + GAP)))
    setPageCount(count)
    setPage(count - 1)
  }, [items, width])

  return (
    <div>
      <div
        className="overflow-hidden rounded-lg bg-white px-6 shadow-paper ring-1 ring-stone-200/60"
        style={{ paddingTop: 20, paddingBottom: 20 }}
      >
        {/* 바깥 칸을 옆으로 밀어서 그 쪽만 보이게 함 (단으로 나뉜 칸 자체는 밀리지 않음) */}
        <div
          className="transition-transform duration-300"
          style={{ transform: `translateX(-${page * (width + GAP)}px)` }}
        >
          {/* 글을 쪽 너비의 단으로 흘려보냄 → 한 쪽이 차면 옆 쪽으로 이어짐 */}
          <div
            ref={content}
            className="font-serif text-[18px] text-stone-700"
            style={{
              height: PAGE_HEIGHT,
              lineHeight: `${LINE}px`,
              columnWidth: width || undefined,
              columnGap: GAP,
              columnFill: 'auto',
            }}
          >
            {items.map((sentence, index) => (
              <p key={sentence.id} className="break-inside-avoid">
                <Piece sentence={sentence} current={index === items.length - 1} />
              </p>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-2 flex items-center justify-center gap-4 text-sm text-stone-500">
        <button
          type="button"
          aria-label="이전 쪽"
          disabled={page === 0}
          onClick={() => setPage((current) => current - 1)}
          className="rounded-lg px-3 py-1 hover:bg-stone-200/60 disabled:opacity-30 disabled:hover:bg-transparent"
        >
          ◀
        </button>
        <span className="tabular-nums">
          {page + 1} / {pageCount}
        </span>
        <button
          type="button"
          aria-label="다음 쪽"
          disabled={page >= pageCount - 1}
          onClick={() => setPage((current) => current + 1)}
          className="rounded-lg px-3 py-1 hover:bg-stone-200/60 disabled:opacity-30 disabled:hover:bg-transparent"
        >
          ▶
        </button>
      </div>
    </div>
  )
}

// 문장 하나. 지금 읽는 문장은 강조, 앞 문장은 누르면 그 문장으로 돌아감 (D-59)
function Piece({ sentence, current }: { sentence: Sentence; current: boolean }) {
  if (sentence.status !== 'active') {
    return (
      <span className="text-stone-400">
        {sentence.status === 'folded' ? '(신고 처리된 문장)' : '(삭제된 문장)'}
      </span>
    )
  }

  if (current) {
    // 지금 읽는 문장 표시는 애니메이션 없이 항상 보이게 (움직임은 선택지 쪽에서만)
    return (
      <span className="rounded bg-brand-50 px-1 font-medium text-stone-900">
        {sentence.content}
      </span>
    )
  }

  return (
    <Link to={`/s/${sentence.id}`} className="rounded hover:bg-stone-100 hover:text-stone-900">
      {sentence.content}
    </Link>
  )
}
