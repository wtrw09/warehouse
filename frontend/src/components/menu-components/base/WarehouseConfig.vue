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
        <p>您没有足够的权限访问仓库配置功能。</p>
        <p>需要权限：<el-tag type="danger">BASE-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 仓库管理内容 -->
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
              新增仓库
            </el-button>
            <el-button 
              type="success" 
              @click="handleImport"
              v-if="hasPermission('BASE-edit')"
              :icon="Upload"
            >
              导入仓库数据
            </el-button>
            <el-button 
              type="info" 
              @click="handleDownloadTemplate"
              v-if="hasPermission('BASE-edit')"
              :icon="Download"
              :loading="templateDownloading"
            >
              下载模板
            </el-button>
            <el-button 
              type="default" 
              @click="refreshWarehouses"
              :loading="loading"
              :icon="Refresh"
            >
              刷新
            </el-button>
            
            <!-- 批量删除按钮 -->
            <el-button 
              v-if="hasPermission('BASE-edit') && selectedWarehouses.length > 0"
              type="danger" 
              @click="handleBatchDelete"
              :icon="Delete"
            >
              批量删除 ({{ selectedWarehouses.length }})
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

      <!-- 仓库列表 -->
      <el-card class="base-table-card base-table-card--flex" shadow="hover">
          <template #header>
            <div class="base-card-header">
              <el-icon><List /></el-icon>
              <span>仓库列表</span>
              <div class="base-card-header__stats" v-if="statistics">
                <span>总计: {{ statistics.total_warehouses || 0 }}</span>
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
          
          <!-- 仓库表格 -->
          <div v-else class="base-table base-table--auto-height">
            <el-table 
              ref="tableRef"
              :data="warehouses" 
              stripe 
              border
              @selection-change="handleSelectionChange"
              @sort-change="handleSortChange"
              :empty-text="'暂无仓库数据'"
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
                prop="warehouse_name" 
                label="仓库名" 
                min-width="150"
                align="center"
                sortable="custom"
                :sort-orders="['ascending', 'descending']"
                fixed="left"
              >
                <template #default="{ row }">
                  <el-tag class="base-tag-primary-dark">{{ row.warehouse_name }}</el-tag>
                </template>
              </el-table-column>
              
              <el-table-column 
                prop="warehouse_city" 
                label="所在城市" 
                min-width="120"
                align="center"
              />
              
              <el-table-column 
                prop="warehouse_address" 
                label="详细地址" 
                min-width="200"
                align="center"
              />
              
              <el-table-column 
                prop="warehouse_manager" 
                label="负责人" 
                width="120"
                align="center"
              />
              
              <el-table-column 
                prop="warehouse_contact" 
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
                  <div class="base-action-buttons" >
                    <ActionTooltip 
                      content="编辑仓库" 
                      :disabled="!hasPermission('BASE-edit')"
                    >
                      <el-button 
                        type="primary" 
                        size="small" 
                        @click="handleEdit(row)"
                        :disabled="!hasPermission('BASE-edit')"
                        :icon="Edit"
                        class="base-button-circle"
                      />
                    </ActionTooltip>
                    
                    <ActionTooltip 
                      content="删除仓库" 
                      :disabled="!hasPermission('BASE-edit')"
                    >
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
        :title="isEdit ? '编辑仓库' : '新增仓库'"
        size="600px"
        direction="rtl"
        :before-close="handleDialogClose"
        :modal="true"
        class="base-drawer"
      >
        <div class="base-drawer-content">
          <el-form
            ref="formRef"
            :model="formData"
            :rules="formRules"
            label-width="100px"
          >
            <el-form-item label="仓库名" prop="warehouse_name">
              <el-input 
                v-model="formData.warehouse_name" 
                placeholder="请输入仓库名" 
                maxlength="100"
              />
            </el-form-item>
            <el-form-item label="仓库城市" prop="warehouse_city">
              <el-input 
                v-model="formData.warehouse_city" 
                placeholder="请输入仓库城市" 
                maxlength="50"
              />
            </el-form-item>
            <el-form-item label="仓库地址" prop="warehouse_address">
              <el-input 
                v-model="formData.warehouse_address" 
                placeholder="请输入仓库地址" 
                maxlength="200"
                type="textarea"
                :rows="3"
              />
            </el-form-item>
            <el-form-item label="负责人" prop="warehouse_manager">
              <el-input 
                v-model="formData.warehouse_manager" 
                placeholder="请输入负责人姓名" 
                maxlength="50"
              />
            </el-form-item>
            <el-form-item label="联系电话" prop="warehouse_contact">
              <el-input 
                v-model="formData.warehouse_contact" 
                placeholder="请输入联系电话" 
                maxlength="20"
              />
            </el-form-item>
          </el-form>
          <div class="base-drawer-footer">
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" @click="submitForm">
              {{ isEdit ? '更新' : '创建' }}
            </el-button>
          </div>
        </div>
      </el-drawer>

      <!-- 仓库导入对话框 -->
      <el-dialog
        v-model="importDialogVisible"
        title="仓库数据导入"
        width="80%"
        :close-on-click-modal="false"
        :destroy-on-close="true"
      >
        <UniversalImport
          :config="warehouseImportConfig"
          @import-completed="handleImportCompleted"
          @close="importDialogVisible = false"
        />
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, ref, Ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Refresh, Edit, Delete, List, Upload, Download } from '@element-plus/icons-vue'
import { warehouseAPI } from '@/services/base/warehouse'
import type { WarehouseResponse, WarehouseCreate, WarehouseUpdate, WarehouseStatistics, WarehouseQueryParams } from '@/services/types/warehouse'
import type { BatchImportResult } from '@/services/types/import'
import { warehouseImportConfig } from '@/services/importConfig'
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
const error = ref<string | null>(null)
const warehouses = ref<WarehouseResponse[]>([])
const selectedWarehouses = ref<WarehouseResponse[]>([])
const statistics = ref<WarehouseStatistics | null>(null)

