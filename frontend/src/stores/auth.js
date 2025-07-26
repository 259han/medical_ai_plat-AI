import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token') || null)

  const isAuthenticated = computed(() => !!token.value)

  const login = async (credentials) => {
    try {
      const response = await api.post('/auth/login', credentials)
      const { token: newToken, user: userData } = response.data
      
      token.value = newToken
      user.value = userData
      localStorage.setItem('token', newToken)
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || '登录失败' 
      }
    }
  }

  const register = async (userData) => {
    try {
      const response = await api.post('/auth/register', userData)
      const { token: newToken, user: userInfo } = response.data
      
      token.value = newToken
      user.value = userInfo
      localStorage.setItem('token', newToken)
      
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || '注册失败' 
      }
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  const fetchProfile = async () => {
    try {
      const response = await api.get('/user/profile')
      user.value = response.data
      return { success: true }
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || '获取用户信息失败' 
      }
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    login,
    register,
    logout,
    fetchProfile
  }
}) 