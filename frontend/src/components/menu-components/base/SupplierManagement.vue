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
        <p>您没有足够的权限访问供应商管理功能。</p>
        <p>需要权限：<el-tag type="danger">BASE-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 供应商管理内容 -->
    <div v-else class="base-content base-flex-content">
      <!-- 操作栏 -->
      <el-card class="base-operation-card" shadow="hover">
        <div class="base-operation-bar">
          <div class="base-operation-bar__left">
            <el-button 
              type="primary" 
              @click="handleCreate"
              v-if="hasPermission('BASE-edit')"
              :icon="Plus"
            >
              新增供应商
            </el-button>
            <el-button 
              type="success" 
              @click="handleImport"
              v-if="hasPermission('BASE-edit')"
              :icon="Upload"
            >
              导入供应商
            </el-button>
            <el-button 
              type="info" 
              @click="handleDownloadTemplate"
              v-if="hasPermission('BASE-read')"
              :icon="Download"
              :loading="templateDownloading"
            >
              下载模板
            </el-button>
            <el-button 
              type="default" 
              @click="refreshSuppliers"
              :loading="loading"
              :icon="Refresh"
            >
              刷新
            </el-button>

            
            <!-- 批量删除按钮 -->
            <el-button 
              v-if="hasPermission('BASE-edit') && selectedSuppliers.length > 0"
              type="danger" 
              @click="handleBatchDelete"
              :icon="Delete"
            >
              批量删除 ({{ selectedSuppliers.length }})
            </el-button>
          </div>
          
          <div class="base-operation-bar__right">
            <el-input
              v-model="searchKeyword"
              placeholder="输入搜索关键词，用空格分隔"
              style="width: 320px;"
              clearable
              @input="handleSearch"
              @clear="handleClearSearch"
            />
          </div>
        </div>
      </el-card>

      <!-- 供应商列表 -->
      <el-card class="base-table-card base-table-card--flex" shadow="hover">
          <template #header>
            <div class="base-card-header">
              <el-icon><List /></el-icon>
              <span>供应商列表</span>
              <div class="base-card-header__stats" v-if="statistics">
                <span>总计: {{ statistics.total_suppliers || 0 }}</span>
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
          
          <!-- 供应商表格 -->
          <div v-else class="base-table base-table--auto-height">
            <el-table 
              ref="tableRef"
              :data="suppliers" 
              stripe 
              border
              @selection-change="handleSelectionChange"
              @sort-change="handleSortChange"
              :empty-text="'暂无供应商数据'"
              class="base-table"
            >
              <el-table-column type="selection" width="55" align="center" />
              
              <el-table-column 
                v-if="false"
                prop="id" 
                label="ID" 
                width="100" 
                align="center"
                sortable="custom"
                :sort-orders="['ascending', 'descending']"
                fixed="left"
              />
              
              <el-table-column 
                prop="supplier_name" 
                label="供应商名称" 
                min-width="150"
                align="center"
                sortable="custom"
                :sort-orders="['ascending', 'descending']"
                fixed="left"
              >
                <template #default="{ row }">
                  <div class="base-cell base-cell-primary">{{ row.supplier_name }}</div>
                </template>
              </el-table-column>
              
              <el-table-column 
                prop="supplier_city" 
                label="所在城市" 
                min-width="120"
                align="center"
              />
              
              <el-table-column 
                prop="supplier_address" 
                label="详细地址" 
                min-width="200"
                align="center"
              />
              
              <el-table-column 
                prop="supplier_manager" 
                label="负责人" 
                width="120"
                align="center"
              />
              
              <el-table-column 
                prop="supplier_contact" 
                label="联系方式" 
                width="150"
                align="center"
              />
              
              <el-table-column 
                prop="creator" 
                label="创建人" 
                width="120"
                align="center"
              />
              
              <el-table-column 
                prop="create_time" 
                label="创建时间" 
                width="180"
                align="center"
                sortable="custom"
                :sort-orders="['ascending', 'descending']"
              >
                <template #default="{ row }">
                  {{ formatDateTime(row.create_time) }}
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
                  {{ formatDateTime(row.update_time) }}
                </template>
              </el-table-column>
              
              <el-table-column 
                label="操作" 
                width="120" 
                align="center" 
                fixed="right"
                v-if="hasPermission('BASE-edit')"
              >
                <template #default="{ row }">
                  <div class="base-action-buttons">
                    <ActionTooltip 
                    content="编辑供应商"
                  >
                    <el-button 
                      type="primary" 
                      size="small" 
                      @click="handleEdit(row)"
                      v-if="hasPermission('BASE-edit')"
                      :icon="Edit"
                      class="base-button-circle"
                    />
                  </ActionTooltip>
                    
                    <ActionTooltip 
                    content="删除供应商"
                  >
                    <el-button 
                      type="danger" 
                      size="small" 
                      @click="handleDelete(row)"
                      v-if="hasPermission('BASE-edit')"
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
        :title="isEdit ? '编辑供应商' : '新增供应商'"
        size="600px"
        direction="rtl"
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
            <el-form-item label="供应商名称" prop="supplier_name">
              <el-input 
                v-model="formData.supplier_name" 
                placeholder="请输入供应商名称" 
                maxlength="100"
              />
            </el-form-item>
            <el-form-item label="所在城市" prop="supplier_city">
              <el-input 
                v-model="formData.supplier_city" 
                placeholder="请输入所在城市" 
                maxlength="50"
              />
            </el-form-item>
            <el-form-item label="详细地址" prop="supplier_address">
              <el-input 
                v-model="formData.supplier_address" 
                placeholder="请输入详细地址" 
                maxlength="200"
                type="textarea"
                :rows="3"
              />
            </el-form-item>
            <el-form-item label="负责人" prop="supplier_manager">
              <el-input 
                v-model="formData.supplier_manager" 
                placeholder="请输入负责人姓名" 
                maxlength="50"
              />
            </el-form-item>
            <el-form-item label="联系方式" prop="supplier_contact">
              <el-input 
                v-model="formData.supplier_contact" 
                placeholder="请输入联系方式" 
                maxlength="20"
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

      <!-- 供应商导入对话框 -->
      <el-dialog
        v-model="importDialogVisible"
        title="供应商数据导入"
        width="80%"
        :close-on-click-modal="false"
        :destroy-on-close="true"
      >
        <UniversalImport
          :config="supplierImportConfig"
          @import-completed="handleImportCompleted"
          @close="importDialogVisible = false"
        />
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject,ref,Ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh, Search, Edit, Delete, List, Upload, Download } from '@element-plus/icons-vue'
import { supplierAPI } from '@/services/base/supplier'
import type { SupplierResponse, SupplierCreate, SupplierUpdate, SupplierStatistics, SupplierQueryParams } from '@/services/types/supplier'
import type { BatchImportResult } from '@/services/types/import'
import { supplierImportConfig } from '@/services/importConfig'
import { UniversalImport } from '@/components/common/import'
import ActionTooltip from './ActionTooltip.vue'

