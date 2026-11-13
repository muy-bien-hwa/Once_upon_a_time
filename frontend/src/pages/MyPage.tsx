import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { fetchMySentences, fetchMySummary, type MeSummary } from '../api/profile.ts'
import DeleteAccount from '../components/DeleteAccount.tsx'
import LevelBadge from '../components/LevelBadge.tsx'
import LoginButton from '../components/LoginButton.tsx'
import LogoutButton from '../components/LogoutButton.tsx'
import Notice from '../components/Notice.tsx'
import ProfileFrame, { Panel } from '../components/ProfileLayout.tsx'
import SentenceRow from '../components/SentenceRow.tsx'
import { daysSince, formatDate } from '../lib/time.ts'
import { useMe } from '../lib/useMe.ts'

// 마이페이지에 미리 보여 줄 문장 수 (나머지는 "모두 보기"로, D-95)
const PREVIEW = 3

export default function MyPage() {
  const { data: me, isPending } = useMe()

  const summary = useQuery({
    queryKey: ['me', 'summary'],
    queryFn: ({ signal }) => fetchMySummary(signal),
    enabled: Boolean(me),
  })
  const sentences = useQuery({
    queryKey: ['me', 'sentences', 'preview'],
    queryFn: ({ signal }) => fetchMySentences({ size: PREVIEW }, signal),
    enabled: Boolean(me),
  })

  if (isPending) {
    return (
      <ProfileFrame width="max-w-4xl">
        <div className="h-64 animate-pulse rounded-lg bg-stone-200/70" />
      </ProfileFrame>
    )
  }

  if (!me) {
    return (
      <ProfileFrame width="max-w-4xl">
        <Notice message="마이페이지는 로그인한 뒤에 볼 수 있어요.">
          <LoginButton small />
        </Notice>
      </ProfileFrame>
    )
  }

  const total = summary.data?.sentence_count ?? 0

  return (
    <ProfileFrame
      width="max-w-4xl"
      top={
        <>
          <Link
            to="/"
            className="btn btn-nav"
          >
            홈
          </Link>
          <LogoutButton />
        </>
      }
    >
      <header>
        <h1 className="font-serif text-2xl font-semibold text-stone-900">
          {me.nickname ?? '이름 없는 작가'}
          <LevelBadge
            name={summary.data?.level_name}
            label={summary.data?.level_label}
            className="ml-2"
          />
        </h1>
        <p className="mt-1 text-sm text-stone-500">
          {summary.data
            ? `${formatDate(summary.data.joined_at)}부터 · ${daysSince(summary.data.joined_at)}일째`
            : ' '}
        </p>
      </header>

      <div className="mt-5 grid gap-4 lg:grid-cols-[17rem_minmax(0,1fr)] lg:items-start">
        <Panel className="lg:col-start-1 lg:row-start-1">
          <div className="grid grid-cols-3 gap-2 text-center">
            <Count label="쓴 문장" value={summary.data?.sentence_count} />
            <Count label="참여한 이야기" value={summary.data?.story_count} />
            <Count label="받은 추천" value={summary.data?.received_up_count} />
          </div>
        </Panel>

        <Panel title="내 단계" className="lg:col-start-1 lg:row-start-2">
          {summary.isPending ? (
            <div className="h-20 animate-pulse rounded-lg bg-stone-100" />
          ) : summary.isError ? (
            <p className="text-sm text-stone-500">{summary.error.message}</p>
          ) : (
            <LevelBox summary={summary.data} />
          )}
          <div className="mt-3 flex flex-wrap gap-1.5">
            <Link
              to="/me/score"
              className="btn btn-tag btn-sm"
            >
              점수 기록
            </Link>
            <Link
              to="/levels"
              className="btn btn-tag btn-sm"
            >
              단계 보기
            </Link>
          </div>
        </Panel>

        <Panel title="내 문장" className="lg:col-start-2 lg:row-start-1 lg:row-span-4">
          {sentences.isPending ? (
            <div className="h-40 animate-pulse rounded-lg bg-stone-100" />
          ) : sentences.isError ? (
            <p className="py-6 text-center text-sm text-stone-500">
              {sentences.error.message}
            </p>
          ) : sentences.data.items.length === 0 ? (
            <div className="py-6 text-center">
              <p className="text-sm text-stone-500">아직 쓴 문장이 없어요.</p>
              <Link
                to="/"
                className="btn btn-tag btn-primary mt-3"
              >
                이야기 둘러보기
              </Link>
            </div>
          ) : (
            <>
              <ul className="-mx-2 divide-y divide-stone-100">
                {sentences.data.items.map((sentence) => (
                  <SentenceRow key={sentence.id} sentence={sentence} />
                ))}
              </ul>
              <Link
                to="/me/sentences"
                className="mt-3 flex min-h-11 items-center justify-center rounded-lg bg-brand-50 text-sm font-medium text-brand-700 ring-1 ring-brand-600/15 transition hover:bg-brand-100"
              >
                내 문장 {total}개 모두 보기
              </Link>
            </>
          )}
        </Panel>

        <Panel title="닉네임" className="lg:col-start-1 lg:row-start-3">
          <p className="text-sm text-stone-600">
            {me.nickname ?? '아직 정하지 않았어요'}
            {me.nickname_editable_at && (
              <span className="text-stone-500">
                {' · '}
                {formatDate(me.nickname_editable_at)}부터 바꿀 수 있어요
              </span>
            )}
          </p>
          <Link
            to="/nickname"
            className="mt-3 inline-flex min-h-11 items-center self-start rounded-lg border border-stone-200 px-3 text-sm text-stone-700 transition hover:bg-stone-100"
          >
            {me.nickname ? '바꾸기' : '정하기'}
          </Link>
        </Panel>

        <Panel title="계정 삭제" danger className="lg:col-start-1 lg:row-start-4">
          <DeleteAccount nickname={me.nickname} />
        </Panel>
      </div>
    </ProfileFrame>
  )
}

