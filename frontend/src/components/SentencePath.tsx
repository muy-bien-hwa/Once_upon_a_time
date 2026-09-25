import { Link } from 'react-router'
import type { Sentence } from '../api/sentences.ts'
import SentenceText from './SentenceText.tsx'

// 왼쪽: 첫 문장부터 지금 문장까지. 앞 문장은 흐리게, 누르면 그 문장으로 돌아감 (D-59)
export default function SentencePath({ items }: { items: Sentence[] }) {
  return (
    <ol className="space-y-1">
      {items.map((sentence, index) =>
        index === items.length - 1 ? (
          <li key={sentence.id} className="rounded-xl bg-white p-3 shadow-sm">
            <SentenceText sentence={sentence} />
            <p className="mt-1 text-xs text-stone-400">지금 읽는 문장</p>
          </li>
        ) : (
          <li key={sentence.id}>
            <Link
              to={`/s/${sentence.id}`}
              className="block rounded-xl p-3 opacity-50 transition hover:bg-stone-200/60 hover:opacity-100"
            >
              <SentenceText sentence={sentence} />
            </Link>
          </li>
        ),
      )}
    </ol>
  )
}
