<template>
  <div class="account-management-container user-management">
    <!-- 权限不足提示 -->
    <el-alert
      v-if="!hasAuthReadPermission"
      title="权限不足"
      type="error"
      :closable="false"
      show-icon
    >
      <template #default>
        <p>您没有足够的权限访问用户管理功能。</p>
        <p>需要权限：<el-tag type="danger">AUTH-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 用户管理内容 -->
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
              新增用户
            </el-button>
            <el-button 
              type="default" 
              @click="loadUsers"
              :loading="loading"
              :icon="Refresh"
            >
              刷新
            </el-button>
            
            <!-- 批量分配角色按钮 -->
            <el-button 
              v-if="selectedUsers.length > 0 && hasAuthEditPermission"
              type="warning" 
              @click="handleBatchRole"
              :icon="UserFilled"
            >
              批量分配角色 ({{ selectedUsers.length }})
            </el-button>
            
            <!-- 查询登录信息按钮 -->
            <el-button 
              type="info" 
              @click="handleViewLoginRecords"
              :icon="DataAnalysis"
            >
              查询登录信息
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

      <!-- 用户列表 -->
      <el-card class="account-table-card account-table-card--flex" shadow="hover">
        <template #header>
          <div class="account-card-header">
            <div class="header-left">
              <el-icon><List /></el-icon>
              <span>用户列表</span>
            </div>
            <div class="header-stats" v-if="statistics">
              <el-tag type="info" size="small">总用户: {{ statistics.total_users }}</el-tag>
              <el-tag type="warning" size="small">近7天新增: {{ statistics.recent_registrations }}</el-tag>
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
        
        <!-- 用户表格 -->
        <div v-else class="account-table account-table--auto-height">
          <el-table 
            ref="userTableRef"
            :data="filteredUserList" 
            stripe 
            border
            :empty-text="'暂无用户数据'"
            @selection-change="handleSelectionChange"
            :default-sort="{ prop: 'id', order: 'ascending' }"
          >
            <el-table-column type="selection" width="55" align="center" fixed="left" />
            <el-table-column prop="id" label="ID" width="70" align="center" fixed="left" sortable />
            
            <el-table-column prop="username" label="用户名" min-width="150" fixed="left" align="center" sortable>
              <template #default="{ row }">
                <el-tag type="primary" effect="dark">{{ row.username }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column 
              prop="role_name" 
              label="角色" 
              min-width="120" 
              align="center"
              column-key="role_name"
              :filters="roleFilters"
              :filter-multiple="true"
              :filter-method="filterRole"
              sortable
            >
              <template #default="{ row }">
                <el-tag type="success" effect="light">{{ row.role_name }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="department" label="所属单位" min-width="150" align="center">
              <template #default="{ row }">
                <el-text type="info" size="small">{{ row.department || '-' }}</el-text>
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
            
            <el-table-column label="操作" width="160" align="center" fixed="right" v-if="hasAuthEditPermission">
              <template #default="{ row }">
                <el-space>
                  <el-tooltip content="编辑用户" placement="top">
                    <el-button 
                      type="warning"
                      size="small"
                      @click="handleEdit(row)"
                      :disabled="!hasAuthEditPermission && !canEditOwnInfo(row)"
                      :icon="Edit"
                      circle
                    />
                  </el-tooltip>
                  <el-tooltip content="重置密码" placement="top">
                    <el-button 
                      type="info"
                      size="small"
                      @click="handleResetPassword(row)"
                      :disabled="!hasAuthEditPermission"
                      :icon="Key"
                      circle
                    />
                  </el-tooltip>
                  <el-tooltip content="删除用户" placement="top">
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
          
          <!-- 统计信息 -->
          <div class="account-statistics">
            <el-space>
              <el-statistic title="总用户数" :value="pagination.total" />
              <el-statistic title="当前显示" :value="filteredUserList.length" />
              <el-statistic title="选中用户" :value="selectedUsers.length" />
            </el-space>
          </div>
          
          <!-- 分页 -->
          <div class="account-pagination-container">
            <el-pagination
              v-model:current-page="searchParams.page"
              v-model:page-size="searchParams.page_size"
              :page-sizes="[5, 10, 20, 50, 100]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              :pager-count="7"
              background
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
              :page-size-suffix="'条/页'"
              :total-text="'共 {total} 条'"
              :jumper-text="'前往'"
            />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 用户新增/编辑对话框 -->
    <el-dialog
      v-model="userDialog.visible"
      :title="userDialog.isEdit ? '编辑用户' : '新增用户'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userFormRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" :disabled="userDialog.isEdit" />
        </el-form-item>
        <el-form-item v-if="!userDialog.isEdit" label="初始密码" prop="password">
          <el-input 
            v-model="userForm.password" 
            type="password"
            placeholder="请输入初始密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="用户角色" prop="role_id">
          <el-select
            v-model="userForm.role_id"
            placeholder="请选择用户角色"
            style="width: 100%;"
            :loading="rolesLoading"
          >
            <el-option
              v-for="role in availableRoles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="所属单位" prop="department">
          <el-input v-model="userForm.department" placeholder="请输入所属单位（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="userDialog.visible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleSaveUser"
            :loading="userDialog.loading"
          >
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 密码重置对话框 -->
    <el-dialog
      v-model="passwordDialog.visible"
      title="重置用户密码"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordFormRules"
        label-width="100px"
      >
        <el-form-item label="用户名">
          <el-input :value="passwordDialog.username" disabled />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input 
            v-model="passwordForm.new_password" 
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="passwordDialog.visible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleSavePassword"
            :loading="passwordDialog.loading"
          >
            确定重置
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 批量角色分配对话框 -->
    <el-dialog
      v-model="batchDialog.visible"
      title="批量分配角色"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="batchFormRef"
        :model="batchForm"
        :rules="batchFormRules"
        label-width="100px"
      >
        <el-form-item label="选中用户">
          <el-text>已选择 {{ selectedUsers.length }} 个用户</el-text>
        </el-form-item>
        <el-form-item label="目标角色" prop="role_id">
          <el-select
            v-model="batchForm.role_id"
            placeholder="请选择目标角色"
            style="width: 100%;"
            :loading="rolesLoading"
          >
            <el-option
              v-for="role in availableRoles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="batchDialog.visible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleSaveBatch"
            :loading="batchDialog.loading"
          >
            确定分配
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 登录记录查询弹窗 -->
    <el-dialog
      v-model="loginRecordDialog.visible"
      :title="loginRecordDialog.title"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      class="login-record-dialog"
    >
      <LoginRecordManagement 
        :selected-username="loginRecordDialog.selectedUsername"
        @close="loginRecordDialog.visible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, inject, Ref } from 'vue';
import { ElMessage, ElMessageBox, FormInstance } from 'element-plus';
import { 
  Plus, 
  Refresh, 
  List, 
  Edit, 
  Delete,
  UserFilled,
  Key,
  DataAnalysis
} from '@element-plus/icons-vue';
import { userAPI, roleAPI } from '../../../services/api';
import LoginRecordManagement from './LoginRecordManagement.vue';
import type {
  UserManagementResponse,
  UserManagementCreate,
  UserManagementUpdate,
  UserPasswordReset,
  UserQueryParams,
  BatchUserRoleAssign,
  UserStatistics
} from '../../../services/types/user';
import type { UserInfo } from '../../../services/types/auth';
import type { RoleWithPermissions } from '../../../services/types/role';

// 响应式数据
const userList = ref<UserManagementResponse[]>([]);
const availableRoles = ref<RoleWithPermissions[]>([]);
const selectedUsers = ref<UserManagementResponse[]>([]);
const loading = ref(false);
const rolesLoading = ref(false);
const error = ref<string | null>(null);
const statistics = ref<UserStatistics | null>(null);

// 表格引用
const userTableRef = ref();

// 角色名称筛选器
const roleFilters = ref<{ text: string; value: string }[]>([]);

// 搜索参数
const searchParams = ref<UserQueryParams>({
  page: 1,
  page_size: 10, // 默认每页显示10条
  search: '',
  role_id: undefined
});

// 分页信息
const pagination = ref({
  total: 0,
  page: 1,
  page_size: 10,
  total_pages: 0
});

// 用户对话框
const userDialog = ref({
  visible: false,
  isEdit: false,
  loading: false
});

// 用户表单
const userForm = ref<UserManagementCreate>({
  username: '',
  password: '',
  role_id: undefined as any,
  department: ''
});

const userFormRef = ref<FormInstance>();
const editingUserId = ref<number | null>(null);

// 表单验证规则
const userFormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 1, max: 10, message: '用户名长度在 1 到 10 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度在 6 到 128 个字符', trigger: 'blur' }
  ],
  role_id: [
    { required: true, message: '请选择用户角色', trigger: 'change' }
  ],
  department: [
    { max: 100, message: '所属单位长度不能超过 100 个字符', trigger: 'blur' }
  ]
};

