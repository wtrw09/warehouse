<template>
  <div class="personal-settings">
    
    <!-- 个人信息卡片 -->
    <el-card class="info-card" v-if="userInfo">
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
          <div class="card-actions">
            <el-button 
              type="primary" 
              size="small" 
              @click="showPasswordDialog"
              :icon="Key"
            >
              修改密码
            </el-button>
            <el-button 
              type="info" 
              size="small" 
              @click="handleViewMyLoginRecords"
              :icon="DataAnalysis"
            >
              查看登录记录
            </el-button>
          </div>
        </div>
      </template>
      
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ userInfo.username || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="用户ID">{{ userInfo.id || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ userInfo.role_name || '未知角色' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(userInfo.create_time || '') }}</el-descriptions-item>
        <el-descriptions-item label="最后更新时间">{{ formatDate(userInfo.update_time || '') }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="passwordDialog.visible"
      title="修改密码"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        :model="passwordForm"
        :rules="passwordRules"
        ref="passwordFormRef"
        label-width="100px"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入原密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="passwordDialog.visible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleChangePassword"
            :loading="passwordDialog.loading"
          >
            确定修改
          </el-button>
        </div>
      </template>
    </el-dialog>
  
    <!-- 登录记录对话框 -->
    <el-dialog
      v-model="loginRecordDialog.visible"
      title="我的登录记录"
      width="90%"
      max-width="1200px"
      :close-on-click-modal="false"
    >
      <el-card class="login-record-table-card" shadow="hover">
        <template #header>
          <div class="login-record-card-header">
            <div class="header-left">
              <el-icon><List /></el-icon>
              <span>登录记录列表</span>
            </div>
            <div class="header-right">
              <el-text class="search-label">搜索：</el-text>
              <el-input
                v-model="loginRecordQueryParams.search"
                placeholder="请输入关键词"
                style="width: 200px;"
                clearable
                @input="handleLoginRecordSearch"
                @clear="handleLoginRecordSearch"
                @keyup.enter="handleLoginRecordSearch"
              />
            </div>
          </div>
        </template>
        
        <!-- 筛选条件 -->
        <div class="filter-conditions">
          <el-row :gutter="16" style="margin-bottom: 16px;">
            <el-col :span="8">
              <el-form-item label="开始日期">
                <el-date-picker
                  v-model="loginRecordQueryParams.start_time"
                  type="date"
                  placeholder="选择开始日期"
                  value-format="YYYY-MM-DD"
                  @change="handleLoginRecordFilterChange"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="结束日期">
                <el-date-picker
                  v-model="loginRecordQueryParams.end_time"
                  type="date"
                  placeholder="选择结束日期"
                  value-format="YYYY-MM-DD"
                  @change="handleLoginRecordFilterChange"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="loginRecordDialog.loading" class="login-record-loading-container">
          <el-skeleton :rows="8" animated />
        </div>
        
        <!-- 错误状态 -->
        <el-alert
          v-else-if="loginRecordError"
          :title="loginRecordError"
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
                  {{ formatDate(row.login_time) }}
                </el-text>
              </template>
            </el-table-column>
            
            <el-table-column prop="logout_time" label="登出时间" width="180" align="center" sortable>
              <template #default="{ row }">
                <el-text type="info" size="small">
                  {{ row.logout_time ? formatDate(row.logout_time) : '-' }}
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
              v-model:current-page="loginRecordQueryParams.page"
              v-model:page-size="loginRecordQueryParams.page_size"
              :page-sizes="[10, 20, 50, 100]"
              :total="loginRecordPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              :pager-count="7"
              background
              @size-change="handleLoginRecordSizeChange"
              @current-change="handleLoginRecordCurrentChange"
              :page-size-suffix="'条/页'"
              :total-text="`共 ${loginRecordPagination.total} 条`"
              :jumper-text="'前往'"
            />
          </div>
        </div>
      </el-card>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Key, DataAnalysis, List } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { userAPI } from '@/services/account/user'
