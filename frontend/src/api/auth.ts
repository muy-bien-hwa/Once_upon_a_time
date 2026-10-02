import { ApiError, apiGet, apiPost, apiPut } from './client.ts'

export type Me = {
  id: number
  // 첫 로그인 직후에는 아직 없음 → 닉네임 정하기 화면으로 (D-48)
  nickname: string | null
  // 다음에 닉네임을 바꿀 수 있는 시각 / null이면 지금 바꿀 수 있음 (D-85)
  nickname_editable_at: string | null
}

// 이 주소로 가면 서버가 구글 로그인 화면으로 보내 줌
export const LOGIN_URL = '/auth/google/login'

// 로그인 안 한 상태(401)는 오류가 아니라 "손님" → null
export async function fetchMe(signal?: AbortSignal): Promise<Me | null> {
  try {
    return await apiGet<Me>('/api/me', signal)
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null
    throw error
  }
}

export function setNickname(nickname: string) {
  return apiPut<Me>('/api/me/nickname', { nickname })
}

export function logout() {
  return apiPost<{ status: string }>('/auth/logout', {})
}
