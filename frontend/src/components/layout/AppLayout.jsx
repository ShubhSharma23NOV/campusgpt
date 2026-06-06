import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { Menu, X, Bell } from 'lucide-react'
import useAuthStore from '../../store/authStore'
import { notificationsAPI } from '../../lib/api'
import { useQuery } from '@tanstack/react-query'

export default function AppLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const { user } = useAuthStore()

    const { data: notifData } = useQuery({
        queryKey: ['notifications-count'],
        queryFn: () => notificationsAPI.getMy(true).then(r => r.data),
        refetchInterval: 60000,
        retry: false,
    })
    const unreadCount = notifData?.unread_count || 0

    return (
        <div className="flex h-screen bg-gray-50 overflow-hidden">
            {/* Mobile overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/30 z-20 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar – mobile: fixed overlay, desktop: static */}
            <div className={`
        fixed inset-y-0 left-0 z-30 lg:static lg:z-auto
        transform transition-transform duration-200
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
                <Sidebar onClose={() => setSidebarOpen(false)} />
            </div>

            {/* Main content */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                {/* Topbar */}
                <header className="flex items-center justify-between px-4 lg:px-6 h-14 bg-white border-b border-gray-100 flex-shrink-0">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="lg:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100"
                    >
                        <Menu className="w-5 h-5" />
                    </button>

                    <div className="hidden lg:block">
                        <p className="text-sm text-gray-400">
                            Welcome back, <span className="font-semibold text-gray-900">{user?.name}</span>
                        </p>
                    </div>

                    <div className="flex items-center gap-2 ml-auto">
                        <a href="/notifications" className="relative p-2 rounded-lg text-gray-500 hover:bg-gray-100">
                            <Bell className="w-5 h-5" />
                            {unreadCount > 0 && (
                                <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center leading-none">
                                    {unreadCount > 9 ? '9+' : unreadCount}
                                </span>
                            )}
                        </a>
                        <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold">
                            {user?.name?.[0]?.toUpperCase() || 'U'}
                        </div>
                    </div>
                </header>

                {/* Page content */}
                <main className="flex-1 overflow-y-auto p-4 lg:p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}
