import { Link } from 'react-router'
import type { ProfileSentence } from '../api/profile.ts'
import { formatDate } from '../lib/time.ts'

// 가려진 문장은 본문 대신 이 문구만 (서버가 본문을 보내지 않음, 약관 26조)
const HIDDEN = {
  deleted: { text: '내가 지운 문장', badge: '삭제함', tone: 'text-stone-500 ring-stone-300' },
  folded: {
    text: '신고 처리된 문장',
    badge: '신고 처리됨',
    tone: 'text-down-600 ring-down-600/40',
  },
}

// 마이페이지·내 문장·작가 화면이 함께 쓰는 한 줄 (6-7)
export default function SentenceRow({ sentence }: { sentence: ProfileSentence }) {
  const hidden = sentence.status === 'active' ? null : HIDDEN[sentence.status]

  const inside = (
    <>
      {hidden ? (
        <p className="text-sm text-stone-400">{hidden.text}</p>
      ) : (
        <p className="font-serif text-[15px] leading-relaxed text-stone-800">{sentence.content}</p>
      )}
      <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-stone-500">
        <span className="max-w-[12rem] truncate">{sentence.story_title}</span>
        <span aria-hidden>·</span>
        <span>{formatDate(sentence.created_at)}</span>
        {hidden ? (
          <span className={`rounded-full px-2 py-0.5 ring-1 ${hidden.tone}`}>{hidden.badge}</span>
        ) : (
          <>
            <span aria-hidden>·</span>
            <span>추천 {sentence.up_count}</span>
          </>
        )}
      </div>
    </>
  )

  // 가려진 문장은 갈 곳이 없으므로 누를 수 없게 둠
  if (hidden) return <li className="px-2 py-3">{inside}</li>

  return (
    <li>
      <Link
        to={`/s/${sentence.id}`}
        className="block rounded-lg px-2 py-3 transition hover:bg-stone-100/70"
      >
        {inside}
      </Link>
    </li>
  )
}
