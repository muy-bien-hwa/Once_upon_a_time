import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { fetchChildren, fetchPath, type SentenceSort } from '../api/sentences.ts'
import { fetchStory } from '../api/stories.ts'
import Notice from '../components/Notice.tsx'
import SentenceChoices from '../components/SentenceChoices.tsx'
import SentencePath from '../components/SentencePath.tsx'
import StoryHeader from '../components/StoryHeader.tsx'

// ④ 골라 읽기 = 공유 주소 (/s/문장번호)
// 왼쪽 = 여기까지 온 길(#6) / 가운데 = 다음에 고를 문장들(#7)
// 문장을 고를 때마다 주소가 바뀜 → 뒤로 가기 = 한 문장 전, 지금 주소 = 공유 주소 (D-59·D-62)
export default function SentenceReadPage() {
  const { sentenceId } = useParams()
  const id = Number(sentenceId)
  const validId = Number.isInteger(id) && id > 0
  // 정렬은 주소에 넣지 않음 → 공유 주소는 깔끔하게, 문장을 옮겨 다니는 동안에는 유지
  const [sort, setSort] = useState<SentenceSort>('score')

  const pathQuery = useQuery({
    queryKey: ['path', id],
    queryFn: ({ signal }) => fetchPath(id, signal),
    enabled: validId,
  })
  // 제목 아래 정보 칸에 쓸 스토리 정보 (시작한 작가·작가 수·최장 문장 수·추천 수)
  const storyId = pathQuery.data?.story.id
  const storyQuery = useQuery({
    queryKey: ['story', storyId],
    queryFn: ({ signal }) => fetchStory(storyId!, signal),
    enabled: storyId !== undefined,
  })
  const childrenQuery = useQuery({
    queryKey: ['children', id, sort],
    queryFn: ({ signal }) => fetchChildren(id, sort, signal),
    enabled: validId && pathQuery.isSuccess,
    // 정렬을 바꾸는 동안 이전 목록을 그대로 보여줌
    placeholderData: keepPreviousData,
  })

  return (
    <main className="min-h-screen bg-stone-50 px-4 py-6 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <StoryHeader title={pathQuery.data?.story.title ?? ''} story={storyQuery.data} />

        <div className="mt-6">
          {!validId ? (
            <Notice message="없거나 사라진 문장이에요">
              <Link to="/" className="underline">
                스토리 목록으로
              </Link>
            </Notice>
          ) : pathQuery.isPending ? (
            <Skeleton />
          ) : pathQuery.isError ? (
            <Notice message={pathQuery.error.message}>
              <Link to="/" className="underline">
                스토리 목록으로
              </Link>
            </Notice>
          ) : (
            <div className="grid gap-6 md:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
              <section>
                <h2 className="mb-3 text-sm font-medium text-stone-500">
                  지금까지 이야기 ({pathQuery.data.items.length}문장)
                </h2>
                <SentencePath items={pathQuery.data.items} />
              </section>

              <section>
                {childrenQuery.isPending ? (
                  <Skeleton />
                ) : childrenQuery.isError ? (
                  <Notice message={childrenQuery.error.message}>
                    <button
                      type="button"
                      onClick={() => childrenQuery.refetch()}
                      className="underline"
                    >
                      다시 시도
                    </button>
                  </Notice>
                ) : (
                  <SentenceChoices
                    parent={pathQuery.data.items[pathQuery.data.items.length - 1]}
                    items={childrenQuery.data.items}
                    sort={sort}
                    onSortChange={setSort}
                    dim={childrenQuery.isPlaceholderData}
                  />
                )}
              </section>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}

function Skeleton() {
  return (
    <div className="space-y-3" aria-label="불러오는 중">
      {[0, 1, 2].map((i) => (
        <div key={i} className="h-20 animate-pulse rounded-2xl bg-stone-200/70" />
      ))}
    </div>
  )
}