// 导入相关状态
const importDialogVisible = ref(false)
const templateDownloading = ref(false)

// 搜索和筛选
const searchKeyword = ref('')
const searchParams = ref({
  page: 1,
  page_size: 10,
  search: '',
  sort_field: 'id',
  sort_asc: true
})

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
  warehouse_name: '',
  warehouse_city: '',
  warehouse_address: '',
  warehouse_contact: '',
  warehouse_manager: ''
} as { id: number } & (WarehouseCreate | WarehouseUpdate))

// 临时保存的数据
const tempFormData = ref<typeof formData | null>(null)
const lastMenuType = ref<'create' | 'edit' | null>(null)
// 保存原始数据用于比较
const originalFormData = ref<typeof formData | null>(null)

// 表单验证规则
const formRules: FormRules = {
  warehouse_name: [
    { required: true, message: '仓库名不能为空', trigger: 'blur' },
    { min: 1, max: 100, message: '仓库名长度在1-100个字符', trigger: 'blur' }
  ],
  warehouse_city: [
    { min: 0, max: 50, message: '仓库城市长度不能超过50个字符', trigger: 'blur' }
  ],
  warehouse_address: [
    { min: 0, max: 200, message: '仓库地址长度不能超过200个字符', trigger: 'blur' }
  ],

  warehouse_manager: [
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
    const supportedSortFields = ['id', 'warehouse_name', 'create_time', 'update_time'];
    
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
      loadWarehouses();
    }
  }
};

// 加载仓库列表
const loadWarehouses = async () => {
  if (!hasPermission('BASE-read')) return
  
  loading.value = true
  error.value = null
  
  try {
    // 构建查询参数 - 使用后端API期望的参数格式
    const queryParams: WarehouseQueryParams = {
      page: searchParams.value.page,
      page_size: searchParams.value.page_size,
      sort_field: searchParams.value.sort_field,
      sort_asc: searchParams.value.sort_asc
    }
    
    // 处理搜索关键词 - 使用统一的search参数，后端支持多关键词搜索
    if (searchParams.value.search && searchParams.value.search.trim()) {
      queryParams.search = searchParams.value.search.trim()
    }
    
    const response = await warehouseAPI.getWarehouses(queryParams)
    warehouses.value = response.data
    pagination.total = response.total
    pagination.current = searchParams.value.page
    pagination.pageSize = searchParams.value.page_size
    
    // 在数据加载完成后，恢复排序状态
    await nextTick();
    restoreSortState();
    
    // 加载统计信息
    await loadStatistics()
  } catch (err: any) {
    error.value = err.message || '加载仓库列表失败'
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
    const stats = await warehouseAPI.getWarehouseStatistics()
    statistics.value = stats
  } catch (err) {
    console.error('加载统计信息失败:', err)
  }
}

// 刷新数据
const refreshWarehouses = () => {
  searchParams.value.page = 1
  loadWarehouses()
}

// 搜索处理
const handleSearch = () => {
  searchParams.value.search = searchKeyword.value
  searchParams.value.page = 1
  loadWarehouses()
}

// 清空搜索
const handleClearSearch = () => {
  searchKeyword.value = ''
  searchParams.value.search = ''
  searchParams.value.page = 1
  loadWarehouses()
}

// 分页处理
const handleSizeChange = (size: number) => {
  searchParams.value.page_size = size
  searchParams.value.page = 1
  loadWarehouses()
}

const handleCurrentChange = (page: number) => {
  searchParams.value.page = page
  loadWarehouses()
}

// 表格选择变化
const handleSelectionChange = (selection: WarehouseResponse[]) => {
  selectedWarehouses.value = selection
}

