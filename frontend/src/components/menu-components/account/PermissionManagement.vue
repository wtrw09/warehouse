<template>
  <div class="account-management-container permission-management">
    <!-- 权限不足提示 -->
    <el-alert
      v-if="!hasAuthReadPermission"
      title="权限不足"
      type="error"
      :closable="false"
      show-icon
    >
      <template #default>
        <p>您没有足够的权限访问权限管理功能。</p>
        <p>需要权限：<el-tag type="danger">AUTH-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 权限管理内容 -->
    <div v-else class="account-content account-flex-content">
      <!-- 操作栏 -->
      <el-card class="account-operation-card" shadow="hover">
        <div class="account-operation-bar">
          <div class="left-actions">
            <el-button 
              type="default" 
              @click="loadPermissions"
              :loading="loading"
              :icon="Refresh"
            >
              刷新
            </el-button>
          </div>
          <div class="right-actions">
            <el-input
              v-model="searchParams.keyword"
              placeholder="请输入关键词，以空格分隔"
              style="width: 300px;"
              clearable
              @clear="handleSearch"
              @keyup.enter="handleSearch"
              class="account-input-group"
            >
              <template #append>
                <el-button @click="handleSearch" :icon="Search">搜索</el-button>
              </template>
            </el-input>
          </div>
        </div>
      </el-card>

      <!-- 权限列表 -->
      <el-card class="account-table-card account-table-card--flex" shadow="hover">
        <template #header>
          <div class="account-card-header">
            <div class="header-left">
              <el-icon><List /></el-icon>
              <span>权限列表</span>
            </div>
            <div class="header-stats">
              <el-tag type="info" size="small">系统权限总数: {{ permissions.length }}</el-tag>
              <el-tag type="success" size="small">当前显示: {{ filteredPermissions.length }}</el-tag>
            </div>
          </div>
        </template>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="account-loading-container">
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
        
        <!-- 权限表格 -->
        <div v-else class="account-table account-table--auto-height">
          <el-table 
            ref="tableRef"
            :data="filteredPermissions" 
            stripe 
            border
            :empty-text="'暂无权限数据'"
            :default-sort="{ prop: 'id', order: 'ascending' }"
          >
            <el-table-column prop="id" label="ID" width="120" align="center" fixed="left" sortable>
              <template #default="{ row }">
                <el-tag type="primary" effect="dark">{{ row.id }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="description" label="权限描述" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">
                <span class="permission-description">{{ row.description }}</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="create_time" label="创建时间" width="180" align="center" sortable>
              <template #default="{ row }">
                <el-text type="info" size="small">
                  {{ formatDate(row.create_time) }}
                </el-text>
              </template>
            </el-table-column>
            
            <el-table-column prop="update_time" label="更新时间" width="180" align="center" sortable>
              <template #default="{ row }">
                <el-text type="info" size="small">
                  {{ formatDate(row.update_time) }}
                </el-text>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, inject, Ref } from 'vue';
import { ElMessage } from 'element-plus';
import type { TableInstance } from 'element-plus';
import { 
  Refresh, 
  Search,
  List
} from '@element-plus/icons-vue';
import { permissionAPI } from '../../../services/api';

// 定义权限数据类型
interface Permission {
  id: string;
  description: string;
  create_time: string;
  update_time: string;
  is_delete: boolean;
}

// 定义用户信息类型
interface UserInfo {
  id: number;
  username: string;
  role_id: number;
  roleName: string;
  permissions: string[];
}

// 响应式数据
const permissions = ref<Permission[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

// 表格引用
const tableRef = ref<TableInstance>();

// 搜索参数
const searchParams = ref({
  keyword: ''
});

// 获取当前用户信息（从父组件注入）
const currentUser = inject<Ref<UserInfo | null>>('currentUser') || ref<UserInfo | null>(null);

// 计算属性：检查是否有AUTH-read权限
const hasAuthReadPermission = computed(() => {
  if (!currentUser.value || !currentUser.value.permissions) {
    return false;
  }
  return currentUser.value.permissions.includes('AUTH-read');
});

// 计算属性：过滤后的权限列表
const filteredPermissions = computed(() => {
  if (!searchParams.value.keyword) {
    return permissions.value;
  }
  
  const keyword = searchParams.value.keyword.toLowerCase();
  return permissions.value.filter(permission => 
    permission.id.toLowerCase().includes(keyword) ||
    permission.description.toLowerCase().includes(keyword)
  );
});

// 格式化日期
const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (err) {
    return dateString;
  }
};

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已通过计算属性实现，这里可以添加其他搜索逻辑
  ElMessage.success(`搜索完成，找到 ${filteredPermissions.value.length} 个权限`);
};

// 加载权限列表
const loadPermissions = async () => {
  if (!hasAuthReadPermission.value) {
    ElMessage.warning('您没有足够的权限访问权限列表');
    return;
  }

  loading.value = true;
  error.value = null;
  
  try {
    const response = await permissionAPI.getPermissions();
    permissions.value = response;
    ElMessage.success(`成功加载 ${response.length} 个权限`);
  } catch (err: any) {
    console.error('加载权限列表失败:', err);
    
    if (err.response?.status === 403) {
      error.value = '权限不足，无法访问权限管理功能';
      ElMessage.error('权限不足，请与管理员联系');
    } else if (err.response?.status === 401) {
      error.value = '身份验证失败，请重新登录';
      // 全局拦截器已经处理了401错误，这里只记录错误不重复显示
      console.error('认证失败:', err.response?.data?.detail || '请重新登录');
    } else {
      error.value = err.response?.data?.detail || '加载权限列表失败';
      ElMessage.error(error.value || '加载权限列表失败');
    }
  } finally {
    loading.value = false;
  }
};

// 组件挂载时初始化
onMounted(async () => {
  // 模拟获取当前用户信息（如果没有注入）
  if (!currentUser.value) {
    const userData = localStorage.getItem('userData');
    if (userData) {
      try {
        currentUser.value = JSON.parse(userData);
      } catch (err) {
        console.error('解析用户数据失败:', err);
      }
    }
  }
  
  // 如果有权限，自动加载权限列表
  if (hasAuthReadPermission.value) {
    await loadPermissions();
  }
});
</script>

<style src="../../../css/base-styles.css"></style>
<style scoped>
/* 权限管理组件特定样式 */
</style>