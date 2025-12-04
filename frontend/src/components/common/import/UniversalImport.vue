<template>
  <div class="import-container universal-import">
    <!-- 导入标题和配置信息 -->
    <div class="import-header">
      <h2>{{ config.entityName }}数据导入</h2>
      <div class="import-info">
        <el-tag type="info" size="small">{{ config.entityKey }}</el-tag>
        <!-- 状态显示由各子组件处理，这里不重复显示 -->
      </div>
    </div>
    
    <!-- 导入步骤指示器 -->
    <div class="import-steps">
      <el-steps :active="currentStep" :finish-status="getStepFinishStatus()" align-center>
        <el-step title="上传数据" description="选择Excel文件或粘贴数据" />
        <el-step title="预览验证" description="检查数据格式和内容" />
        <el-step title="导入处理" description="执行数据导入操作" />
        <el-step title="查看结果" description="查看导入结果详情" />
      </el-steps>
    </div>
    
    <!-- 内容区域 -->
    <div class="import-content">
      <!-- 第一步：数据上传 -->
      <div v-if="currentStep === 0" class="step-content">
        <ImportUploader
          :config="config"
          @data-parsed="handleDataParsed"
          @error="handleError"
        />
      </div>
      
      <!-- 第二步：数据预览和验证 -->
      <div v-if="currentStep === 1" class="step-content">
        <DataPreview
          :config="config"
          :preview-info="previewInfo!"
          :errors-by-row="errorsByRow"
          :updated-data="updatedData"
          :deleted-rows="deletedRows"
          @validation-completed="handleValidationCompleted"
        />
        
        <ValidationResult
          :config="config"
          :validation-errors="validationErrors"
          :total-count="previewInfo?.totalRows || 0"
          :force-download="(previewInfo?.totalRows ?? 0) > 20"
          :parsed-data="parsedData"
          :preview-info="previewInfo"
          @start-import="startImport"
          @submit-fixed-data="handleFixedData"
          @delete-row="handleDeleteRow"
          @reset-import="resetImport"
          @update-row-data="handleUpdateRowData"
        />
      </div>
      
      <!-- 第三步：导入进度 -->
      <div v-if="currentStep === 2" class="step-content">
        <ImportProgress
          :config="config"
          :progress="importProgress"
          @cancel="cancelImport"
          @retry="retryImport"
          @view-result="viewResult"
          @close="closeImport"
        />
      </div>
      
      <!-- 第四步：导入结果 -->
      <div v-if="currentStep === 3" class="step-content">
        <ImportResult
          :config="config"
          :result="importResult!"
          @view-data="viewImportedData"
          @retry-import="retryImport"
          @import-another="importAnother"
          @close="closeImport"
        />
      </div>
    </div>
    
    <!-- 底部操作栏 -->
    <div class="import-footer">
      <div class="footer-info">
        <span v-if="importResult?.has_error_file" class="error-file-info">
          错误文件已生成，可下载修改
        </span>
      </div>
      
      <div class="footer-actions">
        <el-button 
          v-if="currentStep > 0 && currentStep < 3"
          @click="goToPreviousStep"
        >
          上一步
        </el-button>
        
        <!-- 仍然导入按钮（仅在验证阶段且存在未修复的错误时显示） -->
        <el-button 
          v-if="currentStep === 1 && validationErrors.length > 0"
          type="warning"
          @click="forceImportWithErrors"
          class="force-import-btn"
        >
          <el-icon><Warning /></el-icon>
          仍然导入
        </el-button>
        
        <el-button 
          v-if="currentStep < 3"
          @click="resetImport"
        >
          重置
        </el-button>
        

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Warning } from '@element-plus/icons-vue';
import ImportUploader from './ImportUploader.vue';
import DataPreview from './DataPreview.vue';
import ValidationResult from './ValidationResult.vue';
import ImportProgress from './ImportProgress.vue';
import ImportResult from './ImportResult.vue';
import type { 
  ImportConfig, 
  ParsedData, 
  PreviewInfo, 
  ImportError, 
  ImportProgress as IImportProgress,
  BatchImportResult
} from '@/services/types/import';

