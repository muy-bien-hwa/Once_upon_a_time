import { Link } from 'react-router'
import { CONTACT, LEGAL_PAGES } from '../content/legal.ts'

// 모든 화면 맨 아래 줄 — 약관·정책으로 가는 길 (D-94)
export default function Footer() {
  return (
    <footer className="bg-paper px-4 pt-6 pb-10 text-center text-xs text-stone-400 sm:px-6">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-3 gap-y-2">
        {LEGAL_PAGES.map((page) => (
          <Link key={page.path} to={page.path} className="transition hover:text-stone-700">
            {page.label}
          </Link>
        ))}
        <a href={`mailto:${CONTACT}`} className="transition hover:text-stone-700">
          {CONTACT}
        </a>
      </div>
      <p className="mt-2">옛날 옛적에</p>
    </footer>
  )
}
