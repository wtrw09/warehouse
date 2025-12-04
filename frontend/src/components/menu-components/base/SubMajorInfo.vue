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
        <p>您没有足够的权限访问二级专业管理功能。</p>
        <p>需要权限：<el-tag type="danger">BASE-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 二级专业管理内容 -->
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
              新增二级专业
            </el-button>
            <el-button 
              type="default" 
              @click="refreshSubMajors"
              :loading="loading"
              :icon="Refresh"
            >
              刷新
            </el-button>
            
            <!-- 批量删除按钮 -->
            <el-button 
              v-if="hasPermission('BASE-edit') && selectedSubMajors.length > 0"
              type="danger" 
              @click="handleBatchDelete"
              :icon="Delete"
            >
              批量删除 ({{ selectedSubMajors.length }})
            </el-button>
          </div>
          
          <div class="base-operation-bar__right">
            <!-- 一级专业筛选 -->
            <el-select
              v-model="queryParams.major_id"
              placeholder="一级专业"
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
              style="width: 300px;"
              clearable
              @input="handleSearch"
              @clear="handleSearch"
            />
          </div>
        </div>
      </el-card>

      <!-- 二级专业列表 -->
      <el-card class="base-table-card" shadow="hover">
          <template #header>
            <div class="base-card-header">
              <el-icon><List /></el-icon>
              <span>二级专业列表</span>
              <div class="base-card-header__stats">
                <span>总计: {{ subMajorList.length || 0 }}</span>
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
            :data="subMajorList"
            v-loading="loading"
            empty-text="暂无数据"
            stripe
            border
            height="400"
            @selection-change="handleSelectionChange"
            :default-sort="{ prop: 'id', order: 'ascending' }"
          >
            <el-table-column type="selection" width="55" align="center" fixed="left" />
            <el-table-column prop="id" label="ID" width="70" align="center" fixed="left" sortable />

            <el-table-column 
              prop="sub_major_name" 
              label="二级专业名称" 
              min-width="200" 
              align="center"
              sortable
            >
              <template #default="{ row }">
                <el-tag type="primary" effect="dark">{{ row.sub_major_name }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column 
              prop="sub_major_code" 
              label="专业代码" 
              width="120" 
              align="center"
              sortable
            >
              <template #default="{ row }">
                <el-tag type="success" effect="plain">{{ row.sub_major_code }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column 
              prop="major_name" 
              label="所属一级专业" 
              width="150" 
              align="center"
              column-key="major_name"
              :filters="majorNameFilters"
              :filter-multiple="true"
              :filter-method="filterMajorName"
              sortable
            >
              <template #default="{ row }">
                <el-tag v-if="row.major_name" type="info" effect="light">{{ row.major_name }}</el-tag>
                <span v-else class="text-muted">未关联</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="description" label="描述" min-width="250" align="center">
              <template #default="{ row }">
                <div v-if="row.description">
                  <el-tag
                    v-for="(desc, index) in parseDescription(row.description)"
                    :key="index"
                    size="small"
                    style="margin-right: 4px; margin-bottom: 4px;"
                  >
                    {{ desc }}
                  </el-tag>
                </div>
                <span v-else style="color: #c0c4cc;">-</span>
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
                    content="编辑二级专业" 
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
                    content="删除二级专业" 
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
            label-width="120px"
          >
            <el-form-item label="二级专业代码" prop="sub_major_code">
              <el-input
                v-model="formData.sub_major_code"
                placeholder="请输入2位专业代码（如：SE）"
                maxlength="2"
                show-word-limit
              />
              <template #label>
                <span>二级专业代码
                  <el-tooltip content="2位字符代码，如：SE表示软件工程，01表示数字代码" placement="top">
                    <el-icon style="margin-left: 4px;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </span>
              </template>
            </el-form-item>
            
            <el-form-item label="二级专业名称" prop="sub_major_name">
              <el-input
                v-model="formData.sub_major_name"
                placeholder="请输入二级专业名称"
                maxlength="100"
                show-word-limit
              />
            </el-form-item>
            
            <el-form-item label="所属一级专业" prop="major_id">
              <el-select
                v-model="formData.major_id"
                placeholder="请选择一级专业"
                clearable
                style="width: 100%;"
              >
                <el-option
                  v-for="major in majors"
                  :key="major.id"
                  :label="major.major_name"
                  :value="major.id"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="描述">
              <div class="description-tags-container">
                <div class="description-tags-list">
                  <el-tag
                    v-for="(desc, index) in descriptionTags"
                    :key="index"
                    size="small"
                    closable
                    @close="removeDescriptionTagFromForm(index)"
                    style="margin-right: 8px; margin-bottom: 8px;"
                  >
                    {{ desc }}
                  </el-tag>
                </div>
                <div class="description-input-container">
                  <el-input
                    v-model="newDescriptionInput"
                    placeholder="输入描述内容，按回车添加"
                    size="small"
                    style="width: 200px;"
                    @keyup.enter="addDescriptionTag"
                    maxlength="50"
                    show-word-limit
                  />
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click="addDescriptionTag"
                    style="margin-left: 8px;"
                  >
                    添加
                  </el-button>
                </div>
              </div>
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
        <p>确定要删除选中的 {{ selectedSubMajors.length }} 个二级专业吗？</p>
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
import { ref, onMounted, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Refresh, Delete, Search, List, Edit, QuestionFilled } from '@element-plus/icons-vue';
import { subMajorAPI } from '../../../services/base/sub_major';
import { majorAPI } from '../../../services/base/major';
import { usePermission } from '../../../composables/usePermission';
import ActionTooltip from './ActionTooltip.vue';
import type { SubMajorCreate, SubMajorResponse, SubMajorUpdate } from '../../../services/types/sub_major';
import type { MajorResponse } from '../../../services/types/major';

// 权限检查
const { hasPermission } = usePermission();

// 响应式数据
const loading = ref(false);
const subMajorList = ref<SubMajorResponse[]>([]);
const selectedSubMajors = ref<SubMajorResponse[]>([]);
const majors = ref<MajorResponse[]>([]);
const dialogVisible = ref(false);
const batchDeleteDialogVisible = ref(false);
const submitting = ref(false);
const deleting = ref(false);

// 查询参数
const queryParams = ref({
  search: '',
  major_id: undefined as number | undefined
});

// 临时数据管理
const tempFormData = ref<SubMajorFormData | null>(null);
const lastMenuType = ref<string | null>(null);
const originalFormData = ref<SubMajorFormData | null>(null);

// 筛选相关数据
const majorNameFilters = ref<{ text: string, value: string }[]>([]);

// 描述标签相关数据
const descriptionTags = ref<string[]>([]);
const newDescriptionInput = ref('');

// 表单数据
interface SubMajorFormData extends SubMajorCreate {
  id?: number;
}

const formData = ref<SubMajorFormData>({
  sub_major_name: '',
  sub_major_code: '',
  description: '',
  major_id: undefined
});

// 表单引用
const formRef = ref();

// 计算属性
const dialogTitle = computed(() => {
  return formData.value.id ? '编辑二级专业' : '新增二级专业';
});

// 表单验证规则
const formRules = {
  sub_major_code: [
    { pattern: /^.{0,2}$/, message: '二级专业代码必须是2位字符', trigger: 'blur' }
  ],
  sub_major_name: [
    { required: true, message: '请输入二级专业名称', trigger: 'blur' },
    { min: 1, max: 100, message: '二级专业名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '描述长度不能超过 500 个字符', trigger: 'blur' }
  ]
};

// 生命周期
onMounted(() => {
  loadSubMajors();
  loadMajors();
});

// 方法
const loadSubMajors = async () => {
  try {
    loading.value = true;
    const params: any = {};
    if (queryParams.value.search) params.search = queryParams.value.search;
    if (queryParams.value.major_id) params.major_id = queryParams.value.major_id;
    
    const response = await subMajorAPI.getSubMajors(params);
    subMajorList.value = response.data;
    // 生成筛选器
    updateFilters();
  } catch (error) {
    console.error('加载二级专业列表失败:', error);
    ElMessage.error('加载二级专业列表失败');
  } finally {
    loading.value = false;
  }
};

const loadMajors = async () => {
  try {
    const response = await majorAPI.getMajors();
    majors.value = response.data;
  } catch (error) {
    console.error('加载一级专业列表失败:', error);
    ElMessage.error('加载一级专业列表失败');
  }
};

// 更新筛选器
const updateFilters = () => {
  // 一级专业名称筛选器
  const uniqueMajorNames = [...new Set(subMajorList.value.map(item => item.major_name).filter(Boolean))];
  majorNameFilters.value = uniqueMajorNames.map(name => ({
    text: name!,
    value: name!
  }));
};

// 筛选方法
const filterMajorName = (value: string, row: SubMajorResponse) => {
  return row.major_name === value;
};

const refreshSubMajors = () => {
  queryParams.value.search = '';
  queryParams.value.major_id = undefined;
  loadSubMajors();
};

const handleSearch = () => {
  loadSubMajors();
};

const handleCreate = () => {
  // 检查是否有临时数据
  if (tempFormData.value && lastMenuType.value === 'create') {
    // 恢复临时数据
    formData.value = { ...tempFormData.value };
  } else {
    // 初始化表单数据
    formData.value = {
      sub_major_name: '',
      sub_major_code: '',
      description: '',
      major_id: undefined
    };
  }
  
  // 初始化描述标签
  descriptionTags.value = parseDescription(formData.value.description || '');
  newDescriptionInput.value = '';
  
  // 保存原始数据用于后续比较
  originalFormData.value = { ...formData.value };
  
  dialogVisible.value = true;
};

const handleEdit = (row: SubMajorResponse) => {
  // 检查是否有临时数据
  if (tempFormData.value && lastMenuType.value === 'edit' && tempFormData.value.id === row.id) {
    // 恢复临时数据
    formData.value = { ...tempFormData.value };
  } else {
    // 从行数据初始化表单
    formData.value = {
      id: row.id,
      sub_major_name: row.sub_major_name,
      sub_major_code: row.sub_major_code,
      description: row.description || '',
      major_id: row.major_id
    };
  }
  
  // 初始化描述标签
  descriptionTags.value = parseDescription(formData.value.description || '');
  newDescriptionInput.value = '';
  
  // 保存原始数据用于后续比较
  originalFormData.value = { ...formData.value };
  
  dialogVisible.value = true;
};

const handleDelete = async (row: SubMajorResponse) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有删除二级专业的权限');
    return;
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除二级专业 "${row.sub_major_name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );

    deleting.value = true;
    await subMajorAPI.deleteSubMajor(row.id);
    ElMessage.success('删除成功');
    refreshSubMajors();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除二级专业失败:', error);
      ElMessage.error('删除失败');
    }
  } finally {
    deleting.value = false;
  }
};

