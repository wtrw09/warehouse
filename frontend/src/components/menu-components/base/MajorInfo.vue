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
        <p>您没有足够的权限访问专业管理功能。</p>
        <p>需要权限：<el-tag type="danger">BASE-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 专业管理内容 -->
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
            >
              新增专业
            </el-button>
            <el-button 
              type="default" 
              @click="refreshMajors"
              :loading="loading"
              :icon="Refresh"
            >
              刷新
            </el-button>
            
            <!-- 批量删除按钮 -->
            <el-button 
              v-if="hasPermission('BASE-edit') && selectedMajors.length > 0"
              type="danger" 
              @click="handleBatchDelete"
              :icon="Delete"
            >
              批量删除 ({{ selectedMajors.length }})
            </el-button>
          </div>
          
          <div class="base-operation-bar__right">
            <el-input
              v-model="searchKeyword"
              placeholder="输入搜索关键词，用空格分隔"
              style="width: 300px;"
              clearable
              @input="handleSearch"
              @clear="handleClearSearch"
            />
          </div>
        </div>
      </el-card>

      <!-- 专业列表 -->
      <el-card class="base-table-card" shadow="hover">
          <template #header>
            <div class="base-card-header">
              <el-icon><List /></el-icon>
              <span>专业列表</span>
              <div class="base-card-header__stats">
                <span>总计: {{ majorList.length || 0 }}</span>
              </div>
            </div>
          </template>

          <!-- 加载状态 -->
          <div v-if="loading" class="base-loading-container">
            <el-skeleton :rows="5" animated />
          </div>

          <!-- 数据表格 -->
          <el-table
            v-else
            :data="majorList"
            v-loading="loading"
            empty-text="暂无数据"
            stripe
            border
            height="400"
            @selection-change="handleSelectionChange"
            :default-sort="{ prop: 'id', order: 'ascending' }"
          >
            <el-table-column type="selection" width="55" align="center" fixed="left" />
            <el-table-column v-if="false" prop="id" label="ID" width="70" align="center" fixed="left" sortable />

            <el-table-column 
              prop="major_name" 
              label="专业名称" 
              min-width="200" 
              align="center"
              column-key="major_name"
              :filters="majorNameFilters"
              :filter-multiple="true"
              :filter-method="filterMajorName"
              sortable
            >
              <template #default="{ row }">
                <el-tag type="primary" effect="dark">{{ row.major_name }}</el-tag>
              </template>
            </el-table-column>
                        <el-table-column 
              prop="major_code" 
              label="专业代码" 
              width="120" 
              align="center"
              sortable
            >
              <template #default="{ row }">
                <el-tag type="success" effect="plain">{{ row.major_code }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="creator" label="创建人" width="120" align="center" sortable />
            <el-table-column prop="create_time" label="创建时间" width="180" align="center" sortable>
              <template #default="{ row }">
                <el-text type="info" size="small">
                  {{ formatDateTime(row.create_time) }}
                </el-text>
              </template>
            </el-table-column>
            
            <el-table-column prop="update_time" label="更新时间" width="180" align="center" sortable>
              <template #default="{ row }">
                <el-text type="info" size="small">
                  {{ formatDateTime(row.update_time) }}
                </el-text>
              </template>
            </el-table-column>
            <el-table-column 
              label="操作" 
              width="120" 
              align="center" 
              fixed="right"
            >
              <template #default="{ row }">
                <div class="base-action-buttons">
                  <ActionTooltip 
                    content="编辑专业" 
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
                    content="删除专业" 
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
      </el-card>

      <!-- 新增/编辑抽屉 -->
      <el-drawer
        v-model="dialogVisible"
        :title="dialogTitle"
        size="500px"
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
            <el-form-item label="专业代码" prop="major_code">
              <el-input
                v-model="formData.major_code"
                placeholder="请输入2位专业代码（如：CS）"
                maxlength="2"
                show-word-limit
              />
              <template #label>
                <span>专业代码
                  <el-tooltip content="2位字母代码，如：CS表示计算机科学" placement="top">
                    <el-icon style="margin-left: 4px;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </span>
              </template>
            </el-form-item>
            <el-form-item label="专业名称" prop="major_name">
              <el-input
                v-model="formData.major_name"
                placeholder="请输入专业名称"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
          </el-form>
          <div class="base-drawer-footer">
            <el-button @click="handleDialogClose">取消</el-button>
            <el-button type="primary" @click="handleSubmit" :loading="submitting">
              {{ formData.id ? '更新' : '创建' }}
            </el-button>
          </div>
        </div>
      </el-drawer>

      <!-- 批量删除确认对话框 -->
      <el-dialog
        v-model="batchDeleteDialogVisible"
        title="批量删除确认"
        width="400px"
        :close-on-click-modal="false"
      >
        <p>确定要删除选中的 {{ selectedMajors.length }} 个专业吗？</p>
        <p style="color: #f56c6c; margin-top: 8px;">此操作不可恢复！</p>
        
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="batchDeleteDialogVisible = false">取消</el-button>
            <el-button type="danger" @click="confirmBatchDelete" :loading="deleting">
              确定删除
            </el-button>
          </span>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref,onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Refresh, Delete, Search, List, Edit, QuestionFilled } from '@element-plus/icons-vue';
