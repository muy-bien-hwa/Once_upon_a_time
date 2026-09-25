const MINUTE = 60 * 1000
const HOUR = 60 * MINUTE
const DAY = 24 * HOUR

// 한국 시간 기준 "2026.09.21"
const dateFormat = new Intl.DateTimeFormat('ko-KR', {
  timeZone: 'Asia/Seoul',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})

// 서버 시간(UTC) → 7일 안이면 "3일 전", 그 뒤로는 날짜 (D-71)
// export = 다른 파일에서 가져다 쓸 수 있게 함
// function ... : string = string 으로 return
export function formatTimeAgo(iso: string, now: Date = new Date()): string {
  const diff = now.getTime() - new Date(iso).getTime()

  if (diff < MINUTE) return '방금 전'
  if (diff < HOUR) return `${Math.floor(diff / MINUTE)}분 전`
  if (diff < DAY) return `${Math.floor(diff / HOUR)}시간 전`
  if (diff < 7 * DAY) return `${Math.floor(diff / DAY)}일 전`
  return formatDate(iso)
}

export function formatDate(iso: string): string {
  const parts = dateFormat.formatToParts(new Date(iso))
  const get = (type: string) => parts.find((part) => part.type === type)?.value
  return `${get('year')}.${get('month')}.${get('day')}`
}
