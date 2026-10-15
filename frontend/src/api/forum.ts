import { apiDelete, apiGet, apiPost, apiPut } from './client.ts'

// 백엔드 app/schemas/forum.py와 같은 모양
export type PostSort = 'new' | 'hot'

export type QuotedSentence = {
  id: number
  content: string
}

export type PostSummary = {
  id: number
  story_id: number
  // 신고로 접히면 제목·작성자·본문·인용이 비어서 옴 (D-69와 같은 방식)
  title: string | null
  author_nickname: string | null
  status: 'active' | 'folded'
  created_at: string
  up_count: number
  down_count: number
  // 내가 누른 표: 1 추천 · -1 비추천 · null 안 누름
  my_vote: number | null
  comment_count: number
  // 1·2 = 고정 자리 / null = 보통 글 (D-91)
  pin_slot: number | null
  quoted_sentence: QuotedSentence | null
}

export type Post = PostSummary & {
  body: string | null
  // 내가 이 글을 고정·해제할 수 있는지 (창시자·관리자만)
  can_pin: boolean
}

export type PostList = {
  items: PostSummary[]
  can_pin: boolean
  page: number
  size: number
  total: number
}

export type Comment = {
  id: number
  post_id: number
  // null이면 맨 위 댓글 / 답글의 답글도 맨 위 댓글을 가리킴 (2단 유지, D-91)
  parent_id: number | null
  body: string | null
  author_nickname: string | null
  status: 'active' | 'folded'
  // 누구에게 한 말인지 (@닉네임)
  reply_to_nickname: string | null
  created_at: string
}

export function fetchPosts(storyId: number, sort: PostSort, page: number, signal?: AbortSignal) {
  const params = new URLSearchParams({ sort, page: String(page) })
  return apiGet<PostList>(`/api/stories/${storyId}/forum/posts?${params}`, signal)
}

export function fetchPost(postId: number, signal?: AbortSignal) {
  return apiGet<Post>(`/api/forum/posts/${postId}`, signal)
}

export function fetchComments(postId: number, signal?: AbortSignal) {
  return apiGet<{ items: Comment[] }>(`/api/forum/posts/${postId}/comments`, signal)
}

export function createPost(
  storyId: number,
  data: { title: string; body: string; quoted_sentence_id?: number },
) {
  return apiPost<Post>(`/api/stories/${storyId}/forum/posts`, data)
}

export function deletePost(postId: number) {
  return apiDelete<{ status: string }>(`/api/forum/posts/${postId}`)
}

export function createComment(postId: number, body: string, parentId?: number) {
  return apiPost<Comment>(`/api/forum/posts/${postId}/comments`, {
    body,
    parent_id: parentId ?? null,
  })
}

export function deleteComment(commentId: number) {
  return apiDelete<{ status: string }>(`/api/forum/comments/${commentId}`)
}

export function votePost(postId: number, value: 1 | -1) {
  return apiPut<Post>(`/api/forum/posts/${postId}/vote`, { value })
}

export function cancelPostVote(postId: number) {
  return apiDelete<Post>(`/api/forum/posts/${postId}/vote`)
}

export function pinPost(postId: number) {
  return apiPut<Post>(`/api/forum/posts/${postId}/pin`)
}

export function unpinPost(postId: number) {
  return apiDelete<Post>(`/api/forum/posts/${postId}/pin`)
}