// 导入状态类型
type ImportStatus = 'idle' | 'uploading' | 'parsing' | 'validating' | 'importing' | 'completed' | 'error';

// Props
interface Props {
  config: ImportConfig;
}

const props = defineProps<Props>();

// Emits
const emit = defineEmits<{
  'import-completed': [result: BatchImportResult];
  'close': [];
}>();

// Refs - 只保留流程控制所需的状态
const currentStep = ref(0);
const importStatus = ref<ImportStatus>('idle' as ImportStatus);
const previewInfo = ref<PreviewInfo | null>(null);
const importProgress = ref<IImportProgress>({
  current: 0,
  total: 0,
  percentage: 0,
  status: 'uploading',
  message: '准备中...'
});
const importResult = ref<BatchImportResult | null>(null);
const parsedData = ref<ParsedData[]>([]);
// 数据来源跟踪
const dataSource = ref<'excel' | 'paste'>('paste');
const originalExcelFile = ref<File | null>(null);

// 验证相关状态由 ValidationResult 组件管理
const validationErrors = ref<ImportError[]>([]);
const errorsByRow = ref<Record<number, Record<string, string>>>({});

// 用于传递给 DataPreview 组件的数据变化状态
const updatedData = ref<any[]>([]); // 更新后的数据
const deletedRows = ref<number[]>([]); // 被删除的行号

// Methods - 只保留流程控制所需的方法
const getStepFinishStatus = () => {
  return importStatus.value === 'error' ? 'error' : 'success';
};

// 处理数据解析完成
const handleDataParsed = (data: { parsedData: ParsedData[]; originalFile?: File | null; hasExceededLimit?: boolean }) => {
  handleUploadCompleted(data);
};

// 处理数据上传完成
const handleUploadCompleted = (data: { parsedData: ParsedData[]; originalFile?: File | null; hasExceededLimit?: boolean }) => {
  try {
    importStatus.value = 'parsing';
    
    const parsedDataArray = data.parsedData;
    const totalRows = parsedDataArray.length;
    const source = parsedDataArray[0]?.source || 'file';
    
    // 记录数据来源和原始文件
    dataSource.value = source === 'file' ? 'excel' : 'paste';
    
    if (source === 'file' && data.originalFile) {
      originalExcelFile.value = data.originalFile;
    }
    
    // 统一数据管理逻辑：
    // 1. 粘贴数据：无论条数多少，都截取前20条，且支持在线编辑
    // 2. Excel导入数据：
    //    - 小于等于20条：复制一份用于在线编辑
    //    - 大于20条：只显示前20条，不支持在线编辑
    
    let previewData: any[] = [];
    let editableData: any[] = [];
    let isEditable = false;
    
    if (source === 'paste') {
      // 粘贴数据：截取前20条，支持在线编辑
      const previewRows = Math.min(totalRows, 20);
      previewData = parsedDataArray.slice(0, previewRows);
      editableData = [...previewData]; // 复制一份用于编辑
      isEditable = true;
      console.log(`粘贴数据：总${totalRows}条，截取${previewRows}条预览，支持在线编辑`);
    } else {
      // Excel导入数据
      if (totalRows <= 20) {
        // 小数据量：复制一份用于在线编辑
        previewData = [...parsedDataArray];
        editableData = [...parsedDataArray];
        isEditable = true;
        console.log(`Excel导入小数据：${totalRows}条，复制一份用于在线编辑`);
      } else {
        // 大数据量：只显示前20条，不支持在线编辑
        const previewRows = 20;
        previewData = parsedDataArray.slice(0, previewRows);
        editableData = []; // 空数组表示不支持编辑
        isEditable = false;
        console.log(`Excel导入大数据：${totalRows}条，只显示前${previewRows}条，不支持在线编辑`);
      }
    }
    
    const hasMoreData = totalRows > 20;
    const previewRows = previewData.length;
    
    previewInfo.value = {
      previewData,
      totalRows,
      previewRows,
      hasMoreData,
      source,
      isEditable,
      hasExceededLimit: data.hasExceededLimit || false
    };
    
    // 保存完整的解析数据（传给 ValidationResult 组件进行验证）
    // 对于小数据量，保存可编辑数据副本；对于大数据量，保存原始数据
    parsedData.value = isEditable ? editableData : parsedDataArray;
    
    // 进入预览步骤，验证由 DataPreview 组件处理
    currentStep.value = 1;
    importStatus.value = 'validating';
    
  } catch (error: any) {
    handleError(`数据解析失败：${error.message}`);
  }
};

