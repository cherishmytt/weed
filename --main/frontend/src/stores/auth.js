import { defineStore } from 'pinia'

import { authApi } from '@/api/service'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('fire-token') || '',
    profile: JSON.parse(localStorage.getItem('fire-profile') || 'null'),
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    isAdmin: (state) => state.profile?.role === 'admin',
  },
  actions: {
    setSession(token, profile) {
      this.token = token
      this.profile = profile
      localStorage.setItem('fire-token', token)
      localStorage.setItem('fire-profile', JSON.stringify(profile))
    },
    clearSession() {
      this.token = ''
      this.profile = null
      localStorage.removeItem('fire-token')
      localStorage.removeItem('fire-profile')
    },
    async login(payload) {
      const data = await authApi.login(payload)
      localStorage.setItem('fire-token', data.access_token)
      this.token = data.access_token
      const profile = await authApi.profile()
      this.profile = profile
      localStorage.setItem('fire-profile', JSON.stringify(profile))
      return profile
    },
    async fetchProfile() {
      if (!this.token) return null
      const profile = await authApi.profile()
      this.profile = profile
      localStorage.setItem('fire-profile', JSON.stringify(profile))
      return profile
    },
  },
})
