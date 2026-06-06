import { useQuery } from '@tanstack/react-query'
import { adminAPI } from '../../lib/api'
import { PageLoader } from '../../components/ui/LoadingSpinner'
import StatCard from '../../components/ui/StatCard'
import { Users, BookOpen, DollarSign, Home, Award, AlertTriangle, TrendingUp } from 'lucide-react'
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend
} from 'recharts'

export default function AdminDashboard() {
    const { data, isLoading } = useQuery({
        queryKey: ['admin-dashboard'],
        queryFn: () => adminAPI.dashboard('2024-25').then(r => r.data),
    })

    const { data: attDistrib } = useQuery({
        queryKey: ['att-distrib'],
        queryFn: () => adminAPI.attendanceDistrib('2024-25').then(r => r.data),
    })

    const { data: feeTrend } = useQuery({
        queryKey: ['fee-trend'],
        queryFn: () => adminAPI.feeCollectionTrend().then(r => r.data),
    })

    if (isLoading) return <PageLoader />

    const d = data || {}

    const feeDonut = [
        { name: 'Collected', value: d.fees?.total_collected || 0, fill: '#22c55e' },
        { name: 'Pending', value: d.fees?.pending || 0, fill: '#ef4444' },
    ]

    const schDonut = [
        { name: 'Approved', value: d.scholarships?.approved || 0, fill: '#22c55e' },
        { name: 'Submitted', value: d.scholarships?.submitted || 0, fill: '#3b82f6' },
        { name: 'Rejected', value: d.scholarships?.rejected || 0, fill: '#ef4444' },
    ]

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                <p className="text-sm text-gray-500 mt-0.5">Academic Year 2024-25 Overview</p>
            </div>

            {/* Top stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Total Students" value={d.students?.total || 0} subtitle={`${d.students?.hostel || 0} in hostel`} icon={Users} color="blue" />
                <StatCard title="Avg Attendance" value={`${d.attendance?.average_percentage || 0}%`} subtitle={`${d.attendance?.students_below_75 || 0} below 75%`} icon={BookOpen} color="green" />
                <StatCard title="Fee Collected" value={`₹${((d.fees?.total_collected || 0) / 100000).toFixed(1)}L`} subtitle={`${d.fees?.collection_rate || 0}% rate`} icon={DollarSign} color="green" />
                <StatCard title="Hostel Occupied" value={d.hostel?.occupied_rooms || 0} subtitle="Active allocations" icon={Home} color="purple" />
            </div>

            <div className="grid lg:grid-cols-3 gap-6">
                {/* Fee pie */}
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-3">Fee Collection</h2>
                    <ResponsiveContainer width="100%" height={180}>
                        <PieChart>
                            <Pie data={feeDonut} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" strokeWidth={0}>
                                {feeDonut.map((e, i) => <Cell key={i} fill={e.fill} />)}
                            </Pie>
                            <Tooltip formatter={v => `₹${v.toLocaleString()}`} />
                            <Legend iconSize={10} />
                        </PieChart>
                    </ResponsiveContainer>
                    <p className="text-center text-sm text-gray-500 mt-1">
                        <span className="font-bold text-gray-900">{d.fees?.collection_rate || 0}%</span> collected
                    </p>
                </div>

                {/* Scholarship pie */}
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-3">Scholarship Status</h2>
                    <ResponsiveContainer width="100%" height={180}>
                        <PieChart>
                            <Pie data={schDonut} cx="50%" cy="50%" innerRadius={45} outerRadius={70} dataKey="value" strokeWidth={0}>
                                {schDonut.map((e, i) => <Cell key={i} fill={e.fill} />)}
                            </Pie>
                            <Tooltip />
                            <Legend iconSize={10} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Fines summary */}
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-3">Fines Summary</h2>
                    <div className="space-y-3 mt-2">
                        <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
                            <span className="text-sm text-gray-600">Total Imposed</span>
                            <span className="font-semibold">₹{(d.fines?.total_amount || 0).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between p-3 bg-green-50 rounded-lg">
                            <span className="text-sm text-gray-600">Collected</span>
                            <span className="font-semibold text-green-700">₹{(d.fines?.collected || 0).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between p-3 bg-gray-50 rounded-lg">
                            <span className="text-sm text-gray-600">Total Count</span>
                            <span className="font-semibold">{d.fines?.total_count || 0}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Attendance by course */}
            {attDistrib?.by_course?.length > 0 && (
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-4">Attendance by Course</h2>
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={attDistrib.by_course}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="course" tick={{ fontSize: 11 }} />
                            <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                            <Tooltip formatter={(v) => [`${v}%`, 'Average Attendance']} />
                            <Bar dataKey="average" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Fee collection trend */}
            {feeTrend?.monthly_trend?.length > 0 && (
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-4">Monthly Fee Collection</h2>
                    <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={[...feeTrend.monthly_trend].reverse()}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                            <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${(v / 1000).toFixed(0)}K`} />
                            <Tooltip formatter={v => `₹${v.toLocaleString()}`} />
                            <Bar dataKey="amount" fill="#22c55e" radius={[4, 4, 0, 0]} name="Amount" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            )}
        </div>
    )
}
