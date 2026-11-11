import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { createPost } from '../api/forum.ts'
import { fetchStory, type QuoteCandidate } from '../api/stories.ts'
import ConfirmDialog from '../components/ConfirmDialog.tsx'
import { ChevronLeft } from '../components/icons.tsx'
import LoginNotice from '../components/LoginNotice.tsx'
import QuotePicker from '../components/QuotePicker.tsx'
import { useMe } from '../lib/useMe.ts'

const TITLE_MAX = 100
const BODY_MAX = 5000

// 커뮤니티 글쓰기 (F-17·D-91)
// 인용할 문장은 이 화면에서 낱말로 찾아 고름 (D-102 — 읽기 화면의 [글쓰기] 버튼은 없앰)
export default function NewPostPage() {
  const { storyId } = useParams()
  const id = Number(storyId)

  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [quote, setQuote] = useState<QuoteCandidate | null>(null)
  const [confirming, setConfirming] = useState(false)
  const { data: me } = useMe()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const storyQuery = useQuery({
    queryKey: ['story', id],
    queryFn: ({ signal }) => fetchStory(id, signal),
    enabled: Number.isInteger(id) && id > 0,
  })

  const write = useMutation({
    mutationFn: () =>
      createPost(id, {
        title: title.trim(),
        body: body.trim(),
        ...(quote ? { quoted_sentence_id: quote.id } : {}),
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
        <Link
          to={`/stories/${id}/forum`}
          className="inline-flex items-center gap-1 text-sm text-stone-500 hover:text-stone-800"
        >
          <ChevronLeft className="h-4 w-4" /> 커뮤니티
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
            <QuotePicker storyId={id} value={quote} onChange={setQuote} />

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
