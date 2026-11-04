import { Route, Routes } from 'react-router'
import AuthorPage from './pages/AuthorPage.tsx'
import ForumPage from './pages/ForumPage.tsx'
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
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
