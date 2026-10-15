// 주소 복사. 요즘 방식(clipboard)이 막혀 있으면 예전 방식으로 한 번 더 시도
// (앱 안의 작은 브라우저나 권한이 막힌 환경 대비)
export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return copyByTextarea(text)
  }
}

// 화면 밖에 입력칸을 잠깐 만들어 복사 (오래된 방식이지만 대부분의 브라우저에서 동작)
function copyByTextarea(text: string) {
  const area = document.createElement('textarea')
  area.value = text
  area.readOnly = true
  area.style.position = 'fixed'
  area.style.opacity = '0'
  document.body.append(area)
  area.select()
  const copied = document.execCommand('copy')
  area.remove()
  return copied
}
