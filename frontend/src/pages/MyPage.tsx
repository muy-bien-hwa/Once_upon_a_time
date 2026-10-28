import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { fetchMySentences, fetchMySummary } from '../api/profile.ts'
import DeleteAccount from '../components/DeleteAccount.tsx'
import LoginButton from '../components/LoginButton.tsx'
import LogoutButton from '../components/LogoutButton.tsx'
import Notice from '../components/Notice.tsx'
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
      <Frame>
        <div className="h-64 animate-pulse rounded-lg bg-stone-200/70" />
      </Frame>
    )
  }

  if (!me) {
    return (
      <Frame>
        <Notice message="마이페이지는 로그인한 뒤에 볼 수 있어요.">
          <LoginButton small />
        </Notice>
      </Frame>
    )
  }

  const total = summary.data?.sentence_count ?? 0

  return (
    <Frame
      top={
        <>
          <Link
            to="/"
            className="inline-flex min-h-11 items-center text-sm text-stone-500 transition hover:text-stone-800"
          >
            ‹ 홈
          </Link>
          <LogoutButton />
        </>
      }
    >
      <header>
        <h1 className="font-serif text-2xl font-semibold text-stone-900">
          {me.nickname ?? '이름 없는 작가'}
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

        <Panel title="내 문장" className="lg:col-start-2 lg:row-start-1 lg:row-span-3">
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
                className="mt-3 inline-flex min-h-11 items-center rounded-lg bg-brand-600 px-4 text-sm font-medium text-white transition hover:bg-brand-700"
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

        <Panel title="닉네임" className="lg:col-start-1 lg:row-start-2">
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

        <Panel title="계정 삭제" danger className="lg:col-start-1 lg:row-start-3">
          <DeleteAccount nickname={me.nickname} />
        </Panel>
      </div>
    </Frame>
  )
}

// 맨 위 줄(홈·로그아웃)과 바깥 여백 — 휴대폰 시계·손잡이 자리를 피해 위아래를 넉넉히 둠
function Frame({ children, top }: { children: ReactNode; top?: ReactNode }) {
  return (
    <main className="min-h-screen bg-paper px-4 pt-4 pb-20 sm:px-6">
      <div className="mx-auto max-w-4xl">
        <div className="flex min-h-11 items-center justify-between gap-3">{top}</div>
        <div className="mt-3">{children}</div>
      </div>
    </main>
  )
}

function Panel({
  title,
  children,
  danger = false,
  className = '',
}: {
  title?: string
  children: ReactNode
  danger?: boolean
  className?: string
}) {
  return (
    <section
      className={`flex flex-col rounded-lg bg-white p-4 shadow-paper ring-1 ${
        danger ? 'ring-down-600/25' : 'ring-stone-200/60'
      } ${className}`}
    >
      {title && (
        <h2 className={`mb-3 text-sm font-semibold ${danger ? 'text-down-600' : 'text-stone-700'}`}>
          {title}
        </h2>
      )}
      {children}
    </section>
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
