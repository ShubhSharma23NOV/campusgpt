import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useAuthStore from '../store/authStore'
import { GraduationCap, Eye, EyeOff, Loader2, Shield } from 'lucide-react'

export default function LoginPage() {
    const [tab, setTab] = useState('student')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [showPw, setShowPw] = useState(false)
    const { login, isLoading, error } = useAuthStore()
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        const result = await login(email, password, tab)
        if (result.success) {
            navigate(tab === 'admin' ? '/admin' : '/dashboard')
        }
    }

    return (
        <div className="min-h-screen flex">
            {/* Left panel – branding */}
            <div className="hidden lg:flex lg:flex-1 bg-gradient-to-br from-primary-700 via-primary-600 to-blue-500 flex-col items-center justify-center p-12 text-white">
                <div className="max-w-md text-center">
                    <div className="w-20 h-20 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center mx-auto mb-6">
                        <GraduationCap className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-4xl font-bold mb-4">CampusGPT</h1>
                    <p className="text-xl text-blue-100 mb-8">AI Student Copilot</p>
                    <div className="grid grid-cols-2 gap-4 text-left">
                        {[
                            ['📚', 'Policy Navigator', 'Get instant answers from official college documents'],
                            ['📊', 'Smart Dashboard', 'Track attendance, fees, hostel & more in one place'],
                            ['🤖', 'AI Assistant', 'Personalized guidance powered by Gemini AI'],
                            ['🔔', 'Smart Alerts', 'Never miss a deadline or important update'],
                        ].map(([emoji, title, desc]) => (
                            <div key={title} className="bg-white/10 rounded-xl p-4">
                                <p className="text-2xl mb-2">{emoji}</p>
                                <p className="font-semibold text-sm">{title}</p>
                                <p className="text-xs text-blue-200 mt-1">{desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Right panel – form */}
            <div className="flex-1 flex items-center justify-center p-6 bg-gray-50">
                <div className="w-full max-w-md">
                    {/* Logo (mobile) */}
                    <div className="flex items-center gap-3 mb-8 lg:hidden">
                        <div className="w-10 h-10 rounded-xl bg-primary-600 flex items-center justify-center">
                            <GraduationCap className="w-5 h-5 text-white" />
                        </div>
                        <span className="text-xl font-bold text-gray-900">CampusGPT</span>
                    </div>

                    <div className="card shadow-md">
                        <h2 className="text-xl font-bold text-gray-900 mb-1">Sign in</h2>
                        <p className="text-sm text-gray-500 mb-6">Access your campus portal</p>

                        {/* Tabs */}
                        <div className="flex gap-2 mb-6 bg-gray-100 p-1 rounded-lg">
                            {[
                                { key: 'student', label: '🎓 Student' },
                                { key: 'admin', label: '🛡 Admin' },
                            ].map(({ key, label }) => (
                                <button
                                    key={key}
                                    onClick={() => setTab(key)}
                                    className={`flex-1 py-1.5 text-sm font-medium rounded-md transition-all ${tab === key
                                            ? 'bg-white text-gray-900 shadow-sm'
                                            : 'text-gray-500 hover:text-gray-700'
                                        }`}
                                >
                                    {label}
                                </button>
                            ))}
                        </div>

                        {error && (
                            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder={tab === 'admin' ? 'admin@campusgpt.edu' : 'student@campusgpt.edu'}
                                    className="input"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                                <div className="relative">
                                    <input
                                        type={showPw ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="Enter your password"
                                        className="input pr-10"
                                        required
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPw(!showPw)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                    >
                                        {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                </div>
                            </div>

                            <div className="flex items-center justify-between text-sm">
                                <label className="flex items-center gap-2 text-gray-600">
                                    <input type="checkbox" className="rounded" /> Remember me
                                </label>
                                <a href="#" className="text-primary-600 hover:underline">Forgot password?</a>
                            </div>

                            <button type="submit" disabled={isLoading} className="btn-primary w-full justify-center py-2.5">
                                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                                {isLoading ? 'Signing in…' : 'Sign in'}
                            </button>
                        </form>

                        {/* Demo credentials */}
                        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                            <p className="text-xs font-medium text-blue-700 mb-1">Demo credentials:</p>
                            <p className="text-xs text-blue-600">Student: arjun@campusgpt.edu</p>
                            <p className="text-xs text-blue-600">Admin: admin@campusgpt.edu</p>
                            <p className="text-xs text-blue-600">Password: any (demo mode)</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