const currentUser = inject<Ref<any | null>>('currentUser') || ref<any | null>(null)

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
const templateDownloading = ref(false)
const error = ref<string | null>(null)
const suppliers = ref<SupplierResponse[]>([])
const selectedSuppliers = ref<SupplierResponse[]>([])
const statistics = ref<SupplierStatistics | null>(null)

// 搜索和筛选
const searchKeyword = ref('')
const searchParams = ref<SupplierQueryParams>({
  page: 1,
  page_size: 10,
  search: '',
  sort_field: 'id', // 默认按ID排序
  sort_asc: true   // 默认升序
})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

// 对话框
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive({
  id: 0,
  supplier_name: '',
  supplier_city: '',
  supplier_address: '',
  supplier_contact: '',
  supplier_manager: ''
} as { id: number } & (SupplierCreate | SupplierUpdate))

// 临时保存的数据
const tempFormData = ref<typeof formData | null>(null)
const lastMenuType = ref<'create' | 'edit' | null>(null)
// 保存原始数据用于比较
const originalFormData = ref<typeof formData | null>(null)

// 表单验证规则
const formRules: FormRules = {
  supplier_name: [
    { required: true, message: '供应商名称不能为空', trigger: 'blur' },
    { min: 1, max: 100, message: '供应商名称长度在1-100个字符', trigger: 'blur' }
  ],
  supplier_city: [
    { min: 0, max: 50, message: '所在城市长度不能超过50个字符', trigger: 'blur' }
  ],
  supplier_address: [
    { min: 0, max: 200, message: '地址长度不能超过200个字符', trigger: 'blur' }
  ],
  supplier_contact: [
    { pattern: /^(\d{3,4}-)?\d{7,8}$|^1[3-9]\d{9}$/, message: '请输入正确的电话号码（手机或固定电话）', trigger: 'blur' }
  ],
  supplier_manager: [
    { min: 0, max: 50, message: '负责人姓名长度不能超过50个字符', trigger: 'blur' }
  ]
}

