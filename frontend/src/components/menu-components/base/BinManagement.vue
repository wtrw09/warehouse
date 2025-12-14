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
        <p>您没有足够的权限访问货位管理功能。</p>
        <p>需要权限：<el-tag type="danger">BASE-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 操作栏 -->
    <div v-else class="base-content base-flex-content">
    <el-card class="base-operation-card" shadow="hover">
      <div class="base-operation-bar">
        <div class="base-operation-bar__left">
          <el-button 
            type="primary" 
            @click="handleCreate"
            v-if="hasPermission('BASE-edit')"
            :icon="Plus"
          >
            新增货位
          </el-button>
          <el-button 
            type="default" 
            @click="getBinList"
            :loading="loading"
            :icon="Refresh"
          >
            刷新
          </el-button>
          <!-- 批量删除按钮 -->
          <el-button 
            v-if="hasPermission('BASE-edit') && selectedIds.length > 0"
            type="danger" 
            @click="handleBatchDelete" 
            :icon="Delete"
          >
            批量删除 ({{ selectedIds.length }})
          </el-button>
        </div>
        <div class="base-operation-bar__right">
          <!-- 仓库筛选下拉框 -->
          <el-select
            v-model="queryParams.warehouse_id"
            placeholder="筛选仓库"
            clearable
            style="width: 150px;"
            @change="handleSearch"
          >
            <el-option
              v-for="warehouse in warehouses"
              :key="warehouse.id"
              :label="warehouse.warehouse_name"
              :value="warehouse.id"
            />
          </el-select>
          
          <!-- 货位属性筛选下拉框 -->
          <el-select
            v-model="queryParams.bin_property"
            placeholder="筛选货位属性"
            clearable
            style="width: 150px;"
            @change="handleSearch"
          >
            <el-option
              v-for="property in binProperties"
              :key="property"
              :label="property"
              :value="property"
            />
          </el-select>
          
          <el-input
            v-model="queryParams.search"
            placeholder="输入搜索关键词，用空格分隔"
            style="width: 320px;"
            clearable
            @input="handleSearch"
            @clear="handleSearch"
          />
        </div>
      </div>
    </el-card>

    <!-- 货位列表 -->
    <el-card class="base-table-card base-table-card--flex" shadow="hover">
      <template #header>
        <div class="base-card-header">
          <el-icon><List /></el-icon>
          <span>货位列表</span>
          <div class="base-card-header__stats" v-if="total > 0">
            <span>总计: {{ total }}</span>
          </div>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="base-loading-container">
        <el-skeleton :rows="8" animated />
      </div>

      <!-- 货位表格 -->
      <div v-else class="base-table base-table--auto-height">
        <el-table
          ref="tableRef"
          :data="tableData"
          stripe
          border
          :empty-text="'暂无货位数据'"
          class="base-table"
          @selection-change="handleSelectionChange"
          @sort-change="handleSortChange"
        >
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column 
            prop="bin_name" 
            label="货位名称" 
            min-width="120" 
            align="center" 
            fixed="left"
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          >
            <template #default="{ row }">
              <el-tag class="base-tag-primary-dark">{{ row.bin_name }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column 
            prop="warehouse_name" 
            label="所属仓库" 
            width="120" 
            align="center" 
            fixed="left"
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column 
            v-if="false"
            prop="id" 
            label="ID" 
            width="80" 
            align="center" 
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column prop="bin_size" label="货位规格" width="120" align="center" />
          <el-table-column 
            prop="bin_property" 
            label="货位属性" 
            width="120" 
            align="center" 
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column 
            prop="empty_label" 
            label="是否为空" 
            width="100" 
            align="center"
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          >
            <template #default="{ row }">
              <el-tag :type="row.empty_label ? 'success' : 'danger'">
                {{ row.empty_label ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="bar_code" label="货位码" width="120" align="center" />
          <el-table-column 
            prop="create_time" 
            label="创建时间" 
            width="150" 
            align="center" 
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column prop="creator" label="创建人" width="100" align="center" />
          <el-table-column label="操作" width="120" align="center" fixed="right" v-if="hasPermission('BASE-edit')">
            <template #default="{ row }">
              <div class="base-action-buttons">
                <ActionTooltip content="编辑货位">
                  <el-button 
                    type="primary"
                    size="small"
                    @click="handleEdit(row)"
                    :icon="Edit"
                    class="base-button-circle"
                  />
                </ActionTooltip>
                <ActionTooltip content="删除货位">
                  <el-button 
                    type="danger"
                    size="small"
                    @click="handleDelete(row)"
                    :icon="Delete"
                    class="base-button-circle"
                  />
                </ActionTooltip>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="base-pagination-container">
          <el-pagination
            v-model:current-page="queryParams.page"
            v-model:page-size="queryParams.page_size"
            :page-sizes="[5,10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            :pager-count="7"
            background
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          >
            <template #sizes="{ size }">
              <span>{{ size }}条/页</span>
            </template>
            <template #total="{ total }">
              <span>共 {{ total }} 条</span>
            </template>
            <template #jumper>
              <span>前往</span>
            </template>
          </el-pagination>
        </div>
      </div>
    </el-card>

    <!-- 新增/编辑抽屉 -->
    <el-drawer
      :title="dialogTitle"
      v-model="dialogVisible"
      direction="rtl"
      size="600px"
      :before-close="handleDialogClose"
      :modal="true"
      class="base-drawer"
    >
      <div class="base-drawer-body">
        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
          <el-form-item label="货位名称" prop="bin_name">
            <el-input v-model="form.bin_name" placeholder="请输入货位名称" />
          </el-form-item>
          
          <el-form-item label="所属仓库" prop="warehouse_id">
            <el-select v-model="form.warehouse_id" placeholder="请选择仓库">
              <el-option
                v-for="warehouse in warehouses"
                :key="warehouse.id"
                :label="warehouse.warehouse_name"
                :value="warehouse.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="货位规格">
            <el-input v-model="form.bin_size" placeholder="例如：2m×2m×2m" />
          </el-form-item>
          
          <el-form-item label="货位属性">
            <el-input v-model="form.bin_property" placeholder="例如：周转区、质检区等" />
          </el-form-item>
          
          <el-form-item label="是否为空" prop="empty_label">
            <el-switch v-model="form.empty_label" />
          </el-form-item>
          
          <el-form-item label="货位码">
            <el-input v-model="form.bar_code" placeholder="请输入货位码" />
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <div class="base-drawer-footer">
          <el-button @click="dialogVisible = false" class="base-button">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="dialogLoading" class="base-button">
            确定
          </el-button>
        </div>
      </template>
    </el-drawer>
  </div>
</div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, inject, type Ref } from 'vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { 
  Plus, 
  Refresh, 
  List, 
  Edit, 
  Delete
} from '@element-plus/icons-vue';
import { binApi } from '@/services/base/bin';
import { warehouseAPI } from '@/services/base/warehouse';
import type { Bin, BinCreateRequest, BinUpdateRequest, BinQueryParams } from '@/services/types';
import ActionTooltip from './ActionTooltip.vue';

const currentUser = inject<Ref<any | null>>('currentUser') || ref<any | null>(null);

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
};

