// 단계 이름 399개를 글자표로 그릴 때 쓰는 계산 (6-8)
// 이름은 받침 없는 한글 한 글자 — 「가」부터 「히」까지 사전 순서

// 한글 글자는 '가' 다음에 받침 있는 글자 27개가 이어지므로, 받침 없는 글자는 28칸마다 하나
const FIRST_SYLLABLE = 0xac00 // '가'
const WITH_FINALS = 28

// 한 자음 줄에 모음 21개 → 19줄(가줄 … 하줄) × 21칸 = 399
export const LEVEL_COLUMNS = 21
export const LEVEL_ROWS = 19
export const LEVEL_COUNT = LEVEL_ROWS * LEVEL_COLUMNS

// 1단계 = '가' … 399단계 = '히'
export function levelName(level: number): string {
  return String.fromCodePoint(FIRST_SYLLABLE + (level - 1) * WITH_FINALS)
}

// 그 단계가 몇 번째 자음 줄인지 (가줄 = 0 … 하줄 = 18)
export function levelRow(level: number): number {
  return Math.floor((level - 1) / LEVEL_COLUMNS)
}

// 그 줄의 첫 글자 ('가' '까' '나' … '하')
export function rowName(row: number): string {
  return levelName(row * LEVEL_COLUMNS + 1)
}

// 글자표에 그릴 단계 번호 1~399 (한 번만 만들어 두고 다시 씀)
export const LEVELS: number[] = Array.from({ length: LEVEL_COUNT }, (_, i) => i + 1)
