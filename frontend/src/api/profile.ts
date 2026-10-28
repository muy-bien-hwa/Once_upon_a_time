// 마이페이지·작가 화면 (#34~#37)
import { apiDelete, apiGet } from './client.ts'

export type MeSummary = {
  joined_at: string
  // 아래 숫자 셋은 목록과 같은 범위 (지운 문장·접힌 문장 포함)
  sentence_count: number
  story_count: number
  received_up_count: number
  live_sentence_count: number
}

export type ProfileSentence = {
  id: number
  // 지운 문장·접힌 문장은 본문이 null (서버가 보내지 않음)
  content: string | null
  status: 'active' | 'folded' | 'deleted'
  story_id: number
  story_title: string
  created_at: string
  up_count: number
}

export type ProfileSentenceList = {
  items: ProfileSentence[]
  page: number
  size: number
  total: number
}

// 최신순(기본) · 추천순
export type ProfileSort = 'latest' | 'votes'

export type ListOptions = { page?: number; size?: number; sort?: ProfileSort; q?: string }

export function fetchMySummary(signal?: AbortSignal) {
  return apiGet<MeSummary>('/api/me/summary', signal)
}

export function fetchMySentences(options: ListOptions, signal?: AbortSignal) {
  return apiGet<ProfileSentenceList>(withOptions('/api/me/sentences', options), signal)
}

export function withdraw() {
  return apiDelete<{ status: string }>('/api/me')
}

// 기본값과 같은 것은 주소에 붙이지 않음 (주소가 짧아지고, 같은 목록이면 같은 주소가 됨)
function withOptions(path: string, { page = 1, size, sort = 'latest', q }: ListOptions) {
  const params = new URLSearchParams()
  if (page > 1) params.set('page', String(page))
  if (size) params.set('size', String(size))
  if (sort !== 'latest') params.set('sort', sort)
  if (q) params.set('q', q)
  const query = params.toString()
  return query ? `${path}?${query}` : path
}
