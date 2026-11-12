import { useMutation, useQueryClient } from '@tanstack/react-query'
import { logout } from '../api/auth.ts'

// 로그아웃 버튼 (오른쪽 위 줄·마이페이지에서 같이 씀)
export default function LogoutButton() {
  const queryClient = useQueryClient()
  const signOut = useMutation({
    mutationFn: logout,
    // 로그아웃하면 받아 둔 내용을 모두 비움 (다른 사람 화면이 남지 않게)
    onSuccess: () => queryClient.clear(),
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
