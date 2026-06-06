import { useQuery } from '@tanstack/react-query'
import { hostelAPI } from '../lib/api'
import { PageLoader } from '../components/ui/LoadingSpinner'
import StatCard from '../components/ui/StatCard'
import { Home, DollarSign, Calendar, Wifi, Wind, Coffee } from 'lucide-react'

export default function HostelPage() {
    const { data, isLoading } = useQuery({
        queryKey: ['my-hostel'],
        queryFn: () => hostelAPI.getMy().then(r => r.data),
    })

    if (isLoading) return <PageLoader />

    if (!data?.has_hostel) {
        return (
            <div className="space-y-4 animate-fade-in">
                <h1 className="text-2xl font-bold text-gray-900">Hostel</h1>
                <div className="card text-center py-12">
                    <Home className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 font-medium">You are not allocated a hostel room</p>
                    <p className="text-sm text-gray-400 mt-1">Contact the hostel office for allocation</p>
                </div>
            </div>
        )
    }

    const { hostel, allocation, last_payment, payment_history } = data
    const pct = allocation.total_fee > 0
        ? Math.round((allocation.paid_amount / allocation.total_fee) * 100)
        : 0

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Hostel</h1>
                <p className="text-sm text-gray-500 mt-0.5">Your hostel allocation details</p>
            </div>

            {/* Room info card */}
            <div className="bg-gradient-to-br from-primary-600 to-blue-500 rounded-2xl p-6 text-white">
                <div className="flex items-start justify-between">
                    <div>
                        <p className="text-blue-200 text-sm mb-1">Allocated Room</p>
                        <p className="text-3xl font-bold">{hostel.room_number}</p>
                        <p className="text-blue-100 mt-1">{hostel.hostel_name} · {hostel.block || 'Main Block'}</p>
                        <p className="text-blue-100 text-sm mt-0.5 capitalize">
                            Floor {hostel.floor || 'G'} · {hostel.room_type} room
                        </p>
                    </div>
                    <div className="w-14 h-14 rounded-2xl bg-white/20 flex items-center justify-center">
                        <Home className="w-7 h-7 text-white" />
                    </div>
                </div>

                {/* Amenities */}
                {hostel.amenities && (
                    <div className="flex gap-3 mt-4">
                        {hostel.amenities.wifi && <span className="flex items-center gap-1 text-xs bg-white/20 px-2 py-1 rounded-full"><Wifi className="w-3 h-3" /> WiFi</span>}
                        {hostel.amenities.ac && <span className="flex items-center gap-1 text-xs bg-white/20 px-2 py-1 rounded-full"><Wind className="w-3 h-3" /> AC</span>}
                        {hostel.amenities.mess && <span className="flex items-center gap-1 text-xs bg-white/20 px-2 py-1 rounded-full"><Coffee className="w-3 h-3" /> Mess</span>}
                    </div>
                )}
            </div>

            {/* Stat cards */}
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
                <StatCard title="Monthly Rent" value={`₹${hostel.monthly_rent.toLocaleString()}`} subtitle="Per month" icon={DollarSign} color="blue" />
                <StatCard title="Remaining Fee" value={`₹${allocation.remaining_fee.toLocaleString()}`} subtitle={`${pct}% paid`} icon={DollarSign} color={allocation.remaining_fee > 0 ? 'red' : 'green'} />
                <StatCard title="Next Due Date" value={allocation.next_due_date || 'N/A'} subtitle="Payment deadline" icon={Calendar} color="yellow" />
            </div>

            {/* Payment progress */}
            <div className="card">
                <div className="flex justify-between items-center mb-3">
                    <h2 className="font-semibold text-gray-900">Fee Payment Progress</h2>
                    <span className="text-sm font-bold text-primary-600">{pct}%</span>
                </div>
                <div className="progress-track mb-3">
                    <div className="progress-bar bg-primary-500" style={{ width: `${pct}%` }} />
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                    <div><p className="text-gray-400 text-xs">Total Fee</p><p className="font-semibold">₹{allocation.total_fee.toLocaleString()}</p></div>
                    <div><p className="text-gray-400 text-xs">Paid</p><p className="font-semibold text-green-600">₹{allocation.paid_amount.toLocaleString()}</p></div>
                    <div><p className="text-gray-400 text-xs">Remaining</p><p className="font-semibold text-red-600">₹{allocation.remaining_fee.toLocaleString()}</p></div>
                </div>

                {last_payment && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                        <p className="text-xs font-medium text-gray-500 mb-1">Last Payment</p>
                        <p className="text-sm">₹{Number(last_payment.amount).toLocaleString()} on {last_payment.payment_date.slice(0, 10)}</p>
                        <p className="text-xs text-gray-400">Receipt: {last_payment.receipt_number}</p>
                    </div>
                )}
            </div>

            {/* Payment history */}
            {payment_history?.length > 0 && (
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-4">Payment History</h2>
                    <div className="space-y-2">
                        {payment_history.map((p, i) => (
                            <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50">
                                <div>
                                    <p className="text-sm font-medium text-gray-900">{p.month_year}</p>
                                    <p className="text-xs text-gray-400">{p.payment_date.slice(0, 10)} · {p.payment_method}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm font-semibold text-green-700">₹{Number(p.amount).toLocaleString()}</p>
                                    <p className="text-xs text-gray-400">{p.receipt_number}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
