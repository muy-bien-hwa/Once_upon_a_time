// 단계 사다리 화면 (6-8) — 로그인하지 않아도 볼 수 있는 공개 정보
import { apiGet } from './client.ts'

export type LevelCount = {
  level: number
  // 그 단계의 이름 한 글자 ("개")
  name: string
  count: number
}

export type LevelDistribution = {
  // 작가가 한 명이라도 있는 단계만, 낮은 단계부터
  items: LevelCount[]
  total_writers: number
}

export function fetchLevelDistribution(signal?: AbortSignal) {
  return apiGet<LevelDistribution>('/api/levels/distribution', signal)
}
