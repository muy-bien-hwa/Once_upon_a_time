import { Route, Routes } from 'react-router'
import NewStoryPage from './pages/NewStoryPage.tsx'
import NotFoundPage from './pages/NotFoundPage.tsx'
import SentenceReadPage from './pages/SentenceReadPage.tsx'
import StoryListPage from './pages/StoryListPage.tsx'

// 주소(URL)마다 보여줄 화면을 정함 (라우팅)
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<StoryListPage />} />
      <Route path="/stories/new" element={<NewStoryPage />} />
      <Route path="/s/:sentenceId" element={<SentenceReadPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
