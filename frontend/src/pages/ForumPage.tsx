import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router'
import { fetchPosts, type PostSort } from '../api/forum.ts'
import { fetchStory } from '../api/stories.ts'
import Notice from '../components/Notice.tsx'
import Pagination from '../components/Pagination.tsx'
import PostCard from '../components/PostCard.tsx'
import StoryHeader from '../components/StoryHeader.tsx'

const SORTS: { value: PostSort; label: string }[] = [
  { value: 'new', label: '최신' },
  { value: 'hot', label: 'Hot' },
]
const SIZE = 20

// 스토리별 커뮤니티 글 목록 (F-17·D-91)
// 주소에 정렬·페이지를 담아 공유·뒤로 가기가 그대로 되게 함
export default function ForumPage() {
  const { storyId } = useParams()
  const id = Number(storyId)
  const validId = Number.isInteger(id) && id > 0
  const [searchParams, setSearchParams] = useSearchParams()
  const sort: PostSort = searchParams.get('sort') === 'hot' ? 'hot' : 'new'
  const page = Math.max(Number(searchParams.get('page')) || 1, 1)

  const storyQuery = useQuery({
    queryKey: ['story', id],
    queryFn: ({ signal }) => fetchStory(id, signal),
    enabled: validId,
  })
  const postsQuery = useQuery({
    queryKey: ['posts', id, sort, page],
    queryFn: ({ signal }) => fetchPosts(id, sort, page, signal),
    enabled: validId,
    // 정렬·페이지를 바꾸는 동안 이전 목록을 그대로 (깜빡임 방지)
    placeholderData: keepPreviousData,
  })

  function change(changes: { sort?: PostSort; page?: number }) {
    const next = { sort, page, ...changes }
    const params = new URLSearchParams()
    if (next.sort !== 'new') params.set('sort', next.sort)
    if (next.page !== 1) params.set('page', String(next.page))
    setSearchParams(params)
    window.scrollTo({ top: 0 })
  }

  return (
    <main className="min-h-screen bg-paper px-4 py-6 sm:px-6">
      <div className="mx-auto max-w-4xl">
        <StoryHeader title={storyQuery.data?.title ?? ''} story={storyQuery.data} tab="forum" />

        <div className="mt-5 flex flex-wrap items-center gap-2">
          <div className="flex gap-1">
            {SORTS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => change({ sort: option.value, page: 1 })}
                aria-current={sort === option.value}
                className={`rounded-lg px-3 py-1.5 text-sm transition ${
                  sort === option.value
                    ? 'bg-brand-600 font-medium text-white'
                    : 'text-stone-600 hover:bg-stone-200'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>

          <Link
            to={`/stories/${id}/forum/new`}
            className="ml-auto rounded-full bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"
          >
            글쓰기
          </Link>
        </div>

        <div className="mt-4">
          {!validId ? (
            <Notice message="없는 스토리예요">
              <Link to="/" className="underline">
                스토리 목록으로
              </Link>
            </Notice>
          ) : postsQuery.isPending ? (
            <div className="space-y-3">
              {[0, 1, 2].map((key) => (
                <div key={key} className="h-24 animate-pulse rounded-lg bg-stone-200/70" />
              ))}
            </div>
          ) : postsQuery.isError ? (
            <Notice message={postsQuery.error.message}>
              <Link to="/" className="underline">
                스토리 목록으로
              </Link>
            </Notice>
          ) : postsQuery.data.items.length === 0 ? (
            <Notice message="아직 글이 없어요. 이 스토리의 첫 글을 남겨 보세요.">
              <Link to={`/stories/${id}/forum/new`} className="underline">
                글쓰기
              </Link>
            </Notice>
          ) : (
            <>
              <ul className={`space-y-3 ${postsQuery.isPlaceholderData ? 'opacity-70' : ''}`}>
                {postsQuery.data.items.map((post) => (
                  <li key={post.id}>
                    <PostCard post={post} />
                  </li>
                ))}
              </ul>
              <Pagination
                page={page}
                totalPages={Math.ceil(postsQuery.data.total / SIZE)}
                onChange={(next) => change({ page: next })}
              />
            </>
          )}
        </div>
      </div>
    </main>
  )
}
