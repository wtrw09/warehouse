<template>
  <div class="base-management-container">
    <!-- 权限检查 -->
    <el-alert
      v-if="!hasPermission('BASE-read')"
      title="权限不足"
      type="error"
      :closable="false"
      show-icon
      class="base-permission-alert"
    >
      <template #default>
        <p>您没有足够的权限访问客户管理功能。</p>
        <p>需要权限：<el-tag type="danger">BASE-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 客户管理内容 -->
    <div v-else class="base-content">
      <!-- 操作栏 -->
      <el-card class="base-operation-card" shadow="hover">
        <div class="base-operation-bar">
          <div class="base-operation-bar__left">
            <el-button 
              type="primary" 
              @click="handleCreate"
              :disabled="!hasPermission('BASE-edit')"
              :icon="Plus"
              class="base-button"
            >
              新增客户
            </el-button>
            
            <!-- 导入相关按钮 -->
            <el-button 
              type="success" 
              @click="handleImport"
              :disabled="!hasPermission('BASE-edit')"
              :icon="Upload"
              class="base-button"
            >
              导入客户数据
            </el-button>
            <el-button 
              type="info" 
              @click="handleDownloadTemplate"
              :disabled="!hasPermission('BASE-edit')"
              :icon="Download"
              class="base-button"
            >
              下载模板
            </el-button>
            <el-button 
              type="default" 
              @click="refreshCustomers"
              :loading="loading"
              :icon="Refresh"
              class="base-button"
            >
              刷新
            </el-button>
            
            <!-- 批量删除按钮 -->
            <el-button 
              v-if="hasPermission('BASE-edit') && selectedCustomers.length > 0"
              type="danger" 
              @click="handleBatchDelete"
              :icon="Delete"
              class="base-button"
            >
              批量删除 ({{ selectedCustomers.length }})
            </el-button>
          </div>
          
          <div class="base-operation-bar__right">
            <el-input
              v-model="searchKeyword"
              placeholder="输入搜索关键词，用空格分隔"
              style="width: 320px;"
              class="base-select"
              clearable
              @input="handleSearch"
              @clear="handleClearSearch"
            />
          </div>
        </div>
      </el-card>

      <!-- 客户列表 -->
      <el-card class="base-table-card" shadow="hover">
          <template #header>
            <div class="base-card-header">
              <el-icon><List /></el-icon>
              <span>客户列表</span>
              <div class="base-card-header__stats" v-if="statistics">
                <span>总计: {{ statistics.total_customers || 0 }}</span>
              </div>
            </div>
          </template>

          <!-- 加载状态 -->
          <div v-if="loading" class="base-loading-container">
            <el-skeleton :rows="8" animated />
          </div>
          
          <!-- 错误状态 -->
          <el-alert
            v-else-if="error"
            :title="error"
            type="error"
            show-icon
            :closable="false"
            class="base-error-state"
          />
          
          <!-- 客户表格 -->
          <div v-else>
            <el-table 
              ref="tableRef"
              :data="customers" 
              stripe 
              border
              height="400"
              @selection-change="handleSelectionChange"
              @sort-change="handleSortChange"
              :empty-text="'暂无客户数据'"
              class="base-table"
            >
              <el-table-column type="selection" width="55" align="center" />
              
              <el-table-column v-if="false"
                prop="id" 
                label="ID" 
                width="80" 
                align="center" 
                fixed="left"
                sortable="custom"
                :sort-orders="['ascending', 'descending']"
              />
              
              <el-table-column 
                prop="customer_name" 
                label="客户名称" 
                min-width="150" 
                fixed="left" 
                align="center"
                sortable="custom"
                :sort-orders="['ascending', 'descending']"
              >
                <template #default="{ row }">
                  <div class="base-cell base-cell-primary">{{ row.customer_name }}</div>
                </template>
              </el-table-column>
              
              <el-table-column prop="customer_city" label="所在城市" width="120" align="center" />
              
              <el-table-column prop="customer_address" label="地址" min-width="200" align="center">
                <template #default="{ row }">
                  <div class="base-cell">{{ row.customer_address }}</div>
                </template>
              </el-table-column>
              
              <el-table-column prop="customer_manager" label="负责人" width="120" align="center" />
              
              <el-table-column prop="customer_contact" label="联系方式" width="120" align="center" />
              
              <el-table-column prop="creator" label="创建者" width="120" align="center" />
              
              <el-table-column 
                prop="create_time" 
                label="创建时间" 
                width="180" 
                align="center"
                sortable="custom"
                :sort-orders="['ascending', 'descending']"
              >
                <template #default="{ row }">
                  <el-text type="info" size="small">
                    {{ formatDateTime(row.create_time) }}
                  </el-text>
                </template>
              </el-table-column>
              
              <el-table-column 
                prop="update_time" 
                label="更新时间" 
                width="180" 
                align="center"
                sortable="custom"
                :sort-orders="['ascending', 'descending']"
              >
                <template #default="{ row }">
                  <el-text type="info" size="small">
                    {{ formatDateTime(row.update_time) }}
                  </el-text>
                </template>
              </el-table-column>
              
              <el-table-column label="操作" width="120" align="center" fixed="right">
                <template #default="{ row }">
                  <div class="base-action-buttons">
                    <ActionTooltip content="编辑客户" :disabled="!hasPermission('BASE-edit')">
                      <el-button 
                        type="primary"
                        size="small"
                        @click="handleEdit(row)"
                        :disabled="!hasPermission('BASE-edit')"
                        :icon="Edit"
                        class="base-button-circle"
                      />
                    </ActionTooltip>
                    <ActionTooltip content="删除客户" :disabled="!hasPermission('BASE-edit')">
                      <el-button 
                        type="danger"
                        size="small"
                        @click="handleDelete(row)"
                        :disabled="!hasPermission('BASE-edit')"
                        :icon="Delete"
                        class="base-button-circle"
                      />
                    </ActionTooltip>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 分页控件 -->
          <div class="base-pagination-container" v-if="pagination.total > 0">
            <el-pagination
              v-model:current-page="pagination.current"
              v-model:page-size="pagination.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>

      <!-- 新增/编辑抽屉 -->
      <el-drawer
        v-model="dialogVisible"
        :title="isEdit ? '编辑客户' : '新增客户'"
        direction="rtl"
        size="600px"
        :before-close="handleDialogClose"
        :modal="true"
        class="base-drawer"
      >
        <div class="base-drawer-body">
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="100px"
          >
            <el-form-item label="客户名称" prop="customer_name" class="base-form-label">
              <el-input 
                v-model="formData.customer_name" 
                placeholder="请输入客户名称" 
                maxlength="100"
              />
            </el-form-item>
            <el-form-item label="所在城市" prop="customer_city" class="base-form-label">
              <el-input 
                v-model="formData.customer_city" 
                placeholder="请输入所在城市" 
                maxlength="50"
              />
            </el-form-item>
            <el-form-item label="地址" prop="customer_address" class="base-form-label">
              <el-input 
                v-model="formData.customer_address" 
                placeholder="请输入地址" 
                maxlength="200"
                type="textarea"
                :rows="3"
              />
            </el-form-item>
            <el-form-item label="联系方式" prop="customer_contact" class="base-form-label">
              <el-input 
                v-model="formData.customer_contact" 
                placeholder="请输入联系方式" 
                maxlength="20"
              />
            </el-form-item>
            <el-form-item label="负责人" prop="customer_manager" class="base-form-label">
              <el-input 
                v-model="formData.customer_manager" 
                placeholder="请输入负责人姓名" 
                maxlength="50"
              />
            </el-form-item>
          </el-form>
        </div>
        <template #footer>
          <div class="base-drawer-footer">
            <el-button @click="dialogVisible = false" class="base-button">取消</el-button>
            <el-button type="primary" @click="submitForm" class="base-button">
              {{ isEdit ? '更新' : '创建' }}
            </el-button>
          </div>
        </template>
      </el-drawer>

      <!-- 导入对话框 -->
      <el-dialog
        v-model="importDialogVisible"
        title="导入客户数据"
        width="80%"
        destroy-on-close
      >
        <div class="base-dialog-body">
          <UniversalImport
            ref="importDialogRef"
            :config="customerImportConfig"
            @import-completed="handleImportCompleted"
            @close="importDialogVisible = false"
          />
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, ref, Ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh, Search, Edit, Delete, List, Upload, Download } from '@element-plus/icons-vue'
import { customerAPI } from '@/services/base/customer'
import type { CustomerResponse, CustomerCreate, CustomerUpdate, CustomerStatistics, CustomerQueryParams } from '@/services/types/customer'
import type { BatchImportResult } from '@/services/types/import'
import ActionTooltip from './ActionTooltip.vue'
import { customerImportConfig, customerService } from '@/services/importConfig'
import { UniversalImport } from '@/components/common/import'
// 删除useBaseStyles导入