// 处理 DataPreview 组件的前端验证结果
const handleValidationCompleted = (errors: Record<number, Record<string, string>>) => {
  errorsByRow.value = errors;
  
  // 转换为 ValidationResult 组件需要的格式
  const validationErrorsList: ImportError[] = [];
  Object.entries(errors).forEach(([rowIndex, fieldErrors]) => {
    Object.entries(fieldErrors).forEach(([field, message]) => {
      validationErrorsList.push({
        row_index: parseInt(rowIndex),
        field: field,
        error_message: message,
        raw_data: parsedData.value[parseInt(rowIndex) - 1]?.data || {}
      });
    });
  });
  
  validationErrors.value = validationErrorsList;
};


// 导入数据函数
const startImport = async () => {
  if (!previewInfo.value || !parsedData.value.length) {
    ElMessage.error('没有可导入的数据');
    return;
  }
  
  try {
    // 应用在线编辑修改
    const finalData = [...parsedData.value];
    
    console.log('应用在线编辑修改:', updatedData.value);
    
    // 遍历所有更新过的数据行
    updatedData.value.forEach(updatedRow => {
      const rowIndex = updatedRow.rowIndex;
      // 在 parsedData 中找到对应的索引位置
      const dataIndex = finalData.findIndex(item => 
        item.rowIndex === rowIndex
      );
      
      if (dataIndex >= 0 && dataIndex < finalData.length) {
        // 创建更新的数据项，保持原有结构但更新data字段
        const updatedRowData = { ...updatedRow };
        delete updatedRowData.rowIndex; // 移除元数据字段
        
        finalData[dataIndex] = {
          ...finalData[dataIndex], // 保持原有结构（rowIndex, source等）
          data: updatedRowData     // 更新实际数据
        };
      }
    });
    
    // 删除标记为删除的行
    const filteredData = finalData.filter((_, index) => !deletedRows.value.includes(index));
    
    // 转换数据格式
    const dataToImport = filteredData.map(item => item.data || item);
    
    // 统一调用executeImport函数，由它内部处理提交方式
    await executeImport(false, dataToImport);
  } catch (error) {
    console.error('导入过程中发生错误:', error);
    ElMessage.error('导入失败：' + (error as Error).message);
  }
};

// 仍然导入（包含错误数据）
const forceImportWithErrors = async () => {
  if (!previewInfo.value || !parsedData.value.length) {
    ElMessage.error('没有可导入的数据');
    return;
  }
  
  // 显示确认对话框
  try {
    await ElMessageBox.confirm(
      `将强制导入所有数据（包含错误数据）。错误数据将被跳过或进行默认处理。是否继续？`,
      '确认强制导入',
      {
        confirmButtonText: '确定导入',
        cancelButtonText: '取消',
        type: 'warning',
        dangerouslyUseHTMLString: false
      }
    );
    
    // 用户确认后，执行强制导入
    // 合并在线编辑修改后的数据
    let finalData = [...parsedData.value];
    
    if (updatedData.value.length > 0) {
      console.log('强制导入时应用在线编辑修改:', updatedData.value);
      
      updatedData.value.forEach(updatedRow => {
        const rowIndex = updatedRow.rowIndex;
        const dataIndex = finalData.findIndex(item => 
          item.rowIndex === rowIndex
        );
        
        if (dataIndex >= 0 && dataIndex < finalData.length) {
          const updatedRowData = { ...updatedRow };
          delete updatedRowData.rowIndex;
          
          finalData[dataIndex] = {
            ...finalData[dataIndex],
            data: updatedRowData
          };
        }
      });
    }
    
    const dataToImport = finalData.map(item => item.data || item);
    await executeImport(true, dataToImport); // 传递 true 表示强制导入
  } catch {
    // 用户取消了导入
    ElMessage.info('已取消强制导入');
  }
};




