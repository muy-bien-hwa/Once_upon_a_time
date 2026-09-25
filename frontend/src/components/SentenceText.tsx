import type { Sentence } from '../api/sentences.ts'

// 문장 본문. 접힘·삭제는 서버가 내용을 보내지 않으므로 문구만 (D-63·D-69)
export default function SentenceText({ sentence }: { sentence: Sentence }) {
  if (sentence.status === 'folded') {
    return <p className="text-stone-400">신고 처리된 문장입니다.</p>
  }
  if (sentence.status === 'deleted') {
    return <p className="text-red-400">삭제된 문장</p>
  }
  return <p className="text-stone-800">{sentence.content}</p>
}
