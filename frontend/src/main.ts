import { createApp } from 'vue'
import './style.css'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.ts'

const app = createApp(App)
const pinia = createPinia()

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn
})

// 全局配置Element Plus消息组件
import { ElMessage } from 'element-plus'

// 重写ElMessage.error方法，设置默认不自动关闭
const originalError = ElMessage.error
ElMessage.error = (options) => {
  if (typeof options === 'string') {
    return originalError({
      message: options,
      showClose: true,
      duration: 8000
    })
  } else if (typeof options === 'object') {
    return originalError({
      ...options,
      showClose: true,
      duration: 8000
    })
  }
  return originalError(options)
}

// 初始化Redis状态定时检查
import { useRedisStatus } from './stores/redisStatus'

// 在应用挂载前启动定时检查
app.mount('#app')

// 全局Redis状态检查启动函数
window.startRedisStatusCheck = async () => {
  console.log('启动Redis状态检查...')
  try {
    // 强制从服务器获取最新的认证策略信息，避免使用缓存
    const { forceCheckRedisStatus } = useRedisStatus()
    const status = await forceCheckRedisStatus()
    
    if (status.auth_strategy === 'sliding_session') {
      console.log('当前认证策略为滑动会话模式，启动Redis状态检查')
      const { startPeriodicCheck } = useRedisStatus()
      startPeriodicCheck()
      console.log('Redis状态检查已启动')
    } else {
      console.log('当前认证策略为JWT固定模式，跳过Redis状态检查')
    }
  } catch (error) {
    console.error('启动Redis状态检查失败:', error)
  }
}

