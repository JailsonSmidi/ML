import { Routes, Route } from 'react-router-dom'
import { AppShell } from './components/Shell'
import Upload from './pages/Upload'
import Session from './pages/Session'
import BatchReview from './pages/BatchReview'
import History from './pages/History'

export default function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path="/session/:id" element={<Session />} />
        <Route path="/session/:sessionId/batch/:batchId" element={<BatchReview />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </AppShell>
  )
}
