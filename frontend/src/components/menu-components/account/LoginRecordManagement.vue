<template>
  <div class="login-record-management">
    <!-- 权限不足提示 -->
    <el-alert
      v-if="!hasAuthReadPermission"
      title="权限不足"
      type="error"
      :closable="false"
      show-icon
    >
      <template #default>
        <p>您没有足够的权限访问用户登录记录查询功能。</p>
        <p>需要权限：<el-tag type="danger">AUTH-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 登录记录查询内容 -->
    <div v-else class="login-record-content">
      <!-- 操作栏 -->
        <el-card class="login-record-operation-card" shadow="hover">
          <div class="login-record-operation-bar">
            <div class="left-actions">
              <el-button 
                type="primary" 
                @click="loadLoginRecords"
                :loading="loading"
                :icon="Refresh"
              >
                刷新
              </el-button>
              <el-button 
                type="info" 
                @click="loadStatistics"
                :loading="statisticsLoading"
                :icon="DataAnalysis"
              >
                统计摘要
              </el-button>
              <el-button 
                v-if="props.selectedUsername"
                type="warning" 
                @click="clearUserFilter"
                :icon="Close"
              >
                清除用户筛选
              </el-button>
            </div>
            <div class="right-actions">
              <el-button 
                v-if="props.selectedUsername"
                type="default" 
                @click="handleClose"
                :icon="CloseBold"
              >
                关闭
              </el-button>
              <el-text class="search-label">搜索：</el-text>
              <el-input
                v-model="searchParams.search"
                placeholder="请输入关键词，以空格分隔"
                style="width: 300px;"
                clearable
                @input="handleSearch"
                @clear="handleSearch"
                @keyup.enter="handleSearch"
              />
            </div>
          </div>

        <!-- 筛选条件 -->
        <div class="filter-conditions">
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="用户名">
                <el-input
                  v-model="searchParams.username"
                  placeholder="请输入用户名"
                  clearable
                  @change="handleFilterChange"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="IP地址">
                <el-input
                  v-model="searchParams.ip_address"
                  placeholder="请输入IP地址"
                  clearable
                  @change="handleFilterChange"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="开始日期">
                <el-date-picker
                  v-model="searchParams.start_time"
                  type="date"
                  placeholder="选择开始日期"
                  value-format="YYYY-MM-DD"
                  @change="handleFilterChange"
                />
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="结束日期">
                <el-date-picker
                  v-model="searchParams.end_time"
                  type="date"
                  placeholder="选择结束日期"
                  value-format="YYYY-MM-DD"
                  @change="handleFilterChange"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>
      </el-card>

      <!-- 统计信息卡片 -->
      <el-card v-if="statistics" class="statistics-card" shadow="hover">
        <template #header>
          <div class="statistics-header">
            <el-icon><DataAnalysis /></el-icon>
            <span>登录统计摘要（近{{ statistics.analysis_period_days }}天）</span>
          </div>
        </template>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="总登录次数" :value="statistics.total_logins" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="活跃用户数" :value="statistics.active_users" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="不同IP数量" :value="statistics.distinct_ips" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="今日登录次数" :value="statistics.today_logins" />
          </el-col>
        </el-row>
      </el-card>

      <!-- 登录记录列表 -->
      <el-card class="login-record-table-card" shadow="hover">
        <template #header>
          <div class="login-record-card-header">
            <div class="header-left">
              <el-icon><List /></el-icon>
              <span>登录记录列表</span>
            </div>
            <div class="header-stats">
              <el-tag type="info" size="small">总记录: {{ pagination.total }}</el-tag>
              <el-tag type="success" size="small">当前页: {{ loginRecords?.length || 0 }}</el-tag>
            </div>
          </div>
        </template>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="login-record-loading-container">
          <el-skeleton :rows="8" animated />
        </div>
        
        <!-- 错误状态 -->
        <el-alert
          v-else-if="error"
          :title="error"
          type="error"
          show-icon
          :closable="false"
        />
        
        <!-- 登录记录表格 -->
        <div v-else class="login-record-table">
          <el-table 
            :data="loginRecords" 
            stripe 
            border
            :empty-text="'暂无登录记录数据'"
            :default-sort="{ prop: 'login_time', order: 'descending' }"
          >
            <el-table-column prop="id" label="ID" width="70" align="center" fixed="left" sortable />
            
            <el-table-column prop="username" label="用户名" min-width="120" fixed="left" align="center" sortable>
              <template #default="{ row }">
                <el-tag type="primary" effect="dark">{{ row.username }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="ip_address" label="IP地址" min-width="140" align="center" sortable>
              <template #default="{ row }">
                <el-text type="info" size="small">{{ row.ip_address }}</el-text>
              </template>
            </el-table-column>
            
            <el-table-column prop="user_agent" label="用户代理" min-width="200" align="center">
              <template #default="{ row }">
                <el-tooltip :content="row.user_agent" placement="top">
                  <el-text type="info" size="small">
                    {{ truncateUserAgent(row.user_agent) }}
                  </el-text>
                </el-tooltip>
              </template>
            </el-table-column>
            
            <el-table-column prop="login_time" label="登录时间" width="180" align="center" sortable>
              <template #default="{ row }">
                <el-text type="info" size="small">
                  {{ formatDateTime(row.login_time) }}
                </el-text>
              </template>
            </el-table-column>
            
            <el-table-column prop="logout_time" label="登出时间" width="180" align="center" sortable>
              <template #default="{ row }">
                <el-text type="info" size="small">
                  {{ row.logout_time ? formatDateTime(row.logout_time) : '-' }}
                </el-text>
              </template>
            </el-table-column>
            
            <el-table-column prop="is_active" label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" effect="light">
                  {{ row.is_active ? '活跃' : '已登出' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页 -->
          <div class="login-record-pagination-container">
            <el-pagination
              v-model:current-page="searchParams.page"
              v-model:page-size="searchParams.page_size"
              :page-sizes="[10, 20, 50, 100]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              :pager-count="7"
              background
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
              :page-size-suffix="'条/页'"
              :total-text="`共 ${pagination.total} 条`"
              :jumper-text="'前往'"
            />
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, inject, Ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { 
  Refresh, 
  List, 
  DataAnalysis,
  Close,
  CloseBold
} from '@element-plus/icons-vue';
import { loginRecordAPI } from '../../../services/account/login-record';
import type {
  LoginRecordResponse,
  LoginRecordQueryParams,
  LoginStatisticsSummary
} from '../../../services/types/login-record';
import type { UserInfo } from '../../../services/types/auth';

// 组件属性定义
interface Props {
  selectedUsername?: string;
}

// 组件事件定义
interface Emits {
  (e: 'close'): void;
}

// 组件属性
const props = withDefaults(defineProps<Props>(), {
  selectedUsername: ''
});

// 组件事件
const emit = defineEmits<Emits>();

// 响应式数据
const loginRecords = ref<LoginRecordResponse[]>([]);
const loading = ref(false);
const statisticsLoading = ref(false);
const error = ref<string | null>(null);
const statistics = ref<LoginStatisticsSummary | null>(null);

// 获取上个月第一天的日期
const getLastMonthFirstDay = (): string => {
  const now = new Date();
  const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
  // 使用本地时区避免 UTC 偏移导致日期偏差
  const y = lastMonth.getFullYear();
  const m = String(lastMonth.getMonth() + 1).padStart(2, '0');
  const d = String(lastMonth.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

// 获取当前日期
const getCurrentDate = (): string => {
  const now = new Date();
  return now.toISOString().substring(0, 10);
};

// 搜索参数
const searchParams = ref<LoginRecordQueryParams>({
  page: 1,
  page_size: 20,
  search: '',
  username: '',
  ip_address: '',
  start_time: getLastMonthFirstDay(),
  end_time: getCurrentDate()
});

// 分页信息
const pagination = ref({
  total: 0,
  page: 1,
  page_size: 20,
  total_pages: 0
});

// 获取当前用户信息（从父组件注入）
const currentUser = inject<Ref<UserInfo | null>>('currentUser') || ref<UserInfo | null>(null);

/**
 * 检查当前用户是否拥有指定权限
 * @param permission 权限名称字符串，如 'AUTH-read', 'AUTH-edit'
 * @returns boolean - 用户是否拥有该权限
 */
const hasPermission = (permission: string): boolean => {
  if (!currentUser.value || !currentUser.value.permissions) {
    // 如果没有用户信息或权限信息，尝试从localStorage获取
    const userData = localStorage.getItem('userData');
    if (userData) {
      try {
        const parsedUserData = JSON.parse(userData);
        return parsedUserData.permissions?.includes(permission) || false;
      } catch (err) {
        console.error('解析用户数据失败:', err);
      }
    }
    return false;
  }
  return currentUser.value.permissions.includes(permission);
};

// 计算属性：检查是否有AUTH-read权限
const hasAuthReadPermission = computed(() => {
  return hasPermission('AUTH-read');
});

// 格式化日期时间
const formatDateTime = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  } catch (err) {
    return dateString;
  }
};

// 截断用户代理信息
const truncateUserAgent = (userAgent: string): string => {
  if (userAgent.length > 50) {
    return userAgent.substring(0, 50) + '...';
  }
  return userAgent;
};

// 加载登录记录
const loadLoginRecords = async () => {
  if (!hasAuthReadPermission.value) {
    ElMessage.warning('您没有足够的权限访问登录记录');
    return;
  }

  loading.value = true;
  error.value = null;
  
  try {
    const response = await loginRecordAPI.getLoginRecords(searchParams.value);
    console.log('API响应数据:', response);
    console.log('登录记录数据:', response.records);
    console.log('数据条数:', response.records?.length || 0);
    
    loginRecords.value = response.records || [];
    
    pagination.value = {
      total: response.total,
      page: response.page,
      page_size: response.page_size,
      total_pages: response.total_pages
    };
    
  } catch (err: any) {
    console.error('加载登录记录失败:', err);
    
    if (err.response?.status === 403) {
      error.value = '权限不足，无法访问登录记录查询功能';
      ElMessage.error('权限不足，请与管理员联系');
    } else if (err.response?.status === 401) {
      error.value = '身份验证失败，请重新登录';
      console.error('认证失败:', err.response?.data?.detail || '请重新登录');
    } else {
      error.value = err.response?.data?.detail || '加载登录记录失败';
      ElMessage.error(error.value || '加载登录记录失败');
    }
  } finally {
    loading.value = false;
  }
};

// 加载统计信息
const loadStatistics = async () => {
  statisticsLoading.value = true;
  
  try {
    statistics.value = await loginRecordAPI.getLoginStatistics(90);
  } catch (err: any) {
    console.error('加载统计信息失败:', err);
    ElMessage.error('加载统计信息失败');
  } finally {
    statisticsLoading.value = false;
  }
};

// 搜索处理
const handleSearch = () => {
  searchParams.value.page = 1;
  loadLoginRecords();
};

// 筛选条件变化处理
const handleFilterChange = () => {
  searchParams.value.page = 1;
  loadLoginRecords();
};

// 分页大小变化处理
const handleSizeChange = (size: number) => {
  searchParams.value.page_size = size;
  searchParams.value.page = 1;
  loadLoginRecords();
};

// 页码变化处理
const handleCurrentChange = (page: number) => {
  searchParams.value.page = page;
  loadLoginRecords();
};

// 关闭弹窗
const handleClose = () => {
  emit('close');
};

// 清除用户筛选
const clearUserFilter = () => {
  searchParams.value.username = '';
  searchParams.value.page = 1;
  loadLoginRecords();
};

// 监听 selectedUsername 变化，自动筛选用户
watch(() => props.selectedUsername, (newUsername) => {
  if (newUsername) {
    searchParams.value.username = newUsername;
    searchParams.value.page = 1;
    loadLoginRecords();
  }
}, { immediate: true });

onMounted(() => {
  if (hasAuthReadPermission.value) {
    loadLoginRecords();
    loadStatistics();
  }
});
</script>

<style scoped>
.login-record-management {
  padding: 0;
  max-width: 100%;
  margin: 0;
}

.login-record-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.login-record-operation-card {
  margin-bottom: 0;
}

.login-record-operation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.filter-conditions {
  margin-top: 16px;
}

.statistics-card {
  margin-bottom: 0;
}

.statistics-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.login-record-table-card {
  margin-bottom: 0;
}

.login-record-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.login-record-loading-container {
  padding: 20px;
}

.login-record-table {
  margin-top: 0;
}

.login-record-pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

:deep(.el-form-item) {
  margin-bottom: 0;
}

:deep(.el-statistic__content) {
  font-size: 24px;
  font-weight: bold;
}
</style>

<!-- 定义组件类型 -->
<script lang="ts">
export default {
  name: 'LoginRecordManagement'
}
</script>