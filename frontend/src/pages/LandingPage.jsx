import { Link } from 'react-router-dom'
import { GraduationCap, MessageSquare, BarChart3, Shield, Zap, Globe, ChevronRight, Star } from 'lucide-react'

const FEATURES = [
    { icon: MessageSquare, title: 'AI Policy Navigator', desc: 'Ask questions about attendance, exams, hostel rules & more. Get instant, cited answers from official documents.', color: 'bg-blue-50 text-blue-600' },
    { icon: BarChart3, title: 'Smart Dashboard', desc: 'Track attendance trends, fee dues, hostel payments, scholarship status and fines in a single clean view.', color: 'bg-green-50 text-green-600' },
    { icon: Shield, title: 'Secure & Private', desc: 'JWT-protected authentication, role-based access control, and no data shared outside the campus system.', color: 'bg-purple-50 text-purple-600' },
    { icon: Zap, title: 'Personalized AI', desc: 'The AI combines your personal academic data with policy knowledge for context-aware, accurate responses.', color: 'bg-yellow-50 text-yellow-600' },
    { icon: Globe, title: 'Hindi & Hinglish', desc: 'Fully multilingual – ask questions in Hindi, Hinglish, or English and get responses in your preferred language.', color: 'bg-pink-50 text-pink-600' },
    { icon: GraduationCap, title: 'Complete ERP', desc: 'Attendance, fees, hostel, scholarships, fines, and notifications – everything you need in one platform.', color: 'bg-orange-50 text-orange-600' },
]

export default function LandingPage() {
    return (
        <div className="min-h-screen bg-white">
            {/* Nav */}
            <nav className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-100 px-6 py-4">
                <div className="max-w-6xl mx-auto flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-600 to-blue-500 flex items-center justify-center">
                            <GraduationCap className="w-4 h-4 text-white" />
                        </div>
                        <span className="font-bold text-gray-900">CampusGPT</span>
                    </div>
                    <Link to="/login" className="btn-primary text-sm py-2 px-4">
                        Sign In <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                </div>
            </nav>

            {/* Hero */}
            <section className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center">
                <span className="inline-flex items-center gap-2 px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm font-medium mb-6">
                    <Zap className="w-3.5 h-3.5" /> Powered by Gemini AI
                </span>
                <h1 className="text-5xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
                    Your AI-Powered<br />
                    <span className="text-gradient">Campus Copilot</span>
                </h1>
                <p className="text-xl text-gray-500 max-w-2xl mx-auto mb-8">
                    Ask questions in Hindi, Hinglish, or English. Get instant answers from official college policies.
                    Track attendance, fees, hostel, and scholarships — all in one place.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <Link to="/login" className="btn-primary py-3 px-8 text-base">
                        Get Started Free <ChevronRight className="w-4 h-4" />
                    </Link>
                    <a href="#features" className="btn-secondary py-3 px-8 text-base">
                        See Features
                    </a>
                </div>

                {/* Hero screenshot mockup */}
                <div className="mt-16 relative">
                    <div className="bg-gradient-to-b from-gray-900 to-gray-800 rounded-2xl shadow-2xl p-4 text-left max-w-3xl mx-auto">
                        <div className="flex gap-1.5 mb-3">
                            {['#ff5f57', '#febc2e', '#28c840'].map(c => (
                                <div key={c} className="w-3 h-3 rounded-full" style={{ background: c }} />
                            ))}
                        </div>
                        <div className="bg-gray-800 rounded-xl p-4 space-y-3 text-sm">
                            <div className="flex gap-3">
                                <div className="w-7 h-7 rounded-full bg-gray-600 flex-shrink-0" />
                                <div className="bg-gray-700 rounded-2xl px-3 py-2 text-gray-200 max-w-xs">
                                    What is the minimum attendance required?
                                </div>
                            </div>
                            <div className="flex gap-3 flex-row-reverse">
                                <div className="w-7 h-7 rounded-full bg-primary-600 flex-shrink-0 flex items-center justify-center">
                                    <GraduationCap className="w-3.5 h-3.5 text-white" />
                                </div>
                                <div className="bg-primary-600 rounded-2xl px-3 py-2 text-white max-w-sm text-xs leading-relaxed">
                                    According to the Attendance Policy, students must maintain a minimum of <strong>75% attendance</strong> in each subject to be eligible for examinations.
                                    <div className="mt-1.5 pt-1.5 border-t border-primary-500 text-primary-200 text-xs">
                                        📄 Source: Attendance Policy 2024-25
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features */}
            <section id="features" className="max-w-6xl mx-auto px-6 py-16">
                <h2 className="text-3xl font-bold text-center text-gray-900 mb-3">Everything in One Place</h2>
                <p className="text-center text-gray-500 mb-12">A complete student information system with AI at its core</p>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    {FEATURES.map(({ icon: Icon, title, desc, color }) => (
                        <div key={title} className="card-hover">
                            <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center mb-4`}>
                                <Icon className="w-5 h-5" />
                            </div>
                            <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
                            <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* CTA */}
            <section className="bg-gradient-to-br from-primary-600 to-blue-500 py-16 px-6 text-center">
                <h2 className="text-3xl font-bold text-white mb-4">Ready to get started?</h2>
                <p className="text-blue-100 mb-8 text-lg">Join thousands of students managing their campus life smarter</p>
                <Link to="/login" className="inline-flex items-center gap-2 bg-white text-primary-700 font-semibold py-3 px-8 rounded-xl hover:bg-blue-50 transition-colors text-base">
                    Open CampusGPT <ChevronRight className="w-4 h-4" />
                </Link>
            </section>

            {/* Footer */}
            <footer className="text-center py-8 text-sm text-gray-400 border-t border-gray-100">
                <p>© 2025 CampusGPT · AI Student Copilot · Built with Gemini AI + FastAPI + React</p>
            </footer>
        </div>
    )
}
