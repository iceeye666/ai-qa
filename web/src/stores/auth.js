import { defineStore } from 'pinia'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    loading: false
  }),
  getters: {
    isLogin: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    nickname: (state) => state.user?.nickname || state.user?.username || '未登录'
  },
  actions: {
    async login(username, password) {
      this.loading = true
      try {
        const data = await authApi.login(username, password)
        this.token = data.access_token
        localStorage.setItem('token', this.token)
        await this.fetchMe()
        return true
      } finally {
        this.loading = false
      }
    },
    async fetchMe() {
      try {
        this.user = await authApi.me()
        localStorage.setItem('user', JSON.stringify(this.user))
      } catch (e) {
        this.logout()
      }
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
