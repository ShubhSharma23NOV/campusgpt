import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsAPI } from '../lib/api'
import { PageLoader } from '../components/ui/LoadingSpinner'
import { Bell, BellOff, CheckCheck, BookOpen, DollarSign, Home, Award, AlertTriangle } from 'lucide-react'

const TYPE_ICONS = {
    attendance_shortage: { icon: BookOpen, color: 'text-red-500', bg: 'bg-red-50' },
    fee_due: { icon: DollarSign, color: 'text-blue-500', bg: 'bg-blue-50' },
    hostel_fee_due: { icon: Home, color: 'text-purple-500', bg: 'bg-purple-50' },
    scholarship_deadline: { icon: Award, color: 'text-yellow-500', bg: 'bg-yellow-50' },
    fine_reminder: { icon: AlertTriangle, color: 'text-orange-500', bg: 'bg-orange-50' },
    general: { icon: Bell, color: 'text-gray-500', bg: 'bg-gray-50' },
    system: { icon: Bell, color: 'text-primary-500', bg: 'bg-primary-50' },
}

export default function NotificationsPage() {
    const qc = useQueryClient()

    const { data, isLoading } = useQuery({
        queryKey: ['notifications-all'],
        queryFn: () => notificationsAPI.getMy(false).then(r => r.data),
    })

    const markRead = useMutation({
        mutationFn: (id) => notificationsAPI.markRead(id),
        onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications-all'] }),
    })

    const markAll = useMutation({
        mutationFn: () => notificationsAPI.markAllRead(),
        onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications-all'] }),
    })

    if (isLoading) return <PageLoader />

    const { notifications = [], unread_count = 0 } = data || {}

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
                    <p className="text-sm text-gray-500 mt-0.5">
                        {unread_count > 0 ? `${unread_count} unread` : 'All caught up'}
                    </p>
                </div>
                {unread_count > 0 && (
                    <button
                        onClick={() => markAll.mutate()}
                        className="btn-secondary text-xs"
                    >
                        <CheckCheck className="w-3.5 h-3.5" />
                        Mark all read
                    </button>
                )}
            </div>

            {notifications.length === 0 ? (
                <div className="card text-center py-12">
                    <BellOff className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="font-medium text-gray-500">No notifications yet</p>
                </div>
            ) : (
                <div className="space-y-2">
                    {notifications.map(n => {
                        const t = TYPE_ICONS[n.type] || TYPE_ICONS.general
                        const Icon = t.icon
                        return (
                            <div
                                key={n.id}
                                className={`flex gap-3 p-4 rounded-xl border cursor-pointer transition-colors ${n.is_read
                                        ? 'bg-white border-gray-100'
                                        : 'bg-blue-50/60 border-blue-100 hover:bg-blue-50'
                                    }`}
                                onClick={() => !n.is_read && markRead.mutate(n.id)}
                            >
                                <div className={`w-9 h-9 rounded-xl ${t.bg} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                                    <Icon className={`w-4 h-4 ${t.color}`} />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between gap-2">
                                        <p className={`text-sm font-medium ${n.is_read ? 'text-gray-700' : 'text-gray-900'}`}>
                                            {n.title}
                                        </p>
                                        {!n.is_read && (
                                            <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-1.5" />
                                        )}
                                    </div>
                                    <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{n.message}</p>
                                    <p className="text-xs text-gray-400 mt-1">{n.created_at?.slice(0, 16).replace('T', ' ')}</p>
                                </div>
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}
