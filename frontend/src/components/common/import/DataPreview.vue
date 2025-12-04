<template>
  <div class="data-preview">
    
    <!-- 数据来源提示 -->
    <div v-if="previewInfo.hasMoreData && previewInfo.source === 'file'" class="large-data-tip">
      <el-alert
        :title="`${config.entityName}数据量较大，预览仅显示前20条数据`"
        type="warning"
        :closable="false"
        show-icon
      >
        <p>预览主要目的是检查{{ config.entityName }}数据读取和字段映射是否正确。如需查看完整数据，请导入后查看系统记录。</p>
      </el-alert>
    </div>
    
    <div v-if="previewInfo.source === 'paste'" class="paste-data-tip">
      <el-alert
        :title="previewInfo.hasExceededLimit ? `粘贴${config.entityName}数据预览（数据量超出限制）` : previewInfo.hasMoreData ? `粘贴${config.entityName}数据预览（已自动截断）` : `粘贴${config.entityName}数据预览`"
        :type="previewInfo.hasExceededLimit ? 'warning' : previewInfo.hasMoreData ? 'warning' : 'success'"
        :closable="false"
        show-icon
      >
        <p v-if="previewInfo.hasExceededLimit">
          粘贴{{ config.entityName }}数据超过20条，已自动保留前20条数据。
        </p>
        <p v-else-if="previewInfo.hasMoreData">
          粘贴{{ config.entityName }}数据共{{ previewInfo.totalRows }}条，已自动保留前20条进行预览和导入。
        </p>
        <p v-else>
          已成功解析{{ previewInfo.totalRows }}条粘贴{{ config.entityName }}数据。
        </p>
      </el-alert>
    </div>
    
    <!-- 数据预览表格 -->
    <div class="preview-table">
      <el-table 
        :data="previewTableData" 
        border 
        size="small"
        max-height="400"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <!-- 行号列 -->
        <el-table-column 
          prop="rowIndex" 
          label="行号" 
          width="80" 
          align="center"
          fixed="left"
        />
        
        <!-- 动态数据列 -->
        <el-table-column 
          v-for="column in config.previewColumns" 
          :key="column.key"
          :prop="`data.${column.key}`" 
          :label="column.label" 
          :min-width="column.width || 120"
          show-overflow-tooltip
        >
          <template #default="scope">
            <div 
              :class="{
                'error-cell': hasFieldError(scope.row, column.key),
                'empty-cell': isEmpty(scope.row.data[column.key])
              }"
            >
              <span v-if="column.formatter">
                {{ column.formatter(scope.row.data[column.key]) }}
              </span>
              <span v-else>
                {{ formatCellValue(scope.row.data[column.key]) }}
              </span>
            </div>
          </template>
        </el-table-column>
        
        <!-- 错误信息列 - 唯一的错误信息显示位置 -->
        <el-table-column 
          v-if="hasAnyErrors"
          label="错误信息" 
          width="200" 
          fixed="right"
          :show-overflow-tooltip="false"
        >
          <template #default="scope">
            <div v-if="scope.row._errors && Object.keys(scope.row._errors).length > 0" class="error-messages">
              <div 
                v-for="(error, field) in scope.row._errors" 
                :key="field" 
                class="error-item"
              >
                <el-tag type="danger" size="small" class="error-tag">{{ getFieldLabel(String(field)) }}: {{ error }}</el-tag>
              </div>
            </div>
          </template>
        </el-table-column>
        

      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue';
import type { ImportConfig, PreviewInfo } from '@/services/types/import';

// Props
interface Props {
  config: ImportConfig;
  previewInfo: PreviewInfo;
  errorsByRow?: Record<number, Record<string, string>>;
  // 新增：用于接收外部数据更新
  updatedData?: any[]; // 更新后的数据
  deletedRows?: number[]; // 被删除的行号
}

const props = defineProps<Props>();

// Emits - 发送验证结果给父组件
const emit = defineEmits<{
  'validation-completed': [errors: Record<number, Record<string, string>>];
}>();

// 获取最新行数据的工具函数
const getLatestRowData = (rowIndex: number) => {
  // 先检查是否有更新的数据
  const updatedRow = props.updatedData?.find(item => 
    (item.rowIndex || item.row_index) === rowIndex
  );
  
  if (updatedRow) {
    return updatedRow.data || updatedRow;
  }
  
  // 否则返回原始数据
  const originalRow = props.previewInfo.previewData.find(item => 
    (item.rowIndex || item.row_index) === rowIndex
  );
  return originalRow?.data || originalRow;
};

