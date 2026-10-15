// 앱 안에 들어 있는 작은 브라우저(인앱 브라우저) 알아내기 (F-24·D-45)
// 여기서는 구글이 로그인을 막기 때문에, 로그인 버튼을 누르기 전에 밖에서 열라고 안내해야 함

// 브라우저가 스스로 밝히는 이름(User-Agent)에 앱 이름이 들어 있음
const APPS: { name: string; mark: RegExp }[] = [
  { name: '카카오톡', mark: /KAKAOTALK/i },
  { name: '네이버 앱', mark: /NAVER\(inapp/i },
  { name: '인스타그램', mark: /Instagram/i },
  { name: '페이스북', mark: /FBAN|FBAV/i },
  { name: '라인', mark: /\bLine\// },
  { name: '다음', mark: /DaumApps/i },
]

export function detectInAppBrowser(userAgent: string = navigator.userAgent): string | null {
  return APPS.find((app) => app.mark.test(userAgent))?.name ?? null
}

export function isAndroid(userAgent: string = navigator.userAgent): boolean {
  return /Android/i.test(userAgent)
}

// 안드로이드는 크롬으로 바로 여는 주소를 만들 수 있음 (아이폰은 방법이 없어 글 안내만)
export function chromeIntentUrl(url: string = window.location.href): string {
  return `intent://${url.replace(/^https?:\/\//, '')}#Intent;scheme=https;package=com.android.chrome;end`
}
