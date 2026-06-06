import { useQuery } from '@tanstack/react-query'
import { attendanceAPI } from '../lib/api'
import { PageLoader } from '../components/ui/LoadingSpinner'
import { AttendanceProgressBar } from '../components/ui/AttendanceBadge'
import StatCard from '../components/ui/StatCard'
import { BookOpen, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, ReferenceLine, Cell
} from 'recharts'

export default function AttendancePage() {
    const { data, isLoading } = useQuery({
        queryKey: ['my-attendance-full'],
        queryFn: () => attendanceAPI.getMy('2024-25').then(r => r.data),
    })

    const { data: trendData } = useQuery({
        queryKey: ['att-trend-60'],
        queryFn: () => attendanceAPI.getTrend(60).then(r => r.data),
    })

    if (isLoading) return <PageLoader />

    const overall = data?.overall || {}
    const subjects = data?.subjects || []

    const belowMin = subjects.filter(s => s.percentage < 75)
    const safe = subjects.filter(s => s.percentage >= 75)

    // Chart data
    const chartData = subjects.map(s => ({
        name: s.subject_code,
        fullName: s.subject_name,
        percentage: s.percentage,
        attended: s.attended_classes,
        total: s.total_classes,
    }))

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Attendance</h1>
                <p className="text-sm text-gray-500 mt-0.5">Academic Year 2024-25</p>
            </div>

            {/* Stat cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Overall" value={`${overall.percentage || 0}%`} subtitle="Combined average" icon={TrendingUp} color={overall.percentage >= 75 ? 'green' : 'red'} />
                <StatCard title="Total Classes" value={overall.total_classes || 0} subtitle="Across all subjects" icon={BookOpen} color="blue" />
                <StatCard title="Attended" value={overall.attended_classes || 0} subtitle={`${overall.total_classes - overall.attended_classes || 0} absent`} icon={CheckCircle} color="green" />
                <StatCard title="At Risk" value={belowMin.length} subtitle={`${safe.length} subjects safe`} icon={AlertTriangle} color={belowMin.length > 0 ? 'red' : 'green'} />
            </div>

            {/* Bar chart */}
            <div className="card">
                <h2 className="font-semibold text-gray-900 mb-4">Subject-wise Attendance</h2>
                <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={chartData} margin={{ left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip
                            formatter={(v, _, p) => [`${v}% (${p.payload.attended}/${p.payload.total})`, 'Attendance']}
                            labelFormatter={l => {
                                const s = chartData.find(d => d.name === l)
                                return s?.fullName || l
                            }}
                        />
                        <ReferenceLine y={75} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '75%', position: 'right', fontSize: 11, fill: '#ef4444' }} />
                        <Bar dataKey="percentage" radius={[4, 4, 0, 0]}>
                            {chartData.map((entry, i) => (
                                <Cell
                                    key={i}
                                    fill={entry.percentage >= 75 ? '#22c55e' : entry.percentage >= 65 ? '#eab308' : '#ef4444'}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Subject cards */}
            <div>
                <h2 className="font-semibold text-gray-900 mb-3">Subject Details</h2>
                <div className="grid lg:grid-cols-2 gap-4">
                    {subjects.map(sub => (
                        <div
                            key={sub.subject_id}
                            className={`card border-l-4 ${sub.status === 'safe' ? 'border-green-400' :
                                    sub.status === 'warning' ? 'border-yellow-400' : 'border-red-400'
                                }`}
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div>
                                    <p className="font-semibold text-gray-900 text-sm">{sub.subject_name}</p>
                                    <p className="text-xs text-gray-500">{sub.subject_code} · {sub.type}</p>
                                </div>
                                <span className={`badge ${sub.status === 'safe' ? 'badge-green' :
                                        sub.status === 'warning' ? 'badge-yellow' : 'badge-red'
                                    }`}>
                                    {sub.percentage}%
                                </span>
                            </div>

                            <AttendanceProgressBar percentage={sub.percentage} />

                            <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                                <span>{sub.attended_classes} attended / {sub.total_classes} total</span>
                                {sub.classes_needed_for_75 > 0 && (
                                    <span className="text-orange-600 font-medium">
                                        Attend {sub.classes_needed_for_75} more to reach 75%
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Trend chart */}
            {trendData?.trend?.length > 0 && (
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-4">Daily Attendance (Last 60 days)</h2>
                    <ResponsiveContainer width="100%" height={180}>
                        <BarChart data={trendData.trend}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d.slice(5)} />
                            <YAxis tick={{ fontSize: 10 }} />
                            <Tooltip />
                            <Bar dataKey="present" fill="#22c55e" name="Present" radius={[2, 2, 0, 0]} />
                            <Bar dataKey="total" fill="#e5e7eb" name="Total" radius={[2, 2, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    )
}