interface Warehouse {
  id: number;
  warehouse_name: string;
}

const loading = ref(false);
const dialogVisible = ref(false);
const dialogLoading = ref(false);
const dialogTitle = ref('');
const formRef = ref<FormInstance>();
const tableRef = ref(); // 添加表格引用
const selectedIds = ref<number[]>([]);

const queryParams = reactive<BinQueryParams>({
  page: 1,
  page_size: 10,
  sort_field: 'id',
  sort_asc: true
});

const form = reactive({
  id: 0,
  bin_name: '',
  warehouse_id: undefined as number | undefined,
  bin_size: undefined as string | undefined,
  bin_property: undefined as string | undefined,
  empty_label: true,
  bar_code: undefined as string | undefined
});

// 临时保存的数据
const tempFormData = ref<typeof form | null>(null)
const lastMenuType = ref<'create' | 'edit' | null>(null)
// 保存原始数据用于比较
const originalFormData = ref<typeof form | null>(null)

const rules: FormRules = {
  bin_name: [{ required: true, message: '请输入货位名称', trigger: 'blur' }],
  warehouse_id: [{ required: true, message: '请选择仓库', trigger: 'change' }],
  empty_label: [{ required: true, message: '请选择是否为空', trigger: 'change' }]
};

const tableData = ref<Bin[]>([]);
const total = ref(0);
const warehouses = ref<Warehouse[]>([]);
const binProperties = ref<string[]>(['重型货架', '中型货架', '轻型货架', '托盘货位', '流利架']);

