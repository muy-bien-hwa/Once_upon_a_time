import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { setNickname } from '../api/auth.ts'
import LoginButton from '../components/LoginButton.tsx'
import { formatDate } from '../lib/time.ts'
import { useMe } from '../lib/useMe.ts'

const MIN = 2
const MAX = 12

// 닉네임 정하기 (첫 로그인 직후, D-48·D-84)
export default function NicknamePage() {
  const { data: me, isPending } = useMe()
  const [nickname, setValue] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const save = useMutation({
    mutationFn: () => setNickname(nickname.trim()),
    onSuccess: (updated) => {
      queryClient.setQueryData(['me'], updated)
      navigate('/', { replace: true })
    },
  })

  const length = [...nickname.trim()].length
  const canSubmit = length >= MIN && length <= MAX && !save.isPending

  return (
    <main className="min-h-screen bg-paper px-4 py-10 sm:px-6">
      <div className="mx-auto max-w-md">
        <h1 className="text-center text-2xl font-bold text-stone-900">닉네임 정하기</h1>
        <p className="mt-2 text-center text-sm text-stone-500">
          문장 옆에 표시되는 이름이에요. 2~12자, 다른 사람과 겹칠 수 없어요.
          <br />한 번 정하면 2주 동안 바꿀 수 없어요.
        </p>

        {isPending ? (
          <div className="mt-6 h-32 animate-pulse rounded-lg bg-stone-200/70" />
        ) : !me ? (
          <div className="mt-6 rounded-lg bg-white p-6 text-center shadow-paper ring-1 ring-stone-200/60">
            <p className="text-stone-600">먼저 로그인해 주세요.</p>
            <div className="mt-3">
              <LoginButton small />
            </div>
          </div>
        ) : me.nickname_editable_at ? (
          // 2주에 한 번만 바꿀 수 있음 (D-85)
          <div className="mt-6 rounded-lg bg-white p-6 text-center shadow-paper ring-1 ring-stone-200/60">
            <p className="text-lg font-medium text-stone-800">{me.nickname}</p>
            <p className="mt-3 text-stone-600">닉네임은 2주에 한 번만 바꿀 수 있어요.</p>
            <p className="mt-1 text-sm text-stone-500">
              다음에 바꿀 수 있는 날: {formatDate(me.nickname_editable_at)}
            </p>
            <Link to="/" className="mt-4 inline-block text-sm text-stone-600 underline">
              목록으로
            </Link>
          </div>
        ) : (
          <form
            className="mt-6 rounded-lg bg-white p-5 shadow-paper ring-1 ring-stone-200/60"
            onSubmit={(event) => {
              event.preventDefault()
              if (canSubmit) save.mutate()
            }}
          >
            <label className="block">
              <span className="flex items-center gap-2 text-sm text-stone-500">
                닉네임
                <span className={`ml-auto ${length > MAX ? 'text-red-500' : 'text-stone-400'}`}>
                  {[...nickname].length}/{MAX}
                </span>
              </span>
              <input
                type="text"
                autoFocus
                value={nickname}
                onChange={(event) => setValue(event.target.value)}
                placeholder={me.nickname ?? '예) 밤의작가'}
                className="mt-1 w-full border-b border-stone-200 pb-2 text-lg text-stone-800 outline-none placeholder:text-stone-300 focus:border-brand-600"
              />
            </label>

            {save.isError && <p className="mt-4 text-sm text-red-500">{save.error.message}</p>}

            <div className="mt-6 flex justify-end gap-2">
              <Link to="/" className="rounded-lg px-3 py-2 text-sm text-stone-600 hover:bg-stone-100">
                나중에
              </Link>
              <button
                type="submit"
                disabled={!canSubmit}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-40"
              >
                {save.isPending ? '저장 중…' : '정하기'}
              </button>
            </div>
          </form>
        )}
      </div>
    </main>
  )
}