const currentUser = inject<Ref<any | null>>('currentUser') || ref<any | null>(null)

// 删除样式管理相关代码
// const { classes } = useBaseStyles()

/**
 * 检查当前用户是否拥有指定权限
 * @param permission 权限名称字符串，如 'BASE-read', 'BASE-edit'
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
const error = ref<string | null>(null)
const customers = ref<CustomerResponse[]>([])
const selectedCustomers = ref<CustomerResponse[]>([])
const statistics = ref<CustomerStatistics | null>(null)

// 表格引用
import type { ElTable } from 'element-plus'
const tableRef = ref<InstanceType<typeof ElTable>>()

// 搜索和筛选
const searchKeyword = ref('')
const searchParams = ref({
  page: 1,
  page_size: 10,
  search: '',
  sort_field: 'id',
  sort_asc: true
})

// 当前排序状态
const currentSortProp = ref<string>('')
const currentSortOrder = ref<'ascending' | 'descending' | null>(null)

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive({
  id: 0,
  customer_name: '',
  customer_city: '',
  customer_address: '',
  customer_contact: '',
  customer_manager: ''
} as { id: number } & (CustomerCreate | CustomerUpdate))

// 导入相关状态
const importDialogVisible = ref(false)
const importDialogRef = ref<InstanceType<typeof UniversalImport>>()

// 临时保存的数据
const tempFormData = ref<typeof formData | null>(null)
const lastMenuType = ref<'create' | 'edit' | null>(null)
// 保存原始数据用于比较
const originalFormData = ref<typeof formData | null>(null)

// 表单验证规则
const formRules: FormRules = {
  customer_name: [
    { required: true, message: '客户名称不能为空', trigger: 'blur' },
    { min: 1, max: 100, message: '客户名称长度在1-100个字符', trigger: 'blur' }
  ],
  customer_city: [
    { min: 0, max: 50, message: '所在城市长度不能超过50个字符', trigger: 'blur' }
  ],
  customer_address: [
    { min: 0, max: 200, message: '地址长度不能超过200个字符', trigger: 'blur' }
  ],
  customer_contact: [
    { pattern: /^(\d{3,4}-)?\d{7,8}$|^1[3-9]\d{9}$/, message: '请输入正确的电话号码（手机或固定电话）', trigger: 'blur' }
  ],
  customer_manager: [
    { min: 0, max: 50, message: '负责人姓名长度不能超过50个字符', trigger: 'blur' }
  ]
}

// 格式化日期时间
const formatDateTime = (dateString: string): string => {
  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (err) {
    return dateString
  }
}

// 加载客户列表
const loadCustomers = async () => {
  if (!hasPermission('BASE-read')) return
  
  loading.value = true
  error.value = null
  
  try {
    // 构建查询参数 - 使用后端API期望的参数格式
    const queryParams: CustomerQueryParams = {
      page: searchParams.value.page,
      page_size: searchParams.value.page_size,
      sort_field: searchParams.value.sort_field as "id" | "customer_name" | "create_time" | "update_time",
      sort_asc: searchParams.value.sort_asc
    }
    
    // 处理搜索关键词 - 使用统一的search参数，后端支持多关键词搜索
    if (searchParams.value.search && searchParams.value.search.trim()) {
      queryParams.search = searchParams.value.search.trim()
    }
    
    const response = await customerAPI.getCustomers(queryParams)
    customers.value = response.data
    pagination.total = response.total
    pagination.current = searchParams.value.page
    pagination.pageSize = searchParams.value.page_size
    
    // 在数据加载完成后，恢复排序状态
    await nextTick();
    restoreSortState();
    
    // 加载统计信息
    await loadStatistics()
  } catch (err: any) {
    error.value = err.message || '加载客户列表失败'
    if (error.value) {
      ElMessage.error(error.value)
    }
  } finally {
    loading.value = false
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const stats = await customerAPI.getCustomerStatistics()
    statistics.value = stats
  } catch (err) {
    console.error('加载统计信息失败:', err)
  }
}

// 刷新数据
const refreshCustomers = () => {
  searchParams.value.page = 1
  loadCustomers()
}

// 搜索处理
const handleSearch = () => {
  searchParams.value.search = searchKeyword.value
  searchParams.value.page = 1
  loadCustomers()
}

// 清空搜索
const handleClearSearch = () => {
  searchKeyword.value = ''
  searchParams.value.search = ''
  searchParams.value.page = 1
  loadCustomers()
}

// 恢复排序状态
const restoreSortState = () => {
  if (tableRef.value && currentSortProp.value && currentSortOrder.value) {
    // 手动设置表格的排序状态
    tableRef.value.sort(currentSortProp.value, currentSortOrder.value);
  }
};

// 表头排序处理
const handleSortChange = ({ prop, order }: { prop: string; order: 'ascending' | 'descending' | null }) => {
  // 保存当前排序状态，用于在表格刷新后恢复排序图标
  currentSortProp.value = prop;
  currentSortOrder.value = order;
  
  if (prop) {
    // 只处理支持排序的字段
    const supportedSortFields = ['id', 'customer_name', 'create_time', 'update_time'];
    
    if (supportedSortFields.includes(prop)) {
      if (order) {
        // 有排序方向：升序或降序
        searchParams.value.sort_field = prop as any;
        searchParams.value.sort_asc = order === 'ascending';
      } else {
        // 取消排序：重置为默认排序
        searchParams.value.sort_field = 'id';
        searchParams.value.sort_asc = true;
      }
      searchParams.value.page = 1;
      loadCustomers();
    }
  }
};

// 分页处理
const handleSizeChange = (size: number) => {
  searchParams.value.page_size = size
  searchParams.value.page = 1
  loadCustomers()
}

const handleCurrentChange = (page: number) => {
  searchParams.value.page = page
  loadCustomers()
}

// 表格选择变化
const handleSelectionChange = (selection: CustomerResponse[]) => {
  selectedCustomers.value = selection
}

// 新增客户
const handleCreate = () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有创建客户的权限')
    return
  }
  
  // 检查是否是同一个菜单类型
  if (lastMenuType.value === 'create' && tempFormData.value) {
    // 恢复之前的数据
    Object.assign(formData, tempFormData.value)
  } else {
    // 清空数据
    Object.assign(formData, {
      id: 0,
      customer_name: '',
      customer_city: '',
      customer_address: '',
      customer_contact: '',
      customer_manager: ''
    })
    // 保存原始数据用于比较
    originalFormData.value = { ...formData }
  }
  
  isEdit.value = false
  lastMenuType.value = 'create'
  dialogVisible.value = true
}

// 编辑客户
const handleEdit = (customer: CustomerResponse) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有编辑客户的权限')
    return
  }
  
  // 检查是否是同一个菜单类型
  if (lastMenuType.value === 'edit' && tempFormData.value) {
    // 恢复之前的数据
    Object.assign(formData, tempFormData.value)
  } else {
    // 填充表单数据
    Object.assign(formData, {
      id: customer.id,
      customer_name: customer.customer_name,
      customer_city: customer.customer_city,
      customer_address: customer.customer_address,
      customer_contact: customer.customer_contact,
      customer_manager: customer.customer_manager
    })
    // 保存原始数据用于比较
    originalFormData.value = { ...formData }
  }
  
  isEdit.value = true
  lastMenuType.value = 'edit'
  dialogVisible.value = true
}

// 删除客户
const handleDelete = async (customer: CustomerResponse) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有删除客户的权限')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除客户"${customer.customer_name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await customerAPI.deleteCustomer(customer.id)
    ElMessage.success('删除成功')
    refreshCustomers()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有批量删除客户的权限')
    return
  }

  if (selectedCustomers.value.length === 0) {
    ElMessage.warning('请选择要删除的客户')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedCustomers.value.length} 个客户吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const ids = selectedCustomers.value.map((item: CustomerResponse) => item.id)
    await customerAPI.batchDeleteCustomers({ customer_ids: ids })
    ElMessage.success('批量删除成功')
    selectedCustomers.value = []
    refreshCustomers()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 对话框关闭处理
const handleDialogClose = (done: () => void) => {
  // 检查是否有真正的数据修改
  const hasRealChanges = originalFormData.value && (
    formData.customer_name !== originalFormData.value.customer_name ||
    formData.customer_city !== originalFormData.value.customer_city ||
    formData.customer_address !== originalFormData.value.customer_address ||
    formData.customer_contact !== originalFormData.value.customer_contact ||
    formData.customer_manager !== originalFormData.value.customer_manager
  )
  
  if (hasRealChanges) {
    // 有真正的数据修改，自动保存并提示用户
    tempFormData.value = { ...formData }
    ElMessage.success('编辑信息已保存')
    done()
  } else {
    // 没有真正的数据修改，直接关闭
    tempFormData.value = null
    done()
  }
}

// 提交表单
const submitForm = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    if (isEdit.value) {
      await customerAPI.updateCustomer(formData.id!, formData as CustomerUpdate)
      ElMessage.success('更新成功')
    } else {
      await customerAPI.createCustomer(formData as CustomerCreate)
      ElMessage.success('创建成功')
    }
    
    // 清除临时保存的数据
    tempFormData.value = null
    lastMenuType.value = null
    originalFormData.value = null
    
    dialogVisible.value = false
    refreshCustomers()
  } catch (err: any) {
    if (err.errors) {
      // 表单验证错误
      return
    }
    
    // 显示具体的错误信息
    let errorMessage = isEdit.value ? '更新失败' : '创建失败'
    
    if (err.response?.data?.detail) {
      // 处理Pydantic验证错误
      if (Array.isArray(err.response.data.detail)) {
        const errorDetail = err.response.data.detail[0]
        errorMessage = errorDetail.msg || errorMessage
      } else {
        errorMessage = err.response.data.detail
      }
    } else if (err.response?.data?.message) {
      errorMessage = err.response.data.message
    } else if (err.message) {
      errorMessage = err.message
    }
    
    ElMessage.error(errorMessage)
  }
}

// 导入相关函数
const handleImport = () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有导入客户数据的权限')
    return
  }
  importDialogVisible.value = true
}

const handleImportCompleted = (result: BatchImportResult) => {
  console.log('客户导入完成:', result)
  
  // 不自动关闭对话框，让用户在进度页面查看结果
  // importDialogVisible.value = false
  
  // 不显示结果消息，由进度页面显示
  // if (result.error_count === 0) {
  //   ElMessage.success(`客户数据导入成功！共导入${result.success_count}条数据`)
  // } else if (result.success_count === 0) {
  //   ElMessage.error(`客户数据导入失败！${result.error_count}条数据有错误`)
  // } else {
  //   ElMessage.warning(`客户数据部分导入成功！成功${result.success_count}条，失败${result.error_count}条`)
  // }
  
  // 在后台刷新客户列表，但不显示给用户
  refreshCustomers()
}

const handleDownloadTemplate = async () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有下载模板的权限')
    return
  }
  
  try {
    const blob = await customerService.downloadTemplate()
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '客户导入模板.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('模板下载成功')
  } catch (err: any) {
    console.error('下载模板失败:', err)
    ElMessage.error('下载模板失败: ' + (err.message || '未知错误'))
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadCustomers()
})
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';

/* 使用现代Sass混入 */
@include mixins.table-sort-arrows;

/* 组件特定样式 */


</style>