// 密码重置对话框
const passwordDialog = ref({
  visible: false,
  loading: false,
  userId: 0,
  username: ''
});

const passwordForm = ref({
  new_password: ''
});

const passwordFormRef = ref<FormInstance>();
const passwordFormRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 128, message: '密码长度在 6 到 128 个字符', trigger: 'blur' }
  ]
};

// 批量操作对话框
const batchDialog = ref({
  visible: false,
  loading: false
});

const batchForm = ref({
  role_id: undefined as any
});

// 登录记录查询对话框
const loginRecordDialog = ref({
  visible: false,
  title: '所有用户登录记录',
  selectedUsername: ''
});

const batchFormRef = ref<FormInstance>();
const batchFormRules = {
  role_id: [
    { required: true, message: '请选择目标角色', trigger: 'change' }
  ]
};

// 获取当前用户信息（从父组件注入）
const currentUser = inject<Ref<UserInfo | null>>('currentUser') || ref<UserInfo | null>(null);

/**
 * 检查当前用户是否拥有指定权限
 * @param permission 权限名称字符串，如 'AUTH-read', 'AUTH-edit'
 * @returns boolean - 用户是否拥有该权限
 */
const hasPermission = (permission: string): boolean => {
  console.log('当前用户:', currentUser.value);
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

// 计算属性：检查是否有AUTH-edit权限
const hasAuthEditPermission = computed(() => {
  console.log('用户权限:', currentUser.value?.permissions);
  return hasPermission('AUTH-edit');
});

// 计算属性：检查是否有AUTH-own权限
const hasAuthOwnPermission = computed(() => {
  return hasPermission('AUTH-own');
});

// 检查是否可以编辑自己的信息
const canEditOwnInfo = (user: UserManagementResponse): boolean => {
  return hasAuthOwnPermission.value && currentUser.value?.id === user.id;
};

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

// 加载用户列表
const loadUsers = async () => {
  if (!hasAuthReadPermission.value) {
    ElMessage.warning('您没有足够的权限访问用户列表');
    return;
  }

  loading.value = true;
  error.value = null;
  
  try {
    const response = await userAPI.getUsers(searchParams.value);
    userList.value = response.data || [];
    
    // 动态生成角色名称筛选器选项
    const uniqueRoles = [...new Set((response.data || []).map(user => user.role_name))];
    roleFilters.value = uniqueRoles.map(role => ({
      text: role,
      value: role
    }));
    
    pagination.value = {
      total: response.total,
      page: response.page,
      page_size: response.page_size,
      total_pages: response.total_pages
    };
    
  } catch (err: any) {
    console.error('加载用户列表失败:', err);
    
    if (err.response?.status === 403) {
      error.value = '权限不足，无法访问用户管理功能';
      ElMessage.error('权限不足，请与管理员联系');
    } else if (err.response?.status === 401) {
      error.value = '身份验证失败，请重新登录';
      // 全局拦截器已经处理了401错误，这里只记录错误不重复显示
      console.error('认证失败:', err.response?.data?.detail || '请重新登录');
    } else {
      error.value = err.response?.data?.detail || '加载用户列表失败';
      ElMessage.error(error.value || '加载用户列表失败');
    }
  } finally {
    loading.value = false;
  }
};

// 加载角色列表
const loadRoles = async () => {
  rolesLoading.value = true;
  
  try {
    const response = await roleAPI.getRoles({ page: 1, page_size: 100 });
    availableRoles.value = response.data || [];
  } catch (err: any) {
    console.error('加载角色列表失败:', err);
    ElMessage.error('加载角色列表失败');
  } finally {
    rolesLoading.value = false;
  }
};

// 加载统计信息
const loadStatistics = async () => {
  try {
    statistics.value = await userAPI.getStatistics();
  } catch (err: any) {
    console.error('加载统计信息失败:', err);
  }
};

// 计算属性：过滤后的用户列表
const filteredUserList = computed(() => {
  if (!searchParams.value.search || !searchParams.value.search.trim()) {
    return userList.value;
  }
  
  const keywords = (searchParams.value.search || '').trim().toLowerCase().split(/\s+/);
  
  return userList.value.filter(user => {
    const searchText = `${user.username} ${user.role_name}`.toLowerCase();
    return keywords.every(keyword => searchText.includes(keyword));
  });
});

// 搜索处理
const handleSearch = () => {
  // 不再重新加载数据，使用客户端过滤
  // searchParams.value.page = 1;
  // loadUsers();
};

// 角色筛选方法
const filterRole = (value: string, row: UserManagementResponse) => {
  return row.role_name === value;
};

// 分页大小变化处理
const handleSizeChange = (size: number) => {
  searchParams.value.page_size = size;
  searchParams.value.page = 1;
  loadUsers();
};

// 当前页码变化处理
const handleCurrentChange = (page: number) => {
  searchParams.value.page = page;
  loadUsers();
};

// 选择变化处理
const handleSelectionChange = (selection: UserManagementResponse[]) => {
  selectedUsers.value = selection;
};

// 批量分配角色
const handleBatchRole = () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('请选择要操作的用户');
    return;
  }
  batchDialog.value.visible = true;
  batchForm.value.role_id = undefined as any;
};

