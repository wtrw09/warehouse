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
        <p>您没有足够的权限访问装备管理功能。</p>
        <p>需要权限：<el-tag type="danger">BASE-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 装备管理内容 -->
    <div v-else class="base-content base-flex-content">
    <!-- 操作栏 -->
    <el-card class="base-operation-card" shadow="hover">
      <div class="base-operation-bar">
        <div class="base-operation-bar__left">
          <el-button 
            v-if="hasPermission('BASE-edit')"
            type="primary" 
            @click="handleCreate"
            :icon="Plus"
          >
            新增装备
          </el-button>
          <el-button 
            type="default" 
            @click="getEquipmentList"
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
          <!-- 专业名称筛选 -->
          <el-select
            v-model="queryParams.major_id"
            placeholder="专业名称"
            clearable
            style="width: 150px;"
            @change="handleSearch"
          >
            <el-option
              v-for="major in majors"
              :key="major.id"
              :label="major.major_name"
              :value="major.id"
            />
          </el-select>
          
          <!-- 多关键词搜索 -->
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

    <!-- 装备列表 -->
    <el-card class="base-table-card base-table-card--flex" shadow="hover">
      <template #header>
        <div class="base-card-header">
          <el-icon><List /></el-icon>
          <span>装备列表</span>
          <div class="base-card-header__stats" v-if="total > 0">
            <span>总计: {{ total }}</span>
          </div>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="base-loading-container">
        <el-skeleton :rows="8" animated />
      </div>

      <!-- 装备表格 -->
      <div v-else class="base-table base-table--auto-height">
        <el-table
          ref="tableRef"
          :data="tableData"
          stripe
          border
          :empty-text="'暂无装备数据'"
          class="base-table"
          @selection-change="handleSelectionChange"
          @sort-change="handleSortChange"
        >
          <el-table-column type="selection" width="55" align="center" />
          <el-table-column 
            prop="equipment_name" 
            label="装备名称" 
            min-width="120"
            align="center" 
            fixed="left"
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          >
            <template #default="{ row }">
              <el-tag class="base-tag-primary-dark">{{ row.equipment_name }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column 
            prop="specification" 
            label="规格型号" 
            width="100" 
            align="center" 
          />
          <el-table-column 
            prop="major_name" 
            label="所属专业" 
            width="120" 
            align="center" 
            fixed="left"
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column v-if="false" prop="id" label="ID" width="80" align="center" sortable="custom"
            :sort-orders="['ascending', 'descending']"
          />
          
          <el-table-column 
            prop="create_time" 
            label="创建时间" 
            width="150" 
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
          <el-table-column prop="creator" label="创建人" width="100" align="center" />
          <el-table-column 
            prop="update_time" 
            label="更新时间" 
            width="150" 
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
          <el-table-column label="操作" width="120" align="center" fixed="right" v-if="hasPermission('BASE-edit')">
            <template #default="{ row }">
              <div class="base-action-buttons">
                <template v-if="hasPermission('BASE-edit')">
                  <ActionTooltip content="编辑装备">
                    <el-button 
                      type="primary"
                      size="small"
                      @click="handleEdit(row)"
                      :icon="Edit"
                      class="base-button-circle"
                    />
                  </ActionTooltip>
                  <ActionTooltip content="删除装备">
                    <el-button 
                      type="danger"
                      size="small"
                      @click="handleDelete(row)"
                      :icon="Delete"
                      class="base-button-circle"
                    />
                  </ActionTooltip>
                </template>
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
          <el-form-item label="装备名称" prop="equipment_name">
            <el-input v-model="form.equipment_name" placeholder="请输入装备名称" />
          </el-form-item>
          
          <el-form-item label="所属专业" prop="major_id">
            <el-select v-model="form.major_id" placeholder="请选择专业">
              <el-option
                v-for="major in majors"
                :key="major.id"
                :label="major.major_name"
                :value="major.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="规格型号">
            <el-input v-model="form.specification" placeholder="请输入规格型号" />
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
import { equipmentApi } from '@/services/base/equipment';
import { majorAPI } from '@/services/base/major';
import type { Equipment, EquipmentCreateRequest, EquipmentUpdateRequest, EquipmentQueryParams } from '@/services/types/equipment';
import ActionTooltip from './ActionTooltip.vue';

interface Major {
  id: number;
  major_name: string;
}

const loading = ref(false);
const dialogVisible = ref(false);
const dialogLoading = ref(false);
const dialogTitle = ref('');
const formRef = ref<FormInstance>();
const tableRef = ref(); // 添加表格引用
const selectedIds = ref<number[]>([]);

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

const queryParams = reactive<EquipmentQueryParams>({
  page: 1,
  page_size: 10,
  search: '',
  major_id: undefined,
  sort_field: 'id',
  sort_asc: true
});

const form = reactive({
  id: 0,
  equipment_name: '',
  major_id: undefined as number | undefined,
  specification: ''
});

// 临时保存的数据
const tempFormData = ref<typeof form | null>(null)
const lastMenuType = ref<'create' | 'edit' | null>(null)
// 保存原始数据用于比较
const originalFormData = ref<typeof form | null>(null)

const rules: FormRules = {
  equipment_name: [{ required: true, message: '请输入装备名称', trigger: 'blur' }],
  specification: [{ required: true, message: '请输入规格型号', trigger: 'blur' }],
  // 移除major_id的required验证，或者改为false
  major_id: [{ required: false, message: '请选择专业', trigger: 'change' }]
};

const tableData = ref<Equipment[]>([]);
const total = ref(0);
const majors = ref<Major[]>([]);


// 获取装备列表
const getEquipmentList = async () => {
  if (!hasPermission('BASE-read')) return;
  loading.value = true;
  try {
    const response = await equipmentApi.getEquipments(queryParams);
    console.log('装备列表数据:', response.data);
    tableData.value = response.data;
    total.value = response.total;
    
    // 在数据加载完成后，恢复排序状态
    await nextTick();
    restoreSortState();
  } catch (error) {
    ElMessage.error('获取装备列表失败');
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

// 获取专业列表
const getMajorList = async () => {
  if (!hasPermission('BASE-read')) return;
  try {
    const response = await majorAPI.getMajors();
    majors.value = response.data;
    console.log('专业列表:', majors.value);
  } catch (error) {
    ElMessage.error('获取专业列表失败');
  }
};



// 刷新页面数据（包括装备列表和专业列表）
const refreshAllData = () => {
  getEquipmentList();
  getMajorList();
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
    'equipment_name': 'equipment_name',
    'major_name': 'major_name',
    'create_time': 'create_time',
    'update_time': 'update_time'
  }
    
    const sortField = fieldMap[prop]
    if (sortField) {
      if (order) {
        // 有排序方向：升序或降序
        queryParams.sort_field = sortField as 'id' | 'equipment_name' | 'major_name' | 'create_time' | 'update_time'
        queryParams.sort_asc = order === 'ascending'
      } else {
        // 取消排序：重置为默认排序
        queryParams.sort_field = 'id'
        queryParams.sort_asc = true
      }
      queryParams.page = 1
      getEquipmentList()
    }
  }
};

// 搜索处理
const handleSearch = () => {
  queryParams.page = 1;
  getEquipmentList();
};

// 分页大小改变
const handleSizeChange = (size: number) => {
  queryParams.page_size = size;
  queryParams.page = 1;
  getEquipmentList();
};

// 当前页改变
const handleCurrentChange = (page: number) => {
  queryParams.page = page;
  getEquipmentList();
};

// 表格选择改变
const handleSelectionChange = (selection: Equipment[]) => {
  selectedIds.value = selection.map(item => item.id);
};

// 新增装备
const handleCreate = () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有新增装备的权限')
    return
  }
  dialogTitle.value = '新增装备';
  
  // 检查是否是同一个菜单类型
  if (lastMenuType.value === 'create' && tempFormData.value) {
    // 恢复之前的数据
    Object.assign(form, tempFormData.value);
  } else {
    resetForm();
    // 保存原始数据用于比较
    originalFormData.value = { ...form }
  }
  
  lastMenuType.value = 'create';
  dialogVisible.value = true;
  
  // 清除表单验证
  nextTick(() => {
    formRef.value?.clearValidate();
  });
};