// 新增仓库
const handleCreate = () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有创建仓库的权限')
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
      warehouse_name: '',
      warehouse_city: '',
      warehouse_address: '',
      warehouse_contact: '',
      warehouse_manager: ''
    })
    // 保存原始数据用于比较
    originalFormData.value = { ...formData }
  }
  
  isEdit.value = false
  lastMenuType.value = 'create'
  dialogVisible.value = true
}

// 编辑仓库
 const handleEdit = (warehouse: WarehouseResponse) => {
   if (!hasPermission('BASE-edit')) {
     ElMessage.warning('没有编辑仓库的权限')
     return
   }
   
   // 检查是否是同一个菜单类型
   if (lastMenuType.value === 'edit' && tempFormData.value) {
     // 恢复之前的数据
     Object.assign(formData, tempFormData.value)
   } else {
     // 从仓库数据初始化
     Object.assign(formData, {
       id: warehouse.id,
       warehouse_name: warehouse.warehouse_name,
       warehouse_city: warehouse.warehouse_city,
       warehouse_address: warehouse.warehouse_address,
       warehouse_contact: warehouse.warehouse_contact,
        warehouse_manager: warehouse.warehouse_manager || ''
     })
     // 保存原始数据用于比较
     originalFormData.value = { ...formData }
   }
   
   isEdit.value = true
   lastMenuType.value = 'edit'
   dialogVisible.value = true
 }

// 删除仓库
const handleDelete = async (warehouse: WarehouseResponse) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有删除仓库的权限')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除仓库"${warehouse.warehouse_name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await warehouseAPI.deleteWarehouse(warehouse.id)
    ElMessage.success('删除成功')
    // 删除后清除所有选中状态，让用户重新选择
    selectedWarehouses.value = []
    refreshWarehouses()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有批量删除仓库的权限')
    return
  }

  if (selectedWarehouses.value.length === 0) {
    ElMessage.warning('请选择要删除的仓库')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedWarehouses.value.length} 个仓库吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const ids = selectedWarehouses.value.map((item: WarehouseResponse) => item.id)
    await warehouseAPI.batchDeleteWarehouses({ warehouse_ids: ids })
    ElMessage.success('批量删除成功')
    selectedWarehouses.value = []
    refreshWarehouses()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
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
  console.log('仓库导入完成:', result)
  
  // 不自动关闭对话框，让用户在进度页面查看结果
  // importDialogVisible.value = false
  
  // 不显示结果消息，由进度页面显示
  // if (result.error_count === 0) {
  //   ElMessage.success(`仓库数据导入成功！共导入${result.success_count}条数据`)
  // } else if (result.success_count === 0) {
  //   ElMessage.error(`仓库数据导入失败！${result.error_count}条数据有错误`)
  // } else {
  //   ElMessage.warning(`仓库数据部分导入成功！成功${result.success_count}条，失败${result.error_count}条`)
  // }
  
  // 在后台刷新仓库列表，但不显示给用户
  loadWarehouses()
}

// 处理下载模板
const handleDownloadTemplate = async () => {
  if (!hasPermission('BASE-read')) {
    ElMessage.warning('您没有查看权限')
    return
  }
  
  try {
    templateDownloading.value = true
    const blob = await warehouseAPI.downloadWarehouseTemplate()
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = '仓库导入模板.xls'
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('模板下载成功')
  } catch (error: any) {
    ElMessage.error(`模板下载失败：${error.response?.data?.detail || error.message || '网络错误'}`)
  } finally {
    templateDownloading.value = false
  }
}

// 对话框关闭处理
const handleDialogClose = (done: () => void) => {
  // 检查是否有真正的数据修改
  const hasRealChanges = originalFormData.value && (
    formData.warehouse_name !== originalFormData.value.warehouse_name ||
    formData.warehouse_city !== originalFormData.value.warehouse_city ||
    formData.warehouse_address !== originalFormData.value.warehouse_address ||
    formData.warehouse_contact !== originalFormData.value.warehouse_contact ||
    formData.warehouse_manager !== originalFormData.value.warehouse_manager
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
      await warehouseAPI.updateWarehouse(formData.id!, formData as WarehouseUpdate)
      ElMessage.success('更新成功')
    } else {
      await warehouseAPI.createWarehouse(formData as WarehouseCreate)
      ElMessage.success('创建成功')
    }
    
    // 清除临时保存的数据
    tempFormData.value = null
    lastMenuType.value = null
    originalFormData.value = null
    
    dialogVisible.value = false
    refreshWarehouses()
  } catch (err: any) {
    // 验证失败或API调用失败
    if (err.response?.data?.detail) {
      // 显示后端返回的详细错误信息
      ElMessage.error(err.response.data.detail)
    } else if (err.message) {
      // 显示通用错误信息
      ElMessage.error(err.message)
    } else {
      // 显示默认错误信息
      ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
    }
  }
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return ''
  const date = new Date(dateTime)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

onMounted(() => {
  loadWarehouses()
})
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';

/* 使用现代Sass混入 */
@include mixins.table-sort-arrows;
</style>