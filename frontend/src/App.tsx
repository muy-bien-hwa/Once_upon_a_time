import { Route, Routes } from 'react-router'
import Footer from './components/Footer.tsx'
import { OPERATION } from './content/operation.ts'
import { PRIVACY } from './content/privacy.ts'
import { TERMS } from './content/terms.ts'
import AuthorPage from './pages/AuthorPage.tsx'
import ForumPage from './pages/ForumPage.tsx'
import LegalPage from './pages/LegalPage.tsx'
import ForumPostPage from './pages/ForumPostPage.tsx'
import MyPage from './pages/MyPage.tsx'
import MySentencesPage from './pages/MySentencesPage.tsx'
import NewPostPage from './pages/NewPostPage.tsx'
import NewStoryPage from './pages/NewStoryPage.tsx'
import NicknamePage from './pages/NicknamePage.tsx'
import NotFoundPage from './pages/NotFoundPage.tsx'
import SentenceReadPage from './pages/SentenceReadPage.tsx'
import StoryListPage from './pages/StoryListPage.tsx'

// 주소(URL)마다 보여줄 화면을 정함 (라우팅)
export default function App() {
  return (
    <>
        <Routes>
        <Route path="/" element={<StoryListPage />} />
        <Route path="/stories/new" element={<NewStoryPage />} />
        <Route path="/s/:sentenceId" element={<SentenceReadPage />} />
        <Route path="/stories/:storyId/forum" element={<ForumPage />} />
        <Route path="/stories/:storyId/forum/new" element={<NewPostPage />} />
        <Route path="/forum/posts/:postId" element={<ForumPostPage />} />
        <Route path="/nickname" element={<NicknamePage />} />
        <Route path="/me" element={<MyPage />} />
        <Route path="/me/sentences" element={<MySentencesPage />} />
        <Route path="/u/:nickname" element={<AuthorPage />} />
        <Route path="/terms" element={<LegalPage doc={TERMS} />} />
        <Route path="/policy" element={<LegalPage doc={OPERATION} />} />
        <Route path="/privacy" element={<LegalPage doc={PRIVACY} />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      {/* 어느 화면에서든 맨 아래에서 약관으로 갈 수 있게 */}
      <Footer />
    </>
  )
}
