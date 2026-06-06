import { NavLink, useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/authStore'
import {
    LayoutDashboard, MessageSquare, BookOpen, DollarSign, Home,
    Award, AlertTriangle, Bell, Settings, LogOut, GraduationCap,
    Users, Shield, BarChart3, Upload, ChevronRight
} from 'lucide-react'

const studentNav = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/chat', icon: MessageSquare, label: 'AI Assistant' },
    { to: '/attendance', icon: BookOpen, label: 'Attendance' },
    { to: '/fees', icon: DollarSign, label: 'Fees' },
    { to: '/hostel', icon: Home, label: 'Hostel' },
    { to: '/scholarship', icon: Award, label: 'Scholarships' },
    { to: '/fines', icon: AlertTriangle, label: 'Fines' },
    { to: '/notifications', icon: Bell, label: 'Notifications' },
]

const adminNav = [
    { to: '/admin', icon: BarChart3, label: 'Analytics' },
    { to: '/admin/students', icon: Users, label: 'Students' },
    { to: '/admin/attendance', icon: BookOpen, label: 'Attendance' },
    { to: '/admin/fees', icon: DollarSign, label: 'Fees' },
    { to: '/admin/policies', icon: Upload, label: 'Policies' },
    { to: '/admin/fines', icon: AlertTriangle, label: 'Fines' },
    { to: '/admin/notify', icon: Bell, label: 'Notify' },
]

export default function Sidebar({ onClose }) {
    const { user, userType, logout } = useAuthStore()
    const navigate = useNavigate()
    const nav = userType === 'admin' ? adminNav : studentNav

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <aside className="flex flex-col h-full w-64 bg-white border-r border-gray-100">
            {/* Logo */}
            <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-100">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-600 to-blue-500 flex items-center justify-center">
                    <GraduationCap className="w-5 h-5 text-white" />
                </div>
                <div>
                    <p className="font-bold text-gray-900 text-sm leading-tight">CampusGPT</p>
                    <p className="text-xs text-gray-400">AI Student Copilot</p>
                </div>
            </div>

            {/* User pill */}
            <div className="mx-4 mt-4 mb-2 p-3 rounded-xl bg-primary-50 border border-primary-100">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary-200 flex items-center justify-center text-primary-700 font-semibold text-xs">
                        {user?.name?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <div className="min-w-0">
                        <p className="text-xs font-semibold text-gray-900 truncate">{user?.name || 'User'}</p>
                        <p className="text-xs text-primary-600 truncate">
                            {userType === 'admin' ? user?.role || 'Admin' : user?.student_id || user?.course}
                        </p>
                    </div>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-0.5 scrollbar-hide">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider px-3 py-2">
                    {userType === 'admin' ? 'Administration' : 'My Portal'}
                </p>
                {nav.map(({ to, icon: Icon, label }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={to === '/dashboard' || to === '/admin'}
                        onClick={onClose}
                        className={({ isActive }) =>
                            `sidebar-link ${isActive ? 'active' : ''}`
                        }
                    >
                        <Icon className="w-4 h-4 flex-shrink-0" />
                        <span className="flex-1">{label}</span>
                    </NavLink>
                ))}
            </nav>

            {/* Bottom */}
            <div className="px-3 py-4 border-t border-gray-100 space-y-0.5">
                <NavLink to="/settings" className="sidebar-link" onClick={onClose}>
                    <Settings className="w-4 h-4" />
                    <span>Settings</span>
                </NavLink>
                <button onClick={handleLogout} className="sidebar-link w-full text-red-500 hover:bg-red-50 hover:text-red-700">
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                </button>
            </div>
        </aside>
    )
}