// 表格引用
import type { ElTable } from 'element-plus'
const tableRef = ref<InstanceType<typeof ElTable>>();

// 当前排序状态
const currentSortProp = ref<string>('');
const currentSortOrder = ref<'ascending' | 'descending' | null>(null);

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
    const supportedSortFields = ['id', 'supplier_name', 'create_time', 'update_time'];
    
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
      loadSuppliers();
    }
  }
};

// 加载供应商列表
const loadSuppliers = async () => {
  if (!hasPermission('BASE-read')) return
  
  loading.value = true
  error.value = null
  
  try {
    // 构建查询参数 - 使用后端API期望的参数格式
    const queryParams: SupplierQueryParams = {
      page: searchParams.value.page,
      page_size: searchParams.value.page_size,
      sort_field: searchParams.value.sort_field,
      sort_asc: searchParams.value.sort_asc
    }
    
    // 处理搜索关键词 - 使用统一的search参数，后端支持多关键词搜索
    if (searchParams.value.search && searchParams.value.search.trim()) {
      queryParams.search = searchParams.value.search.trim()
    }
    
    const response = await supplierAPI.getSuppliers(queryParams)
    suppliers.value = response.data
    pagination.total = response.total
    pagination.current = searchParams.value.page || 1
    pagination.pageSize = searchParams.value.page_size || 10
    
    // 在数据加载完成后，恢复排序状态
    await nextTick();
    restoreSortState();
    
    // 加载统计信息
    await loadStatistics()
  } catch (err: any) {
    console.error('加载供应商列表失败:', err)
    error.value = err.response?.data?.detail || '加载供应商列表失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const response = await supplierAPI.getSupplierStatistics()
    statistics.value = response
  } catch (err) {
    console.error('加载供应商统计信息失败:', err)
  }
}

// 刷新供应商列表
const refreshSuppliers = () => {
  searchParams.value.page = 1
  loadSuppliers()
}

// 处理搜索
const handleSearch = () => {
  searchParams.value.search = searchKeyword.value
  searchParams.value.page = 1
  loadSuppliers()
}

// 清除搜索
const handleClearSearch = () => {
  searchKeyword.value = ''
  searchParams.value.search = ''
  searchParams.value.page = 1
  loadSuppliers()
}



// 处理选择变化
const handleSelectionChange = (selection: SupplierResponse[]) => {
  selectedSuppliers.value = selection
}

// 处理分页大小变化
const handleSizeChange = (size: number) => {
  searchParams.value.page_size = size
  searchParams.value.page = 1
  loadSuppliers()
}

// 处理当前页变化
const handleCurrentChange = (page: number) => {
  searchParams.value.page = page
  loadSuppliers()
}

// 处理创建
const handleCreate = () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('您没有编辑权限')
    return
  }
  
  // 检查是否是同一个菜单类型
  if (lastMenuType.value === 'create' && tempFormData.value) {
    // 恢复之前的数据
    Object.assign(formData, tempFormData.value)
  } else {
    // 重置表单数据
    Object.assign(formData, {
      id: 0,
      supplier_name: '',
      supplier_city: '',
      supplier_address: '',
      supplier_contact: '',
      supplier_manager: ''
    })
    // 保存原始数据用于比较
    originalFormData.value = { ...formData }
  }
  
  isEdit.value = false
  lastMenuType.value = 'create'
  dialogVisible.value = true
}

// 处理导入
const handleImport = () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('您没有编辑权限')
    return
  }
  
  importDialogVisible.value = true
}

// 处理导入完成
const handleImportCompleted = (result: BatchImportResult) => {
  console.log('供应商导入完成:', result)
  
  // 在后台刷新供应商列表，但不显示给用户
  loadSuppliers()
}

// 处理下载模板
const handleDownloadTemplate = async () => {
  if (!hasPermission('BASE-read')) {
    ElMessage.warning('您没有查看权限')
    return
  }
  
  try {
    templateDownloading.value = true
    const blob = await supplierAPI.downloadSupplierTemplate()
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '供应商导入模板.xls'
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('模板下载成功')
  } catch (error: any) {
    console.error('下载模板失败:', error)
    ElMessage.error(`模板下载失败：${error.response?.data?.detail || error.message || '网络错误'}`)
  } finally {
    templateDownloading.value = false
  }
}

