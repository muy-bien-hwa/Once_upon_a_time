import { apiDelete, apiGet, apiPost, apiPut } from './client.ts'
import type { Sentence } from './sentences.ts'

// 백엔드 app/schemas/story.py와 같은 모양
export type StorySort = 'latest' | 'oldest' | 'recommended' | 'deepest' | 'shallowest'

export type Story = {
  id: number
  title: string
  first_sentence_id: number
  // 신고로 접히면 null (D-69)
  first_sentence: string | null
  first_sentence_status: 'active' | 'folded'
  // 스토리를 시작한 작가 (첫 문장을 쓴 사람)
  creator_nickname: string
  recommend_count: number
  // 내가 이 스토리를 추천했는지 (로그인 안 했으면 항상 false, F-13)
  my_recommendation: boolean
  author_count: number
  max_depth: number
  // 커뮤니티 탭에 적는 글 개수 (F-17)
  post_count: number
  created_at: string
}

export type StoryList = {
  items: Story[]
  page: number
  size: number
  total: number
}

export type StoryListQuery = {
  sort: StorySort
  page: number
  size: number
}

// 새 스토리 = 제목 + 첫 문장 (한 번에 저장, D-65)
export function createStory(data: { title: string; content: string }) {
  return apiPost<{ story: Story; sentence: Sentence }>('/api/stories', data)
}

export function fetchStory(storyId: number, signal?: AbortSignal) {
  return apiGet<Story>(`/api/stories/${storyId}`, signal)
}

export function fetchStories(query: StoryListQuery, signal?: AbortSignal) {
  const params = new URLSearchParams({
    sort: query.sort,
    page: String(query.page),
    size: String(query.size),
  })
  return apiGet<StoryList>(`/api/stories?${params}`, signal)
}


// 추천 누르기 / 다시 누르면 취소 (F-13). 둘 다 바뀐 스토리를 돌려줌
export function recommendStory(storyId: number) {
  return apiPut<Story>(`/api/stories/${storyId}/recommendation`)
}

export function cancelRecommendation(storyId: number) {
  return apiDelete<Story>(`/api/stories/${storyId}/recommendation`)
}
