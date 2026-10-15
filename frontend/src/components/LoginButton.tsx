import { useState } from 'react'
import { LOGIN_URL } from '../api/auth.ts'
import { detectInAppBrowser } from '../lib/inAppBrowser.ts'
import InAppBrowserDialog from './InAppBrowserDialog.tsx'

// 구글 로그인으로 보내는 버튼 (서버가 구글 화면으로 넘겨줌)
// 화면 안에서 주소를 바꾸는 게 아니라 서버로 나가야 하므로 <a> 사용
export default function LoginButton({ small = false }: { small?: boolean }) {
  // 카카오톡 등 앱 안의 브라우저에서는 구글이 로그인을 막음 → 보내지 말고 안내 (F-24)
  const [app] = useState(() => detectInAppBrowser())
  const [notice, setNotice] = useState(false)

  const style = small
    ? 'inline-block rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700'
    : 'inline-block rounded-full bg-brand-600 px-5 py-2.5 font-medium text-white hover:bg-brand-700'

  if (app) {
    return (
      <>
        <button type="button" onClick={() => setNotice(true)} className={style}>
          구글로 로그인
        </button>
        <InAppBrowserDialog app={app} open={notice} onClose={() => setNotice(false)} />
      </>
    )
  }

  return (
    <a href={LOGIN_URL} className={style}>
      구글로 로그인
    </a>
  )
}
