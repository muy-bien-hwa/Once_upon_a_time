import { apiGet, apiPost } from './client.ts'

// 백엔드 app/schemas/sentence.py와 같은 모양
export type SentenceStatus = 'active' | 'folded' | 'deleted'

export type Sentence = {
  id: number
  story_id: number
  parent_id: number | null
  depth: number
  // 접힌 문장·삭제된 문장은 서버가 내용과 작성자를 보내지 않음 (D-63·D-69)
  content: string | null
  status: SentenceStatus
  author_nickname: string | null
  created_at: string
  up_count: number
  down_count: number
  // 이 문장 뒤에 이어진 문장 수 → 오른쪽 회색 박스 개수 (D-59)
  child_count: number
}

export type SentencePath = {
  story: { id: number; title: string }
  // 첫 문장 → 지금 문장 순서
  items: Sentence[]
}

// 기본(투표 + 최신성) · 추천순 · 날짜순 (D-60)
export type SentenceSort = 'score' | 'votes' | 'latest'

export function fetchPath(sentenceId: number, signal?: AbortSignal) {
  return apiGet<SentencePath>(`/api/sentences/${sentenceId}/path`, signal)
}

export function fetchChildren(sentenceId: number, sort: SentenceSort, signal?: AbortSignal) {
  return apiGet<{ items: Sentence[] }>(`/api/sentences/${sentenceId}/children?sort=${sort}`, signal)
}

// 이어 쓰기 (#8). 스토리 번호와 깊이는 서버가 부모 문장에서 계산
export function createChild(sentenceId: number, content: string) {
  return apiPost<Sentence>(`/api/sentences/${sentenceId}/children`, { content })
}