// 执行导入操作
const executeImport = async (isForceImport: boolean, dataToImport?: any[]) => {
  const importData = dataToImport || parsedData.value.map(item => item.data || item);
 
  if (!previewInfo.value || !importData.length) {
    ElMessage.error('没有可导入的数据');
    return;
  }
  
  try {
    currentStep.value = 2;
    importStatus.value = 'importing';
    
    const importType = isForceImport ? '强制导入' : '导入';
    const totalRecords = importData.length;
    
    // 阶段1：准备导入
    importProgress.value = {
      current: 0,
      total: totalRecords,
      percentage: 0,
      status: 'uploading',
      message: `正在准备${importType}${props.config.entityName}数据...`
    };
    
    // 短暂延迟显示准备阶段
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 阶段2：解析数据
    importProgress.value = {
      ...importProgress.value,
      percentage: 10,
      status: 'parsing',
      message: `正在解析${props.config.entityName}数据...`
    };
    
    await new Promise(resolve => setTimeout(resolve, 800));
    
    // 阶段3：验证数据
    importProgress.value = {
      ...importProgress.value,
      percentage: 25,
      status: 'validating',
      message: `正在验证${props.config.entityName}数据格式...`
    };
    
    await new Promise(resolve => setTimeout(resolve, 600));
    
    
    // 阶段4：开始导入
    importProgress.value = {
      ...importProgress.value,
      percentage: 35,
      status: 'importing',
      message: `正在${importType}${props.config.entityName}数据...`
    };
    
    // 提交策略：根据数据来源和数量选择提交方式
    let result: BatchImportResult;
    console.log('开始导入的数据:', importData,dataSource.value,originalExcelFile.value);
    if (dataSource.value === 'excel' && originalExcelFile.value && importData.length > 20) {
      // Excel导入数据超过20条：提交原始Excel文件
      console.log('使用Excel文件提交：', originalExcelFile.value.name);
      importProgress.value.message = `正在提交Excel文件中的${importData.length}条${props.config.entityName}数据...`;
      
      const formData = new FormData();
      formData.append('file', originalExcelFile.value);
      formData.append('entityName', props.config.entityName);
      formData.append('entityKey', props.config.entityKey);
      formData.append('forceImport', isForceImport.toString());
      console.log('导入的文件格式:', formData);
      result = await props.config.batchImportAPI(formData);
    } else {
      // 粘贴数据或Excel小数据量：JSON格式提交前20条
      const dataToSend = importData.slice(0, 20);
      
      // 在提交前进行字段类型转换，确保数据类型符合后端要求
      const processedData = dataToSend.map(item => {
        const processedItem = { ...item };
        
        // 将数字类型的联系方式转换为字符串类型
        if (processedItem.supplier_contact && typeof processedItem.supplier_contact === 'number') {
          processedItem.supplier_contact = processedItem.supplier_contact.toString();
        }
        if (processedItem.customer_contact && typeof processedItem.customer_contact === 'number') {
          processedItem.customer_contact = processedItem.customer_contact.toString();
        }
        
        // 将数字类型的等级字段转换为整数类型
        if (processedItem.supplier_level && typeof processedItem.supplier_level === 'string') {
          const level = parseInt(processedItem.supplier_level);
          if (!isNaN(level)) {
            processedItem.supplier_level = level;
          }
        }
        if (processedItem.customer_level && typeof processedItem.customer_level === 'string') {
          const level = parseInt(processedItem.customer_level);
          if (!isNaN(level)) {
            processedItem.customer_level = level;
          }
        }
        
        return processedItem;
      });
      
      console.log(`使用JSON格式提交前${processedData.length}条数据:`, processedData);
      importProgress.value.message = `正在提交前${processedData.length}条${props.config.entityName}数据...`;
      
      result = await props.config.batchImportAPI(processedData);
    }
    
    // 阶段5：处理结果
    importProgress.value = {
      ...importProgress.value,
      percentage: 95,
      status: 'importing',
      message: '正在处理导入结果...'
    };
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 阶段6：完成
    importProgress.value = {
      current: result.total_count,
      total: result.total_count,
      percentage: 100,
      status: 'completed',
      message: '导入完成',
      success_count: result.success_count,
      error_count: result.error_count,
      has_error_file: result.has_error_file,
      error_file_name: result.error_file_name
    };
    
    // 保存结果但不自动跳转到结果页，停留在进度页面
    importResult.value = result;
    // 更新步骤指示器到"查看结果"阶段
    currentStep.value = 3;
    importStatus.value = 'completed';
    
    // 发出完成事件
    emit('import-completed', result);
    
    // 显示结果消息
    if (isForceImport && result.has_error_file) {
      ElMessage.warning(`${importType}完成：成功 ${result.success_count} 条，失败 ${result.error_count} 条。错误文件已生成，请在结果页面下载。`);
    } else if (result.error_count > 0) {
      ElMessage.warning(`${importType}完成：成功 ${result.success_count} 条，失败 ${result.error_count} 条`);
    } else {
      ElMessage.success(`${importType}成功：共导入 ${result.success_count} 条${props.config.entityName}数据`);
    }
    
  } catch (error: any) {
    importStatus.value = 'error';
    importProgress.value.status = 'error';
    importProgress.value.message = `导入失败：${error.message}`;
    handleError(`导入失败：${error.message}`);
  }
};

