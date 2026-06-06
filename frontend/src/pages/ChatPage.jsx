import { useState, useRef, useEffect } from 'react'
import useChatStore from '../store/chatStore'
import useAuthStore from '../store/authStore'
import {
    Send, Mic, MicOff, Trash2, Bot, User2, Loader2,
    ChevronDown, Globe, RefreshCw, BookOpen, Sparkles
} from 'lucide-react'

const SUGGESTIONS = [
    'What is the minimum attendance required?',
    'What happens if attendance falls below 75%?',
    'What are the hostel timing rules?',
    'How can I apply for scholarships?',
    'What is the examination eligibility criteria?',
    'What are the fine rules for late fee payment?',
]

export default function ChatPage() {
    const [input, setInput] = useState('')
    const [listening, setListening] = useState(false)
    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)

    const { messages, isLoading, mode, language, setMode, setLanguage, sendMessage, clearChat, initSession } = useChatStore()
    const { userType } = useAuthStore()

    useEffect(() => { initSession() }, [])
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages, isLoading])

    const handleSend = async () => {
        if (!input.trim() || isLoading) return
        const q = input.trim()
        setInput('')
        await sendMessage(q)
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
    }

    const startVoice = () => {
        if (!('webkitSpeechRecognition' in window)) {
            alert('Speech recognition not supported in this browser.')
            return
        }
        const recognition = new window.webkitSpeechRecognition()
        recognition.lang = language === 'hi' ? 'hi-IN' : 'en-IN'
        recognition.interimResults = false
        recognition.onstart = () => setListening(true)
        recognition.onresult = (e) => setInput(e.results[0][0].transcript)
        recognition.onend = () => setListening(false)
        recognition.start()
    }

    return (
        <div className="flex flex-col h-[calc(100vh-3.5rem-3rem)] max-h-[800px] animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div>
                    <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                        <Bot className="w-5 h-5 text-primary-600" />
                        AI Assistant
                    </h1>
                    <p className="text-xs text-gray-500 mt-0.5">Powered by Gemini AI + Campus Policy Documents</p>
                </div>

                <div className="flex items-center gap-2">
                    {/* Mode toggle */}
                    {userType === 'student' && (
                        <select
                            value={mode}
                            onChange={e => setMode(e.target.value)}
                            className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-primary-400"
                        >
                            <option value="policy">📋 Policy Mode</option>
                            <option value="personalized">👤 My Data Mode</option>
                        </select>
                    )}

                    {/* Language toggle */}
                    <select
                        value={language}
                        onChange={e => setLanguage(e.target.value)}
                        className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-primary-400"
                    >
                        <option value="english">🇬🇧 English</option>
                        <option value="hindi">🇮🇳 Hindi</option>
                        <option value="hinglish">🔀 Hinglish</option>
                    </select>

                    <button onClick={clearChat} className="btn-ghost text-gray-400 hover:text-red-500" title="Clear chat">
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Mode info banner */}
            {mode === 'personalized' && (
                <div className="mb-3 px-3 py-2 bg-primary-50 border border-primary-100 rounded-lg text-xs text-primary-700 flex items-center gap-2">
                    <Sparkles className="w-3.5 h-3.5 flex-shrink-0" />
                    Personalized mode: AI uses your attendance, fees, hostel, and scholarship data for accurate answers.
                </div>
            )}

            {/* Messages area */}
            <div className="flex-1 overflow-y-auto bg-gray-50 rounded-xl border border-gray-100 p-4 space-y-4">
                {messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-center py-8">
                        <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center mb-4">
                            <Bot className="w-8 h-8 text-primary-600" />
                        </div>
                        <h3 className="font-semibold text-gray-900 mb-1">How can I help you today?</h3>
                        <p className="text-sm text-gray-500 mb-6 max-w-sm">
                            Ask me anything about campus policies, your attendance, fees, hostel, or scholarships.
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
                            {SUGGESTIONS.map((s) => (
                                <button
                                    key={s}
                                    onClick={() => { setInput(s); inputRef.current?.focus() }}
                                    className="text-left text-xs px-3 py-2.5 bg-white border border-gray-200 rounded-xl hover:border-primary-300 hover:bg-primary-50 transition-colors"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <>
                        {messages.map((msg) => (
                            <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                {/* Avatar */}
                                <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-primary-600' : 'bg-white border border-gray-200'
                                    }`}>
                                    {msg.role === 'user'
                                        ? <User2 className="w-3.5 h-3.5 text-white" />
                                        : <Bot className="w-3.5 h-3.5 text-primary-600" />
                                    }
                                </div>

                                {/* Bubble */}
                                <div className={msg.role === 'user' ? 'chat-user' : 'chat-bot'}>
                                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                                    {/* Sources */}
                                    {msg.sources?.length > 0 && (
                                        <div className="mt-2 pt-2 border-t border-gray-100">
                                            <p className="text-xs text-gray-400 mb-1 flex items-center gap-1">
                                                <BookOpen className="w-3 h-3" /> Sources:
                                            </p>
                                            {msg.sources.map((src, i) => (
                                                <span key={i} className="inline-block text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full mr-1 mb-1">
                                                    {src.title}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    {msg.responseTime && (
                                        <p className="text-xs text-gray-300 mt-1">{msg.responseTime.toFixed(2)}s</p>
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* Loading indicator */}
                        {isLoading && (
                            <div className="flex gap-3">
                                <div className="w-7 h-7 rounded-full bg-white border border-gray-200 flex items-center justify-center">
                                    <Bot className="w-3.5 h-3.5 text-primary-600" />
                                </div>
                                <div className="chat-bot">
                                    <div className="flex gap-1 items-center py-1">
                                        {[0, 1, 2].map(i => (
                                            <div
                                                key={i}
                                                className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                                style={{ animationDelay: `${i * 0.15}s` }}
                                            />
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </>
                )}
            </div>

            {/* Input area */}
            <div className="mt-3 bg-white rounded-xl border border-gray-200 shadow-sm">
                <div className="flex items-end gap-2 p-3">
                    <textarea
                        ref={inputRef}
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={`Ask about ${mode === 'personalized' ? 'your data or ' : ''}campus policies…`}
                        rows={1}
                        className="flex-1 resize-none text-sm text-gray-900 placeholder:text-gray-400 outline-none bg-transparent max-h-28 overflow-y-auto"
                    />
                    <div className="flex items-center gap-1 flex-shrink-0">
                        <button
                            onClick={startVoice}
                            className={`p-2 rounded-lg transition-colors ${listening ? 'bg-red-50 text-red-500' : 'text-gray-400 hover:bg-gray-100'}`}
                            title="Voice input"
                        >
                            {listening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                        </button>
                        <button
                            onClick={handleSend}
                            disabled={!input.trim() || isLoading}
                            className="p-2 rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                        >
                            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        </button>
                    </div>
                </div>
                <p className="px-3 pb-2 text-xs text-gray-400">
                    Press Enter to send · Shift+Enter for new line
                </p>
            </div>
        </div>
    )
}
