import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import useAuthStore from './store/authStore'

// Layout
import AppLayout from './components/layout/AppLayout'

// Pages – Student
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ChatPage from './pages/ChatPage'
import AttendancePage from './pages/AttendancePage'
import FeesPage from './pages/FeesPage'
import HostelPage from './pages/HostelPage'
import ScholarshipPage from './pages/ScholarshipPage'
import FinesPage from './pages/FinesPage'
import NotificationsPage from './pages/NotificationsPage'

// Pages – Admin
import AdminDashboard from './pages/admin/AdminDashboard'
import AdminPolicies from './pages/admin/AdminPolicies'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60000,
      retry: 1,
    },
  },
})

// Route guards
function RequireAuth({ children, adminOnly = false }) {
  const { isAuthenticated, isAdmin } = useAuthStore()
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  if (adminOnly && !isAdmin()) return <Navigate to="/dashboard" replace />
  return children
}

function RequireGuest({ children }) {
  const { isAuthenticated, isAdmin } = useAuthStore()
  if (isAuthenticated()) return <Navigate to={isAdmin() ? '/admin' : '/dashboard'} replace />
  return children
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<RequireGuest><LoginPage /></RequireGuest>} />

          {/* Student routes */}
          <Route element={<RequireAuth><AppLayout /></RequireAuth>}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/attendance" element={<AttendancePage />} />
            <Route path="/fees" element={<FeesPage />} />
            <Route path="/hostel" element={<HostelPage />} />
            <Route path="/scholarship" element={<ScholarshipPage />} />
            <Route path="/fines" element={<FinesPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
            <Route path="/settings" element={<div className="card"><p className="text-gray-500">Settings coming soon</p></div>} />
          </Route>

          {/* Admin routes */}
          <Route element={<RequireAuth adminOnly><AppLayout /></RequireAuth>}>
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/students" element={<div className="card"><p className="text-gray-500">Student management coming soon</p></div>} />
            <Route path="/admin/attendance" element={<div className="card"><p className="text-gray-500">Attendance management coming soon</p></div>} />
            <Route path="/admin/fees" element={<div className="card"><p className="text-gray-500">Fee management coming soon</p></div>} />
            <Route path="/admin/policies" element={<AdminPolicies />} />
            <Route path="/admin/fines" element={<div className="card"><p className="text-gray-500">Fine management coming soon</p></div>} />
            <Route path="/admin/notify" element={<div className="card"><p className="text-gray-500">Notification management coming soon</p></div>} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: { borderRadius: '10px', fontSize: '14px' },
        }}
      />
    </QueryClientProvider>
  )
}