const handleDeleteRow = (rowIndex: number) => {
  console.log('=== 开始删除操作 ===');
  console.log('传入的行号:', rowIndex);
  console.log('当前parsedData长度:', parsedData.value.length);
  console.log('当前deletedRows:', deletedRows.value);
  
  // 验证行号是否有效
  if (rowIndex < 2) {
    console.log('行号无效，小于2');
    ElMessage.error('无效的行号，无法删除');
    return;
  }
  
  // 检查该行是否存在于原始数据中
  const dataIndex = rowIndex - 2; // Excel行号从2开始，数据索引从0开始
  console.log('计算的数据索引:', dataIndex);
  
  const existsInOriginalData = dataIndex >= 0 && dataIndex < parsedData.value.length;
  console.log('行是否存在:', existsInOriginalData);
  
  if (!existsInOriginalData) {
    console.log('行不存在于原始数据中');
    ElMessage.error('无效的行号，无法删除');
    return;
  }
  
  // 添加到已删除行列表（不修改原始数据）
  if (!deletedRows.value.includes(rowIndex)) {
    console.log('添加行号到deletedRows:', rowIndex);
    deletedRows.value.push(rowIndex);
  } else {
    console.log('行号已在deletedRows中，跳过添加');
  }
  
  console.log('删除后的deletedRows:', deletedRows.value);
  
  // 只清除被删除行的错误信息，保留其他行的错误信息
  validationErrors.value = validationErrors.value.filter(error => error.row_index !== rowIndex);
  if (errorsByRow.value[rowIndex]) {
    delete errorsByRow.value[rowIndex];
  }
  
  // 重新计算剩余的有效行数
  const remainingRows = parsedData.value.length - deletedRows.value.length;
  console.log('剩余有效行数:', remainingRows);
  
  // 更新预览信息中的总行数（但不修改previewData）
  if (previewInfo.value) {
    console.log('更新previewInfo.totalRows:', remainingRows);
    previewInfo.value.totalRows = remainingRows;
    previewInfo.value.hasMoreData = remainingRows > 20;
  }
  
  console.log('=== 删除操作完成 ===');
  ElMessage.success(`已删除第 ${rowIndex} 行数据，剩余 ${remainingRows} 条数据`);
};

