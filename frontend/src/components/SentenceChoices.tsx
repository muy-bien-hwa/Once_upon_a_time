import type { Sentence, SentenceSort } from '../api/sentences.ts'
import SentenceBox from './SentenceBox.tsx'
import SentenceInput from './SentenceInput.tsx'

const SORTS: { value: SentenceSort; label: string }[] = [
  { value: 'score', label: '기본' },
  { value: 'votes', label: '추천순' },
  { value: 'latest', label: '날짜순' },
]

type Props = {
  // 지금 읽는 문장 = 새 문장을 붙일 부모
  parent: Sentence
  items: Sentence[]
  sort: SentenceSort
  onSortChange: (sort: SentenceSort) => void
  dim: boolean
}

// 가운데: 지금 문장 뒤에 이어진 문장들 + 이어 쓰기 (D-59·D-64)
export default function SentenceChoices({ parent, items, sort, onSortChange, dim }: Props) {
  return (
    <>
      <div className="mb-3 flex items-center gap-2">
        <h2 className="text-sm font-medium text-stone-500">다음 문장 고르기</h2>
        <select
          aria-label="문장 정렬"
          value={sort}
          onChange={(event) => onSortChange(event.target.value as SentenceSort)}
          className="ml-auto rounded-lg border border-stone-300 bg-white px-2 py-1 text-sm text-stone-700"
        >
          {SORTS.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </select>
      </div>

      {items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-stone-300 p-8 text-center text-stone-500">
          <p>이야기가 여기서 멈춰 있어요.</p>
          <p className="mt-1 text-sm">다음 문장을 쓰는 첫 작가가 되어 보세요.</p>
        </div>
      ) : (
        <ul className={`space-y-3 transition-opacity ${dim ? 'opacity-60' : ''}`}>
          {items.map((sentence) => (
            <li key={sentence.id}>
              <SentenceBox sentence={sentence} />
            </li>
          ))}
        </ul>
      )}

      <SentenceInput parent={parent} />
    </>
  )
}
