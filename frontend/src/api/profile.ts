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

export type ProfileCounts = { all: number; active: number; deleted: number; folded: number }

export type ProfileSentenceList = {
  items: ProfileSentence[]
  page: number
  size: number
  // 지금 고른 거르개(와 검색)에 해당하는 문장 수
  total: number
  // 거르개 버튼에 적는 수 — 내 화면에서만 옴 (작가 화면은 null)
  counts: ProfileCounts | null
}

// 최신순(기본) · 추천순
export type ProfileSort = 'latest' | 'votes'

// 내 문장 거르개: 전체(기본) · 보임 · 삭제함 · 신고 처리됨
export type ProfileFilter = 'all' | 'active' | 'deleted' | 'folded'

export type ListOptions = {
  page?: number
  size?: number
  sort?: ProfileSort
  q?: string
  status?: ProfileFilter
}

export type Author = {
  nickname: string
  // 날짜까지는 공개하지 않음 — "2026-05" (D-95)
  joined_month: string
  sentence_count: number
  story_count: number
  received_up_count: number
}

export function fetchAuthor(nickname: string, signal?: AbortSignal) {
  return apiGet<Author>(`/api/users/${encodeURIComponent(nickname)}`, signal)
}

export function fetchAuthorSentences(
  nickname: string,
  options: ListOptions,
  signal?: AbortSignal,
) {
  const path = `/api/users/${encodeURIComponent(nickname)}/sentences`
  return apiGet<ProfileSentenceList>(withOptions(path, options), signal)
}

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
function withOptions(
  path: string,
  { page = 1, size, sort = 'latest', q, status = 'all' }: ListOptions,
) {
  const params = new URLSearchParams()
  if (page > 1) params.set('page', String(page))
  if (size) params.set('size', String(size))
  if (sort !== 'latest') params.set('sort', sort)
  if (q) params.set('q', q)
  if (status !== 'all') params.set('status', status)
  const query = params.toString()
  return query ? `${path}?${query}` : path
}