const handleFixedData = (fixedData: any[]) => {
  // 不可以直接替换所有数据，应该将修复后的数据与原始数据合并
  if (!previewInfo.value) {
    ElMessage.error('没有预览数据，无法修复');
    return;
  }
  
  // 保持原始数据，只替换错误行
  const allData = [...parsedData.value];
  
  // 将修复后的数据按行号替换到原数据中
  fixedData.forEach(fixedRow => {
    // 从 ValidationResult 组件传来的数据可能包含 rowIndex
    // 需要找到对应的原始数据位置
    const originalRowIndex = fixedRow.rowIndex || fixedRow.row_index;
    if (originalRowIndex) {
      // 在 parsedData 中找到对应的索引位置
      // parsedData 的索引是从 0 开始，而 rowIndex 从 2 开始（Excel行号）
      const dataIndex = originalRowIndex - 2;
      if (dataIndex >= 0 && dataIndex < allData.length) {
        // 移除 rowIndex 等元数据字段，只保留实际的业务数据
        const cleanFixedRow = { ...fixedRow };
        delete cleanFixedRow.rowIndex;
        delete cleanFixedRow.row_index;
        delete cleanFixedRow._errors;
        
        allData[dataIndex] = cleanFixedRow;
        
        // 添加到更新数据列表
        const existingIndex = updatedData.value.findIndex(item => {
          const itemRowIndex = item.rowIndex || item.row_index;
          return itemRowIndex === originalRowIndex;
        });
        
        if (existingIndex >= 0) {
          // 更新现有数据
          updatedData.value[existingIndex] = { ...cleanFixedRow, rowIndex: originalRowIndex };
        } else {
          // 添加新数据
          updatedData.value.push({ ...cleanFixedRow, rowIndex: originalRowIndex });
        }
      }
    }
  });
  
  // 更新数据
  parsedData.value = allData;
  
  // 清除错误信息
  validationErrors.value = [];
  errorsByRow.value = {};
  
  ElMessage.success(`数据修复完成，共修复 ${fixedData.length} 条错误数据，可以开始导入`);
};