// 新增用户
const handleCreate = () => {
  if (!hasAuthEditPermission.value) {
    ElMessage.warning('您没有权限创建用户');
    return;
  }
  
  userDialog.value.isEdit = false;
  userDialog.value.visible = true;
  editingUserId.value = null;
  
  userForm.value = {
    username: '',
    password: '',
    role_id: undefined as any,
    department: ''
  };
  
  loadRoles();
};

// 编辑用户
const handleEdit = (user: UserManagementResponse) => {
  if (!hasAuthEditPermission.value && !canEditOwnInfo(user)) {
    ElMessage.warning('您没有权限编辑此用户');
    return;
  }
  
  userDialog.value.isEdit = true;
  userDialog.value.visible = true;
  editingUserId.value = user.id;
  
  userForm.value = {
    username: user.username,
    password: '',
    role_id: user.role_id,
    department: user.department || ''
  };
  
  loadRoles();
};

// 重置密码
const handleResetPassword = (user: UserManagementResponse) => {
  if (!hasAuthEditPermission.value) {
    ElMessage.warning('您没有权限重置密码');
    return;
  }
  
  passwordDialog.value.visible = true;
  passwordDialog.value.userId = user.id;
  passwordDialog.value.username = user.username;
  passwordForm.value.new_password = '';
};

