<template>
  <div class="account-management-container role-management">
    <!-- 权限不足提示 -->
    <el-alert
      v-if="!hasAuthReadPermission"
      title="权限不足"
      type="error"
      :closable="false"
      show-icon
    >
      <template #default>
        <p>您没有足够的权限访问角色管理功能。</p>
        <p>需要权限：<el-tag type="danger">AUTH-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 角色管理内容 -->
    <div v-else class="account-content account-flex-content">
      <!-- 操作栏 -->
      <el-card class="account-operation-card" shadow="hover">
        <div class="account-operation-bar">
          <div class="left-actions">
            <el-button 
              type="primary" 
              @click="handleCreate"
              v-if="hasAuthEditPermission"
              :icon="Plus"
            >
              新增角色
            </el-button>
            <el-button 
              type="default" 
              @click="loadRoles"
              :loading="loading"
              :icon="Refresh"
            >
              刷新
            </el-button>
          </div>
          <div class="right-actions">
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
      </el-card>

      <!-- 角色列表 -->
      <el-card class="account-table-card account-table-card--flex" shadow="hover">
        <template #header>
          <div class="account-card-header">
            <div class="header-left">
              <el-icon><List /></el-icon>
              <span>角色列表</span>
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
        
        <!-- 角色表格 -->
        <div v-else class="account-table account-table--auto-height">
          <el-table 
            ref="tableRef"
            :data="filteredRoleList" 
            stripe 
            border
            :empty-text="'暂无角色数据'"
            :default-sort="{ prop: 'id', order: 'ascending' }"
          >
            <el-table-column prop="id" label="ID" width="70" align="center" fixed="left" sortable />
            
            <el-table-column 
              prop="name" 
              label="角色名称" 
              min-width="150" 
              fixed="left" 
              align="center" 
              sortable
              column-key="name"
              :filters="nameFilters"
              :filter-method="filterName"
            >
              <template #default="{ row }">
                <el-tag type="primary" effect="dark">{{ row.name }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="description" label="角色描述" min-width="200" show-overflow-tooltip />
            
            <el-table-column label="权限列表" min-width="300">
              <template #default="{ row }">
                <el-space wrap v-if="row.permissions && row.permissions.length > 0">
                  <el-tag
                    v-for="permission in row.permissions"
                    :key="permission"
                    type="info"
                    size="small"
                    effect="light"
                  >
                    {{ permission }}
                  </el-tag>
                </el-space>
                <el-text v-else type="info">暂无权限</el-text>
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
            

            
            <el-table-column label="操作" width="120" align="center" fixed="right" v-if="hasAuthEditPermission">
              <template #default="{ row }">
                <el-space>
                  <el-tooltip content="编辑角色" placement="top">
                    <el-button 
                      type="warning"
                      size="small"
                      @click="handleEdit(row)"
                      :disabled="!hasAuthEditPermission"
                      :icon="Edit"
                      circle
                    />
                  </el-tooltip>
                  <el-tooltip content="删除角色" placement="top">
                    <el-button 
                      type="danger"
                      size="small"
                      @click="handleDelete(row)"
                      :disabled="!hasAuthEditPermission"
                      :icon="Delete"
                      circle
                    />
                  </el-tooltip>
                </el-space>
              </template>
            </el-table-column>
          </el-table>
          

        </div>
      </el-card>
    </div>

    <!-- 角色新增/编辑对话框 -->
    <el-dialog
      v-model="roleDialog.visible"
      :title="roleDialog.isEdit ? '编辑角色' : '新增角色'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="roleFormRef"
        :model="roleForm"
        :rules="roleFormRules"
        label-width="100px"
      >
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="roleForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="角色描述" prop="description">
          <el-input 
            v-model="roleForm.description" 
            type="textarea"
            :rows="3"
            placeholder="请输入角色描述"
          />
        </el-form-item>
        <el-form-item label="角色权限" prop="permissions">
          <el-select
            v-model="roleForm.permissions"
            multiple
            placeholder="请选择角色权限"
            style="width: 100% !important;"
            :loading="permissionsLoading"
          >
            <el-option
              v-for="permission in availablePermissions"
              :key="permission.id"
              :label="permission.id"
              :value="permission.id"
            />
          </el-select>
          <div class="permission-hint">
            <el-text type="info" size="small">
              已选择 {{ roleForm.permissions.length }} 个权限
            </el-text>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="roleDialog.visible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleSaveRole"
            :loading="roleDialog.loading"
          >
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, inject, Ref } from 'vue';
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus';
import type { TableInstance } from 'element-plus';
import { 
  Plus, 
  Refresh, 
  List, 
  Edit, 
  Delete
} from '@element-plus/icons-vue';
import { roleAPI, permissionAPI } from '../../../services/api';
import type { RoleWithPermissions, RoleForm } from '../../../services/types/role';
import type { Permission } from '../../../services/types/permission';
import type { UserInfo } from '../../../services/types/auth';

