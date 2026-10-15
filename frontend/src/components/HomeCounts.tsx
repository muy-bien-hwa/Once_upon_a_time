import { useQuery } from '@tanstack/react-query'
import { fetchRecord } from '../api/stats.ts'
import { useCountUp } from '../lib/useCountUp.ts'

// 홈 제목 아래 한 줄: 지금까지 몇 명이 몇 문장을 썼는지 (F-14·D-90)
// 핵심 지표라 가장 먼저 보이는 자리에 두고, 화면을 열 때마다 0에서 올라감
export default function HomeCounts() {
  // HotRecord와 같은 데이터 → 요청은 한 번만 나감
  const { data } = useQuery({
    queryKey: ['stats', 'record'],
    queryFn: ({ signal }) => fetchRecord(signal),
  })
  const authors = useCountUp(data?.total_authors)
  const sentences = useCountUp(data?.total_sentences)

  // 받아오기 전·아무도 안 썼을 때는 자리만 비워 둠 (제목이 위아래로 흔들리지 않게)
  if (!data || data.total_authors === 0) return <p className="mt-3 h-6" />

  return (
    <p className="mt-3 h-6 text-stone-500">
      지금까지 <Count value={authors} unit="명" />의 작가가 <Count value={sentences} unit="개" />의
      문장을 만들었어요
    </p>
  )
}

function Count({ value, unit }: { value: number; unit: string }) {
  return (
    <span className="font-semibold text-brand-700 tabular-nums">
      {value.toLocaleString('ko-KR')}
      {unit}
    </span>
  )
}
