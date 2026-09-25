// 서버와 주고받는 공통 부분: 요청 보내기 + 실패 응답을 ApiError로 바꾸기

const FALLBACK_MESSAGE = '서버와 연결이 원활하지 않아요. 잠시 후 다시 시도해 주세요.'

// 서버의 실패 응답 {"detail": {"code", "message"}} (D-57)
// 화면에는 message만 보여주고, code는 코드 안에서 에러 종류를 나눌 때 씀
export class ApiError extends Error {
  status: number
  code: string | null

  constructor(status: number, code: string | null, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, { signal })
  } catch (error) {
    // 요청 취소는 그대로 넘김 (화면이 사라졌을 때 등)
    if (signal?.aborted) throw error
    throw new ApiError(0, null, FALLBACK_MESSAGE)
  }

  if (!response.ok) throw await toApiError(response)
  return (await response.json()) as T
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, null, FALLBACK_MESSAGE)
  }

  if (!response.ok) throw await toApiError(response)
  return (await response.json()) as T
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = await response.json()
    const detail = body?.detail
    // 422(입력 형식 오류)는 detail이 배열이라 여기로 오지 않음 → 기본 문구
    if (typeof detail?.message === 'string') {
      return new ApiError(response.status, detail.code ?? null, detail.message)
    }
  } catch {
    // 응답이 JSON이 아님 (서버가 꺼져 있을 때 등)
  }
  return new ApiError(response.status, null, FALLBACK_MESSAGE)
}
