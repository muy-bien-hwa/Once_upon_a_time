import { useQuery } from '@tanstack/react-query'
import { fetchMe } from '../api/auth.ts'

// 로그인한 사람 정보. data가 null이면 로그인 안 한 상태
export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: ({ signal }) => fetchMe(signal),
    staleTime: 60 * 1000,
  })
}
