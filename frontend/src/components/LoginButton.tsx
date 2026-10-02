import { LOGIN_URL } from '../api/auth.ts'

// 구글 로그인으로 보내는 버튼 (서버가 구글 화면으로 넘겨줌)
// 화면 안에서 주소를 바꾸는 게 아니라 서버로 나가야 하므로 <a> 사용
export default function LoginButton({ small = false }: { small?: boolean }) {
  return (
    <a
      href={LOGIN_URL}
      className={
        small
          ? 'inline-block rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700'
          : 'inline-block rounded-full bg-brand-600 px-5 py-2.5 font-medium text-white hover:bg-brand-700'
      }
    >
      구글로 로그인
    </a>
  )
}
