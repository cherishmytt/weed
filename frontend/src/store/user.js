import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getToken, removeToken } from '@/utils/auth'

// 从 localStorage 获取用户信息
function getUserInfoFromStorage() {
  try {
    const userInfo = localStorage.getItem('lwr-user-info')
    return userInfo ? JSON.parse(userInfo) : null
  } catch (e) {
    console.error('Failed to get user info from storage:', e)
    return null
  }
}

export const useUserStore = defineStore('user', () => {
  const token = ref(getToken() || '')
  const userInfo = getUserInfoFromStorage()
  const userId = ref(userInfo?.userId || null)
  const username = ref(userInfo?.username || '')
  const role = ref(userInfo?.role || '')

  const isLoggedIn = computed(() => !!token.value)

  function setUserInfo(info) {
    userId.value = info.userId
    username.value = info.username
    role.value = info.role
    // 持久化用户信息到 localStorage
    localStorage.setItem('lwr-user-info', JSON.stringify({
      userId: info.userId,
      username: info.username,
      role: info.role
    }))
  }

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('lwr-token', newToken)
  }

  function logout() {
    token.value = ''
    userId.value = null
    username.value = ''
    role.value = ''
    removeToken()
    // 清除 localStorage 中的用户信息
    localStorage.removeItem('lwr-user-info')
  }

  return {
    token,
    userId,
    username,
    role,
    isLoggedIn,
    setUserInfo,
    setToken,
    logout
  }
})