// 响应式数据
const roleList = ref<RoleWithPermissions[]>([]);
const availablePermissions = ref<Permission[]>([]);
const loading = ref(false);
const permissionsLoading = ref(false);
const error = ref<string | null>(null);

// 表格引用
const tableRef = ref<TableInstance>();

// 角色名称筛选器
const nameFilters = ref<{ text: string; value: string }[]>([]);

// 搜索参数
const searchParams = ref({
  page_size: 1000, // 设置为大值获取全部数据
  search: ''
});

// 角色对话框
const roleDialog = ref({
  visible: false,
  isEdit: false,
  loading: false
});

// 角色表单
const roleForm = ref<RoleForm>({
  name: '',
  description: '',
  permissions: []
});

const roleFormRef = ref<FormInstance>();
const editingRoleId = ref<number | null>(null);

// 表单验证规则
const roleFormRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '角色描述长度不能超过 200 个字符', trigger: 'blur' }
  ],
  permissions: []
};

// 获取当前用户信息（从父组件注入）
const currentUser = inject<Ref<UserInfo | null>>('currentUser') || ref<UserInfo | null>(null);

// 计算属性：检查是否有AUTH-read权限
const hasAuthReadPermission = computed(() => {
  if (!currentUser.value || !currentUser.value.permissions) {
    return false;
  }
  return currentUser.value.permissions.includes('AUTH-read');
});

