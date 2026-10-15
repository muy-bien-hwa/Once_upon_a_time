import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'
import { createPost } from '../api/forum.ts'
import { fetchPath } from '../api/sentences.ts'
import { fetchStory } from '../api/stories.ts'
import ConfirmDialog from '../components/ConfirmDialog.tsx'
import LoginNotice from '../components/LoginNotice.tsx'
import { useMe } from '../lib/useMe.ts'

const TITLE_MAX = 100
const BODY_MAX = 5000

// 커뮤니티 글쓰기 (F-17·D-91)
// 읽기 화면에서 [이 문장으로 글쓰기]로 오면 ?quote=문장번호가 붙어 인용이 채워짐
export default function NewPostPage() {
  const { storyId } = useParams()
  const id = Number(storyId)
  const [searchParams] = useSearchParams()
  const quoteId = Number(searchParams.get('quote')) || undefined

  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [confirming, setConfirming] = useState(false)
  const { data: me } = useMe()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const storyQuery = useQuery({
    queryKey: ['story', id],
    queryFn: ({ signal }) => fetchStory(id, signal),
    enabled: Number.isInteger(id) && id > 0,
  })
  // 인용할 문장의 내용 (경로 조회의 마지막 문장이 그 문장)
  const quoteQuery = useQuery({
    queryKey: ['path', quoteId],
    queryFn: ({ signal }) => fetchPath(quoteId!, signal),
    enabled: quoteId !== undefined,
  })
  const quote = quoteQuery.data?.items.at(-1)

  const write = useMutation({
    mutationFn: () =>
      createPost(id, {
        title: title.trim(),
        body: body.trim(),
        ...(quoteId ? { quoted_sentence_id: quoteId } : {}),
      }),
    onSuccess: (post) => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      queryClient.invalidateQueries({ queryKey: ['story', id] })
      navigate(`/forum/posts/${post.id}`, { replace: true })
    },
    onError: () => setConfirming(false),
  })

  const titleLength = [...title.trim()].length
  const bodyLength = [...body.trim()].length
  const canSubmit =
    titleLength > 0 &&
    titleLength <= TITLE_MAX &&
    bodyLength > 0 &&
    bodyLength <= BODY_MAX &&
    !write.isPending

  return (
    <main className="min-h-screen bg-paper px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-2xl">
        <Link to={`/stories/${id}/forum`} className="text-sm text-stone-500 hover:text-stone-800">
          ← 커뮤니티
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-stone-800">글쓰기</h1>
        <p className="mt-1 text-sm text-stone-500">
          {storyQuery.data?.title ?? '…'} 커뮤니티에 올라갑니다. 글은 나중에 고칠 수 없어요.
        </p>

        {!me || !me.nickname ? (
          <LoginNotice me={me} what="글을 쓰려면" />
        ) : (
          <form
            className="mt-6 rounded-lg bg-white p-5 shadow-paper ring-1 ring-stone-200/60"
            onSubmit={(event) => {
              event.preventDefault()
              if (canSubmit) setConfirming(true)
            }}
          >
            {quote && (
              <p className="mb-5 border-l-2 border-brand-600 bg-brand-50/60 py-2 pl-4 font-serif text-[15px] text-stone-700">
                “{quote.content}”
                <span className="mt-1 block text-[13px] text-stone-500">
                  이 문장을 인용해서 씁니다
                </span>
              </p>
            )}

            <Field label="제목" length={[...title].length} max={TITLE_MAX}>
              <input
                type="text"
                autoFocus
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="예) 고양이 장면이 제일 좋았어요"
                className="w-full text-lg text-stone-800 outline-none placeholder:text-stone-300"
              />
            </Field>

            <div className="mt-5">
              <Field label="내용" length={[...body].length} max={BODY_MAX}>
                <textarea
                  value={body}
                  onChange={(event) => setBody(event.target.value)}
                  rows={10}
                  placeholder="어떤 점이 좋았는지, 다음 이야기를 어떻게 이어 가면 좋을지 자유롭게 써 주세요."
                  className="w-full resize-y text-[15px] leading-relaxed text-stone-800 outline-none placeholder:text-stone-300"
                />
              </Field>
            </div>

            {write.isError && <p className="mt-4 text-sm text-red-500">{write.error.message}</p>}

            <div className="mt-6 flex justify-end gap-2">
              <Link
                to={`/stories/${id}/forum`}
                className="rounded-lg px-3 py-2 text-sm text-stone-600 hover:bg-stone-100"
              >
                취소
              </Link>
              <button
                type="submit"
                disabled={!canSubmit}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-40"
              >
                올리기
              </button>
            </div>
          </form>
        )}

        <ConfirmDialog
          open={confirming}
          title="이 글을 올릴까요?"
          confirmLabel="네"
          cancelLabel="아니요"
          busyLabel="올리는 중…"
          busy={write.isPending}
          onConfirm={() => write.mutate()}
          onCancel={() => setConfirming(false)}
        >
          <p className="font-medium text-stone-800">{title.trim()}</p>
          <p className="mt-2 text-stone-500">올린 글은 고칠 수 없어요 (지우는 것은 됩니다).</p>
        </ConfirmDialog>
      </div>
    </main>
  )
}

function Field({
  label,
  length,
  max,
  children,
}: {
  label: string
  length: number
  max: number
  children: ReactNode
}) {
  return (
    <label className="block">
      <span className="flex items-center gap-2 text-sm text-stone-500">
        {label}
        <span className={`ml-auto ${length > max ? 'text-red-500' : 'text-stone-400'}`}>
          {length}/{max}
        </span>
      </span>
      <div className="mt-1 border-b border-stone-200 pb-2 focus-within:border-brand-600">
        {children}
      </div>
    </label>
  )
}
