import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { scholarshipAPI } from '../lib/api'
import { PageLoader } from '../components/ui/LoadingSpinner'
import { Award, CheckCircle, Clock, XCircle, ChevronRight, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

const STATUS_STYLES = {
    submitted: { badge: 'badge-blue', icon: Clock, label: 'Submitted' },
    under_review: { badge: 'badge-yellow', icon: Clock, label: 'Under Review' },
    approved: { badge: 'badge-green', icon: CheckCircle, label: 'Approved' },
    disbursed: { badge: 'badge-green', icon: CheckCircle, label: 'Disbursed' },
    rejected: { badge: 'badge-red', icon: XCircle, label: 'Rejected' },
    draft: { badge: 'badge-gray', icon: Clock, label: 'Draft' },
}

export default function ScholarshipPage() {
    const qc = useQueryClient()

    const { data, isLoading } = useQuery({
        queryKey: ['my-scholarships'],
        queryFn: () => scholarshipAPI.getMy('2024-25').then(r => r.data),
    })

    const applyMutation = useMutation({
        mutationFn: (id) => scholarshipAPI.apply(id),
        onSuccess: () => {
            toast.success('Application submitted!')
            qc.invalidateQueries({ queryKey: ['my-scholarships'] })
        },
        onError: (err) => toast.error(err.response?.data?.detail || 'Failed to apply'),
    })

    if (isLoading) return <PageLoader />

    const { applications = [], total_received = 0, eligible_scholarships = [] } = data || {}

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Scholarships</h1>
                    <p className="text-sm text-gray-500 mt-0.5">Track and apply for scholarships</p>
                </div>
                {total_received > 0 && (
                    <div className="card text-right min-w-[140px]">
                        <p className="text-xs text-gray-500">Total Received</p>
                        <p className="text-xl font-bold text-green-600">₹{total_received.toLocaleString()}</p>
                    </div>
                )}
            </div>

            {/* My applications */}
            {applications.length > 0 && (
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-4">My Applications</h2>
                    <div className="space-y-3">
                        {applications.map(app => {
                            const s = STATUS_STYLES[app.status] || STATUS_STYLES.draft
                            const Icon = s.icon
                            return (
                                <div key={app.application_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                                    <div className="flex items-center gap-3">
                                        <div className="w-9 h-9 rounded-xl bg-yellow-100 flex items-center justify-center">
                                            <Award className="w-4 h-4 text-yellow-600" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-semibold text-gray-900">{app.scholarship_name}</p>
                                            <p className="text-xs text-gray-500 capitalize">{app.scholarship_type} · Applied {app.applied_date.slice(0, 10)}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className={s.badge}>{s.label}</span>
                                        {app.approved_amount && (
                                            <p className="text-xs font-semibold text-green-700 mt-1">₹{app.approved_amount.toLocaleString()}</p>
                                        )}
                                    </div>
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}

            {/* Eligible scholarships */}
            {eligible_scholarships.length > 0 && (
                <div className="card">
                    <h2 className="font-semibold text-gray-900 mb-1">You May Be Eligible</h2>
                    <p className="text-xs text-gray-500 mb-4">Based on your profile and attendance</p>
                    <div className="space-y-3">
                        {eligible_scholarships.map(sch => (
                            <div key={sch.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-xl hover:border-primary-200 transition-colors">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center">
                                        <Award className="w-5 h-5 text-primary-600" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-semibold text-gray-900">{sch.name}</p>
                                        <p className="text-xs text-gray-500 capitalize">{sch.type} · ₹{sch.amount.toLocaleString()}</p>
                                        {sch.deadline && (
                                            <p className="text-xs text-red-500 mt-0.5 flex items-center gap-1">
                                                <Clock className="w-3 h-3" /> Deadline: {sch.deadline}
                                            </p>
                                        )}
                                    </div>
                                </div>
                                <button
                                    onClick={() => applyMutation.mutate(sch.id)}
                                    disabled={applyMutation.isPending || !sch.is_open}
                                    className="btn-primary text-xs py-1.5 px-3"
                                >
                                    {applyMutation.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                                    {sch.is_open ? 'Apply' : 'Closed'}
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {applications.length === 0 && eligible_scholarships.length === 0 && (
                <div className="card text-center py-12">
                    <Award className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500 font-medium">No scholarships available right now</p>
                    <p className="text-sm text-gray-400 mt-1">Check back during application windows</p>
                </div>
            )}
        </div>
    )
}
