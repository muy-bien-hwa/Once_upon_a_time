import { useState } from 'react'
import { Link } from 'react-router'
import AuthorDialog from './AuthorDialog.tsx'

// 작성자 이름 → 그 작가의 작은 정보 창 (6-9, D-95)
// - 탈퇴한 작가는 갈 곳이 없으므로 누를 수 없음 (이름 글자가 아니라 서버가 보낸 값으로 판단)
// - 이름표는 작가 화면 주소를 단 진짜 링크로 둠: 새 탭으로 열 수 있고, 읽어 주는 기기에도 링크로 들림
// - 그냥 왼쪽 클릭만 가로채서 창을 띄우고, 새 탭·새 창으로 열려는 누름은 브라우저에 맡김
// - 내 이름도 남의 이름과 똑같이 창이 뜸 (마이페이지로는 창 안의 버튼으로 감)
export default function AuthorLink({
  nickname,
  withdrawn,
  className = '',
}: {
  nickname: string | null
  withdrawn: boolean
  className?: string
}) {
  const [open, setOpen] = useState(false)

  // 접힌 글·삭제된 문장은 작성자를 보내지 않음
  if (nickname === null) return null
  if (withdrawn) return <span className={className}>{nickname}</span>

  return (
    <>
      <Link
        to={`/u/${encodeURIComponent(nickname)}`}
        aria-haspopup="dialog"
        onClick={(event) => {
          // 문장 박스처럼 바깥이 통째로 링크인 곳이 있어 그 위로 올림
          event.stopPropagation()
          // 가운데 단추·ctrl/⌘·shift·alt 누름은 "새 탭에서 열기" 같은 뜻이라 그대로 둠
          if (event.button !== 0) return
          if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
          event.preventDefault()
          setOpen(true)
        }}
        className={`relative z-10 transition hover:text-brand-700 hover:underline ${className}`}
      >
        {nickname}
      </Link>
      {/* 창은 열렸을 때만 만들어짐. 떠 있는 동안에는 뒤가 잠겨 다른 이름을 누를 수 없어 한 번에 하나만 뜸 */}
      {open && <AuthorDialog nickname={nickname} onClose={() => setOpen(false)} />}
    </>
  )
}
