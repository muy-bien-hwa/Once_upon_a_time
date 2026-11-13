// 작가 이름 옆에 붙는 단계 배지 (6-8)
// 이름을 홑낫표로 묶음 — 「개」처럼 그대로 두면 낱말이나 오타로 보이는 글자가 많아서
// ※ 이야기 문장 옆에는 붙이지 않음: 읽기 화면·문장 목록은 이야기만 보이게 둠
export default function LevelBadge({
  name,
  label,
  className = '',
}: {
  // 0단계면 null로 와서 아무것도 그리지 않음
  name: string | null | undefined
  // 서버가 만들어 보낸 문구 ("「개」 단계")
  label?: string
  className?: string
}) {
  if (!name) return null

  // 처음 본 사람도 뜻과 갈 곳을 알 수 있게
  const full = `${label ?? `「${name}」 단계`} · 작가 단계는 /levels 에서 볼 수 있어요`

  return (
    <span
      title={full}
      aria-label={full}
      className={`inline-block rounded-sm bg-brand-50 px-1.5 py-0.5 align-middle text-[11px] font-bold text-brand-700 ${className}`}
    >
      「{name}」
    </span>
  )
}