// 计算属性：检查是否有AUTH-edit权限
const hasAuthEditPermission = computed(() => {
  if (!currentUser.value || !currentUser.value.permissions) {
    return false;
  }
  return currentUser.value.permissions.includes('AUTH-edit');
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

// 加载角色列表
const loadRoles = async () => {
  if (!hasAuthReadPermission.value) {
    ElMessage.warning('您没有足够的权限访问角色列表');
    return;
  }

  loading.value = true;
  error.value = null;
  
  try {
    const response = await roleAPI.getRoles(searchParams.value);
    roleList.value = response.data;

    // 动态生成角色名称筛选器选项
    const uniqueNames = [...new Set(response.data.map(role => role.name))];
    nameFilters.value = uniqueNames.map(name => ({
      text: name,
      value: name
    }));

  } catch (err: any) {
    console.error('加载角色列表失败:', err);
    
    if (err.response?.status === 403) {
      error.value = '权限不足，无法访问角色管理功能';
      ElMessage.error('权限不足，请与管理员联系');
    } else if (err.response?.status === 401) {
      error.value = '身份验证失败，请重新登录';
      // 全局拦截器已经处理了401错误，这里只记录错误不重复显示
      console.error('认证失败:', err.response?.data?.detail || '请重新登录');
    } else {
      error.value = err.response?.data?.detail || '加载角色列表失败';
      ElMessage.error(error.value || '加载角色列表失败');
    }
  } finally {
    loading.value = false;
  }
};

// 加载权限列表
const loadPermissions = async () => {
  permissionsLoading.value = true;
  
  try {
    const response = await permissionAPI.getPermissions();
    availablePermissions.value = response;
    
    // 如果有权限数据且当前没有选中任何权限，自动选中最后一个权限
    if (response.length > 0 && roleForm.value.permissions.length === 0) {
      roleForm.value.permissions = [response[response.length - 1].id];
    }
  } catch (err: any) {
    console.error('加载权限列表失败:', err);
    ElMessage.error('加载权限列表失败');
  } finally {
    permissionsLoading.value = false;
  }
};

// 计算属性：过滤后的角色列表
const filteredRoleList = computed(() => {
  if (!searchParams.value.search.trim()) {
    return roleList.value;
  }
  
  const keywords = searchParams.value.search.trim().toLowerCase().split(/\s+/);
  
  return roleList.value.filter(role => {
    const searchText = `${role.name} ${role.description} ${role.permissions?.join(' ') || ''}`.toLowerCase();
    return keywords.every(keyword => searchText.includes(keyword));
  });
});

// 搜索处理
const handleSearch = () => {
  // 不再重新加载数据，使用客户端过滤
  // loadRoles();
};

// 角色名称筛选方法
const filterName = (value: string, row: RoleWithPermissions) => {
  return row.name === value;
};



// 新增角色
const handleCreate = () => {
  if (!hasAuthEditPermission.value) {
    ElMessage.warning('您没有权限创建角色');
    return;
  }
  
  roleDialog.value.isEdit = false;
  roleDialog.value.visible = true;
  editingRoleId.value = null;
  
  // 重置表单
  roleForm.value = {
    name: '',
    description: '',
    permissions: []
  };
  
  // 加载权限列表
  loadPermissions();
};

// 编辑角色
const handleEdit = (role: RoleWithPermissions) => {
  if (!hasAuthEditPermission.value) {
    ElMessage.warning('您没有权限编辑角色');
    return;
  }
  
  roleDialog.value.isEdit = true;
  roleDialog.value.visible = true;
  editingRoleId.value = role.id;
  
  // 填充表单
  roleForm.value = {
    name: role.name,
    description: role.description,
    permissions: [...role.permissions]
  };
  
  // 加载权限列表
  loadPermissions();
};

// 删除角色
const handleDelete = async (role: RoleWithPermissions) => {
  if (!hasAuthEditPermission.value) {
    ElMessage.warning('您没有权限删除角色');
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 "${role.name}" 吗？此操作不可恢复。`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    await roleAPI.deleteRole(role.id);
    ElMessage.success('角色删除成功');
    loadRoles(); // 重新加载列表
  } catch (err: any) {
    if (err === 'cancel') {
      return; // 用户取消
    }
    
    console.error('删除角色失败:', err);
    
    if (err.response?.status === 400) {
      ElMessage.error('该角色下存在用户，无法删除');
    } else {
      ElMessage.error(err.response?.data?.detail || '删除角色失败');
    }
  }
};

// 保存角色
const handleSaveRole = async () => {
  if (!roleFormRef.value) return;
  
  try {
    await roleFormRef.value.validate();
  } catch {
    return; // 验证失败
  }
  
  roleDialog.value.loading = true;
  
  try {
    if (roleDialog.value.isEdit && editingRoleId.value) {
      // 编辑模式：先更新基本信息，再更新权限
      await roleAPI.updateRole(editingRoleId.value, {
        name: roleForm.value.name,
        description: roleForm.value.description
      });
      
      await roleAPI.updateRolePermissions(editingRoleId.value, {
        permission_ids: roleForm.value.permissions
      });
      
      ElMessage.success('角色更新成功');
    } else {
      // 新增模式
      await roleAPI.createRole({
        name: roleForm.value.name,
        description: roleForm.value.description,
        permissions: roleForm.value.permissions
      });
      
      ElMessage.success('角色创建成功');
    }
    
    roleDialog.value.visible = false;
    loadRoles(); // 重新加载列表
  } catch (err: any) {
    console.error('保存角色失败:', err);
    
    if (err.response?.status === 400) {
      ElMessage.error('角色名称已存在或参数错误');
    } else {
      ElMessage.error(err.response?.data?.detail || '保存角色失败');
    }
  } finally {
    roleDialog.value.loading = false;
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
  
  // 如果有权限，自动加载角色列表
  if (hasAuthReadPermission.value) {
    await loadRoles();
  }
});
</script>

<style src="../../../css/base-styles.css"></style>
<style scoped>
/* 角色管理组件特定样式 */
.permission-hint {
  margin-top: 8px;
}

/* 确保卡片头部不占用额外空间 */
.account-table-card--flex :deep(.el-card__header) {
  flex-shrink: 0;
  padding: 16px 20px;
}

/* 确保卡片内容区域填充剩余空间 */
.account-table-card--flex :deep(.el-card__body) {
  flex: 1;
  min-height: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}
</style>