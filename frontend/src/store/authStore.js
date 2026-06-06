import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authAPI } from '../lib/api'

const useAuthStore = create(
  persist(
    (set, get) => ({
      user:         null,
      userType:     null,   // 'student' | 'admin'
      accessToken:  null,
      refreshToken: null,
      isLoading:    false,
      error:        null,

      login: async (email, password, userType = 'student') => {
        set({ isLoading: true, error: null })
        try {
          const { data } = await authAPI.login({ email, password, user_type: userType })
          localStorage.setItem('access_token',  data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          set({
            user:         data.user,
            userType:     data.user_type,
            accessToken:  data.access_token,
            refreshToken: data.refresh_token,
            isLoading:    false,
          })
          return { success: true }
        } catch (err) {
          const msg = err.response?.data?.detail || 'Login failed'
          set({ error: msg, isLoading: false })
          return { success: false, error: msg }
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        set({ user: null, userType: null, accessToken: null, refreshToken: null })
      },

      setUser: (user) => set({ user }),

      isAuthenticated: () => !!get().accessToken,
      isAdmin:         () => get().userType === 'admin',
      isStudent:       () => get().userType === 'student',
    }),
    {
      name:    'campus-auth',
      partialize: (s) => ({
        user:         s.user,
        userType:     s.userType,
        accessToken:  s.accessToken,
        refreshToken: s.refreshToken,
      }),
    }
  )
)

export default useAuthStore
