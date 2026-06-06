import { useQuery } from '@tanstack/react-query'
import { attendanceAPI, feesAPI, finesAPI, notificationsAPI, aiAPI } from '../lib/api'
import useAuthStore from '../store/authStore'
import StatCard from '../components/ui/StatCard'
import { PageLoader } from '../components/ui/LoadingSpinner'
import { AttendanceProgressBar } from '../components/ui/AttendanceBadge'
import {
    BookOpen, DollarSign, AlertTriangle, Bell,
    TrendingUp, Calendar, Sparkles, ChevronRight
} from 'lucide-react'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, AreaChart, Area
} from 'recharts'
import { Link } from 'react-router-dom'

export default function DashboardPage() {
    const { user } = useAuthStore()

    const { data: attData, isLoading: attLoading } = useQuery({
        queryKey: ['my-attendance'],
        queryFn: () => attendanceAPI.getMy('2024-25').then(r => r.data),
    })

    const { data: feeData, isLoading: feeLoading } = useQuery({
        queryKey: ['my-fees'],
        queryFn: () => feesAPI.getMy('2024-25').then(r => r.data),
    })

    const { data: fineData } = useQuery({
        queryKey: ['my-fines'],
        queryFn: () => finesAPI.getMy().then(r => r.data),
    })

    const { data: trendData } = useQuery({
        queryKey: ['attendance-trend'],
        queryFn: () => attendanceAPI.getTrend(30).then(r => r.data),
    })

    const { data: adviceData } = useQuery({
        queryKey: ['attendance-advice'],
        queryFn: () => aiAPI.getAttendanceAdvice().then(r => r.data),
        enabled: !!attData,
    })

    const { data: notifData } = useQuery({
        queryKey: ['notifications'],
        queryFn: () => notificationsAPI.getMy(false, 5).then(r => r.data),
    })

    if (attLoading || feeLoading) return <PageLoader />

    const overall = attData?.overall || {}
    const fees = feeData?.summary || {}
    const fines = fineData?.summary || {}

    const criticalSubjects = (attData?.subjects || []).filter(s => s.status === 'critical')
    const warningSubjects = (attData?.subjects || []).filter(s => s.status === 'warning')

    return (
        <div className="space-y-6 animate-fade-in">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-gray-900">
                    Good {getGreeting()}, {user?.name?.split(' ')[0]} 👋
                </h1>
                <p className="text-sm text-gray-500 mt-0.5">
                    {user?.course} · Semester {user?.semester} · {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </p>
            </div>

            {/* AI Advice Banner */}
            {adviceData?.advice && (
                <div className="bg-gradient-to-r from-primary-600 to-blue-500 rounded-xl p-4 text-white">
                    <div className="flex items-start gap-3">
                        <Sparkles className="w-5 h-5 mt-0.5 flex-shrink-0" />
                        <div>
                            <p className="text-sm font-semibold mb-1">AI Attendance Advisor</p>
                            <p className="text-sm text-blue-100 leading-relaxed">{adviceData.advice}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Stat Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="Overall Attendance"
                    value={`${overall.percentage || 0}%`}
                    subtitle={`${overall.attended_classes || 0} / ${overall.total_classes || 0} classes`}
                    icon={BookOpen}
                    color={overall.percentage >= 75 ? 'green' : overall.percentage >= 65 ? 'yellow' : 'red'}
                />
                <StatCard
                    title="Fee Remaining"
                    value={`₹${((fees.total_remaining || 0) / 1000).toFixed(1)}K`}
                    subtitle={`Paid ₹${((fees.total_paid || 0) / 1000).toFixed(1)}K of ₹${((fees.total_amount || 0) / 1000).toFixed(1)}K`}
                    icon={DollarSign}
                    color="blue"
                />
                <StatCard
                    title="Pending Fines"
                    value={`₹${fines.total_pending || 0}`}
                    subtitle={`${fines.total_fines || 0} fine(s) total`}
                    icon={AlertTriangle}
                    color={fines.total_pending > 0 ? 'red' : 'green'}
                />
                <StatCard
                    title="Notifications"
                    value={notifData?.unread_count || 0}
                    subtitle="Unread alerts"
                    icon={Bell}
                    color="purple"
                />
            </div>

            {/* Attendance Trend Chart + Subject Details */}
            <div className="grid lg:grid-cols-5 gap-6">
                {/* Trend Chart */}
                <div className="lg:col-span-3 card">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="font-semibold text-gray-900">Attendance Trend (30 days)</h2>
                        <TrendingUp className="w-4 h-4 text-gray-400" />
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                        <AreaChart data={trendData?.trend || []}>
                            <defs>
                                <linearGradient id="attGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
                            <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                            <Tooltip
                                formatter={(v) => [`${v}%`, 'Attendance']}
                                labelFormatter={(l) => `Date: ${l}`}
                            />
                            <Area type="monotone" dataKey="percentage" stroke="#3b82f6" strokeWidth={2} fill="url(#attGrad)" dot={false} />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>

                {/* Subject breakdown */}
                <div className="lg:col-span-2 card">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="font-semibold text-gray-900">Subject Attendance</h2>
                        <Link to="/attendance" className="text-xs text-primary-600 hover:underline flex items-center gap-1">
                            View all <ChevronRight className="w-3 h-3" />
                        </Link>
                    </div>
                    <div className="space-y-4">
                        {(attData?.subjects || []).slice(0, 4).map(sub => (
                            <div key={sub.subject_id}>
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="font-medium text-gray-700 truncate pr-2">{sub.subject_name}</span>
                                    <span className={
                                        sub.status === 'safe' ? 'text-green-600' :
                                            sub.status === 'warning' ? 'text-yellow-600' : 'text-red-600'
                                    }>{sub.percentage}%</span>
                                </div>
                                <AttendanceProgressBar percentage={sub.percentage} />
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Alerts */}
            {(criticalSubjects.length > 0 || warningSubjects.length > 0) && (
                <div className="card border-l-4 border-red-400">
                    <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                        Attendance Alerts
                    </h3>
                    <div className="space-y-2">
                        {criticalSubjects.map(s => (
                            <div key={s.subject_id} className="flex items-center justify-between p-2 bg-red-50 rounded-lg text-sm">
                                <span className="font-medium text-red-800">{s.subject_name}</span>
                                <span className="text-red-600">
                                    {s.percentage}% — need {s.classes_needed_for_75} more classes
                                </span>
                            </div>
                        ))}
                        {warningSubjects.map(s => (
                            <div key={s.subject_id} className="flex items-center justify-between p-2 bg-yellow-50 rounded-lg text-sm">
                                <span className="font-medium text-yellow-800">{s.subject_name}</span>
                                <span className="text-yellow-600">
                                    {s.percentage}% — need {s.classes_needed_for_75} more classes
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Quick actions */}
            <div>
                <h2 className="font-semibold text-gray-900 mb-3">Quick Actions</h2>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                        { to: '/chat', emoji: '🤖', label: 'Ask AI', desc: 'Policy questions' },
                        { to: '/fees', emoji: '💳', label: 'View Fees', desc: 'Payments & dues' },
                        { to: '/scholarship', emoji: '🏆', label: 'Scholarships', desc: 'Check eligibility' },
                        { to: '/hostel', emoji: '🏠', label: 'Hostel', desc: 'Room & payments' },
                    ].map(({ to, emoji, label, desc }) => (
                        <Link key={to} to={to} className="card-hover text-center p-4 hover:border-primary-200 hover:shadow-primary-100">
                            <p className="text-2xl mb-2">{emoji}</p>
                            <p className="text-sm font-semibold text-gray-900">{label}</p>
                            <p className="text-xs text-gray-500 mt-0.5">{desc}</p>
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    )
}

function getGreeting() {
    const h = new Date().getHours()
    if (h < 12) return 'morning'
    if (h < 17) return 'afternoon'
    return 'evening'
}