import { majorAPI } from '../../../services/base/major';
import { usePermission } from '../../../composables/usePermission';
import ActionTooltip from './ActionTooltip.vue';
import type { MajorCreate, MajorResponse } from '../../../services/types/major';

// 权限检查
const { hasPermission } = usePermission();

// 响应式数据
const loading = ref(false);
const majorList = ref<MajorResponse[]>([]);
const selectedMajors = ref<MajorResponse[]>([]);
const searchKeyword = ref('');
const dialogVisible = ref(false);
const batchDeleteDialogVisible = ref(false);
const submitting = ref(false);
const deleting = ref(false);

// 临时数据管理
const tempFormData = ref<MajorCreate | null>(null);
const lastMenuType = ref<string | null>(null);
const originalFormData = ref<MajorCreate | null>(null);

// 筛选相关数据
const majorNameFilters = ref<{ text: string, value: string }[]>([]);

// 表单数据
const formData = ref<MajorCreate>({
  major_name: '',
  major_code: ''
});

// 表单引用
const formRef = ref();

// 计算属性
const dialogTitle = computed(() => {
  return formData.value.id ? '编辑专业' : '新增专业';
});

// 表单验证规则
const formRules = {
  major_code: [
    { pattern: /^[A-Za-z]{0,2}$/, message: '专业代码必须是2位字母', trigger: 'blur' }
  ],
  major_name: [
    { required: true, message: '请输入专业名称', trigger: 'blur' },
    { min: 1, max: 50, message: '专业名称长度在 1 到 50 个字符', trigger: 'blur' }
  ]
};

// 生命周期
onMounted(() => {
  loadMajors();
});

// 方法
const loadMajors = async () => {
  try {
    loading.value = true;
    const params = searchKeyword.value ? { search: searchKeyword.value } : {};
    const response = await majorAPI.getMajors(params);
    majorList.value = response.data;
    // 生成专业名称筛选器
    updateMajorNameFilters();
  } catch (error) {
    console.error('加载专业列表失败:', error);
    ElMessage.error('加载专业列表失败');
  } finally {
    loading.value = false;
  }
};

// 更新专业名称筛选器
const updateMajorNameFilters = () => {
  const uniqueNames = [...new Set(majorList.value.map(item => item.major_name))];
  majorNameFilters.value = uniqueNames.map(name => ({
    text: name,
    value: name
  }));
};

// 专业名称筛选方法
const filterMajorName = (value: string, row: MajorResponse) => {
  return row.major_name === value;
};

const refreshMajors = () => {
  searchKeyword.value = '';
  loadMajors();
};

const handleSearch = () => {
  loadMajors();
};

const handleClearSearch = () => {
  searchKeyword.value = '';
  loadMajors();
};

const handleCreate = () => {
  // 检查是否有临时数据
  if (tempFormData.value && lastMenuType.value === 'create') {
    // 恢复临时数据
    formData.value = { ...tempFormData.value };
  } else {
    // 初始化表单数据
    formData.value = {
      major_name: '',
      major_code: ''
    };
  }
  
  // 保存原始数据用于后续比较
  originalFormData.value = { ...formData.value };
  
  dialogVisible.value = true;
};

