import { useInfiniteQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { fetchMyScoreHistory, type ScoreEvent } from '../api/profile.ts'
import LoginButton from '../components/LoginButton.tsx'
import LogoutButton from '../components/LogoutButton.tsx'
import Notice from '../components/Notice.tsx'
import ProfileFrame, { Panel } from '../components/ProfileLayout.tsx'
import { formatDate, formatTimeAgo } from '../lib/time.ts'
import { useMe } from '../lib/useMe.ts'

// 점수 기록 (6-8) — 내 문장·받은 추천이 언제 몇 점이 되었는지
// 틀·더 보기·빈 화면은 "내 문장"(MySentencesPage)과 같은 모양
export default function ScoreHistoryPage() {
  const { data: me, isPending } = useMe()

  const list = useInfiniteQuery({
    queryKey: ['me', 'score-history'],
    queryFn: ({ pageParam, signal }) => fetchMyScoreHistory({ page: pageParam }, signal),
    initialPageParam: 1,
    // 받은 만큼이 전체보다 적으면 다음 쪽이 있음
    getNextPageParam: (last) => (last.page * last.size < last.total ? last.page + 1 : undefined),
    enabled: Boolean(me),
  })

  const top = (
    <>
      <Link
        to="/me"
        className="btn btn-nav"
      >
        마이페이지
      </Link>
      {me && <LogoutButton />}
    </>
  )

  if (isPending) {
    return (
      <ProfileFrame top={top}>
        <div className="h-64 animate-pulse rounded-lg bg-stone-200/70" />
      </ProfileFrame>
    )
  }

  if (!me) {
    return (
      <ProfileFrame top={top}>
        <Notice message="점수 기록은 로그인한 뒤에 볼 수 있어요.">
          <LoginButton small />
        </Notice>
      </ProfileFrame>
    )
  }

  const items = list.data?.pages.flatMap((page) => page.items) ?? []
  const total = list.data?.pages[0].total ?? 0

  return (
    <ProfileFrame top={top}>
      <header className="flex flex-wrap items-baseline justify-between gap-2">
        <h1 className="font-serif text-2xl font-semibold text-stone-900">점수 기록</h1>
        {list.isSuccess && <p className="text-sm text-stone-500">모두 {total}개</p>}
      </header>
      <p className="mt-1 text-sm text-stone-500">
        문장 하나를 쓰면 10점, 내 문장이 추천을 하나 받으면 1점이에요.
      </p>

      <div className="mt-4">
        {list.isPending ? (
          <div className="h-64 animate-pulse rounded-lg bg-stone-200/70" />
        ) : list.isError ? (
          <Notice message={list.error.message} />
        ) : items.length === 0 ? (
          <Notice message="아직 쌓인 점수가 없어요.">
            <Link
              to="/"
              className="btn btn-tag btn-primary"
            >
              이야기 둘러보기
            </Link>
          </Notice>
        ) : (
          <>
            <Panel>
              <ul className="-mx-2 divide-y divide-stone-100">
                {items.map((event) => (
                  // 같은 문장이 추천을 여러 번 받으므로 문장 번호만으로는 겹침
                  <ScoreRow key={`${event.kind}-${event.sentence_id}-${event.at}`} event={event} />
                ))}
              </ul>
            </Panel>
            {list.hasNextPage && (
              <button
                type="button"
                onClick={() => list.fetchNextPage()}
                disabled={list.isFetchingNextPage}
                className="mt-3 flex min-h-11 w-full items-center justify-center rounded-lg bg-brand-50 text-sm font-medium text-brand-700 ring-1 ring-brand-600/15 transition hover:bg-brand-100 disabled:opacity-60"
              >
                {list.isFetchingNextPage ? '불러오는 중…' : `더 보기 (${items.length} / ${total})`}
              </button>
            )}
          </>
        )}
      </div>
    </ProfileFrame>
  )
}

function ScoreRow({ event }: { event: ScoreEvent }) {
  // 지운 문장인지 신고 처리된 문장인지는 서버가 구분해 주지 않으므로 한 문구로
  const hidden = event.sentence_content === null

  return (
    <li className="px-2 py-3">
      <div className="flex items-baseline gap-2">
        <b className="shrink-0 text-sm font-semibold text-brand-700 tabular-nums">
          +{event.points}
        </b>
        {hidden ? (
          <p className="min-w-0 flex-1 text-sm text-stone-400">지워졌거나 신고 처리된 문장</p>
        ) : (
          <p className="min-w-0 flex-1 font-serif text-[15px] leading-relaxed text-stone-800">
            {event.sentence_content}
          </p>
        )}
      </div>

      <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 pl-7 text-xs text-stone-500">
        <span>{event.kind === 'sentence' ? '문장을 썼어요' : '추천을 받았어요'}</span>
        <span aria-hidden>·</span>
        {/* 스토리로 가는 길은 문장 주소뿐 — 가려진 문장은 갈 곳이 없어 글자만 둠 */}
        {hidden ? (
          <span className="max-w-[12rem] truncate">{event.story_title}</span>
        ) : (
          <Link
            to={`/s/${event.sentence_id}`}
            className="max-w-[12rem] truncate transition hover:text-brand-700 hover:underline"
          >
            {event.story_title}
          </Link>
        )}
        <span aria-hidden>·</span>
        <time dateTime={event.at} title={formatDate(event.at)}>
          {formatTimeAgo(event.at)}
        </time>
      </div>
    </li>
  )
}
