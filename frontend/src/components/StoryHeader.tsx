import { Link } from 'react-router'
import type { Story } from '../api/stories.ts'
import ShareButton from './ShareButton.tsx'

// 읽기 화면 맨 위: 스토리 제목 + 탭(커뮤니티는 4단계 자리) + 스토리 정보 칸
export default function StoryHeader({ title, story }: { title: string; story?: Story }) {
  return (
    <header>
      <Link to="/" className="text-sm text-stone-500 hover:text-stone-800">
        ← 목록
      </Link>
      <div className="mt-2 flex items-start justify-between gap-3">
        <h1 className="text-2xl font-bold text-stone-800 sm:text-3xl">{title}</h1>
        <ShareButton title={title} />
      </div>

      {/* 탭: 커뮤니티(스토리별 포럼, 4단계 F-17)는 자리만 */}
      <nav className="mt-4 flex gap-1 border-b border-stone-200">
        <span className="-mb-px border-b-2 border-brand-600 px-3 py-2 text-sm font-medium text-brand-700">
          읽기
        </span>
        <span className="px-3 py-2 text-sm text-stone-400" title="커뮤니티는 준비 중이에요">
          커뮤니티
        </span>
      </nav>

      <dl className="mt-3 flex flex-wrap gap-x-6 gap-y-2 rounded-2xl bg-white px-4 py-3 text-sm shadow-sm">
        <Item label="시작한 작가" value={story?.creator_nickname} />
        <Item label="작가" value={story && `${story.author_count}명`} />
        <Item label="최장" value={story && `${story.max_depth + 1}문장`} />
        <Item label="추천" value={story && `${story.recommend_count}`} />
      </dl>
    </header>
  )
}

function Item({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex items-baseline gap-1.5">
      <dt className="text-stone-500">{label}</dt>
      <dd className="font-medium text-stone-800">{value ?? '…'}</dd>
    </div>
  )
}
