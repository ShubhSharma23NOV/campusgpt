/**
 * Axios API client with JWT interceptors
 */
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: attach JWT ──────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (err) => Promise.reject(err)
)

// ── Response interceptor: refresh on 401 ─────────────────
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          localStorage.setItem('access_token', data.access_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(err)
  }
)

export default api

// ── Named API helpers ─────────────────────────────────────

export const authAPI = {
  login:          (data) => api.post('/auth/login', data),
  logout:         ()     => api.post('/auth/logout'),
  refresh:        (data) => api.post('/auth/refresh', data),
  getMe:          ()     => api.get('/auth/me'),
  changePassword: (data) => api.put('/auth/change-password', data),
}

export const attendanceAPI = {
  getMy:      (year) => api.get('/attendance/my', { params: { academic_year: year } }),
  getTrend:   (days) => api.get('/attendance/my/trend', { params: { days } }),
  getSubject: (id)   => api.get(`/attendance/my/subject/${id}`),
}

export const feesAPI = {
  getMy:     (year) => api.get('/fees/my', { params: { academic_year: year } }),
  getHistory: ()    => api.get('/fees/my/history'),
}

export const hostelAPI = {
  getMy: () => api.get('/hostel/my'),
}

export const scholarshipAPI = {
  list:  (year) => api.get('/scholarships', { params: { academic_year: year } }),
  getMy: (year) => api.get('/scholarships/my', { params: { academic_year: year } }),
  apply: (id)   => api.post(`/scholarships/apply/${id}`),
}

export const finesAPI = {
  getMy: () => api.get('/fines/my'),
}

export const notificationsAPI = {
  getMy:      (unread) => api.get('/notifications/my', { params: { unread_only: unread } }),
  markRead:   (id)     => api.post(`/notifications/${id}/read`),
  markAllRead: ()      => api.post('/notifications/read-all'),
}

export const aiAPI = {
  chat:              (data) => api.post('/ai/chat', data),
  getHistory:        (sid)  => api.get(`/ai/chat/history/${sid}`),
  clearHistory:      (sid)  => api.delete(`/ai/chat/history/${sid}`),
  getAttendanceAdvice: ()   => api.get('/ai/attendance-advice'),
  summarizePolicy:   (id)   => api.post(`/ai/summarize-policy/${id}`),
}

export const policiesAPI = {
  list:   (cat)  => api.get('/policies', { params: { category: cat } }),
  get:    (id)   => api.get(`/policies/${id}`),
  upload: (data) => api.post('/policies/upload', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  delete:  (id)  => api.delete(`/policies/${id}`),
  reindex: (id)  => api.post(`/policies/${id}/reindex`),
}

export const adminAPI = {
  dashboard:            (year) => api.get('/admin/dashboard', { params: { academic_year: year } }),
  attendanceDistrib:    (year) => api.get('/admin/analytics/attendance-distribution', { params: { academic_year: year } }),
  feeCollectionTrend:   ()     => api.get('/admin/analytics/fee-collection'),
  listStudents:         (p)    => api.get('/students', { params: p }),
  createStudent:        (data) => api.post('/students', data),
  getStudent:           (id)   => api.get(`/students/${id}`),
  markAttendance:       (data) => api.post('/attendance/mark', data),
  recordFeePayment:     (data) => api.post('/fees/pay', data),
  createFine:           (data) => api.post('/fines', data),
  payFine:              (data) => api.post('/fines/pay', data),
  broadcast:            (data) => api.post('/notifications/broadcast', data),
}
