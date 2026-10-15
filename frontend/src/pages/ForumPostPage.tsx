import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router'
import { fetchComments, fetchPost } from '../api/forum.ts'
import AccountBar from '../components/AccountBar.tsx'
import CommentList from '../components/CommentList.tsx'
import Notice from '../components/Notice.tsx'
import { PostScore } from '../components/PostCard.tsx'
import { formatDate, formatTimeAgo } from '../lib/time.ts'

// 커뮤니티 글 하나 + 댓글 (F-17·D-91)
export default function ForumPostPage() {
  const { postId } = useParams()
  const id = Number(postId)
  const validId = Number.isInteger(id) && id > 0

  const postQuery = useQuery({
    queryKey: ['post', id],
    queryFn: ({ signal }) => fetchPost(id, signal),
    enabled: validId,
    // 삭제된 글은 다시 불러도 그대로라 재시도하지 않음
    retry: false,
  })
  const commentsQuery = useQuery({
    queryKey: ['comments', id],
    queryFn: ({ signal }) => fetchComments(id, signal),
    enabled: validId && postQuery.isSuccess,
  })
  const post = postQuery.data

  return (
    <main className="min-h-screen bg-paper px-4 py-6 sm:px-6">
      <div className="mx-auto max-w-3xl">
        <div className="flex items-center justify-between gap-3">
          <Link
            to={post ? `/stories/${post.story_id}/forum` : '/'}
            className="text-sm text-stone-500 hover:text-stone-800"
          >
            ← 커뮤니티
          </Link>
          <AccountBar />
        </div>

        {!validId || postQuery.isError ? (
          // 지워진 글이면 "삭제된 글입니다" (D-91)
          <div className="mt-6">
            <Notice message={postQuery.error?.message ?? '없는 글이에요'}>
              <Link to="/" className="underline">
                스토리 목록으로
              </Link>
            </Notice>
          </div>
        ) : postQuery.isPending ? (
          <div className="mt-6 h-64 animate-pulse rounded-lg bg-stone-200/70" />
        ) : (
          <>
            <article className="mt-4 rounded-lg bg-white p-5 shadow-paper ring-1 ring-stone-200/60 sm:p-7">
              <div className="flex gap-4">
                <PostScore up={post!.up_count} down={post!.down_count} />
                <div className="min-w-0 flex-1">
                  <h1 className="text-xl font-bold tracking-tight text-stone-900 sm:text-2xl">
                    {post!.pin_slot && (
                      <span className="mr-2 rounded-sm bg-brand-50 px-1.5 py-0.5 align-middle text-xs font-bold text-brand-700">
                        고정
                      </span>
                    )}
                    {post!.title}
                  </h1>
                  <p className="mt-2 flex flex-wrap items-center gap-1.5 text-[13px] text-stone-500">
                    <span className="font-medium text-stone-600">{post!.author_nickname}</span>
                    <span aria-hidden className="text-stone-300">
                      ·
                    </span>
                    <time dateTime={post!.created_at} title={formatDate(post!.created_at)}>
                      {formatTimeAgo(post!.created_at)}
                    </time>
                  </p>
                </div>
              </div>

              {post!.quoted_sentence && (
                // 인용한 문장을 누르면 그 문장으로 이동 (D-42)
                <Link
                  to={`/s/${post!.quoted_sentence.id}`}
                  className="mt-5 block border-l-2 border-brand-600 bg-brand-50/60 py-2 pl-4 font-serif text-sentence text-stone-700 hover:bg-brand-50"
                >
                  “{post!.quoted_sentence.content}”
                </Link>
              )}

              <p className="mt-5 font-serif text-sentence whitespace-pre-wrap text-stone-800">
                {post!.body}
              </p>
            </article>

            <section className="mt-6 rounded-lg bg-white p-5 shadow-paper ring-1 ring-stone-200/60 sm:p-7">
              <h2 className="text-sm font-semibold text-stone-600">
                댓글 <span className="tabular-nums">{post!.comment_count}</span>
              </h2>
              <div className="mt-2">
                {commentsQuery.isPending ? (
                  <div className="h-24 animate-pulse rounded-lg bg-stone-100" />
                ) : commentsQuery.isError ? (
                  <Notice message={commentsQuery.error.message} />
                ) : (
                  <CommentList items={commentsQuery.data.items} />
                )}
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  )
}