const handleSelectionChange = (selection: SubMajorResponse[]) => {
  selectedSubMajors.value = selection;
};

const handleBatchDelete = () => {
  if (selectedSubMajors.value.length === 0) {
    ElMessage.warning('请选择要删除的二级专业');
    return;
  }
  batchDeleteDialogVisible.value = true;
};

const confirmBatchDelete = async () => {
  try {
    deleting.value = true;
    const subMajorIds = selectedSubMajors.value.map(item => item.id);
    await subMajorAPI.batchDeleteSubMajors({ sub_major_ids: subMajorIds });
    ElMessage.success(`成功删除 ${subMajorIds.length} 个二级专业`);
    batchDeleteDialogVisible.value = false;
    selectedSubMajors.value = [];
    loadSubMajors();
  } catch (error) {
    console.error('批量删除二级专业失败:', error);
    ElMessage.error('批量删除失败');
  } finally {
    deleting.value = false;
  }
};

const handleDialogClose = () => {
  // 检查是否有数据修改
  const hasDataChanged = originalFormData.value && 
    (formData.value.sub_major_name !== originalFormData.value.sub_major_name ||
     formData.value.sub_major_code !== originalFormData.value.sub_major_code ||
     formData.value.description !== originalFormData.value.description ||
     formData.value.major_id !== originalFormData.value.major_id);
  
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

// 解析描述字段为字符串数组
const parseDescription = (description: string): string[] => {
  if (!description) return [];
  
  try {
    const parsed = JSON.parse(description);
    if (Array.isArray(parsed)) {
      return parsed.filter(item => typeof item === 'string' && item.trim() !== '');
    }
    return [description];
  } catch {
    return [description];
  }
};

// 从表单中移除描述标签
const removeDescriptionTagFromForm = (index: number) => {
  console.log('removeDescriptionTagFromForm: 删除索引', index, '当前描述标签:', descriptionTags.value);
  descriptionTags.value.splice(index, 1);
  console.log('removeDescriptionTagFromForm: 删除后描述标签:', descriptionTags.value);
  updateFormDescription();
};

// 添加描述标签到表单
const addDescriptionTag = () => {
  const desc = newDescriptionInput.value.trim();
  if (!desc) {
    ElMessage.warning('请输入描述内容');
    return;
  }
  
  if (descriptionTags.value.includes(desc)) {
    ElMessage.warning('描述内容已存在');
    return;
  }
  
  descriptionTags.value.push(desc);
  newDescriptionInput.value = '';
  updateFormDescription();
};

// 更新表单中的描述字段
const updateFormDescription = () => {
  if (descriptionTags.value.length === 0) {
    formData.value.description = '';
    console.log('updateFormDescription: 描述标签为空，设置formData.description为:', formData.value.description);
  } else {
    formData.value.description = JSON.stringify(descriptionTags.value);
    console.log('updateFormDescription: 描述标签不为空，设置formData.description为:', formData.value.description);
  }
};

const handleSubmit = async () => {
  try {
    const valid = await formRef.value.validate();
    if (!valid) return;
    
    submitting.value = true;
    
    // 确保描述字段是最新的
    updateFormDescription();
    
    if (formData.value.id) {
      // 更新二级专业
      const updateData: SubMajorUpdate = {
        sub_major_name: formData.value.sub_major_name,
        sub_major_code: formData.value.sub_major_code || undefined,
        description: formData.value.description,
        major_id: formData.value.major_id
      };
      console.log('更新二级专业数据:', updateData);
      console.log('原始formData.description:', formData.value.description);
      console.log('处理后updateData.description:', updateData.description);
      console.log('描述标签数组:', descriptionTags.value);
      await subMajorAPI.updateSubMajor(formData.value.id, updateData);
      ElMessage.success('更新成功');
    } else {
      // 创建二级专业
      const createData: SubMajorCreate = {
        sub_major_name: formData.value.sub_major_name,
        sub_major_code: formData.value.sub_major_code || undefined,
        description: formData.value.description,
        major_id: formData.value.major_id
      };
      console.log('创建二级专业数据:', createData);
      await subMajorAPI.createSubMajor(createData);
      ElMessage.success('创建成功');
    }
    
    // 清除临时保存的数据
    formData.value = {
      sub_major_name: '',
      sub_major_code: '',
      description: '',
      major_id: undefined
    };
    descriptionTags.value = [];
    newDescriptionInput.value = '';
    lastMenuType.value = null;
    originalFormData.value = null;
    
    dialogVisible.value = false;
    loadSubMajors();
  } catch (error: any) {
    console.error('提交二级专业数据失败:', error);
    if (error.response?.data?.detail?.includes('名称已存在')) {
      ElMessage.error('二级专业名称已存在');
    } else if (error.response?.data?.detail?.includes('二级专业代码')) {
      ElMessage.error('二级专业代码已存在或格式不正确');
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
/* 二级专业管理组件特定样式 */
.text-muted {
  color: #909399;
  font-style: italic;
}

/* 描述标签样式 */
.description-tags-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 8px;
  background-color: #f5f7fa;
}

.description-tags-list {
  margin-bottom: 8px;
  min-height: 32px;
}

.description-input-container {
  display: flex;
  align-items: center;
}

/* 表格中描述标签样式 */
.el-table .cell {
  line-height: 1.5;
}

.el-table .el-tag {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>