// 编辑装备
const handleEdit = (row: Equipment) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有编辑装备的权限')
    return
  }
  dialogTitle.value = '编辑装备';
  
  // 检查是否是同一个菜单类型
  if (lastMenuType.value === 'edit' && tempFormData.value) {
    // 恢复之前的数据
    Object.assign(form, tempFormData.value);
  } else {
    // 填充表单数据
    Object.assign(form, {
      id: row.id,
      equipment_name: row.equipment_name,
      major_id: row.major_id,
      specification: row.specification || ''
    });
    // 保存原始数据用于比较
    originalFormData.value = { ...form }
  }
  
  lastMenuType.value = 'edit';
  dialogVisible.value = true;
  
  console.log('编辑装备数据:', row);
  console.log('major_id值:', row.major_id, '类型:', typeof row.major_id);
  console.log('表单major_id值:', form.major_id, '类型:', typeof form.major_id);
  
  // 清除表单验证
  nextTick(() => {
    formRef.value?.clearValidate();
  });
};

// 删除装备
const handleDelete = async (row: Equipment) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有删除装备的权限')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确定要删除装备"${row.equipment_name}"吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    await equipmentApi.deleteEquipment(row.id);
    ElMessage.success('删除成功');
    // 删除后清除所有选中状态，让用户重新选择
    selectedIds.value = [];
    getEquipmentList();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败');
    }
  }
};

