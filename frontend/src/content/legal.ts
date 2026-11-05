// 약관·운영정책·개인정보 처리방침이 공통으로 쓰는 모양 (D-95)
// 본문은 초안 HTML에서 기계로 옮겨 옴 — terms.ts · operation.ts · privacy.ts

export type LegalTable = { head: string[]; rows: string[][] }
export type LegalBlock = string | { sub: string[] } | LegalTable
export type LegalArticle = { title: string; blocks: LegalBlock[] }
export type LegalChapter = { name?: string; articles: LegalArticle[] }
export type LegalDoc = { title: string; intro?: string; chapters: LegalChapter[] }

// 시행일 — 베타를 여는 날로 정하고 그날 여기만 고치면 세 문서에 함께 반영됨
// 비워 두면 화면에 "서비스 공개일"로 적힘
export const EFFECTIVE = ''

// 세 문서가 서로를 오갈 수 있게 (화면 맨 아래 링크도 이 목록을 씀)
export const LEGAL_PAGES = [
  { path: '/terms', label: '이용약관' },
  { path: '/policy', label: '운영정책' },
  { path: '/privacy', label: '개인정보 처리방침' },
]

export const CONTACT = 'relaystory.help@gmail.com'
