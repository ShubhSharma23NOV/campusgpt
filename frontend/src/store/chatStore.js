import { create } from 'zustand'
import { aiAPI } from '../lib/api'

// Simple UUID generator (no external dependency)
const genId = () => Math.random().toString(36).slice(2) + Date.now().toString(36)

const useChatStore = create((set, get) => ({
  messages:  [],
  sessionId: null,
  isLoading: false,
  mode:      'policy',  // 'policy' | 'personalized'
  language:  'english',
  error:     null,

  setMode:     (mode)     => set({ mode }),
  setLanguage: (language) => set({ language }),

  initSession: () => {
    if (!get().sessionId) set({ sessionId: genId() })
  },

  sendMessage: async (question) => {
    if (!question.trim()) return

    const { sessionId, mode, language } = get()
    const sid = sessionId || genId()

    // Optimistically add user message
    set((s) => ({
      sessionId: sid,
      messages: [...s.messages, { id: genId(), role: 'user', content: question }],
      isLoading: true,
      error: null,
    }))

    try {
      const { data } = await aiAPI.chat({
        question,
        session_id: sid,
        mode,
        language,
      })

      set((s) => ({
        messages: [
          ...s.messages,
          {
            id:          genId(),
            role:        'assistant',
            content:     data.answer,
            sources:     data.sources || [],
            wasAnswered: data.was_answered,
            responseTime: data.response_time,
          },
        ],
        isLoading: false,
      }))
    } catch (err) {
      set((s) => ({
        messages: [
          ...s.messages,
          {
            id:      genId(),
            role:    'assistant',
            content: 'Something went wrong. Please try again.',
            sources: [],
            isError: true,
          },
        ],
        isLoading: false,
        error: err.message,
      }))
    }
  },

  clearChat: () => {
    const { sessionId } = get()
    if (sessionId) aiAPI.clearHistory(sessionId).catch(() => {})
    set({ messages: [], sessionId: genId() })
  },
}))

export default useChatStore
