/**
 * Redis状态全局状态管理
 * 用于存储和管理Redis服务器的状态信息
 */
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { systemAPI } from '../services/system/system'

// Redis状态接口
export interface RedisStatus {
  status: 'success' | 'error' | 'unknown'
  message: string
  redis_available: boolean
  fallback_active: boolean
  last_check: number
  auth_strategy?: string
  redis_version?: string
  connected_clients?: number
  used_memory?: string
  fallback_sessions_count?: number
  error?: boolean
}

// 检查间隔（30分钟）
const CHECK_INTERVAL = 30 * 60 * 1000

// 默认状态
const defaultStatus: RedisStatus = {
  status: 'unknown',
  message: '未检查Redis状态',
  redis_available: false,
  fallback_active: false,
  last_check: 0
}

// 响应式状态
const redisStatus = ref<RedisStatus>(loadFromLocalStorage())

// 从localStorage加载状态
function loadFromLocalStorage(): RedisStatus {
  try {
    const stored = localStorage.getItem('redis_status')
    if (stored) {
      const parsed = JSON.parse(stored)
      // 检查是否过期（超过30分钟）
      const currentTime = Date.now()
      if (currentTime - parsed.last_check < CHECK_INTERVAL) {
        return parsed
      }
    }
  } catch (error) {
    console.error('加载Redis状态失败:', error)
  }
  return defaultStatus
}

// 保存状态到localStorage
function saveToLocalStorage(status: RedisStatus) {
  try {
    localStorage.setItem('redis_status', JSON.stringify(status))
    localStorage.setItem('last_redis_check', status.last_check.toString())
  } catch (error) {
    console.error('保存Redis状态失败:', error)
  }
}

// 检查Redis状态
async function checkRedisStatus(): Promise<RedisStatus> {
  try {
    const response = await systemAPI.config.testRedisStatus()
    
    const newStatus: RedisStatus = {
      status: response.status as 'success' | 'error' | 'unknown',
      message: response.message,
      redis_available: response.redis_available,
      fallback_active: response.fallback_active,
      last_check: Date.now(),
      auth_strategy: response.auth_strategy,
      redis_version: response.redis_version,
      connected_clients: response.connected_clients,
      used_memory: response.used_memory,
      fallback_sessions_count: response.fallback_sessions_count
    }
    
    redisStatus.value = newStatus
    saveToLocalStorage(newStatus)
    
    return newStatus
  } catch (error: any) {
    console.error('检查Redis状态失败:', error)
    
    const errorStatus: RedisStatus = {
      status: 'error',
      message: error.response?.data?.detail || error.message || '未知错误',
      redis_available: false,
      fallback_active: true,
      last_check: Date.now(),
      error: true
    }
    
    redisStatus.value = errorStatus
    saveToLocalStorage(errorStatus)
    
    return errorStatus
  }
}

// 检查是否需要检查Redis状态
function shouldCheckRedisStatus(): boolean {
  const currentTime = Date.now()
  return currentTime - redisStatus.value.last_check > CHECK_INTERVAL
}

// 获取当前状态（如果需要检查则自动检查）
async function getRedisStatus(): Promise<RedisStatus> {
  if (shouldCheckRedisStatus()) {
    return await checkRedisStatus()
  }
  return redisStatus.value
}

// 强制检查Redis状态
async function forceCheckRedisStatus(): Promise<RedisStatus> {
  return await checkRedisStatus()
}

// 显示状态通知
function showStatusNotification(status: RedisStatus, isPeriodicCheck: boolean = false) {
  if (status.fallback_active) {
    // 备选模式激活时的提示
    if (isPeriodicCheck) {
      // 定时检查时的警告（不打扰用户，只在控制台显示）
      console.warn('定时检查: Redis服务器不可用，当前使用备选存储方案')
    } else {
      // 用户主动检查时的详细提示
      ElMessage.warning({
        message: status.message || 'Redis服务器当前不可用，已启用备选存储方案。',
        showClose: true,
        duration: 8000
      })
    }
  } else if (status.redis_available) {
    // Redis正常时的提示
    if (!isPeriodicCheck) {
      // 只在用户主动检查时显示成功消息
      ElMessage.success({
        message: status.message || 'Redis服务器连接正常。',
        showClose: true,
        duration: 5000
      })
    }
  } else {
    // Redis连接失败时的提示
    ElMessage.error({
        message: status.message || 'Redis服务器连接失败。',
        showClose: true,
        duration: 0 // 不自动关闭，需要用户手动关闭
      })
  }
}

// 显示全局状态横幅（用于页面顶部显示持久状态）
function showGlobalStatusBanner(status: RedisStatus) {
  // 移除可能存在的旧横幅
  const existingBanner = document.getElementById('redis-status-banner')
  if (existingBanner) {
    existingBanner.remove()
  }
  
  // 只有在备选模式激活时才显示横幅
  if (status.fallback_active) {
    // 使用Element Plus的错误消息框替代自定义横幅
    ElMessage.error({
      message: '⚠️ Redis服务器不可用，当前使用备选存储方案。部分功能可能受限。',
      showClose: true,
      duration: 0, // 不自动关闭，需要用户手动关闭
      customClass: 'redis-status-banner'
    })
    
    // 标记已显示横幅，避免重复显示
    const banner = document.createElement('div')
    banner.id = 'redis-status-banner'
    banner.style.display = 'none'
    document.body.appendChild(banner)
  } else {
    // 如果Redis恢复正常，移除横幅标记
    const existingBanner = document.getElementById('redis-status-banner')
    if (existingBanner) {
      existingBanner.remove()
    }
  }
}

// 定时检查相关
let checkInterval: number | null = null

// 启动定时检查
function startPeriodicCheck(interval: number = CHECK_INTERVAL) {
  if (checkInterval) {
    clearInterval(checkInterval)
  }
  
  // 立即执行一次检查
  checkRedisStatus().then(status => {
    showGlobalStatusBanner(status)
  })
  
  checkInterval = window.setInterval(async () => {
    try {
      console.log('执行定时Redis状态检查...')
      const status = await checkRedisStatus()
      
      // 显示状态通知（定时检查模式）
      showStatusNotification(status, true)
      
      // 更新全局状态横幅
      showGlobalStatusBanner(status)
    } catch (error) {
      console.error('定时检查Redis状态失败:', error)
    }
  }, interval)
}

// 停止定时检查
function stopPeriodicCheck() {
  if (checkInterval) {
    clearInterval(checkInterval)
    checkInterval = null
  }
}

// 计算属性
export const useRedisStatus = () => {
  const status = computed(() => redisStatus.value)
  const isRedisAvailable = computed(() => redisStatus.value.redis_available)
  const isFallbackActive = computed(() => redisStatus.value.fallback_active)
  const needsCheck = computed(() => shouldCheckRedisStatus())
  
  return {
    status,
    isRedisAvailable,
    isFallbackActive,
    needsCheck,
    checkRedisStatus,
    forceCheckRedisStatus,
    getRedisStatus,
    showStatusNotification,
    showGlobalStatusBanner,
    startPeriodicCheck,
    stopPeriodicCheck
  }
}

export default {
  useRedisStatus,
  checkRedisStatus,
  forceCheckRedisStatus,
  getRedisStatus,
  showStatusNotification
}