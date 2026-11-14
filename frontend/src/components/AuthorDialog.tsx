import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { Link } from 'react-router'
import { ApiError } from '../api/client.ts'
import { fetchAuthor } from '../api/profile.ts'
import { useMe } from '../lib/useMe.ts'
import LevelBadge from './LevelBadge.tsx'

type Props = { nickname: string; onClose: () => void }

// 작가 이름을 누르면 지금 화면 위에 뜨는 작은 작가 정보 창 (6-9)
// 읽던 이야기·글에서 밀려나지 않게, 작가 화면으로 넘어가기 전에 여기서 먼저 보여 줌
// 열렸을 때만 그려짐 — 이름이 수십 개인 목록에서도 <dialog>는 하나만 생기고, 열기 전에는 서버에 묻지 않음
export default function AuthorDialog({ nickname, onClose }: Props) {
  const dialog = useRef<HTMLDialogElement>(null)
  const { data: me } = useMe()

  // 작가 화면과 같은 열쇠 → 창을 봤다가 작가 화면으로 들어가도 같은 것을 두 번 받아오지 않음
  const author = useQuery({
    queryKey: ['author', nickname],
    queryFn: ({ signal }) => fetchAuthor(nickname, signal),
    // 없는 닉네임은 다시 물어도 없음
    retry: false,
  })

  useEffect(() => {
    const element = dialog.current
    if (!element) return
    element.showModal()
    // 닫을 때 React가 이 <dialog>를 지움 — 지우기 전에 닫아야 뒤 화면이 잠긴 채로 남지 않음
    return () => element.close()
  }, [])

  // 닉네임은 중복이 없으므로(D-84) 이름이 같으면 나 → 작가 화면 대신 마이페이지로
  const mine = me?.nickname != null && me.nickname === nickname
  // 없는 닉네임도 탈퇴한 작가도 똑같이 404 (탈퇴 사실을 알려 주지 않음, D-95)
  const gone = author.error instanceof ApiError && author.error.status === 404

  return (
    <dialog
      ref={dialog}
      // 이 창이 문장 박스처럼 바깥이 통째로 링크인 곳 안에서 열릴 수 있어, 클릭이 바깥으로 새지 않게 막음
      // 브라우저가 링크를 따라가는 기본 동작까지 막아야 해서 둘 다 호출 (ConfirmDialog와 같은 이유)
      onClick={(event) => {
        event.preventDefault()
        event.stopPropagation()
      }}
      // Esc 키 = 닫기
      onCancel={(event) => {
        event.preventDefault()
        onClose()
      }}
      className="m-auto w-[min(24rem,90vw)] rounded-lg bg-white p-6 shadow-xl backdrop:bg-stone-900/40"
    >
      <div className="flex items-start gap-2">
        <h2 className="min-w-0 flex-1 text-lg font-semibold text-stone-800">
          {/* 아직 못 받아온 동안에는 눌렀던 이름을 그대로 보여 줌 (창이 빈 채로 뜨지 않게) */}
          {author.isSuccess ? author.data.nickname : nickname}
          {author.isSuccess && (
            <LevelBadge
              name={author.data.level_name}
              label={author.data.level_label}
              className="ml-2"
            />
          )}
        </h2>
        <button
          type="button"
          onClick={onClose}
          className="btn btn-tag btn-sm"
        >
          닫기
        </button>
      </div>

      {author.isPending ? (
        <div className="mt-4 h-24 animate-pulse rounded-lg bg-stone-100" />
      ) : author.isError ? (
        // 없는 작가는 고장이 아니라 그냥 없는 것 → 빨간 글씨는 진짜 실패에만
        <p className={`py-6 text-center text-sm ${gone ? 'text-stone-500' : 'text-red-500'}`}>
          {gone ? '없는 작가예요.' : author.error.message}
        </p>
      ) : (
        <>
          <p className="mt-1 text-[13px] text-stone-500">
            {author.data.level_label} · {joinedText(author.data.joined_month)}
          </p>

          <div className="mt-4 grid grid-cols-3 gap-2 border-t border-stone-100 pt-4 text-center">
            <Count label="쓴 문장" value={author.data.sentence_count} />
            <Count label="참여한 이야기" value={author.data.story_count} />
            <Count label="받은 추천" value={author.data.received_up_count} />
          </div>

          <div className="mt-5 flex justify-end">
            <Link
              to={mine ? '/me' : `/u/${encodeURIComponent(nickname)}`}
              className="btn btn-tag btn-primary"
            >
              {mine ? '마이페이지' : '작가 화면'}
            </Link>
          </div>
        </>
      )}
    </dialog>
  )
}

// "2026-05" → "2026년 5월부터" (날짜까지는 공개하지 않음, D-95)
function joinedText(joinedMonth: string) {
  const [year, month] = joinedMonth.split('-')
  return `${year}년 ${Number(month)}월부터`
}

function Count({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <b className="block text-lg font-semibold text-brand-700 tabular-nums">
        {value.toLocaleString('ko-KR')}
      </b>
      <span className="text-xs text-stone-500">{label}</span>
    </div>
  )
}
