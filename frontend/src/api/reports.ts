import { apiPost } from './client.ts'

// 백엔드 app/schemas/report.py와 같은 모양 (F-10·D-93)
// 신고 창의 토글 순서가 그대로 이 순서
export const REPORT_REASONS = [
  { value: 'abuse', label: '욕설·비방' },
  { value: 'sexual', label: '음란·선정성' },
  { value: 'violence', label: '폭력·잔혹' },
  { value: 'spam', label: '광고·도배' },
  { value: 'privacy', label: '개인정보 노출' },
  { value: 'plagiarism', label: '표절' },
  { value: 'other', label: '기타' },
] as const

export type ReportReason = (typeof REPORT_REASONS)[number]['value']

// 신고할 수 있는 것 세 가지 (주소만 다르고 보내는 내용은 같음)
export type ReportKind = 'sentence' | 'comment' | 'post'

// 설명은 500자까지 / "기타"를 고르면 반드시 적어야 함 (서버도 확인)
export const DETAIL_MAX = 500

const PATHS: Record<ReportKind, (id: number) => string> = {
  sentence: (id) => `/api/sentences/${id}/reports`,
  post: (id) => `/api/forum/posts/${id}/reports`,
  comment: (id) => `/api/forum/comments/${id}/reports`,
}

// 신고 보내기 — 돌아오는 건 "받았다"는 사실뿐 (신고 수는 아무에게도 안 보임, D-93)
export function sendReport(kind: ReportKind, id: number, reason: ReportReason, detail: string) {
  return apiPost<{ reported: boolean }>(PATHS[kind](id), { reason, detail })
}
