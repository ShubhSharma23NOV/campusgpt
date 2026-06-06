import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { policiesAPI } from '../../lib/api'
import { PageLoader } from '../../components/ui/LoadingSpinner'
import { Upload, FileText, Trash2, RefreshCw, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

const CATEGORIES = ['attendance', 'academic', 'examination', 'hostel', 'scholarship', 'fee', 'conduct', 'fine', 'general']

export default function AdminPolicies() {
    const qc = useQueryClient()
    const fileRef = useRef()

    const [form, setForm] = useState({ title: '', category: 'general', version: '' })
    const [file, setFile] = useState(null)
    const [uploading, setUploading] = useState(false)

    const { data, isLoading } = useQuery({
        queryKey: ['policies'],
        queryFn: () => policiesAPI.list().then(r => r.data),
    })

    const deleteMutation = useMutation({
        mutationFn: (id) => policiesAPI.delete(id),
        onSuccess: () => { toast.success('Policy deactivated'); qc.invalidateQueries({ queryKey: ['policies'] }) },
    })

    const reindexMutation = useMutation({
        mutationFn: (id) => policiesAPI.reindex(id),
        onSuccess: (res) => {
            toast.success(`Re-indexed ${res.data.chunks_indexed} chunks`)
            qc.invalidateQueries({ queryKey: ['policies'] })
        },
        onError: () => toast.error('Re-index failed'),
    })

    const handleUpload = async (e) => {
        e.preventDefault()
        if (!file) { toast.error('Select a PDF file'); return }
        if (!form.title) { toast.error('Enter a title'); return }

        setUploading(true)
        const fd = new FormData()
        fd.append('title', form.title)
        fd.append('category', form.category)
        if (form.version) fd.append('version', form.version)
        fd.append('file', file)

        try {
            const res = await policiesAPI.upload(fd)
            toast.success(`Uploaded & indexed ${res.data.chunks_indexed} chunks`)
            setForm({ title: '', category: 'general', version: '' })
            setFile(null)
            fileRef.current.value = ''
            qc.invalidateQueries({ queryKey: ['policies'] })
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Upload failed')
        } finally {
            setUploading(false)
        }
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Policy Documents</h1>
                <p className="text-sm text-gray-500 mt-0.5">Upload and manage policy PDFs for the AI chatbot</p>
            </div>

            {/* Upload form */}
            <div className="card">
                <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                    <Upload className="w-4 h-4 text-primary-600" /> Upload New Policy
                </h2>
                <form onSubmit={handleUpload} className="grid sm:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Title *</label>
                        <input className="input" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} placeholder="Attendance Policy 2024-25" required />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Category *</label>
                        <select className="input" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}>
                            {CATEGORIES.map(c => <option key={c} value={c} className="capitalize">{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Version (optional)</label>
                        <input className="input" value={form.version} onChange={e => setForm({ ...form, version: e.target.value })} placeholder="v2.0" />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">PDF File *</label>
                        <input ref={fileRef} type="file" accept=".pdf" onChange={e => setFile(e.target.files[0])} className="input text-xs py-1.5" required />
                    </div>
                    <div className="sm:col-span-2">
                        <button type="submit" disabled={uploading} className="btn-primary">
                            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                            {uploading ? 'Uploading & Indexing…' : 'Upload & Index'}
                        </button>
                    </div>
                </form>
            </div>

            {/* Policy list */}
            <div className="card">
                <h2 className="font-semibold text-gray-900 mb-4">Uploaded Policies</h2>
                {isLoading ? <PageLoader /> : (
                    <div className="space-y-3">
                        {(data?.policies || []).map(p => (
                            <div key={p.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                                <div className="flex items-center gap-3">
                                    <div className="w-9 h-9 rounded-lg bg-red-50 flex items-center justify-center">
                                        <FileText className="w-4 h-4 text-red-500" />
                                    </div>
                                    <div>
                                        <p className="text-sm font-semibold text-gray-900">{p.title}</p>
                                        <div className="flex items-center gap-2 mt-0.5">
                                            <span className="badge badge-gray capitalize">{p.category}</span>
                                            {p.version && <span className="text-xs text-gray-400">{p.version}</span>}
                                            {p.is_indexed
                                                ? <span className="flex items-center gap-1 text-xs text-green-600"><CheckCircle className="w-3 h-3" /> Indexed</span>
                                                : <span className="flex items-center gap-1 text-xs text-red-500"><XCircle className="w-3 h-3" /> Not indexed</span>
                                            }
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1">
                                    <button
                                        onClick={() => reindexMutation.mutate(p.id)}
                                        className="btn-ghost text-xs text-blue-600"
                                        title="Re-index"
                                        disabled={reindexMutation.isPending}
                                    >
                                        <RefreshCw className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                        onClick={() => deleteMutation.mutate(p.id)}
                                        className="btn-ghost text-xs text-red-500"
                                        title="Delete"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </div>
                        ))}
                        {(data?.policies || []).length === 0 && (
                            <p className="text-center text-gray-400 py-6">No policies uploaded yet</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    )
}
