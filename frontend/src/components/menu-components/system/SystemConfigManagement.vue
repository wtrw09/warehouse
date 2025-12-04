<template>
  <div class="system-config-container">
    <!-- 权限检查 -->
    <el-alert
      v-if="!hasPermission('AUTH-read')"
      title="权限不足"
      type="error"
      :closable="false"
      show-icon
      class="system-permission-alert"
    >
      <template #default>
        <p>您没有足够的权限访问系统配置管理功能。</p>
        <p>需要权限：<el-tag type="danger">AUTH-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 系统配置内容 -->
    <div v-else class="system-content">
      <!-- 操作栏 -->
      <el-card class="system-operation-card" shadow="hover">
        <div class="system-operation-bar">
          <div class="system-operation-bar__left">
            <el-button 
              type="primary" 
              @click="refreshConfigs"
              :loading="loading"
              :icon="Refresh"
            >
              刷新配置
            </el-button>
            <el-button 
              type="success" 
              @click="saveAllConfigs"
              :disabled="!hasPermission('AUTH-edit') || !hasChanges"
              :loading="saving"
              :icon="Check"
            >
              保存所有更改
            </el-button>
            <el-button 
              type="default" 
              @click="resetChanges"
              :disabled="!hasChanges"
              :icon="RefreshLeft"
            >
              重置更改
            </el-button>
          </div>
          
          <div class="system-operation-bar__right">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索配置参数"
              style="width: 300px;"
              clearable
              @clear="handleClearSearch"
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button @click="handleSearch" :icon="Search">搜索</el-button>
              </template>
            </el-input>
          </div>
        </div>
      </el-card>

      <!-- 系统初始化状态 -->
      <el-card class="system-status-card" shadow="hover" v-if="systemStatus">
        <template #header>
          <div class="system-card-header">
            <el-icon><Setting /></el-icon>
            <span>系统状态</span>
          </div>
        </template>
        <div class="system-status-content">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="初始化状态">
              <el-tag :type="systemStatus.initialized ? 'success' : 'warning'">
                {{ systemStatus.initialized ? '已初始化' : '未初始化' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="初始化时间" v-if="systemStatus.initialized">
              {{ formatDateTime(systemStatus.init_time) }}
            </el-descriptions-item>
            <el-descriptions-item label="版本号" v-if="systemStatus.initialized">
              {{ systemStatus.init_version || '未知' }}
            </el-descriptions-item>
            <el-descriptions-item label="Redis状态">
              <el-tag :type="redisStatus ? 'success' : 'danger'">
                {{ redisStatus ? '已连接' : '未连接' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="操作">
              <el-button 
                v-if="!systemStatus.initialized && hasPermission('AUTH-edit')"
                type="primary" 
                size="small" 
                @click="initializeSystem"
                :loading="initializing"
              >
                初始化系统
              </el-button>
              <span v-else-if="!hasPermission('AUTH-edit')">无操作权限</span>
              <span v-else>系统已初始化</span>
            </el-descriptions-item>
            <el-descriptions-item label="Redis测试">
              <el-button 
                type="primary" 
                size="small" 
                @click="testRedisConnection"
                :loading="testingRedis"
              >
                测试Redis连接
              </el-button>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>

      <!-- 配置参数列表 -->
      <el-card class="system-configs-card" shadow="hover">
        <template #header>
          <div class="system-card-header">
            <el-icon><List /></el-icon>
            <span>系统配置参数</span>
            <div class="system-card-header__stats" v-if="configs.length > 0">
              <span>总计: {{ configs.length }}</span>
              <span v-if="hasChanges" class="changes-count">
                待保存更改: {{ changedConfigsCount }}
              </span>
            </div>
          </div>
        </template>

        <!-- 加载状态 -->
        <div v-if="loading" class="system-loading-container">
          <el-skeleton :rows="6" animated />
        </div>
        
        <!-- 错误状态 -->
        <el-alert
          v-else-if="error"
          :title="error"
          type="error"
          show-icon
          :closable="false"
          class="system-error-state"
        />
        
        <!-- 配置参数表格 -->
            <div v-else-if="configs.length > 0">
              <el-table 
                :data="filteredConfigs" 
                stripe 
                border
                :empty-text="'暂无配置数据'"
                class="system-table"
              >
                <el-table-column 
                  prop="config_name" 
                  label="配置名称" 
                  min-width="180"
                  align="center"
                  fixed="left"
                >
                  <template #default="{ row }">
                    <div class="config-name-cell">
                      <span class="config-name-text">{{ getConfigName(row.config_key) }}</span>
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column 
                  prop="config_key" 
                  label="配置键" 
                  min-width="200"
                  align="center"
                  show-overflow-tooltip
                >
                  <template #default="{ row }">
                    <div class="config-key-cell">
                      <span class="config-key-text">{{ row.config_key }}</span>
                      <el-tooltip 
                        v-if="row.description" 
                        :content="row.description" 
                        placement="top"
                      >
                        <el-icon class="config-description-icon"><InfoFilled /></el-icon>
                      </el-tooltip>
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column 
                  prop="config_type" 
                  label="类型" 
                  width="100"
                  align="center"
                >
                  <template #default="{ row }">
                    <el-tag :type="getTypeTagType(row.config_type)">
                      {{ row.config_type }}
                    </el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column 
                  prop="config_value" 
                  label="当前值" 
                  min-width="200"
                  align="center"
                >
                  <template #default="{ row }">
                    <span :class="{ 'config-value-changed': isConfigChanged(row) }">
                      {{ formatConfigValue(row) }}
                    </span>
                  </template>
                </el-table-column>
                
                <el-table-column 
                  label="新值" 
                  min-width="260"
                  align="center"
                >
                  <template #default="{ row }">
                    <!-- 隐藏SECRET_KEY、ALGORITHM、ADMIN_INVITATION_CODE三个配置项 -->
                    <div v-if="['SECRET_KEY', 'ALGORITHM', 'ADMIN_INVITATION_CODE'].includes(row.config_key)" class="config-readonly">
                      <el-tag type="info">不可修改</el-tag>
                    </div>
                    
                    <!-- 根据配置类型显示不同的输入组件 -->
                    <div v-else class="config-input-container">
                      <!-- 认证策略单选（优先级最高） -->
                      <el-radio-group
                        v-if="row.config_key === 'AUTH_STRATEGY'"
                        v-model="row.newValue"
                        size="small"
                        :disabled="!hasPermission('AUTH-edit')"
                        @change="handleConfigChange(row)"
                      >
                        <el-radio-button value="jwt_fixed">固定JWT</el-radio-button>
                        <el-radio-button value="sliding_session">滑动会话</el-radio-button>
                      </el-radio-group>
                      
                      <!-- 字符串类型 -->
                      <el-input
                        v-else-if="row.config_type === 'string'"
                        v-model="row.newValue"
                        :placeholder="`请输入${row.config_key}的值`"
                        size="small"
                        :disabled="!hasPermission('AUTH-edit')"
                        @change="handleConfigChange(row)"
                      />
                      
                      <!-- 整数类型 -->
                      <el-input-number
                        v-else-if="row.config_type === 'int'"
                        v-model="row.newValue"
                        :placeholder="`请输入${row.config_key}的值`"
                        size="small"
                        :min="getMinValue(row.config_key)"
                        :max="getMaxValue(row.config_key)"
                        :disabled="!hasPermission('AUTH-edit')"
                        @change="handleConfigChange(row)"
                      />
                      
                      <!-- 布尔类型 -->
                      <el-radio-group
                        v-else-if="row.config_type === 'bool'"
                        v-model="row.newValue"
                        size="small"
                        :disabled="!hasPermission('AUTH-edit')"
                        @change="handleConfigChange(row)"
                      >
                        <el-radio-button :value="true">true</el-radio-button>
                        <el-radio-button :value="false">false</el-radio-button>
                      </el-radio-group>
                      
                      <!-- 其他类型使用普通输入框 -->
                      <el-input
                        v-else
                        v-model="row.newValue"
                        :placeholder="`请输入${row.config_key}的值`"
                        size="small"
                        :disabled="!hasPermission('AUTH-edit')"
                        @change="handleConfigChange(row)"
                      />
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column 
                  prop="description" 
                  label="描述" 
                  min-width="300"
                  align="center"
                >
                  <template #default="{ row }">
                    <span class="config-description">{{ row.description }}</span>
                  </template>
                </el-table-column>
                
                <el-table-column 
                  label="操作" 
                  width="100" 
                  align="center" 
                  fixed="right"
                >
                  <template #default="{ row }">
                    <el-space>
                      <el-tooltip content="保存此配置" placement="top">
                        <el-button 
                          type="primary"
                          size="small"
                          @click="saveSingleConfig(row)"
                          :disabled="!hasPermission('AUTH-edit') || !isConfigChanged(row) || ['SECRET_KEY', 'ALGORITHM', 'ADMIN_INVITATION_CODE'].includes(row.config_key)"
                          :loading="row.saving"
                          :icon="Check"
                          circle
                        />
                      </el-tooltip>
                      <el-tooltip content="重置此配置" placement="top">
                        <el-button 
                          type="default"
                          size="small"
                          @click="resetSingleConfig(row)"
                          :disabled="!hasPermission('AUTH-edit') || !isConfigChanged(row) || ['SECRET_KEY', 'ALGORITHM', 'ADMIN_INVITATION_CODE'].includes(row.config_key)"
                          :icon="RefreshLeft"
                          circle
                        />
                      </el-tooltip>
                    </el-space>
                  </template>
                </el-table-column>
              </el-table>
            </div>
        
        <!-- 空状态 -->
        <div v-else class="system-empty-state">
          <el-empty description="暂无配置数据" />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, Check, RefreshLeft, Search, Setting, List, InfoFilled 
} from '@element-plus/icons-vue'
import { systemAPI } from '../../../services'
import { useRedisStatus } from '../../../stores/redisStatus'
import type { 
  SystemConfigResponse, 
  SystemStatusResponse,
  SystemConfigUpdate 
} from '../../../services/types/system'

const currentUser = inject<any>('currentUser') || ref<any | null>(null)

/**
 * 检查当前用户是否拥有指定权限
 * @param permission 权限名称字符串，如 'SYSTEM-read', 'AUTH-edit'
 * @returns boolean - 用户是否拥有该权限
 */
const hasPermission = (permission: string): boolean => {
  if (!currentUser.value || !currentUser.value.permissions) {
    // 如果没有用户信息或权限信息，尝试从localStorage获取
    const userData = localStorage.getItem('userData')
    if (userData) {
      try {
        const parsedUserData = JSON.parse(userData)
        return parsedUserData.permissions?.includes(permission) || false
      } catch (err) {
        console.error('解析用户数据失败:', err)
      }
    }
    return false
  }
  return currentUser.value.permissions.includes(permission)
}

// 状态管理
const loading = ref(false)
const saving = ref(false)
const initializing = ref(false)
const testingRedis = ref(false)
const error = ref<string | null>(null)
const systemStatus = ref<SystemStatusResponse | null>(null)
const configs = ref<SystemConfigResponse[]>([])
const redisStatus = ref<boolean>(false)

// 搜索和筛选
const searchKeyword = ref('')

// 计算属性
const filteredConfigs = computed(() => {
  // 首先过滤掉SECRET_KEY、ALGORITHM、ADMIN_INVITATION_CODE三个配置项
  const filtered = configs.value.filter((config: SystemConfigResponse) => 
    !['SECRET_KEY', 'ALGORITHM', 'ADMIN_INVITATION_CODE','DATABASE_URL'].includes(config.config_key)
  )
  
  if (!searchKeyword.value.trim()) {
    return filtered
  }
  const keyword = searchKeyword.value.toLowerCase()
  return filtered.filter((config: SystemConfigResponse) => 
    config.config_key.toLowerCase().includes(keyword) ||
    (config.description && config.description.toLowerCase().includes(keyword))
  )
})

const hasChanges = computed(() => {
  return configs.value.some(config => isConfigChanged(config))
})

const changedConfigsCount = computed(() => {
  return configs.value.filter((config: SystemConfigResponse & { newValue?: any }) => isConfigChanged(config)).length
})

// 检查配置是否已更改
const isConfigChanged = (config: SystemConfigResponse & { newValue?: any }) => {
  if (config.newValue === undefined) return false
  
  // 根据配置类型进行值比较
  switch (config.config_type) {
    case 'int':
      return parseInt(config.newValue) !== parseInt(config.config_value)
    case 'bool':
      return String(config.newValue).toLowerCase() !== String(config.config_value).toLowerCase()
    default:
      return config.newValue !== config.config_value
  }
}

// 格式化配置值显示
const formatConfigValue = (config: SystemConfigResponse) => {
  if (config.config_key === 'SECRET_KEY') {
    return '********' // 敏感信息隐藏
  }
  
  if (config.config_type === 'bool') {
    return config.config_value === 'true' ? 'true' : 'false'
  }
  
  return config.config_value
}

// 获取类型标签样式
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    'string': 'success',
    'int': 'warning',
    'bool': 'danger'
  }
  return typeMap[type] || 'info'
}

// 获取最小值限制
const getMinValue = (configKey: string) => {
  const minValues: Record<string, number> = {
    'ACCESS_TOKEN_EXPIRE_MINUTES': 1,
    'SLIDING_SESSION_TIMEOUT_MINUTES': 1,
    'ACCESS_TOKEN_SHORT_EXPIRE_MINUTES': 1
  }
  return minValues[configKey] || 0
}

// 获取最大值限制
const getMaxValue = (configKey: string) => {
  const maxValues: Record<string, number> = {
    'ACCESS_TOKEN_EXPIRE_MINUTES': 1440, // 24小时
    'SLIDING_SESSION_TIMEOUT_MINUTES': 10080, // 7天
    'ACCESS_TOKEN_SHORT_EXPIRE_MINUTES': 60 // 1小时
  }
  return maxValues[configKey] || 1000000
}

// 根据配置键生成中文名称
const getConfigName = (configKey: string) => {
  const nameMap: Record<string, string> = {
    'SECRET_KEY': '密钥',
    'ALGORITHM': '算法',
    'AUTH_STRATEGY': '认证策略',
    'ACCESS_TOKEN_EXPIRE_MINUTES': '访问令牌过期时间',
    'SLIDING_SESSION_TIMEOUT_MINUTES': '滑动会话超时时间',
    'ACCESS_TOKEN_SHORT_EXPIRE_MINUTES': '短期访问令牌过期时间',
    'ADMIN_INVITATION_CODE': '管理员邀请码',
    'REDIS_URL': 'Redis连接地址'
  }
  return nameMap[configKey] || configKey
}

// 处理配置变更
const handleConfigChange = (config: SystemConfigResponse & { newValue?: any }) => {
  console.log(`配置 ${config.config_key} 值变更为:`, config.newValue)
}

// 加载系统状态和配置
const loadSystemStatus = async () => {
  console.log('开始加载系统状态和配置...');
  try {
    // 获取系统初始化状态
    const initStatus = await systemAPI.config.getSystemInitStatus();
    console.log('系统初始化状态API响应:', initStatus);
    
    // 设置系统状态
    systemStatus.value = {
      initialized: initStatus.initialized,
      init_time: initStatus.init_time,
      init_version: initStatus.init_version
    };
    
    console.log('系统初始化状态加载成功:', systemStatus.value);
    
    // 获取系统配置
    const configResponse = await systemAPI.config.getSystemConfig();
    console.log('系统配置API响应:', configResponse);
    
    // 后端返回的是包含configs和total的对象，我们需要提取configs数组
    if (configResponse && configResponse.configs) {
      // 为每个配置项添加newValue属性用于编辑，并根据配置类型进行类型转换
      configs.value = configResponse.configs.map((config: SystemConfigResponse) => {
        let convertedValue: any = config.config_value;
        
        // 根据配置类型转换值
        switch (config.config_type) {
          case 'int':
            convertedValue = parseInt(config.config_value) || 0;
            break;
          case 'bool':
            convertedValue = config.config_value === 'true';
            break;
          default:
            // 字符串类型保持原样
            convertedValue = config.config_value;
        }
        
        return {
          ...config,
          newValue: convertedValue
        };
      });
      console.log('系统配置加载成功，共', configResponse.total, '项配置:', configs.value);
    } else {
      console.warn('API响应中缺少configs字段:', configResponse);
      ElMessage.warning('系统配置数据格式异常');
    }
  } catch (error) {
    console.error('加载系统状态和配置失败:', error);
    ElMessage.error('加载系统状态和配置失败');
  }
};

// 加载系统配置
const loadConfigs = async () => {
  if (!hasPermission('AUTH-read')) {
    console.log('权限检查失败: 缺少AUTH-read权限')
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    console.log('开始加载系统配置...')
    const response = await systemAPI.config.getSystemConfig()
    console.log('系统配置API响应:', response)
    
    if (response && response.configs) {
      console.log('配置列表数量:', response.configs.length)
      console.log('配置列表内容:', response.configs)
      
      // 为每个配置项添加newValue属性用于编辑，并根据配置类型进行类型转换
      configs.value = response.configs.map((config: SystemConfigResponse) => {
        let convertedValue: any = config.config_value;
        
        // 根据配置类型转换值
        switch (config.config_type) {
          case 'int':
            convertedValue = parseInt(config.config_value) || 0;
            break;
          case 'bool':
            convertedValue = config.config_value === 'true';
            break;
          default:
            // 字符串类型保持原样
            convertedValue = config.config_value;
        }
        
        return {
          ...config,
          newValue: convertedValue
        };
      })
      
      console.log('配置数据已设置:', configs.value)
    } else {
      console.warn('API响应中没有configs属性或为空')
      configs.value = []
    }
  } catch (err: any) {
    console.error('加载系统配置失败:', err)
    console.error('错误详情:', err.response?.data || err.message)
    console.error('错误状态码:', err.response?.status)
    error.value = err.response?.data?.detail || '加载系统配置失败，请稍后重试'
  } finally {
    loading.value = false
    console.log('加载配置完成')
  }
}

// 刷新配置
const refreshConfigs = () => {
  loadSystemStatus()
  loadConfigs()
}

// 处理搜索
const handleSearch = () => {
  // 搜索功能由computed属性自动处理
}

// 清除搜索
const handleClearSearch = () => {
  searchKeyword.value = ''
}

// 初始化系统
const initializeSystem = async () => {
  if (!hasPermission('AUTH-edit')) {
    ElMessage.warning('您没有编辑权限')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要初始化系统吗？此操作将创建默认配置参数，且无法撤销。',
      '系统初始化确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    initializing.value = true
    
    // 调用后端初始化系统API
    const response = await systemAPI.config.initializeSystem()
    console.log('系统初始化API响应:', response)
    
    ElMessage.success(response.message || '系统初始化成功')
    
    // 刷新系统状态和配置
    refreshConfigs()
  } catch (err: any) {
    if (err !== 'cancel') {
      console.error('系统初始化失败:', err)
      ElMessage.error(err.response?.data?.detail || '系统初始化失败')
    }
  } finally {
    initializing.value = false
  }
}

// 测试Redis连接
const testRedisConnection = async () => {
  try {
    testingRedis.value = true
    console.log('开始测试Redis连接...')
    
    // 使用全局状态管理检查Redis状态
    const { forceCheckRedisStatus, showStatusNotification } = useRedisStatus()
    const redisStatusInfo = await forceCheckRedisStatus()
    
    // 更新本地状态
    redisStatus.value = redisStatusInfo.redis_available
    
    // 显示状态通知
    showStatusNotification(redisStatusInfo)
    
  } catch (err: any) {
    console.error('Redis连接测试失败:', err)
    redisStatus.value = false
    
    // 处理认证错误
    if (err.response?.status === 401) {
      ElMessage.error('会话已过期，请重新登录')
      // 响应拦截器会自动跳转到登录页
    } else if (err.response?.data?.detail) {
      ElMessage.error(`Redis连接测试失败: ${err.response.data.detail}`)
    } else {
      ElMessage.error('Redis连接测试失败，请检查服务器状态')
    }
  } finally {
    testingRedis.value = false
  }
}

// 保存单个配置
const saveSingleConfig = async (config: SystemConfigResponse & { newValue?: any, saving?: boolean }) => {
  console.log('开始保存配置:', config)
  if (!hasPermission('AUTH-edit')) {
    ElMessage.warning('您没有编辑权限')
    return
  }
  
  if (!isConfigChanged(config)) {
    ElMessage.warning('配置值未更改')
    return
  }
  
  try {
    config.saving = true
    const updateData: SystemConfigUpdate = {
      config_key: config.config_key,
      config_value: String(config.newValue)
    }
    // console.log('发送更新数据:', updateData);
    
    await systemAPI.config.updateSystemConfig(updateData)
    ElMessage.success(`配置 ${config.config_key} 更新成功`)
    
    // 更新原始值
    config.config_value = String(config.newValue)
  } catch (err: any) {
    console.error('保存配置失败:', err)
    ElMessage.error(err.response?.data?.detail || '保存配置失败')
  } finally {
    config.saving = false
  }
}

// 重置单个配置
const resetSingleConfig = (config: SystemConfigResponse & { newValue?: any }) => {
  config.newValue = config.config_value
}

// 保存所有更改
const saveAllConfigs = async () => {
  if (!hasPermission('AUTH-edit')) {
    ElMessage.warning('您没有编辑权限')
    return
  }
  
  if (!hasChanges.value) {
    ElMessage.warning('没有需要保存的更改')
    return
  }
  
  try {
    saving.value = true
    
    const changedConfigs = configs.value.filter((config: SystemConfigResponse & { newValue?: any }) => isConfigChanged(config))
    const promises = changedConfigs.map((config: SystemConfigResponse & { newValue?: any }) => 
      systemAPI.config.updateSystemConfig({
        config_key: config.config_key,
        config_value: String(config.newValue)
      })
    )
    
    await Promise.all(promises)
    ElMessage.success(`成功保存 ${changedConfigs.length} 个配置更改`)
    
    // 刷新配置列表
    await loadConfigs()
  } catch (err: any) {
    console.error('保存配置失败:', err)
    ElMessage.error(err.response?.data?.detail || '保存配置失败')
  } finally {
    saving.value = false
  }
}

// 重置所有更改
const resetChanges = () => {
  configs.value.forEach((config: SystemConfigResponse & { newValue?: any }) => {
    config.newValue = config.config_value
  })
  ElMessage.info('已重置所有更改')
}

// 格式化日期时间
const formatDateTime = (dateTime: string | undefined) => {
  if (!dateTime) return '未知'
  try {
    return new Date(dateTime).toLocaleString('zh-CN')
  } catch {
    return dateTime
  }
}

// 组件挂载时加载数据
onMounted(() => {
  refreshConfigs()
})
</script>

<style scoped>
.system-config-container {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.system-permission-alert {
  margin-bottom: 20px;
}

.system-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.system-operation-card {
  margin-bottom: 0;
}

.system-operation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.system-operation-bar__left {
  display: flex;
  gap: 10px;
}

.system-operation-bar__right {
  display: flex;
  gap: 10px;
}

.system-status-card {
  margin-bottom: 0;
}

.system-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.system-card-header__stats {
  margin-left: auto;
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #606266;
}

.system-card-header__stats .changes-count {
  color: #e6a23c;
  font-weight: 600;
}

.system-status-content {
  padding: 0;
}

.system-configs-card {
  margin-bottom: 0;
}

.system-loading-container {
  padding: 20px;
}

.system-error-state {
  margin: 20px;
}

.system-table {
  width: 100%;
  margin-top: 10px;
}

.config-name-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 4px;
}

.config-name-text {
  font-weight: 600;
  color: #303133;
  word-break: break-all;
  line-height: 1.4;
}

.config-key-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.config-key-text {
  word-break: break-all;
  word-wrap: break-word;
  white-space: normal;
  line-height: 1.4;
  text-align: center;
}

.system-tag-primary {
  background-color: #409eff;
  color: white;
  border: none;
}

.config-description-icon {
  color: #909399;
  cursor: help;
}

.config-readonly {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 32px;
}

.config-input-container {
  display: flex;
  justify-content: center;
}

.config-value-changed {
  color: #e6a23c;
  font-weight: 600;
}

.config-description {
  color: #606266;
  line-height: 1.5;
}

.base-action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.base-button-circle {
  border-radius: 50%;
  width: 32px;
  height: 32px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.system-empty-state {
  padding: 40px 0;
  text-align: center;
}
</style>