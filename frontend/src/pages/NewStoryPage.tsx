import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router'
import { createStory } from '../api/stories.ts'
import ConfirmDialog from '../components/ConfirmDialog.tsx'

const TITLE_MAX = 50
const CONTENT_MAX = 100

// ② 새 스토리: 제목 + 첫 문장을 함께 만듦 (D-65)
export default function NewStoryPage() {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [confirming, setConfirming] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const create = useMutation({
    mutationFn: () => createStory({ title: title.trim(), content: content.trim() }),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ['stories'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      setConfirming(false)
      // 방문 기록을 교체 → 새 스토리 화면에서 뒤로 가면 목록으로 (입력 화면으로 되돌아가지 않음)
      navigate(`/s/${created.sentence.id}`, { replace: true })
    },
  })

  const titleLength = [...title.trim()].length
  const contentLength = [...content.trim()].length
  const canSubmit =
    titleLength > 0 &&
    titleLength <= TITLE_MAX &&
    contentLength > 0 &&
    contentLength <= CONTENT_MAX &&
    !create.isPending

  return (
    <main className="min-h-screen bg-stone-50 px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-2xl">
        <Link to="/" className="text-sm text-stone-500 hover:text-stone-800">
          ← 목록
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-stone-800">새 스토리 열기</h1>
        <p className="mt-1 text-sm text-stone-500">
          제목과 첫 문장을 쓰면 다른 작가들이 뒤를 이어 씁니다.
        </p>

        <form
          className="mt-6 rounded-2xl bg-white p-5 shadow-sm"
          onSubmit={(event) => {
            event.preventDefault()
            if (canSubmit) setConfirming(true)
          }}
        >
          <Field label="제목" length={[...title].length} max={TITLE_MAX}>
            <input
              type="text"
              autoFocus
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="예) 말하는 고양이"
              className="w-full text-lg text-stone-800 outline-none placeholder:text-stone-300"
            />
          </Field>

          <div className="mt-5">
            <Field label="첫 문장" length={[...content].length} max={CONTENT_MAX}>
              <input
                type="text"
                value={content}
                onChange={(event) => setContent(event.target.value)}
                placeholder="예) 옛날 옛적에 산골 마을에 말하는 고양이가 살았다."
                className="w-full text-stone-800 outline-none placeholder:text-stone-300"
              />
            </Field>
          </div>

          {create.isError && <p className="mt-4 text-sm text-red-500">{create.error.message}</p>}

          <div className="mt-6 flex justify-end gap-2">
            <Link to="/" className="rounded-lg px-3 py-2 text-sm text-stone-600 hover:bg-stone-100">
              취소
            </Link>
            <button
              type="submit"
              disabled={!canSubmit}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-40"
            >
              스토리 열기
            </button>
          </div>
        </form>

        <ConfirmDialog
          open={confirming}
          title="이 스토리를 열까요?"
          confirmLabel="열기"
          busyLabel="만드는 중…"
          busy={create.isPending}
          onConfirm={() => create.mutate()}
          onCancel={() => setConfirming(false)}
        >
          <p className="font-medium text-stone-800">{title.trim()}</p>
          <p className="mt-1 rounded-xl bg-stone-100 p-3 text-stone-800">{content.trim()}</p>
          <p className="mt-2 text-stone-500">제목과 첫 문장은 나중에 고치거나 지울 수 없어요.</p>
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
