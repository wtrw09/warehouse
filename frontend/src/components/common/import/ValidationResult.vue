<template>
  <div class="validation-result">
    <!-- 有验证错误的情况 -->
    <div v-if="validationErrors.length > 0" class="validation-errors">
      <div class="errors-header">
        <h4>
          <el-icon><WarningFilled /></el-icon>
          发现 {{ validationErrors.length }} 条数据需要修改
        </h4>
        <div class="edit-strategy-selector">
          <el-button 
            v-if="!forceDownload && validationErrors.length <= 5 && (previewInfo?.isEditable ?? true)" 
            type="primary" 
            size="small"
            @click="enableInlineEdit"
          >
            在线编辑
          </el-button>
        </div>
      </div>
      
      <!-- 编辑策略提示 -->
      <div class="strategy-tip">
        <el-alert
          v-if="forceDownload"
          title="数据量较大，建议下载继续导入Excel文件，提交后端验证，下载错误数据表进行批量编辑"
          type="info"
          :closable="false"
          show-icon
        />
        <el-alert
          v-else-if="validationErrors.length > 5"
          title="错误数量超过5个，只能下载Excel文件进行批量修改"
          type="warning"
          :closable="false"
          show-icon
        />
        <el-alert
          v-else-if="!(previewInfo?.isEditable ?? true)"
          :title="`${previewInfo?.source === 'file' ? 'Excel导入' : '粘贴'}数据不支持在线编辑，请下载文件进行修改`"
          type="info"
          :closable="false"
          show-icon
        />
        <el-alert
          v-else
          title="错误数量较少，可以选择在线编辑或下载文件编辑"
          type="success"
          :closable="false"
          show-icon
        />
      </div>
      
      <!-- 行内编辑表格 -->
      <div v-if="showInlineEdit && validationErrors.length <= 5" class="inline-edit-section">
        <h5>在线编辑错误数据</h5>
        <el-table :data="editableData" border size="small" max-height="400">
          <el-table-column prop="rowIndex" label="行号" width="80" align="center" />
          
          <el-table-column 
            v-for="column in config.previewColumns" 
            :key="column.key"
            :prop="column.key" 
            :label="column.label" 
            :min-width="column.width || 120"
          >
            <template #default="scope">
              <div class="editable-cell">
                <el-input
                  v-if="hasFieldError(scope.row, column.key) || scope.row._editableFields?.includes(column.key)"
                  v-model="scope.row[column.key]"
                  :class="{ 'error-field': hasFieldError(scope.row, column.key) }"
                  :placeholder="`请输入${column.label}`"
                  size="small"
                />
                <span v-else class="readonly-field">{{ scope.row[column.key] }}</span>
                
                <div v-if="hasFieldError(scope.row, column.key)" class="field-error-tip">
                  {{ getFieldError(scope.row, column.key) }}
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="scope">
              <div class="action-buttons">
                <el-button 
                  size="small" 
                  type="success"
                  @click="validateRow(scope.row)"
                >
                  验证
                </el-button>
                <el-button 
                  size="small" 
                  type="danger"
                  @click="handleDeleteRow(scope.row)"
                  :disabled="isDeleting"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="inline-edit-actions">
          <el-button type="primary" @click="submitFixedData" :disabled="hasAnyErrors">
            提交修改后的数据
          </el-button>
          <el-button @click="cancelInlineEdit">
            取消编辑
          </el-button>
        </div>
      </div>
      
      <!-- 错误详情列表 -->
      <div v-else-if="validationErrors.length <= 5" class="errors-list">
        <h5>错误详情</h5>
        <div class="error-summary">
          <div class="summary-item">
            <span class="summary-label">错误行数：</span>
            <span class="summary-value error">{{ errorRowCount }} 行</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">错误字段：</span>
            <span class="summary-value">{{ errorFieldCount }} 个</span>
          </div>
        </div>
        
        <el-table 
          :data="errorTableData" 
          border 
          size="small" 
          max-height="300"
          :row-class-name="getRowClassName"
        >
          <el-table-column prop="rowIndex" label="行号" width="80" align="center" />
          <el-table-column prop="field" label="错误字段" width="120" />
          <el-table-column prop="fieldLabel" label="字段名称" width="120" />
          <el-table-column prop="errorMessage" label="错误信息" min-width="200" />
          <el-table-column prop="currentValue" label="当前值" width="150" show-overflow-tooltip />
        </el-table>
      </div>
    </div>
    
    <!-- 无错误状态 - 统一在此组件处理 -->
    <div v-else class="no-errors">
      <el-result
        icon="success"
        title="数据验证通过"
        :sub-title="`所有 ${totalCount} 条${config.entityName}数据都符合要求`"
      >
        <template #extra>
          <div class="validation-actions">
            <el-button type="primary" size="large" @click="$emit('start-import')">
              开始导入{{ config.entityName }}数据
            </el-button>
            <el-button size="large" @click="$emit('reset-import')">
              重新选择文件
            </el-button>
          </div>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { WarningFilled } from '@element-plus/icons-vue';
