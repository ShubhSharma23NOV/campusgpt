import { useQuery } from '@tanstack/react-query'
import { finesAPI } from '../lib/api'
import { PageLoader } from '../components/ui/LoadingSpinner'
import StatCard from '../components/ui/StatCard'
import { AlertTriangle, CheckCircle, Clock, DollarSign } from 'lucide-react'

const TYPE_LABELS = {
    attendance: '📚 Attendance',
    library: '📖 Library',
    hostel: '🏠 Hostel',
    discipline: '⚠️ Discipline',
    property_damage: '🔨 Property',
    exam_malpractice: '📝 Exam',
    late_fee: '⏰ Late Fee',
    other: '❓ Other',
}

export default function FinesPage() {
    const { data, isLoading } = useQuery({
        queryKey: ['my-fines-full'],
        queryFn: () => finesAPI.getMy().then(r => r.data),
    })

    if (isLoading) return <PageLoader />

    const { summary = {}, fines = [] } = data || {}

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Fines & Penalties</h1>
                <p className="text-sm text-gray-500 mt-0.5">Track and manage your fines</p>
            </div>

            {/* Summary */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Total Fines" value={summary.total_fines || 0} subtitle="All time" icon={AlertTriangle} color="red" />
                <StatCard title="Total Amount" value={`₹${(summary.total_amount || 0).toLocaleString()}`} subtitle="Imposed" icon={DollarSign} color="red" />
                <StatCard title="Paid" value={`₹${(summary.total_paid || 0).toLocaleString()}`} subtitle="Cleared" icon={CheckCircle} color="green" />
                <StatCard title="Pending" value={`₹${(summary.total_pending || 0).toLocaleString()}`} subtitle="Outstanding" icon={Clock} color={summary.total_pending > 0 ? 'yellow' : 'green'} />
            </div>

            {/* Fine cards */}
            {fines.length === 0 ? (
                <div className="card text-center py-12">
                    <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
                    <p className="font-medium text-gray-700">No fines on record</p>
                    <p className="text-sm text-gray-400 mt-1">Keep it up!</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {fines.map(fine => (
                        <div
                            key={fine.id}
                            className={`card border-l-4 ${fine.status === 'paid' ? 'border-green-400' :
                                    fine.is_overdue ? 'border-red-500' :
                                        fine.status === 'partially_paid' ? 'border-yellow-400' : 'border-orange-400'
                                }`}
                        >
                            <div className="flex items-start justify-between mb-2">
                                <div>
                                    <p className="text-sm font-semibold text-gray-900">
                                        {TYPE_LABELS[fine.fine_type] || fine.fine_type}
                                    </p>
                                    <p className="text-xs text-gray-500 mt-0.5">{fine.reason}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-lg font-bold text-gray-900">₹{Number(fine.amount).toLocaleString()}</p>
                                    <span className={`badge ${fine.status === 'paid' ? 'badge-green' :
                                            fine.status === 'partially_paid' ? 'badge-yellow' :
                                                fine.is_overdue ? 'badge-red' : 'badge-gray'
                                        }`}>
                                        {fine.status === 'paid' ? 'Paid' : fine.is_overdue ? 'Overdue' :
                                            fine.status === 'partially_paid' ? 'Partial' : 'Unpaid'}
                                    </span>
                                </div>
                            </div>

                            {fine.status !== 'paid' && (
                                <div className="mt-2">
                                    <div className="progress-track">
                                        <div
                                            className="progress-bar bg-green-500"
                                            style={{ width: `${Math.round((fine.paid_amount / fine.amount) * 100)}%` }}
                                        />
                                    </div>
                                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                                        <span>Paid: ₹{Number(fine.paid_amount).toLocaleString()}</span>
                                        <span>Remaining: ₹{fine.remaining_amount.toLocaleString()}</span>
                                    </div>
                                </div>
                            )}

                            <div className="flex gap-4 mt-2 text-xs text-gray-400">
                                <span>Imposed: {fine.fine_date}</span>
                                {fine.due_date && <span className={fine.is_overdue ? 'text-red-500 font-medium' : ''}>Due: {fine.due_date}</span>}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
