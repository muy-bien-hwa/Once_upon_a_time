import { Link } from 'react-router'
import type { Me } from '../api/auth.ts'
import LoginButton from './LoginButton.tsx'

// 로그인·닉네임이 없을 때 글쓰기 자리에 대신 띄우는 안내 (D-83)
// me가 undefined면 아직 확인 중, null이면 로그인 안 한 상태
export default function LoginNotice({
  me,
  what = '이어 쓰려면',
}: {
  me: Me | null | undefined
  // 무엇을 하려다 막혔는지 (예: '이어 쓰려면', '스토리를 열려면')
  what?: string
}) {
  if (me === undefined) return null

  return (
    <div className="mt-3 rounded-lg border border-dashed border-stone-300 p-5 text-center">
      {me === null ? (
        <>
          <p className="text-stone-600">{what} 로그인이 필요해요.</p>
          <div className="mt-3">
            <LoginButton small />
          </div>
        </>
      ) : (
        <>
          <p className="text-stone-600">닉네임을 먼저 정해 주세요.</p>
          <Link to="/nickname" className="mt-3 inline-block font-medium text-brand-700 underline">
            닉네임 정하기
          </Link>
        </>
      )}
    </div>
  )
}
