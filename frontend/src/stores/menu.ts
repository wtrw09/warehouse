import { defineStore } from 'pinia'
import { ref } from 'vue'

// 定义用户类型接口
export interface User {
  username: string
  [key: string]: any
}

export const useMenuStore = defineStore('menu', () => {
  // 状态定义
  const defaultOpenKeys = ref<string[]>([])
  const currentUser = ref<User | null>(null)
  
  // 设置当前用户
  const setCurrentUser = (user: User | null): void => {
    currentUser.value = user
    // 用户切换时初始化菜单状态
    if (user) {
      initializeMenuState()
    }
  }
  
  // 保存菜单状态
const saveMenuState = (): void => {
  // 不再保存到localStorage
  console.log('菜单状态保存功能已禁用')
}

// 恢复菜单状态
const restoreMenuState = (): void => {
  // 不再从localStorage恢复
  console.log('菜单状态恢复功能已禁用')
}
  
  // 展开菜单
const openMenu = (index: string): void => {
  if (!index || typeof index !== 'string') {
    console.warn('无效的菜单索引:', index)
    return
  }
  
  if (!defaultOpenKeys.value.includes(index)) {
    defaultOpenKeys.value.push(index)
    // 不再自动保存菜单状态
    console.log('菜单展开:', index)
  }
}

// 折叠菜单
const closeMenu = (index: string): void => {
  if (!index || typeof index !== 'string') {
    console.warn('无效的菜单索引:', index)
    return
  }
  
  const indexToRemove = defaultOpenKeys.value.indexOf(index)
  if (indexToRemove > -1) {
    defaultOpenKeys.value.splice(indexToRemove, 1)
    // 不再自动保存菜单状态
    console.log('菜单折叠:', index)
  }
}
  
  // 初始化菜单状态
const initializeMenuState = (): void => {
  try {
    // 设置默认展开的菜单项：出入库管理（索引为'2'）
    defaultOpenKeys.value = ['2'] // 默认展开出入库管理菜单，同时显示主页
    // console.log('菜单状态初始化完成，默认展开出入库管理菜单，显示主页')
  } catch (error) {
    // console.error('初始化菜单状态失败:', error)
    // 失败时使用安全的默认值
    defaultOpenKeys.value = ['2']
  }
}
  
  return {
    defaultOpenKeys,
    currentUser,
    setCurrentUser,
    saveMenuState,
    restoreMenuState,
    openMenu,
    closeMenu,
    initializeMenuState
  }
})