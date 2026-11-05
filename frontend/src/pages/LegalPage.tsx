import { Link, useLocation } from 'react-router'
import {
  CONTACT,
  EFFECTIVE,
  LEGAL_PAGES,
  type LegalBlock,
  type LegalDoc,
} from '../content/legal.ts'
import { ChevronLeft } from '../components/icons.tsx'

// 이용약관·운영정책·개인정보 처리방침을 같은 틀로 보여 줌 (D-95)
// 본문은 content/ 안의 데이터이고, 여기서는 그리기만 함
export default function LegalPage({ doc }: { doc: LegalDoc }) {
  const here = useLocation().pathname

  return (
    <main className="min-h-screen bg-paper px-4 pt-4 pb-20 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <Link
          to="/"
          className="inline-flex min-h-11 items-center gap-1 text-sm text-stone-500 transition hover:text-stone-800"
        >
          <ChevronLeft className="h-4 w-4" /> 홈
        </Link>

        <header className="mt-2">
          <h1 className="font-serif text-2xl font-semibold text-stone-900">
            옛날 옛적에 {doc.title}
          </h1>
          <p className="mt-1 text-sm text-stone-500">시행일 {EFFECTIVE || '서비스 공개일'}</p>
        </header>

        <nav className="mt-4 flex flex-wrap gap-1.5">
          {LEGAL_PAGES.map((page) => (
            <Link
              key={page.path}
              to={page.path}
              aria-current={page.path === here ? 'page' : undefined}
              className={`inline-flex min-h-11 items-center rounded-full px-3.5 text-sm transition ${
                page.path === here
                  ? 'bg-brand-600 font-medium text-white'
                  : 'border border-stone-200 bg-white text-stone-600 hover:bg-stone-100'
              }`}
            >
              {page.label}
            </Link>
          ))}
        </nav>

        <article className="mt-5 rounded-lg bg-white px-5 py-6 text-[15px] leading-relaxed text-stone-700 shadow-paper ring-1 ring-stone-200/60 sm:px-7">
          {doc.intro && <p className="mb-6 text-stone-600">{doc.intro}</p>}

          {doc.chapters.map((chapter) => (
            <section key={chapter.name ?? 'first'}>
              {chapter.name && (
                <h2 className="mt-9 border-b border-stone-200 pb-2 font-serif text-lg font-bold text-brand-700 first:mt-0">
                  {chapter.name}
                </h2>
              )}
              {chapter.articles.map((item) => (
                <section key={item.title} className="mt-6">
                  <h3 className="font-serif font-bold text-stone-900">{item.title}</h3>
                  <div className="mt-1.5 flex flex-col gap-1.5">
                    {item.blocks.map((block, index) => (
                      <Block key={index} block={block} />
                    ))}
                  </div>
                </section>
              ))}
            </section>
          ))}

          <p className="mt-10 border-t border-stone-200 pt-5 text-sm text-stone-500">
            문의: <a href={`mailto:${CONTACT}`} className="text-brand-700 underline">{CONTACT}</a>
          </p>
        </article>
      </div>
    </main>
  )
}

function Block({ block }: { block: LegalBlock }) {
  if (typeof block === 'string') return <p>{block}</p>

  if ('sub' in block) {
    return (
      <div className="flex flex-col gap-1 pl-4 text-stone-600">
        {block.sub.map((line) => (
          <p key={line}>{line}</p>
        ))}
      </div>
    )
  }

  // 표는 좁은 화면에서 옆으로 밀어 볼 수 있게 (화면 전체가 흔들리지 않도록)
  return (
    <div className="my-1 overflow-x-auto">
      <table className="w-full min-w-[22rem] border-collapse text-sm">
        <thead>
          <tr>
            {block.head.map((cell) => (
              <th
                key={cell}
                className="border-b border-stone-200 px-2 py-1.5 text-left font-medium text-stone-500"
              >
                {cell}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {block.rows.map((row) => (
            <tr key={row.join('|')}>
              {row.map((cell) => (
                <td
                  key={cell}
                  className="border-b border-stone-100 px-2 py-1.5 align-top text-stone-600"
                >
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
