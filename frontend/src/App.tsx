import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import Dashboard from './pages/Dashboard'
import Reviews from './pages/Reviews'
import ReviewDetail from './pages/ReviewDetail'
import Projects from './pages/Projects'
import Rules from './pages/Rules'
import Notifications from './pages/Notifications'

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1677ff',
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/reviews" element={<Reviews />} />
          <Route path="/reviews/:id" element={<ReviewDetail />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="/notifications" element={<Notifications />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App