// 前端验证逻辑
const performFrontendValidation = () => {
  const errors: Record<number, Record<string, string>> = {};
  
  props.previewInfo.previewData.forEach((dataItem, _index) => {
    const rowIndex = dataItem.rowIndex; // 直接使用数据项的行号，不要回退到index+1
    
    // 跳过已删除的行
    if (props.deletedRows?.includes(rowIndex)) {
      return;
    }
    
    // 获取最新的数据（可能是更新后的数据）
    const data = getLatestRowData(rowIndex);
    
    props.config.templateFields.forEach(field => {
      const value = data[field.key];
      
      // 必填验证
      if (field.required && isEmpty(value)) {
        if (!errors[rowIndex]) errors[rowIndex] = {};
        errors[rowIndex][field.key] = `${field.label}不能为空`;
      }
      
      // 长度验证
      if (field.maxLength && value && String(value).length > field.maxLength) {
        if (!errors[rowIndex]) errors[rowIndex] = {};
        errors[rowIndex][field.key] = `${field.label}长度不能超过${field.maxLength}个字符`;
      }
      
      // 数据类型验证
      if (field.type && value && !isEmpty(value)) {
        if (field.type === 'number' && isNaN(Number(value))) {
          if (!errors[rowIndex]) errors[rowIndex] = {};
          errors[rowIndex][field.key] = `${field.label}必须是数字`;
        }
      }
      
      // 根据字段名进行特定格式验证
      if (value && !isEmpty(value)) {
        // 邮箱字段验证
        if (field.key.toLowerCase().includes('email') && !isValidEmail(value)) {
          if (!errors[rowIndex]) errors[rowIndex] = {};
          errors[rowIndex][field.key] = `${field.label}邮箱格式不正确`;
        }
        
      }
    });
  });
  
  // 内部重复数据检查
  if (props.config.uniqueFields) {
    props.config.uniqueFields.forEach(fieldKey => {
      const valueMap = new Map<string, number[]>();
      
      props.previewInfo.previewData.forEach((dataItem, _index) => {
        const rowIndex = dataItem.rowIndex; // 直接使用数据项的行号，不要回退到index+1
        
        // 跳过已删除的行
        if (props.deletedRows?.includes(rowIndex)) {
          return;
        }
        
        // 获取最新的数据（可能是更新后的数据）
        const data = getLatestRowData(rowIndex);
        const value = String(data[fieldKey] || '').trim().toLowerCase();
        
        if (value && !isEmpty(value)) {
          if (!valueMap.has(value)) {
            valueMap.set(value, []);
          }
          valueMap.get(value)!.push(rowIndex);
        }
      });
      
      // 找出重复的值
      valueMap.forEach((rowIndices) => {
        if (rowIndices.length > 1) {
          const field = props.config.templateFields.find(f => f.key === fieldKey);
          rowIndices.forEach(rowIndex => {
            if (!errors[rowIndex]) errors[rowIndex] = {};
            errors[rowIndex][fieldKey] = `${field?.label || fieldKey}在当前数据中重复`;
          });
        }
      });
    });
  }
  
  // 发送验证结果给父组件
  emit('validation-completed', errors);
  
  return errors;
};

// 格式验证工具函数
const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};


