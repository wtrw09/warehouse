import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UserInfo } from '@/services/types/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref<UserInfo | null>(null)
  const token = ref<string>('')

  // 计算属性：用户信息（包含权限和角色）
  const userInfo = ref<{
    permissions: string[]
    roles: string[]
    [key: string]: any
  } | null>(null)

  const setUser = (userData: UserInfo) => {
    user.value = userData
    // 设置权限和角色信息
    userInfo.value = {
      ...userData
    }
  }

  const setToken = (newToken: string) => {
    token.value = newToken
  }

  const clearUser = () => {
    user.value = null
    token.value = ''
    userInfo.value = null
  }

  return {
    user,
    token,
    userInfo,
    setUser,
    setToken,
    clearUser
  }
})