import type { ImportConfig, ImportError, PreviewInfo } from '@/services/types/import';

// Props
interface Props {
  config: ImportConfig;
  validationErrors: ImportError[];
  totalCount: number;
  forceDownload?: boolean;
  parsedData?: any[]; // 新增：用于接收解析后的数据
  previewInfo?: PreviewInfo | null; // 修改：支持 null 值
}

const props = defineProps<Props>();

// Emits
const emit = defineEmits<{
  'start-import': [];
  'submit-fixed-data': [data: any[]];
  'reset-import': [];
  'delete-row': [rowIndex: number];
  'update-row-data': [rowIndex: number, rowData: any]; // 新增：更新单行数据
}>();

// Refs
const showInlineEdit = ref(false);
const editableData = ref<any[]>([]);
const isDeleting = ref(false);

// Computed
const errorRowCount = computed(() => {
  const uniqueRows = new Set(props.validationErrors.map(error => error.row_index));
  return uniqueRows.size;
});

const errorFieldCount = computed(() => {
  return props.validationErrors.length;
});

const errorTableData = computed(() => {
  return props.validationErrors.map(error => ({
    rowIndex: error.row_index,
    field: error.field,
    fieldLabel: getFieldLabel(error.field),
    errorMessage: error.error_message,
    currentValue: formatValue(error.raw_data?.[error.field])
  }));
});

const hasAnyErrors = computed(() => {
  return editableData.value.some(row => hasRowErrors(row));
});

// Methods
const enableInlineEdit = () => {
  // 构建可编辑数据
  const errorsByRow: Record<number, ImportError[]> = {};
  props.validationErrors.forEach(error => {
    if (!errorsByRow[error.row_index]) {
      errorsByRow[error.row_index] = [];
    }
    errorsByRow[error.row_index].push(error);
  });
  
  editableData.value = Object.entries(errorsByRow).map(([rowIndex, errors]) => {
    const row: any = {
      rowIndex: parseInt(rowIndex),
      _errors: {},
      _editableFields: [] // 新增：跟踪需要保持输入框状态的字段
    };
    
    // 从第一个错误中获取原始数据
    const firstError = errors[0];
    if (firstError.raw_data) {
      Object.assign(row, firstError.raw_data);
    }
    
    // 设置错误信息
    errors.forEach(error => {
      row._errors[error.field] = error.error_message;
      // 将有错误的字段添加到可编辑字段列表中
      if (!row._editableFields.includes(error.field)) {
        row._editableFields.push(error.field);
      }
    });
    
    return row;
  });
  
  showInlineEdit.value = true;
  ElMessage.info('已切换到在线编辑模式，请修改红色标记的错误字段');
};

const cancelInlineEdit = () => {
  showInlineEdit.value = false;
  editableData.value = [];
  ElMessage.info('已取消在线编辑');
};