// 删除用户
const handleDelete = async (user: UserManagementResponse) => {
  if (!hasAuthEditPermission.value) {
    ElMessage.warning('您没有权限删除用户');
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作为软删除，数据不会物理删除。`,
      '警告',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    await userAPI.deleteUser(user.id);
    ElMessage.success('用户删除成功');
    
    // 如果删除的用户在选中列表中，则从选中列表中移除
    const selectedIndex = selectedUsers.value.findIndex(selectedUser => selectedUser.id === user.id);
    if (selectedIndex > -1) {
      selectedUsers.value.splice(selectedIndex, 1);
    }
    
    loadUsers();
    loadStatistics();
  } catch (err: any) {
    if (err === 'cancel') {
      return;
    }
    
    console.error('删除用户失败:', err);
    
    if (err.response?.status === 409) {
      ElMessage.error('不能删除最后一个管理员用户');
    } else {
      ElMessage.error(err.response?.data?.detail || '删除用户失败');
    }
  }
};

// 保存用户
const handleSaveUser = async () => {
  if (!userFormRef.value) return;
  
  try {
    await userFormRef.value.validate();
  } catch {
    return;
  }
  
  userDialog.value.loading = true;
  
  try {
    if (userDialog.value.isEdit && editingUserId.value) {
      // 编辑模式
      const updateData: UserManagementUpdate = {
        username: userForm.value.username,
        role_id: userForm.value.role_id,
        department: userForm.value.department || undefined
      };
      
      await userAPI.updateUser(editingUserId.value, updateData);
      ElMessage.success('用户更新成功');
    } else {
      // 新增模式
      const createData: UserManagementCreate = {
        username: userForm.value.username,
        password: userForm.value.password,
        role_id: userForm.value.role_id,
        department: userForm.value.department || undefined
      };
      
      await userAPI.createUser(createData);
      ElMessage.success('用户创建成功');
    }
    
    userDialog.value.visible = false;
    loadUsers();
    loadStatistics();
  } catch (err: any) {
    console.error('保存用户失败:', err);
    
    if (err.response?.status === 400 || err.response?.status === 422) {
      // 处理后端验证错误，显示具体的错误信息
      const errorData = err.response?.data;
      if (errorData?.detail && Array.isArray(errorData.detail)) {
        // 提取第一个错误信息显示给用户
        const firstError = errorData.detail[0];
        if (firstError.msg) {
          ElMessage.error(firstError.msg);
        } else {
          ElMessage.error('参数验证失败，请检查输入');
        }
      } else if (errorData?.detail) {
        // 如果是字符串类型的错误信息
        ElMessage.error(errorData.detail);
      } else {
        ElMessage.error('用户名已存在或参数错误');
      }
    } else {
      ElMessage.error(err.response?.data?.detail || '保存用户失败');
    }
  } finally {
    userDialog.value.loading = false;
  }
};

// 保存密码重置
const handleSavePassword = async () => {
  if (!passwordFormRef.value) return;
  
  try {
    await passwordFormRef.value.validate();
  } catch {
    return;
  }
  
  passwordDialog.value.loading = true;
  
  try {
    const resetData: UserPasswordReset = {
      new_password: passwordForm.value.new_password
    };
    
    await userAPI.resetUserPassword(passwordDialog.value.userId, resetData);
    ElMessage.success('密码重置成功');
    passwordDialog.value.visible = false;
  } catch (err: any) {
    console.error('密码重置失败:', err);
    
    if (err.response?.status === 400) {
      ElMessage.error('新密码与当前密码相同，请选择一个不同的密码');
    } else {
      ElMessage.error(err.response?.data?.detail || '密码重置失败');
    }
  } finally {
    passwordDialog.value.loading = false;
  }
};

// 查询登录信息
const handleViewLoginRecords = () => {
  // 检查是否有查看登录记录的权限
  if (!hasAuthReadPermission.value) {
    ElMessage.warning('您没有足够的权限查看登录记录');
    return;
  }
  
  // 设置选中的用户名（如果有选中的用户）
  if (selectedUsers.value.length === 1) {
    const selectedUser = selectedUsers.value[0];
    loginRecordDialog.value.selectedUsername = selectedUser.username;
    loginRecordDialog.value.title = `用户 ${selectedUser.username} 的登录记录`;
  } else {
    loginRecordDialog.value.selectedUsername = '';
    loginRecordDialog.value.title = '所有用户登录记录';
  }
  
  // 打开登录记录弹窗
  loginRecordDialog.value.visible = true;
};

// 保存批量操作
const handleSaveBatch = async () => {
  if (!batchFormRef.value) return;
  
  try {
    await batchFormRef.value.validate();
  } catch {
    return;
  }
  
  batchDialog.value.loading = true;
  
  try {
    const userIds = selectedUsers.value.map(user => user.id);
    const batchData: BatchUserRoleAssign = {
      user_ids: userIds,
      role_id: batchForm.value.role_id
    };
    
    const result = await userAPI.batchAssignRole(batchData);
    ElMessage.success(result.message);
    
    batchDialog.value.visible = false;
    selectedUsers.value = [];
    // 清空表格中的选择状态
    if (userTableRef.value) {
      userTableRef.value.clearSelection();
    }
    loadUsers();
    loadStatistics();
  } catch (err: any) {
    console.error('批量操作失败:', err);
    ElMessage.error(err.response?.data?.detail || '批量操作失败');
  } finally {
    batchDialog.value.loading = false;
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
  
  // 如果有权限，自动加载数据
  if (hasAuthReadPermission.value) {
    await Promise.all([
      loadUsers(),
      loadRoles(),
      loadStatistics()
    ]);
  }
});
</script>

<style src="../../../css/base-styles.css"></style>
<style scoped>
/* 用户管理组件特定样式 */

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
 