// Computed - 更新为使用实时验证结果，并响应外部数据变化
const previewTableData = computed(() => {
  
  // 首先过滤掉被删除的行 - 使用正确的行号匹配
  const filteredData = props.previewInfo.previewData.filter((dataItem) => {
    // 始终使用数据项本身的rowIndex，这是正确的Excel行号
    const rowIndex = dataItem.rowIndex;
    const isDeleted = props.deletedRows?.includes(rowIndex);
    return !isDeleted;
  });
  
  
  // 然后应用更新的数据
  const result = filteredData.map((dataItem) => {
    // 始终使用数据项本身的rowIndex，这是正确的Excel行号
    const rowIndex = dataItem.rowIndex;
    const originalData = dataItem.data || dataItem;
    
    // 查找是否有对应的更新数据
    const updatedRow = props.updatedData?.find(item => {
      const updatedRowIndex = item.rowIndex || item.row_index;
      return updatedRowIndex === rowIndex;
    });
    
    // 如果有更新数据，则使用更新后的数据，否则使用原始数据
    const data = updatedRow ? { ...updatedRow } : { ...originalData };
    
    // 移除更新数据中的元数据字段
    if (updatedRow) {
      delete data.rowIndex;
      delete data.row_index;
      delete data._errors;
    }
    
    // 获取该行的错误信息 - 只有当该行有错误时才显示
    const rowErrors = props.errorsByRow?.[rowIndex] || {};
    
    return {
      rowIndex,
      data,
      source: dataItem.source || props.previewInfo.source,
      _errors: Object.keys(rowErrors).length > 0 ? rowErrors : {} // 只有当有错误时才设置_errors
    };
  });

  return result;
});

const hasAnyErrors = computed(() => {
  // 只有当errorsByRow存在且有实际错误内容时才返回true
  if (!props.errorsByRow) return false;
  
  // 检查errorsByRow中是否有任何行有错误信息
  return Object.values(props.errorsByRow).some(rowErrors => 
    rowErrors && Object.keys(rowErrors).length > 0
  );
});

// Methods
const formatCellValue = (value: any): string => {
  if (value === null || value === undefined) {
    return '';
  }
  if (typeof value === 'boolean') {
    return value ? '是' : '否';
  }
  return String(value);
};

const isEmpty = (value: any): boolean => {
  return value === null || value === undefined || String(value).trim() === '';
};

const hasFieldError = (row: any, fieldKey: string): boolean => {
  // 检查多个错误信息来源，确保实时更新
  const rowErrors = row._errors || {};
  const rowIndex = row.rowIndex;
  
  // 同时检查props.errorsByRow中的错误信息
  const propsErrors = props.errorsByRow?.[rowIndex] || {};
  
  // 如果任一来源有该字段的错误，就返回true
  return !!(rowErrors[fieldKey] || propsErrors[fieldKey]);
};

const getFieldLabel = (fieldKey: string): string => {
  const field = props.config.templateFields.find(f => f.key === fieldKey);
  return field?.label || fieldKey;
};



// 生命周期钩子 - 自动执行前端验证
onMounted(() => {
  if (props.previewInfo.previewData.length > 0) {
    performFrontendValidation();
  }
});

// 监听数据变化，重新验证
watch(
  () => props.previewInfo.previewData,
  (newData) => {
    if (newData && newData.length > 0) {
      performFrontendValidation();
    }
  },
  { deep: true }
);

// 新增：监听 updatedData 变化，当单行数据修改时重新验证
watch(
  () => props.updatedData,
  (newUpdatedData, oldUpdatedData) => {
    // 只有当 updatedData 实际发生变化时才重新验证
    if (newUpdatedData && newUpdatedData.length > 0 && 
        JSON.stringify(newUpdatedData) !== JSON.stringify(oldUpdatedData)) {
      performFrontendValidation();
    }
  },
  { deep: true }
);
</script>

<style scoped>
@import '../../../css/base-styles.css';
@import '../../../css/common-import.css';

/* 组件特有样式 */
:deep(.el-table__header-wrapper) {
  background: #f5f7fa;
}

:deep(.el-table__row:hover) {
  background: #f0f8ff;
}

:deep(.el-table__fixed-column--left) {
  background: #fff;
}

:deep(.el-table__fixed-column--right) {
  background: #fff;
}

/* 错误信息列样式 */
.error-messages {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 120px;
  overflow-y: auto;
}

.error-item {
  display: flex;
  align-items: flex-start;
}

.error-tag {
  white-space: normal !important;
  word-wrap: break-word !important;
  word-break: break-all !important;
  height: auto !important;
  line-height: 1.4 !important;
  padding: 4px 8px !important;
  max-width: 100%;
  display: inline-block;
}

:deep(.error-tag .el-tag__content) {
  white-space: normal !important;
  word-wrap: break-word !important;
  word-break: break-all !important;
  line-height: 1.4 !important;
}

/* 前端验证特有样式 */
.error-cell {
  background-color: #fef0f0 !important;
  border: 1px solid #f56c6c !important;
}

.empty-cell {
  background-color: #fff7e6 !important;
}


</style>