const handleEdit = (row: MajorResponse) => {
  // 检查是否有临时数据
  if (tempFormData.value && lastMenuType.value === 'edit' && tempFormData.value.id === row.id) {
    // 恢复临时数据
    formData.value = { ...tempFormData.value };
  } else {
    // 从行数据初始化表单
    formData.value = {
      id: row.id,
      major_name: row.major_name,
      major_code: row.major_code
    };
  }
  
  // 保存原始数据用于后续比较
  originalFormData.value = { ...formData.value };
  
  dialogVisible.value = true;
};

const handleDelete = async (row: MajorResponse) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有删除专业的权限')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除专业 "${row.major_name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    deleting.value = true;
    await majorAPI.deleteMajor(row.id);
    ElMessage.success('删除成功');
    refreshMajors();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除专业失败:', error);
      ElMessage.error('删除失败');
    }
  } finally {
    deleting.value = false;
  }
};

const handleSelectionChange = (selection: MajorResponse[]) => {
  selectedMajors.value = selection;
};

const handleBatchDelete = () => {
  if (selectedMajors.value.length === 0) {
    ElMessage.warning('请选择要删除的专业');
    return;
  }
  batchDeleteDialogVisible.value = true;
};

const confirmBatchDelete = async () => {
  try {
    deleting.value = true;
    const majorIds = selectedMajors.value.map(item => item.id);
    await majorAPI.batchDeleteMajors({ major_ids: majorIds });
    ElMessage.success(`成功删除 ${majorIds.length} 个专业`);
    batchDeleteDialogVisible.value = false;
    selectedMajors.value = [];
    loadMajors();
  } catch (error) {
    console.error('批量删除专业失败:', error);
    ElMessage.error('批量删除失败');
  } finally {
    deleting.value = false;
  }
};

const handleDialogClose = () => {
  // 检查是否有数据修改
  const hasDataChanged = originalFormData.value && 
    (formData.value.major_name !== originalFormData.value.major_name ||
     formData.value.major_code !== originalFormData.value.major_code);
  
  if (hasDataChanged) {
    // 保存临时数据
    tempFormData.value = { ...formData.value };
    lastMenuType.value = formData.value.id ? 'edit' : 'create';
  } else {
    // 清除临时数据
    tempFormData.value = null;
    lastMenuType.value = null;
  }
  
  dialogVisible.value = false;
  formRef.value?.resetFields();
};

const handleSubmit = async () => {
  try {
    const valid = await formRef.value.validate();
    if (!valid) return;
    
    submitting.value = true;
    
    if (formData.value.id) {
      // 更新专业
      await majorAPI.updateMajor(formData.value.id, {
        major_name: formData.value.major_name,
        major_code: formData.value.major_code || undefined
      });
      ElMessage.success('更新成功');
    } else {
      // 创建专业
      await majorAPI.createMajor({
        major_name: formData.value.major_name,
        major_code: formData.value.major_code || undefined
      });
      ElMessage.success('创建成功');
    }
    
    // 清除临时保存的数据
    formData.value = {
      major_name: '',
      major_code: ''
    };
    lastMenuType.value = null;
    originalFormData.value = null;
    
    dialogVisible.value = false;
    loadMajors();
  } catch (error: any) {
    console.error('提交专业数据失败:', error);
    if (error.response?.data?.detail?.includes('名称已存在')) {
      ElMessage.error('专业名称已存在');
    } else if (error.response?.data?.detail?.includes('专业代码')) {
      ElMessage.error('专业代码已存在或格式不正确');
    } else {
      ElMessage.error('操作失败');
    }
  } finally {
    submitting.value = false;
  }
};

const formatDateTime = (dateTime: string | number | Date) => {
  if (!dateTime) return '';
  return new Date(dateTime).toLocaleString('zh-CN');
};
</script>

<style src="../../../css/base-styles.css"></style>
<style scoped>
/* 专业管理组件特定样式 */
</style>