import { loginRecordAPI } from '@/services/account/login-record'
import type {
  LoginRecordResponse,
  MyLoginRecordQueryParams
} from '@/services/types/login-record'

interface UserInfo {
  id: number
  username: string
  role_name: string
  create_time: string
  update_time: string
}

interface PasswordForm {
  oldPassword: string
  newPassword: string
  confirmPassword: string
}

const userStore = useUserStore()
const userInfo = ref<UserInfo | null>(null)
const passwordFormRef = ref<FormInstance>()

const passwordForm = ref<PasswordForm>({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordDialog = ref({
  visible: false,
  loading: false
})

// 密码验证规则
const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== passwordForm.value.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' },
    { min: 1, message: '密码不能为空', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 格式化日期
const formatDate = (dateString: string) => {
  try {
    return new Date(dateString).toLocaleString('zh-CN')
  } catch (error) {
    console.error('日期格式化失败:', error)
    return dateString || '未知时间'
  }
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    // 优先从用户存储中获取当前用户信息
    if (userStore.user) {
      userInfo.value = {
        id: userStore.user.id,
        username: userStore.user.username,
        role_name: userStore.user.roleName || '未知角色',
        create_time: userStore.user.create_time || new Date().toISOString(),
        update_time: userStore.user.update_time || new Date().toISOString()
      }
    }
    // 尝试从API获取最新用户信息作为后备
    const currentUser = await userAPI.getCurrentUser()
    if (currentUser) {
      userInfo.value = {
        id: currentUser.id,
        username: currentUser.username,
        role_name: currentUser.roleName || '未知角色',
        create_time: currentUser.create_time || new Date().toISOString(),
        update_time: currentUser.update_time || new Date().toISOString()
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    // 如果store中已有数据，则不显示错误提示
    if (!userStore.user) {
      ElMessage.error('获取用户信息失败')
    }
  }
}

// 显示密码修改对话框
const showPasswordDialog = () => {
  passwordDialog.value.visible = true
  resetForm()
}

// 修改密码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    const valid = await passwordFormRef.value.validate()
    if (!valid) return

    passwordDialog.value.loading = true

    await userAPI.changePassword({
      old_password: passwordForm.value.oldPassword,
      new_password: passwordForm.value.newPassword
    })

    ElMessage.success('密码修改成功')
    passwordDialog.value.visible = false
    resetForm()
  } catch (error: any) {
    console.error('修改密码失败:', error)
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    passwordDialog.value.loading = false
  }
}

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

// 登录记录相关响应式数据
const loginRecords = ref<LoginRecordResponse[]>([]);
const loginRecordDialog = ref({
  visible: false,
  loading: false
});
const loginRecordError = ref<string | null>(null);
const loginRecordQueryParams = ref<MyLoginRecordQueryParams>({
  page: 1,
  page_size: 20,
  start_time: getLastMonthFirstDay(),
  end_time: getCurrentDate(),
  search: ''
});
const loginRecordPagination = ref({
  total: 0,
  page: 1,
  page_size: 20,
  total_pages: 0
});

// 截断用户代理信息
const truncateUserAgent = (userAgent: string): string => {
  if (userAgent.length > 50) {
    return userAgent.substring(0, 50) + '...';
  }
  return userAgent;
};

// 加载我的登录记录
const loadMyLoginRecords = async () => {
  if (!userInfo.value) {
    ElMessage.warning('请先获取用户信息');
    return;
  }
  
  loginRecordDialog.value.loading = true;
  loginRecordError.value = null;
  
  try {
    // 获取登录记录
    const response = await loginRecordAPI.getMyLoginRecords(loginRecordQueryParams.value);
    
    loginRecords.value = response || [];
    
    // 假设API返回的数据已经是分页后的结果，这里简化处理
    // 实际项目中，API应该返回完整的分页信息
    const page = loginRecordQueryParams.value.page || 1;
    const pageSize = loginRecordQueryParams.value.page_size || 20;
    
    loginRecordPagination.value = {
      total: response.length,
      page: page,
      page_size: pageSize,
      total_pages: Math.ceil(response.length / pageSize)
    };
    
  } catch (error: any) {
    console.error('获取登录记录失败:', error);
    loginRecordError.value = error.response?.data?.detail || '获取登录记录失败';
    ElMessage.error(loginRecordError.value || '获取登录记录失败');
  } finally {
    loginRecordDialog.value.loading = false;
  }
};

// 分页大小变化处理
const handleLoginRecordSizeChange = (size: number) => {
  loginRecordQueryParams.value.page_size = size;
  loginRecordQueryParams.value.page = 1;
  loadMyLoginRecords();
};

// 页码变化处理
const handleLoginRecordCurrentChange = (page: number) => {
  loginRecordQueryParams.value.page = page;
  loadMyLoginRecords();
};

// 搜索处理
const handleLoginRecordSearch = () => {
  loginRecordQueryParams.value.page = 1;
  loadMyLoginRecords();
};

// 筛选条件变化处理
const handleLoginRecordFilterChange = () => {
  loginRecordQueryParams.value.page = 1;
  loadMyLoginRecords();
};

// 查看本人登录记录
const handleViewMyLoginRecords = async () => {
  if (!userInfo.value) {
    ElMessage.warning('请先获取用户信息');
    return;
  }
  
  try {
    // 检查是否有查看自己登录记录的权限
    const userData = localStorage.getItem('userData');
    let hasAuthOwnPermission = false;
    
    if (userData) {
      try {
        const parsedUserData = JSON.parse(userData);
        hasAuthOwnPermission = parsedUserData.permissions?.includes('AUTH-own') || false;
      } catch (err) {
        console.error('解析用户数据失败:', err);
      }
    }
    
    if (!hasAuthOwnPermission) {
      ElMessage.warning('您没有权限查看登录记录');
      return;
    }
    
    // 打开登录记录对话框
    loginRecordDialog.value.visible = true;
    
    // 重置查询参数
    loginRecordQueryParams.value = {
      page: 1,
      page_size: 20,
      search: '',
      start_time: getLastMonthFirstDay(),
      end_time: getCurrentDate()
    };
    
    // 加载登录记录
    await loadMyLoginRecords();
    
  } catch (error) {
    console.error('查看登录记录失败:', error);
    ElMessage.error('操作失败，请稍后重试');
  }
};

// 重置表单
const resetForm = () => {
  if (passwordFormRef.value) {
    passwordFormRef.value.resetFields()
  }
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.personal-settings {
  padding: 0;
  max-width: 100%;
  margin: 0;
}

.info-card {
  margin-bottom: 0;
  border: none;
  box-shadow: none;
}

.info-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.info-card :deep(.el-card__body) {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0;
  padding: 0;
  gap: 16px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

:deep(.el-descriptions__body) {
  background-color: #fafafa;
  margin: 0;
  padding: 0;
}

:deep(.el-descriptions__table) {
  margin: 0;
}

:deep(.el-descriptions__label) {
  margin: 0;
  padding: 8px;
}

:deep(.el-descriptions__content) {
  margin: 0;
  padding: 8px;
}

/* 登录记录对话框样式 */
.login-record-table-card {
  margin-bottom: 0;
}

.login-record-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.login-record-loading-container {
  padding: 20px;
}

.search-label {
  font-weight: 500;
  margin-right: 8px;
}

.filter-conditions {
  margin-bottom: 16px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

:deep(.el-form-item) {
  margin-bottom: 0;
}

.login-record-table {
  margin-top: 0;
}

.login-record-pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>

<!-- 定义组件类型 -->
<script lang="ts">
export default {
  name: 'PersonalSettings'
}
</script>