// 批量删除
const handleBatchDelete = async () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有批量删除装备的权限')
    return
  }
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要删除的装备');
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedIds.value.length} 个装备吗？此操作不可恢复。`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    await equipmentApi.batchDelete({
      equipment_ids: selectedIds.value
    });
    ElMessage.success('批量删除成功');
    selectedIds.value = [];
    getEquipmentList();
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败');
    }
  }
};

// 表单提交
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  try {
    await formRef.value.validate();
    dialogLoading.value = true;
    
    if (form.id === 0) {
      // 新增
      const createData: EquipmentCreateRequest = {
        equipment_name: form.equipment_name,
        major_id: form.major_id!,
        specification: form.specification
      };
      console.log('新增装备数据:', createData);
      await equipmentApi.createEquipment(createData);
      ElMessage.success('新增成功');
    } else {
      // 编辑
      const updateData: EquipmentUpdateRequest = {
        equipment_name: form.equipment_name,
        major_id: form.major_id!,
        specification: form.specification
      };
      await equipmentApi.updateEquipment(form.id, updateData);
      ElMessage.success('更新成功');
    }
    
    // 清除临时数据
    tempFormData.value = null
    lastMenuType.value = null
    originalFormData.value = null
    
    dialogVisible.value = false;
    getEquipmentList();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('操作失败:', error);
      console.error('错误详情:', (error as any).response?.data || (error as any).message);
      ElMessage.error('操作失败');
    }
  } finally {
    dialogLoading.value = false;
  }
};

// 处理对话框关闭
const handleDialogClose = (done: () => void) => {
  // 检查是否有真正的数据修改
  const hasRealChanges = originalFormData.value && (
    form.equipment_name !== originalFormData.value.equipment_name ||
    form.major_id !== originalFormData.value.major_id ||
    form.specification !== originalFormData.value.specification
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
    equipment_name: '',
    major_id: undefined,
    specification: ''
  });
};

// 格式化日期时间，只显示到秒
const formatDateTime = (dateTime: string | number | Date) => {
  if (!dateTime) return '';
  const date = new Date(dateTime);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

// 组件挂载
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