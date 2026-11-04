import { Link } from 'react-router'
import { useMe } from '../lib/useMe.ts'

// 작성자 이름 → 그 작가의 화면 (D-95)
// - 탈퇴한 작가는 갈 곳이 없으므로 누를 수 없음 (이름 글자가 아니라 서버가 보낸 값으로 판단)
// - 내 이름을 누르면 작가 화면 대신 마이페이지로
export default function AuthorLink({
  nickname,
  withdrawn,
  className = '',
}: {
  nickname: string | null
  withdrawn: boolean
  className?: string
}) {
  const { data: me } = useMe()

  // 접힌 글·삭제된 문장은 작성자를 보내지 않음
  if (nickname === null) return null
  if (withdrawn) return <span className={className}>{nickname}</span>

  return (
    <Link
      to={me?.nickname === nickname ? '/me' : `/u/${encodeURIComponent(nickname)}`}
      // 문장 박스처럼 바깥이 통째로 링크인 곳이 있어 그 위로 올림
      onClick={(event) => event.stopPropagation()}
      className={`relative z-10 transition hover:text-brand-700 hover:underline ${className}`}
    >
      {nickname}
    </Link>
  )
}