// 단계 칸 (6-8) — 지금 단계 · 점수 · 다음 단계까지
function LevelBox({ summary }: { summary: MeSummary }) {
  // next_score가 null이면 더 오를 단계가 없음
  const next = summary.next_score
  const remain = next === null ? 0 : Math.max(next - summary.score, 0)
  // 막대는 **이번 단계 안에서** 얼마나 왔는지 (0점부터가 아니라 이 단계가 시작된 점수부터)
  // 0점부터 재면 막 올라온 사람도 거의 꽉 찬 것처럼 보임 — 46단계 770점이 99%가 되어 버림
  const span = next === null ? 0 : next - summary.level_score
  const filled =
    next === null ? 100 : span > 0 ? Math.min(((summary.score - summary.level_score) / span) * 100, 100) : 0

  return (
    <>
      <p className="font-serif text-lg font-semibold text-stone-900">{summary.level_label}</p>
      <div className="mt-2 flex items-baseline justify-between gap-2 text-xs text-stone-500">
        <span className="tabular-nums">
          <b className="text-sm font-semibold text-brand-700">
            {summary.score.toLocaleString('ko-KR')}
          </b>
          점
        </span>
        <span className="tabular-nums">
          {next === null ? '맨 위 단계예요' : `다음 단계까지 ${remain.toLocaleString('ko-KR')}점`}
        </span>
      </div>
      <span
        aria-hidden
        className="mt-1 block h-1.5 overflow-hidden rounded-full bg-stone-200"
      >
        <span
          className="block h-full rounded-full bg-brand-600"
          style={{ width: `${filled}%` }}
        />
      </span>
    </>
  )
}

function Count({ label, value }: { label: string; value?: number }) {
  return (
    <div>
      <b className="block text-xl font-semibold text-brand-700 tabular-nums">
        {value === undefined ? '–' : value.toLocaleString('ko-KR')}
      </b>
      <span className="text-xs text-stone-500">{label}</span>
    </div>
  )
}