// 处理单行数据更新事件
const handleUpdateRowData = (rowIndex: number, rowData: any) => {
  console.log('收到单行数据更新事件:', rowIndex, rowData);
  
  if (!previewInfo.value) {
    ElMessage.error('没有预览数据，无法更新');
    return;
  }
   
  // 在 parsedData 中找到对应的索引位置
  // 需要根据行号找到对应的数据索引
  const dataIndex = parsedData.value.findIndex(item => 
    item.rowIndex === rowIndex
  );
  
  if (dataIndex >= 0 && dataIndex < parsedData.value.length) {
    // 更新 parsedData 中的对应行数据
    const newParsedData = [...parsedData.value];
    newParsedData[dataIndex] = {
      ...newParsedData[dataIndex],
      ...rowData
    };
    
    // 更新数据，触发响应式更新
    parsedData.value = newParsedData;
    
    // 更新预览信息中的预览数据（如果该行在预览范围内）
    if (previewInfo.value.previewData) {
      const previewIndex = previewInfo.value.previewData.findIndex(item => 
        (item.rowIndex || item.row_index) === rowIndex
      );
      
      if (previewIndex >= 0) {
        const newPreviewData = [...previewInfo.value.previewData];
        newPreviewData[previewIndex] = {
          ...newPreviewData[previewIndex],
          ...rowData
        };
        previewInfo.value.previewData = newPreviewData;
      }
    }
    
    // 更新 updatedData，确保 DataPreview 组件能够正确显示更新后的数据
    const existingIndex = updatedData.value.findIndex(item => {
      const itemRowIndex = item.rowIndex || item.row_index;
      return itemRowIndex === rowIndex;
    });
    
    if (existingIndex >= 0) {
      // 更新现有数据
      updatedData.value[existingIndex] = { ...rowData, rowIndex };
    } else {
      // 添加新数据
      updatedData.value.push({ ...rowData, rowIndex });
    }
    
    // 清除该行的错误信息 - 使用响应式更新确保状态同步
    // 注意：不要手动修改 validationErrors，让 DataPreview 组件重新验证后自动更新
    // 但是需要立即清除 errorsByRow 中的该行错误，避免界面显示延迟
    if (errorsByRow.value[rowIndex]) {
      const newErrorsByRow = { ...errorsByRow.value };
      delete newErrorsByRow[rowIndex];
      errorsByRow.value = newErrorsByRow;
    }
    
    console.log('单行数据更新完成，预览表数据已刷新');
    // 不显示成功消息，避免干扰用户体验
  } else {
    console.error('无效的行索引:', rowIndex, '数据索引:', dataIndex);
    ElMessage.error(`无效的行号 ${rowIndex}，无法更新数据`);
  }
};



const cancelImport = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要取消导入吗？已导入的数据将会保留。',
      '确认取消',
      {
        confirmButtonText: '确定',
        cancelButtonText: '继续导入',
        type: 'warning'
      }
    );
    
    importStatus.value = 'idle';
    resetImport();
    ElMessage.info('导入已取消');
  } catch {
    // 用户取消了取消操作
  }
};

const retryImport = () => {
  if (parsedData.value.length > 0) {
    startImport();
  } else {
    resetImport();
  }
};

const viewResult = () => {
  currentStep.value = 3; // 跳转到结果页面
};

const viewImportedData = () => {
  ElMessage.success('跳转到数据列表页面');
  emit('close');
};

const importAnother = () => {
  resetImport();
};

const closeImport = () => {
  // 重置步骤状态，确保下次打开时从第一步开始
  currentStep.value = 0;
  emit('close');
};

const goToPreviousStep = () => {
  if (currentStep.value > 0) {
    // 如果从预览界面（步骤1）返回到上传界面（步骤0），需要重置预览数据
    if (currentStep.value === 1) {
      // 重置预览相关的数据状态，但保留导入配置
      previewInfo.value = null;
      validationErrors.value = [];
      errorsByRow.value = {};
      parsedData.value = [];
      updatedData.value = [];
      deletedRows.value = [];
      console.log('从预览界面返回上传界面，已重置预览数据状态');
    }
    currentStep.value--;
  }
};

const resetImport = () => {
  currentStep.value = 0;
  importStatus.value = 'idle';
  previewInfo.value = null;
  validationErrors.value = [];
  errorsByRow.value = {};
  parsedData.value = [];
  importResult.value = null;
  importProgress.value = {
    current: 0,
    total: 0,
    percentage: 0,
    status: 'uploading',
    message: '准备中...',
    success_count: 0,
    error_count: 0,
    has_error_file: false
  };
};

const handleError = (message: string) => {
  importStatus.value = 'error';
  ElMessage.error(message);
};





// Watchers
watch(() => currentStep.value, (newStep) => {
  if (newStep === 0) {
    importStatus.value = 'idle';
  }
});
</script>

<style scoped>
@import '../../../css/base-styles.css';
@import '../../../css/common-import.css';

/* 组件特有样式（如果有） */

/* 仍然导入按钮样式 */
.force-import-btn {
  background-color: #e6a23c;
  border-color: #e6a23c;
  color: #fff;
}

.force-import-btn:hover {
  background-color: #ebb563;
  border-color: #ebb563;
}

.footer-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>