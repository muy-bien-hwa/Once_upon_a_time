import { useMutation, useQueryClient } from '@tanstack/react-query'
import { logout } from '../api/auth.ts'

// 로그아웃 버튼 (오른쪽 위 줄·마이페이지에서 같이 씀)
export default function LogoutButton() {
  const queryClient = useQueryClient()
  const signOut = useMutation({
    mutationFn: logout,
    // 받아 둔 내용을 모두 비우고 지금 보고 있는 것만 손님으로 다시 받아 옴
    // ⚠️ clear()만 하면 안 됨 — 캐시에서 지워도 이미 화면에 붙어 있는 화면은
    //    다시 그려지지 않아서, 새로고침할 때까지 로그인한 모습이 그대로 남는다
    onSuccess: () => {
      queryClient.resetQueries()
    },
  })

  return (
    <button
      type="button"
      onClick={() => signOut.mutate()}
      disabled={signOut.isPending}
      className="btn btn-tag btn-sm"
    >
      로그아웃
    </button>
  )
}