// 获取货位列表
const getBinList = async () => {
  if (!hasPermission('BASE-read')) return
  loading.value = true;
  try {
    const response = await binApi.getBins(queryParams);
    tableData.value = response.data;
    total.value = response.total;
    
    // 在数据加载完成后，恢复排序状态
    await nextTick();
    restoreSortState();
  } catch (error) {
    ElMessage.error('获取货位列表失败');
  } finally {
    loading.value = false;
  }
};

// 恢复排序状态
const restoreSortState = () => {
  if (tableRef.value && currentSortProp.value && currentSortOrder.value) {
    // 手动设置表格的排序状态
    tableRef.value.sort(currentSortProp.value, currentSortOrder.value);
  }
};

// 获取仓库列表
const getWarehouseList = async () => {
  try {
    const response = await warehouseAPI.getAllWarehouses();
    warehouses.value = response;
    console.log('仓库列表:', warehouses.value);
  } catch (error) {
    ElMessage.error('获取仓库列表失败');
  }
};

// 获取货位属性列表
const getBinProperties = async () => {
  try {
    const response = await binApi.getBinProperties();
    binProperties.value = response.properties;
  } catch (error) {
    ElMessage.error('获取货位属性列表失败');
    // 如果API调用失败，使用默认的货位属性列表
    binProperties.value = ['重型货架', '中型货架', '轻型货架', '托盘货位', '流利架'];
  }
};

// 刷新页面数据（包括货位列表、仓库列表和货位属性）
const refreshAllData = () => {
  getBinList();
  getWarehouseList();
  getBinProperties();
}

// 当前排序状态
const currentSortProp = ref<string>('');
const currentSortOrder = ref<'ascending' | 'descending' | null>(null);

// 表头排序处理
const handleSortChange = ({ prop, order }: { prop: string; order: 'ascending' | 'descending' | null }) => {
  // 保存当前排序状态，用于在表格刷新后恢复排序图标
  currentSortProp.value = prop;
  currentSortOrder.value = order;
  
  if (prop) {
    const fieldMap: Record<string, string> = {
      'id': 'id',
      'bin_name': 'bin_name',
      'warehouse_name': 'warehouse_name',
      'bin_property': 'bin_property',
      'empty_label': 'empty_label',
      'create_time': 'create_time',
      'update_time': 'update_time'
    }
    
    const sortField = fieldMap[prop]
    if (sortField) {
      if (order) {
        // 有排序方向：升序或降序
        queryParams.sort_field = sortField as 'id' | 'bin_name' | 'warehouse_name' | 'bin_property' | 'empty_label' | 'create_time' | 'update_time'
        queryParams.sort_asc = order === 'ascending'
      } else {
        // 取消排序：重置为默认排序
        queryParams.sort_field = 'id'
        queryParams.sort_asc = true
      }
      queryParams.page = 1
      getBinList()
    }
  }
}

// 搜索
const handleSearch = () => {
  queryParams.page = 1;
  getBinList();
};

// 分页大小变化
const handleSizeChange = (size: number) => {
  queryParams.page_size = size;
  getBinList();
};

// 页码变化
const handleCurrentChange = (page: number) => {
  queryParams.page = page;
  getBinList();
};

// 表格选择变化
const handleSelectionChange = (selection: Bin[]) => {
  selectedIds.value = selection.map(item => item.id);
};

// 新增货位
const handleCreate = () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有创建货位的权限')
    return
  }
  dialogTitle.value = '新增货位';
  
  // 检查是否是同一个菜单类型
  if (lastMenuType.value === 'create' && tempFormData.value) {
    // 恢复之前的数据
    Object.assign(form, tempFormData.value);
  } else {
    resetForm();
    // 保存原始数据用于比较
    originalFormData.value = { ...form };
  }
  
  lastMenuType.value = 'create';
  dialogVisible.value = true;
};