// 处理编辑
const handleEdit = (supplier: SupplierResponse) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有编辑供应商的权限')
    return
  }
  
  // 检查是否是同一个菜单类型
  if (lastMenuType.value === 'edit' && tempFormData.value) {
    // 恢复之前的数据
    Object.assign(formData, tempFormData.value)
  } else {
    // 填充表单数据
    Object.assign(formData, {
      id: supplier.id,
      supplier_name: supplier.supplier_name,
      supplier_city: supplier.supplier_city,
      supplier_address: supplier.supplier_address,
      supplier_contact: supplier.supplier_contact,
      supplier_manager: supplier.supplier_manager
    })
    // 保存原始数据用于比较
    originalFormData.value = { ...formData }
  }
  
  isEdit.value = true
  lastMenuType.value = 'edit'
  dialogVisible.value = true
}

// 处理删除
const handleDelete = async (supplier: SupplierResponse) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有删除供应商的权限')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除供应商"${supplier.supplier_name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await supplierAPI.deleteSupplier(supplier.id)
    ElMessage.success('删除成功')
    // 删除后清除所有选中状态，让用户重新选择
    selectedSuppliers.value = []
    loadSuppliers()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 处理批量删除
const handleBatchDelete = async () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('您没有删除权限')
    return
  }
  
  if (selectedSuppliers.value.length === 0) {
    ElMessage.warning('请选择要删除的供应商')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedSuppliers.value.length} 个供应商吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    const ids = selectedSuppliers.value.map(s => s.id)
    await supplierAPI.batchDeleteSuppliers({ supplier_ids: ids })
    ElMessage.success('批量删除成功')
    selectedSuppliers.value = []
    loadSuppliers()
  } catch (err) {
    if (err !== 'cancel') {
      console.error('批量删除供应商失败:', err)
      ElMessage.error('批量删除失败，请稍后重试')
    }
  }
}

// 处理对话框关闭
const handleDialogClose = (done: () => void) => {
  // 检查是否有真正的数据修改
  const hasRealChanges = originalFormData.value && (
    formData.supplier_name !== originalFormData.value.supplier_name ||
    formData.supplier_city !== originalFormData.value.supplier_city ||
    formData.supplier_address !== originalFormData.value.supplier_address ||
    formData.supplier_contact !== originalFormData.value.supplier_contact ||
    formData.supplier_manager !== originalFormData.value.supplier_manager
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
      // 更新供应商
      const updateData: SupplierUpdate = {
        supplier_name: formData.supplier_name,
        supplier_city: formData.supplier_city,
        supplier_address: formData.supplier_address,
        supplier_contact: formData.supplier_contact,
        supplier_manager: formData.supplier_manager
      }
      await supplierAPI.updateSupplier(formData.id, updateData)
      ElMessage.success('更新成功')
    } else {
      // 创建供应商
      const createData: SupplierCreate = {
        supplier_name: formData.supplier_name || '',
        supplier_city: formData.supplier_city,
        supplier_address: formData.supplier_address,
        supplier_contact: formData.supplier_contact,
        supplier_manager: formData.supplier_manager
      }
      await supplierAPI.createSupplier(createData)
      ElMessage.success('创建成功')
    }
    
    // 清除临时保存的数据
    tempFormData.value = null
    lastMenuType.value = null
    originalFormData.value = null
    
    dialogVisible.value = false
    loadSuppliers()
  } catch (err: any) {
    if (err.errors) {
      // 表单验证错误
      return
    }
    
    console.error('提交表单失败:', err)
    const errorMsg = err.response?.data?.detail || (isEdit.value ? '更新失败' : '创建失败')
    ElMessage.error(errorMsg)
  }
}

// 格式化日期时间
const formatDateTime = (dateTime: string): string => {
  if (!dateTime) return ''
  
  try {
    const date = new Date(dateTime)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (err) {
    return dateTime
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadSuppliers()
})

// 向模板暴露变量和方法
// 添加导入相关的暴露
defineExpose({
  importDialogVisible,
  supplierImportConfig,
  handleImport,
  handleImportCompleted,
  templateDownloading,
  handleDownloadTemplate
})
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';

/* 使用现代Sass混入 */
@include mixins.table-sort-arrows;
</style>