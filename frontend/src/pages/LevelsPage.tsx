import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { fetchLevelDistribution, type LevelDistribution } from '../api/levels.ts'
import { fetchMySummary } from '../api/profile.ts'
import AccountBar from '../components/AccountBar.tsx'
import LevelBadge from '../components/LevelBadge.tsx'
import ProfileFrame, { Panel } from '../components/ProfileLayout.tsx'
import { LEVEL_COLUMNS, LEVEL_ROWS, LEVELS, levelName, levelRow, rowName } from '../lib/levels.ts'
import { useMe } from '../lib/useMe.ts'

// 작가 단계 사다리 (6-8) — 로그인하지 않아도 볼 수 있음
export default function LevelsPage() {
  const { data: me } = useMe()

  // 내 단계는 마이페이지가 쓰는 요약을 그대로 씀 — 손님은 요청하지 않음(401 방지)
  const summary = useQuery({
    queryKey: ['me', 'summary'],
    queryFn: ({ signal }) => fetchMySummary(signal),
    enabled: Boolean(me),
  })
  const distribution = useQuery({
    queryKey: ['levels', 'distribution'],
    queryFn: ({ signal }) => fetchLevelDistribution(signal),
  })

  // 0단계(아직 점수가 없음)와 로그인 안 한 상태는 똑같이 "표시할 칸 없음"
  const myLevel = summary.data?.level ?? 0

  return (
    <ProfileFrame
      top={
        <>
          <Link
            to="/"
            className="btn btn-nav"
          >
            홈
          </Link>
          <AccountBar />
        </>
      }
    >
      <header>
        <h1 className="font-serif text-2xl font-semibold text-stone-900">작가 단계</h1>
        <p className="mt-1 text-sm text-stone-500">
          쓴 문장과 받은 추천이 점수가 되고, 점수만큼 이름이 올라가요.
        </p>
      </header>

      <div className="mt-4 flex flex-col gap-4">
        <Panel title="올라가는 방법">
          <ul className="flex flex-col gap-1.5 text-sm text-stone-600">
            <li>문장 하나를 쓰면 10점, 내 문장이 추천을 하나 받으면 1점이에요.</li>
            <li>점수가 쌓이면 이름이 「가」에서 「히」까지 사전 순서로 한 칸씩 올라가요.</li>
            <li>자음 줄이 올라갈수록 한 칸 오르는 데 드는 점수가 무거워져요.</li>
          </ul>
          {myLevel > 0 && (
            <p className="mt-3 border-t border-stone-100 pt-3 text-sm text-stone-600">
              지금 내 단계는{' '}
              <LevelBadge name={summary.data?.level_name} label={summary.data?.level_label} />{' '}
              <span className="tabular-nums">
                ({summary.data?.score.toLocaleString('ko-KR')}점)
              </span>
            </p>
          )}
        </Panel>

        <Panel title="단계 이름 399개">
          <p className="text-sm text-stone-500">
            왼쪽 위 「가」가 1단계, 오른쪽 아래 「히」가 399단계예요.
            {myLevel > 0 && ' 초록 칸이 내 자리예요.'}
          </p>
          {/* 휴대폰에서는 글자표만 옆으로 움직임 — 화면 전체가 밀리지 않게 */}
          <div className="mt-3 overflow-x-auto pb-1">
            <div className="grid min-w-[36rem] grid-cols-[repeat(21,minmax(0,1fr))] gap-1">
              {LEVELS.map((level) => {
                const mine = level === myLevel
                return (
                  <span
                    key={level}
                    aria-current={mine ? 'true' : undefined}
                    title={`${level}단계 「${levelName(level)}」${mine ? ' · 지금 내 단계' : ''}`}
                    className={`flex aspect-square items-center justify-center rounded-sm text-[11px] ${
                      mine ? 'bg-brand-600 font-bold text-white' : 'bg-stone-100 text-stone-600'
                    }`}
                  >
                    {levelName(level)}
                  </span>
                )
              })}
            </div>
          </div>
        </Panel>

        <Panel title="작가들이 서 있는 자리">
          {distribution.isPending ? (
            <div className="h-64 animate-pulse rounded-lg bg-stone-100" />
          ) : distribution.isError ? (
            <p className="py-6 text-center text-sm text-stone-500">
              {distribution.error.message}
            </p>
          ) : (
            <Spread data={distribution.data} myLevel={myLevel} />
          )}
        </Panel>
      </div>
    </ProfileFrame>
  )
}

// 399칸을 그대로 세우면 휴대폰에서 읽을 수 없어 자음 줄(가줄 … 하줄) 19개로 묶음
function Spread({ data, myLevel }: { data: LevelDistribution; myLevel: number }) {
  const counts = Array.from({ length: LEVEL_ROWS }, () => 0)
  for (const item of data.items) counts[levelRow(item.level)] += item.count
  // 가장 많은 줄을 꽉 찬 길이로 보고 나머지를 견줌
  const most = Math.max(...counts, 1)
  const myRow = myLevel > 0 ? levelRow(myLevel) : -1

  return (
    <>
      <p className="text-sm text-stone-500">
        단계가 있는 작가 {data.total_writers.toLocaleString('ko-KR')}명
      </p>
      <ul className="mt-3 flex flex-col gap-1">
        {counts.map((count, row) => {
          const mine = row === myRow
          return (
            <li
              key={row}
              aria-current={mine ? 'true' : undefined}
              className={`flex items-center gap-2 rounded px-1 py-0.5 ${mine ? 'bg-brand-50' : ''}`}
            >
              <span
                className={`w-11 shrink-0 text-xs ${
                  mine ? 'font-bold text-brand-700' : 'text-stone-500'
                }`}
              >
                {rowName(row)}줄
              </span>
              <span className="h-2.5 min-w-0 flex-1 overflow-hidden rounded-full bg-stone-100">
                <span
                  className="block h-full rounded-full bg-brand-600"
                  style={{ width: `${(count / most) * 100}%` }}
                />
              </span>
              <span className="w-10 shrink-0 text-right text-xs text-stone-500 tabular-nums">
                {count.toLocaleString('ko-KR')}
              </span>
            </li>
          )
        })}
      </ul>
      <p className="mt-3 text-xs text-stone-500">
        한 줄은 단계 {LEVEL_COLUMNS}칸을 묶은 것이에요.
        {myRow >= 0 && ` 내 자리인 ${rowName(myRow)}줄은 연한 초록으로 표시했어요.`}
      </p>
    </>
  )
}
