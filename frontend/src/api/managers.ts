import { apiDelete, apiGet, apiPut } from './client.ts'

// 백엔드 app/schemas/story.py (StoryAuthor)와 같은 모양
export type StoryAuthor = {
  user_id: number
  nickname: string
  sentence_count: number
  // 창시자 = 금색 만년필 · 관리자 = 은색 만년필 (D-91)
  is_creator: boolean
  is_manager: boolean
}

export type StoryAuthors = {
  items: StoryAuthor[]
  // 내가 권한을 주고 거둘 수 있는지 (스토리를 시작한 작가만)
  can_appoint: boolean
  // 내가 글을 고정할 수 있는지 (창시자 + 관리자)
  can_pin: boolean
}

export function fetchAuthors(storyId: number, signal?: AbortSignal) {
  return apiGet<StoryAuthors>(`/api/stories/${storyId}/authors`, signal)
}

export function appointManager(storyId: number, userId: number) {
  return apiPut<StoryAuthors>(`/api/stories/${storyId}/managers/${userId}`)
}

export function dismissManager(storyId: number, userId: number) {
  return apiDelete<StoryAuthors>(`/api/stories/${storyId}/managers/${userId}`)
}
