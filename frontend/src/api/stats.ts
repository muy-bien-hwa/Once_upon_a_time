import type { Sentence } from './sentences.ts'
import { apiGet } from './client.ts'
import type { Story } from './stories.ts'

export type Record = {
  // 참여 작가가 가장 많은 스토리 / 스토리가 없으면 null
  most_authors_story: Story | null
}

export type HotPeriod = 'day' | 'week' | 'month'

export type HotStory = {
  story: Story
  // 그 기간에 받은 추천 수
  recommend_count: number
}

export type HotSentence = {
  sentence: Sentence
  story: { id: number; title: string }
  vote_count: number
}

// 일간·주간·월간을 한 번에 받음
export type ByPeriod<T> = { day: T[]; week: T[]; month: T[] }

export function fetchRecord(signal?: AbortSignal) {
  return apiGet<Record>('/api/stats/record', signal)
}

export function fetchTopStories(signal?: AbortSignal) {
  return apiGet<ByPeriod<HotStory>>('/api/stats/top-stories', signal)
}

export function fetchTopSentences(signal?: AbortSignal) {
  return apiGet<ByPeriod<HotSentence>>('/api/stats/top-sentences', signal)
}
