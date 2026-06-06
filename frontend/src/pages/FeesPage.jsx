import { useQuery } from '@tanstack/react-query'
import { feesAPI } from '../lib/api'
import { PageLoader } from '../components/ui/LoadingSpinner'
import StatCard from '../components/ui/StatCard'
import { DollarSign, CreditCard, Calendar, CheckCircle, Clock } from 'lucide-react'
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'

const STATUS_COLORS = {
    paid: { badge: 'badge-green', label: 'Paid' },
    partially_paid: { badge: 'badge-yellow', label: 'Partial' },
    unpaid: { badge: 'badge-gray', label: 'Unpaid' },
    overdue: { badge: 'badge-red', label: 'Overdue' },
}

export default function FeesPage() {
    const { data, isLoading } = useQuery({
        queryKey: ['my-fees-full'],
        queryFn: () => feesAPI.getMy('2024-25').then(r => r.data),
    })

    const { data: histData } = useQuery({
        queryKey: ['fee-history'],
        queryFn: () => feesAPI.getHistory().then(r => r.data),
    })

    if (isLoading) return <PageLoader />

    const summary = data?.summary || {}
    const fees = data?.fees || []

    const pieData = [
        { name: 'Paid', value: summary.total_paid || 0, fill: '#22c55e' },
        { name: 'Remaining', value: summary.total_remaining || 0, fill: '#ef4444' },
    ].filter(d => d.value > 0)

    const pctPaid = summary.total_amount > 0
        ? Math.round((summary.total_paid / summary.total_amount) * 100)
        : 0

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Fees</h1>
                <p className="text-sm text-gray-500 mt-0.5">Academic Year 2024-25</p>
            </div>

            {/* Summary cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard title="Total Fee" value={`₹${(summary.total_amount || 0).toLocaleString()}`} subtitle="Full course fee" icon={DollarSign} color="blue" />
                <StatCard title="Paid" value={`₹${(summary.total_paid || 0).toLocaleString()}`} subtitle={`${pctPaid}% paid`} icon={CheckCircle} color="green" />
                <StatCard title="Remaining" value={`₹${(summary.total_remaining || 0).toLocaleString()}`} subtitle="Balance due" icon={CreditCard} color={summary.total_remaining > 0 ? 'red' : 'green'} />
                <StatCard title="Installments" value={`${summary.installments_paid}/${summary.total_installments}`} subtitle={`${summary.installments_remaining} remaining`} icon={Calendar} color="purple" />
            </div>

            {/* Pie + Breakdown */}
            <div className="grid lg:grid-cols-5 gap-6">
                {/* Pie */}
                <div className="lg:col-span-2 card flex flex-col items-center justify-center">
                    <h2 className="font-semibold text-gray-900 mb-4 self-start">Payment Overview</h2>
                    <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                            <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} dataKey="value" strokeWidth={0}>
                                {pieData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                            </Pie>
                            <Tooltip formatter={v => `₹${v.toLocaleString()}`} />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                    <p className="text-center text-sm text-gray-500">
                        <span className="font-bold text-gray-900 text-lg">{pctPaid}%</span> paid
                    </p>
                </div>

                {/* Fee type breakdown */}
                <div className="lg:col-span-3 card">
                    <h2 className="font-semibold text-gray-900 mb-4">Fee Breakdown</h2>
                    <div className="space-y-3">
                        {fees.map(fee => {
                            const s = STATUS_COLORS[fee.status] || STATUS_COLORS.unpaid
                            const pct = fee.net_amount > 0 ? Math.round((fee.paid_amount / fee.net_amount) * 100) : 0
                            return (
                                <div key={fee.id} className="p-3 bg-gray-50 rounded-xl">
                                    <div className="flex items-center justify-between mb-2">
                                        <p className="font-medium text-gray-900 text-sm capitalize">{fee.fee_type.replace('_', ' ')} Fee</p>
                                        <span className={s.badge}>{s.label}</span>
                                    </div>
                                    <div className="grid grid-cols-3 gap-2 text-xs text-gray-600 mb-2">
                                        <div><p className="text-gray-400">Total</p><p className="font-semibold">₹{fee.net_amount.toLocaleString()}</p></div>
                                        <div><p className="text-gray-400">Paid</p><p className="font-semibold text-green-600">₹{fee.paid_amount.toLocaleString()}</p></div>
                                        <div><p className="text-gray-400">Due</p><p className="font-semibold text-red-600">₹{fee.remaining_amount.toLocaleString()}</p></div>
                                    </div>
                                    <div className="progress-track">
                                        <div className="progress-bar bg-green-500" style={{ width: `${pct}%` }} />
                                    </div>
                                    {fee.due_date && (
                                        <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                                            <Calendar className="w-3 h-3" />
                                            Due: {fee.due_date}
                                        </p>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                </div>
            </div>

            {/* Payment History */}
            {histData?.history?.length > 0 && (
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-4">Payment History</h2>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-gray-100">
                                    {['Date', 'Type', 'Amount', 'Method', 'Receipt'].map(h => (
                                        <th key={h} className="text-left py-2 px-3 text-xs font-medium text-gray-500">{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {histData.history.map(p => (
                                    <tr key={p.id} className="border-b border-gray-50 hover:bg-gray-50">
                                        <td className="py-2 px-3 text-gray-600">{p.payment_date.slice(0, 10)}</td>
                                        <td className="py-2 px-3 capitalize">{p.fee_type}</td>
                                        <td className="py-2 px-3 font-semibold text-green-700">₹{Number(p.amount).toLocaleString()}</td>
                                        <td className="py-2 px-3 capitalize text-gray-500">{p.payment_method}</td>
                                        <td className="py-2 px-3 font-mono text-xs text-gray-400">{p.receipt_number}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
