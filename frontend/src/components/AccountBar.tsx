import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router'
import { logout } from '../api/auth.ts'
import { useMe } from '../lib/useMe.ts'
import LoginButton from './LoginButton.tsx'

// 화면 오른쪽 위 로그인 상태 (F-06)
export default function AccountBar() {
  const { data: me, isPending } = useMe()
  const queryClient = useQueryClient()
  const signOut = useMutation({
    mutationFn: logout,
    // 로그아웃하면 받아 둔 내용을 모두 비움 (다른 사람 화면이 남지 않게)
    onSuccess: () => queryClient.clear(),
  })

  // 확인하는 동안에는 자리만 (버튼이 깜빡이지 않게)
  if (isPending) return <span className="h-9" />
  if (!me) return <LoginButton />

  return (
    <div className="flex items-center gap-3 text-sm">
      {me.nickname ? (
        <span className="font-medium text-stone-700">{me.nickname}</span>
      ) : (
        <Link to="/nickname" className="font-medium text-brand-700 underline">
          닉네임 정하기
        </Link>
      )}
      <button
        type="button"
        onClick={() => signOut.mutate()}
        disabled={signOut.isPending}
        className="text-stone-500 hover:text-stone-800 disabled:opacity-50"
      >
        로그아웃
      </button>
    </div>
  )
}
