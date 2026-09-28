import type { Sentence } from '../api/sentences.ts'

// 문장 본문. 접힘·삭제는 서버가 내용을 보내지 않으므로 문구만 (D-63·D-69)
export default function SentenceText({ sentence }: { sentence: Sentence }) {
  // 시스템 안내 문구는 고딕 (이야기 문장과 구분)
  if (sentence.status === 'folded') {
    return <p className="text-[15px] text-stone-500">신고 처리된 문장입니다.</p>
  }
  if (sentence.status === 'deleted') {
    return <p className="text-[15px] text-red-500">삭제된 문장</p>
  }
  // 이야기 문장은 명조 (D-79) / 한 줄이 너무 길지 않게 폭 제한
  return <p className="max-w-[34em] font-serif text-sentence text-stone-800">{sentence.content}</p>
}
