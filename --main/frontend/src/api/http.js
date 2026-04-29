import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8002',
  timeout: 60000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('fire-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

const normalizeErrorMessage = (payload) => {
  if (Array.isArray(payload)) {
    const messages = payload
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          const field = Array.isArray(item.loc)
            ? item.loc.filter((part) => part !== 'body').slice(-1)[0]
            : ''
          return field ? `${field}：${item.msg || '输入不正确'}` : item.msg
        }
        return ''
      })
      .filter(Boolean)
    return messages.join('；') || '请求失败'
  }

  if (typeof payload === 'string') return payload

  if (payload && typeof payload === 'object') {
    if (typeof payload.detail === 'string') return payload.detail
    if (typeof payload.message === 'string') return payload.message
  }

  return '请求失败'
}

http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const isTimeout = error?.code === 'ECONNABORTED' || String(error?.message || '').includes('timeout')
    const message = isTimeout
      ? '请求耗时较长，请稍后重试'
      : normalizeErrorMessage(error?.response?.data?.detail ?? error?.response?.data ?? error.message)
    if (error?.response?.status === 401) {
      localStorage.removeItem('fire-token')
      localStorage.removeItem('fire-profile')
      if (location.pathname !== '/login') {
        location.href = '/login'
      }
    }
    if (!error?.config?.silent) {
      ElMessage.error(message || '请求失败')
    }
    return Promise.reject(error)
  },
)

export default http
