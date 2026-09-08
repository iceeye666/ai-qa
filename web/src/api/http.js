import axios from 'axios'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 60000
})

// 请求拦截：自动携带 JWT
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截：统一剥壳 + 401 自动登出
http.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (!location.hash.startsWith('#/login')) {
        location.hash = '#/login'
      }
    }
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      '请求失败'
    return Promise.reject(new Error(typeof message === 'string' ? message : JSON.stringify(message)))
  }
)

export default http