const validateField = (row: any, fieldKey: string) => {
  // 手动验证单个字段
  const field = props.config.templateFields.find(f => f.key === fieldKey);
  if (!field) return true;
  
  const value = row[fieldKey];
  
  // 清除之前的错误
  if (row._errors) {
    delete row._errors[fieldKey];
  }
  
  // 必填验证
  if (field.required && (!value || String(value).trim() === '')) {
    if (!row._errors) row._errors = {};
    row._errors[fieldKey] = `${field.label}不能为空`;
    return false;
  }
  
  // 如果字段为空且不是必填，直接通过验证
  if (!value || String(value).trim() === '') {
    return true;
  }
  
  // 长度验证
  if (field.maxLength && String(value).length > field.maxLength) {
    if (!row._errors) row._errors = {};
    row._errors[fieldKey] = `${field.label}长度不能超过${field.maxLength}个字符`;
    return false;
  }
  
  // 数字范围验证
  if (field.type === 'number' && value) {
    const numValue = parseInt(value);
    if (isNaN(numValue)) {
      if (!row._errors) row._errors = {};
      row._errors[fieldKey] = `${field.label}必须是有效的整数`;
      return false;
    }
    
    // 检查供应商等级范围（1-5）
    if (fieldKey === 'supplier_level' && (numValue < 1 || numValue > 5)) {
      if (!row._errors) row._errors = {};
      row._errors[fieldKey] = `${field.label}必须是1-5的整数`;
      return false;
    }
  }
  
  return true;
};

const validateRow = (row: any) => {
  // 验证整行数据
  let hasErrors = false;
  let validatedFields = 0;
  
  // 第一步：验证字段格式（必填、长度、类型等）
  props.config.templateFields.forEach(field => {
    const isValid = validateField(row, field.key);
    if (!isValid) {
      hasErrors = true;
      // 如果有错误，确保该字段在可编辑字段列表中
      if (!row._editableFields?.includes(field.key)) {
        if (!row._editableFields) row._editableFields = [];
        row._editableFields.push(field.key);
      }
    }
    validatedFields++;
  });
  
  // 第二步：与预览表中的其他数据进行比对（排除自身）
  if (props.parsedData && props.parsedData.length > 0) {
    // 检查唯一性字段是否重复
    if (props.config.uniqueFields && props.config.uniqueFields.length > 0) {
      props.config.uniqueFields.forEach(fieldKey => {
        const currentValue = String(row[fieldKey] || '').trim().toLowerCase();
        
        if (currentValue && currentValue !== '') {
          // 在预览表中查找重复值（排除自身）
          const duplicateRows = (props.parsedData || []).filter(dataItem => {
            // 排除行号相同的自身数据
            if (dataItem.rowIndex === row.rowIndex) {
              return false;
            }
            
            const otherValue = String(dataItem[fieldKey] || dataItem.data?.[fieldKey] || '').trim().toLowerCase();
            return otherValue === currentValue;
          });
          
          if (duplicateRows.length > 0) {
            hasErrors = true;
            if (!row._errors) row._errors = {};
            
            const field = props.config.templateFields.find(f => f.key === fieldKey);
            const duplicateRowNumbers = duplicateRows.map(r => r.rowIndex).join(', ');
            
            row._errors[fieldKey] = `${field?.label || fieldKey}与第${duplicateRowNumbers}行数据重复`;
            
            // 确保重复字段在可编辑字段列表中
            if (!row._editableFields?.includes(fieldKey)) {
              if (!row._editableFields) row._editableFields = [];
              row._editableFields.push(fieldKey);
            }
          }
        }
      });
    }
  }
  
  // 强制Vue重新渲染该行数据
  const rowIndex = editableData.value.findIndex(r => r.rowIndex === row.rowIndex);
  if (rowIndex !== -1) {
    // 通过重新赋值触发响应式更新
    editableData.value[rowIndex] = { ...editableData.value[rowIndex] };
  }
  
  if (!hasErrors) {
    // 验证通过后，通过emit事件通知父组件更新预览表数据
    // 创建清理后的数据副本（移除错误信息等元数据）
    const cleanRow: any = { ...row };
    delete cleanRow._errors;
    delete cleanRow.rowIndex;
    
    // 通知父组件更新该行数据
    emit('update-row-data', row.rowIndex, cleanRow);
    
    // 清除该行的错误信息，以便其他行可以正确比对
    if (row._errors) {
      delete row._errors;
    }
    
    // 注意：不删除 _editableFields，这样验证通过后输入框仍然保持打开状态
    
    // 重要：更新editableData中的当前行数据，确保重新复制文本时显示正确的数据
    const rowIndex = editableData.value.findIndex(r => r.rowIndex === row.rowIndex);
    if (rowIndex !== -1) {
      // 保留可编辑字段状态，但更新数据内容
      editableData.value[rowIndex] = { 
        ...cleanRow,
        rowIndex: row.rowIndex,
        _editableFields: row._editableFields || []
      };
    }
    
    ElMessage.success(`第${row.rowIndex}行数据验证通过，已通知更新预览表数据`);
  } else {
    ElMessage.warning(`第${row.rowIndex}行数据存在错误，请修改后重新验证`);
  }
};