// 编辑货位
  const handleEdit = (row: Bin) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有编辑货位的权限')
    return
  }
    dialogTitle.value = '编辑货位';
    
    // 检查是否是同一个菜单类型
  if (lastMenuType.value === 'edit' && tempFormData.value) {
    // 恢复之前的数据
    Object.assign(form, tempFormData.value);
  } else {
    Object.assign(form, {
      id: row.id,
      bin_name: row.bin_name,
      warehouse_id: row.warehouse_id,
      bin_size: row.bin_size || undefined,
      bin_property: row.bin_property || undefined,
      empty_label: row.empty_label,
      bar_code: row.bar_code || undefined
    });
    // 保存原始数据用于比较
    originalFormData.value = { ...form };
  }
  
  lastMenuType.value = 'edit';
  dialogVisible.value = true;
};

// 删除货位
const handleDelete = async (row: Bin) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有删除货位的权限')
    return
  }
  try {
    await ElMessageBox.confirm(`确定要删除货位"${row.bin_name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    await binApi.deleteBin(row.id);
    ElMessage.success('删除成功');
    // 删除后清除所有选中状态，让用户重新选择
    selectedIds.value = [];
    getBinList();
    getBinProperties(); // 新增：刷新货位属性列表
  } catch (error) {
    // 用户取消删除
  }
};

// 批量删除
const handleBatchDelete = async () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有批量删除货位的权限')
    return
  }
  if (selectedIds.value.length === 0) return;
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 个货位吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    await binApi.batchDelete({ bin_ids: selectedIds.value });
    ElMessage.success('批量删除成功');
    selectedIds.value = [];
    getBinList();
    getBinProperties(); // 新增：刷新货位属性列表
  } catch (error) {
    // 用户取消删除
  }
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  try {
    await formRef.value.validate();
    dialogLoading.value = true;
    
    if (dialogTitle.value === '新增货位') {
      const createData: BinCreateRequest = {
        bin_name: form.bin_name,
        warehouse_id: form.warehouse_id!,
        bin_size: form.bin_size?.trim() ?? null, // 将空字符串转换为null
        bin_property: form.bin_property?.trim() ?? null, // 将空字符串转换为null
        empty_label: form.empty_label,
        bar_code: form.bar_code?.trim() ?? null // 将空字符串转换为null
      };
      await binApi.createBin(createData);
      ElMessage.success('新增成功');
    } else {
      const updateData: BinUpdateRequest = {
        bin_name: form.bin_name,
        warehouse_id: form.warehouse_id,
        bin_size: form.bin_size?.trim() ?? null, // 将空字符串转换为null
        bin_property: form.bin_property?.trim() ?? null, // 将空字符串转换为null
        empty_label: form.empty_label,
        bar_code: form.bar_code?.trim() ?? null // 将空字符串转换为null
      };
      await binApi.updateBin(form.id, updateData);
      ElMessage.success('更新成功');
    }
    
    // 清除临时保存的数据
    tempFormData.value = null
    lastMenuType.value = null
    originalFormData.value = null
    
    dialogVisible.value = false;
    getBinList();
    getBinProperties(); // 新增：刷新货位属性列表
  } catch (error) {
    // 验证失败或API调用失败
  } finally {
    dialogLoading.value = false;
  }
};

// 处理对话框关闭
const handleDialogClose = (done: () => void) => {
  // 检查是否有真正的数据修改
  const hasRealChanges = originalFormData.value && (
    form.bin_name !== originalFormData.value.bin_name ||
    form.warehouse_id !== originalFormData.value.warehouse_id ||
    form.bin_size !== originalFormData.value.bin_size ||
    form.bin_property !== originalFormData.value.bin_property ||
    form.empty_label !== originalFormData.value.empty_label ||
    form.bar_code !== originalFormData.value.bar_code
  )
  
  if (hasRealChanges) {
    // 有真正的数据修改，自动保存并提示用户
    tempFormData.value = { ...form }
    ElMessage.success('编辑信息已保存')
    done()
  } else {
    // 没有真正的数据修改，直接关闭
    tempFormData.value = null
    done()
  }
};



// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
  Object.assign(form, {
    id: 0,
    bin_name: '',
    warehouse_id: undefined,
    bin_size: '',
    bin_property: '',
    empty_label: true,
    bar_code: ''
  });
};

onMounted(() => {
  refreshAllData();
});
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';

/* 使用现代Sass混入 */
@include mixins.table-sort-arrows;
</style>