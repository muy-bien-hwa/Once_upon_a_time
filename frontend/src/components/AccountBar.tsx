import { Link } from 'react-router'
import { useMe } from '../lib/useMe.ts'
import LoginButton from './LoginButton.tsx'
import LogoutButton from './LogoutButton.tsx'

// 화면 오른쪽 위 로그인 상태 (F-06) — 닉네임을 누르면 마이페이지 (D-95)
export default function AccountBar() {
  const { data: me, isPending } = useMe()

  // 확인하는 동안에는 자리만 (버튼이 깜빡이지 않게)
  if (isPending) return <span className="h-11" />
  if (!me) return <LoginButton />

  return (
    <div className="flex items-center gap-2">
      <Link
        to={me.nickname ? '/me' : '/nickname'}
        className={`inline-flex min-h-11 items-center rounded-lg px-2 font-medium transition hover:text-brand-700 ${
          me.nickname ? 'text-stone-700' : 'text-brand-700 underline'
        }`}
      >
        {me.nickname ?? '닉네임 정하기'}
      </Link>
      <LogoutButton />
    </div>
  )
}