const submitFixedData = () => {
  if (hasAnyErrors.value) {
    ElMessage.warning('请先修复所有错误后再提交');
    return;
  }
  
  const fixedData = editableData.value.map(row => {
    const cleanRow: any = { ...row };
    delete cleanRow._errors;
    delete cleanRow.rowIndex;
    return cleanRow;
  });
  
  emit('submit-fixed-data', fixedData);
  showInlineEdit.value = false;
  ElMessage.success('已提交修改后的数据');
};

// 删除行方法
const handleDeleteRow = async (row: any) => {
  console.log('=== ValidationResult: 开始删除操作 ===');
  console.log('要删除的行数据:', row);
  console.log('要删除的行号:', row.rowIndex);
  console.log('当前editableData长度:', editableData.value.length);
  
  try {
    isDeleting.value = true;
    
    // 确认删除对话框
    await ElMessageBox.confirm(
      `确定要删除第 ${row.rowIndex} 行数据吗？此操作不可撤销。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }
    );
    
    console.log('用户确认删除，发送delete-row事件，行号:', row.rowIndex);
    
    // 发送删除事件给父组件
    emit('delete-row', row.rowIndex);
    
    // 从可编辑数据中移除该行
    const rowIndex = editableData.value.findIndex(r => r.rowIndex === row.rowIndex);
    console.log('在editableData中找到的行索引:', rowIndex);
    
    if (rowIndex !== -1) {
      console.log('从editableData中删除行，索引:', rowIndex);
      editableData.value.splice(rowIndex, 1);
    }
    
    console.log('删除后的editableData长度:', editableData.value.length);
    console.log('=== ValidationResult: 删除操作完成 ===');
    
    ElMessage.success(`第 ${row.rowIndex} 行数据已删除`);
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(`删除失败：${error.message || '未知错误'}`);
    }
  } finally {
    isDeleting.value = false;
  }
};

const hasFieldError = (row: any, fieldKey: string): boolean => {
  return row._errors && row._errors[fieldKey];
};

const getFieldError = (row: any, fieldKey: string): string => {
  return row._errors?.[fieldKey] || '';
};

const hasRowErrors = (row: any): boolean => {
  return row._errors && Object.keys(row._errors).length > 0;
};

const getFieldLabel = (fieldKey: string): string => {
  const field = props.config.templateFields.find(f => f.key === fieldKey);
  return field?.label || fieldKey;
};

const formatValue = (value: any): string => {
  if (value === null || value === undefined) {
    return '';
  }
  return String(value);
};

const getRowClassName = ({ rowIndex }: { rowIndex: number }): string => {
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row';
};
</script>

<style scoped>
@import '../../../css/base-styles.css';
@import '../../../css/common-import.css';

/* 组件特有样式 */
.no-errors {
  text-align: center;
  padding: 40px 20px;
}

:deep(.el-table__row.even-row) {
  background: #fafafa;
}

:deep(.el-table__row.odd-row) {
  background: #fff;
}

:deep(.el-result__title) {
  color: #67c23a;
}

.edit-strategy-selector {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.action-buttons .el-button {
  flex: 1;
  min-width: 60px;
}

.action-buttons .el-button--success {
  background: linear-gradient(135deg, #67c23a, #5daf34);
  border-color: #5daf34;
}

.action-buttons .el-button--success:hover {
  background: linear-gradient(135deg, #5daf34, #529b2f);
  border-color: #529b2f;
}

.action-buttons .el-button--danger {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  border-color: #ee5a52;
}

.action-buttons .el-button--danger:hover {
  background: linear-gradient(135deg, #ff5252, #d32f2f);
  border-color: #d32f2f;
}
</style>