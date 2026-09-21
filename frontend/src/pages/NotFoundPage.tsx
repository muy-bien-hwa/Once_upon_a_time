import { Link } from 'react-router'

export default function NotFoundPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-stone-50">
      <p className="text-stone-500">없는 페이지예요.</p>
      <Link to="/" className="text-stone-800 underline">
        처음으로
      </Link>
    </main>
  )
}
