<template>
  <div class="import-uploader">
    <!-- 文件上传区域 -->
    <div class="upload-section">
      <el-upload
        ref="uploadRef"
        action="#"
        :auto-upload="false"
        :show-file-list="false"
        :before-upload="beforeUpload"
        @change="handleFileChange"
        :accept="acceptedTypes"
        drag
        class="upload-dragger"
      >
        <div class="upload-content">
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">
            <p>点击或拖拽{{ config.entityName }}Excel文件到此处上传</p>
            <p class="upload-hint">支持 .xls 和 .xlsx 格式，文件大小不超过10MB</p>
          </div>
        </div>
      </el-upload>
    </div>
    
    <!-- 分隔线 -->
    <el-divider>或直接粘贴数据</el-divider>
    
    <!-- 粘贴数据区域 -->
    <div class="paste-section">
      <div class="paste-input-container">
        <el-input
          v-model="pasteData"
          type="textarea"
          :rows="8"
          :placeholder="generatePastePlaceholder()"
          @input="handlePasteInput"
          class="paste-textarea"
        />
        <div class="paste-tips">
          <el-icon><InfoFilled /></el-icon>
          <span>提示：请粘贴{{ config.entityName }}数据行（不包含标题），字段间用Tab键分隔，最多支持20条数据</span>
        </div>
      </div>
      
      <div class="paste-actions" v-if="pasteData.trim()">
        <el-button type="primary" @click="handlePasteData">
          解析粘贴的{{ config.entityName }}数据
        </el-button>
        <el-button @click="clearPasteData">
          清空
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElMessage, ElUpload } from 'element-plus';
import { UploadFilled, InfoFilled } from '@element-plus/icons-vue';
import * as XLSX from 'xlsx';
import type { ImportConfig, ParsedData } from '@/services/types/import';
import { SUPPORTED_FILE_TYPES, MAX_FILE_SIZE, MAX_PASTE_ROWS } from '@/services/types/import';

// Props
interface Props {
  config: ImportConfig;
}

const props = defineProps<Props>();

// Emits
const emit = defineEmits<{
  'data-parsed': [data: { parsedData: ParsedData[]; originalFile?: File | null; hasExceededLimit?: boolean }];
  'error': [message: string];
}>();

// Refs
const uploadRef = ref<InstanceType<typeof ElUpload>>();
const pasteData = ref('');

// Computed
const acceptedTypes = computed(() => {
  return '.xls,.xlsx';
});

// Methods
const beforeUpload = (file: File) => {
  // 检查文件类型
  if (!SUPPORTED_FILE_TYPES.includes(file.type)) {
    ElMessage.error('请选择Excel文件（.xls或.xlsx格式）');
    return false;
  }
  
  // 检查文件大小
  if (file.size > MAX_FILE_SIZE) {
    ElMessage.error(`文件大小不能超过${Math.round(MAX_FILE_SIZE / 1024 / 1024)}MB`);
    return false;
  }
  
  return true;
};

const handleFileChange = (file: any) => {
  if (file.raw) {
    parseExcelFile(file.raw);
  }
};

const parseExcelFile = (file: File) => {
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target?.result as ArrayBuffer);
      const workbook = XLSX.read(data, { type: 'array' });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 }) as any[][];
      
      const parsedData = parseDataWithConfig(jsonData, 'file');
      if (parsedData.length > 0) {
        // 传递原始Excel文件给父组件
        emit('data-parsed', {
          parsedData,
          originalFile: file
        });
        ElMessage.success(`成功解析${parsedData.length}条${props.config.entityName}数据`);
      } else {
        ElMessage.warning(`未解析到有效的${props.config.entityName}数据，请检查文件格式`);
      }
    } catch (error: any) {
      emit('error', `${props.config.entityName}Excel文件解析失败：${error.message}`);
      ElMessage.error(`Excel文件解析失败：${error.message}`);
    }
  };
  reader.readAsArrayBuffer(file);
};

const parseDataWithConfig = (jsonData: any[][], source: 'file' | 'paste'): ParsedData[] => {
  if (jsonData.length < 2) {
    throw new Error(`${props.config.entityName}数据至少需要包含标题行和数据行`);
  }
  
  const dataRows = jsonData.slice(1); // 从第二行开始为数据（第一行为标题）
  const fieldKeys = props.config.templateFields.map(f => f.key);
  
  return dataRows.map((row, index) => {
    const entityData: any = {};
    
    // 根据配置字段映射数据
    fieldKeys.forEach((key, keyIndex) => {
      entityData[key] = row[keyIndex] || '';
    });
    
    return {
      data: entityData,
      rowIndex: index + 1, // 统一行号从1开始，与粘贴模式保持一致
      source: source
    };
  }).filter(item => {
    // 过滤空行（至少有一个字段有值）
    return Object.values(item.data).some(value => value && value.toString().trim());
  });
};



const generatePastePlaceholder = () => {
  const fields = props.config.templateFields;
  const example1 = fields.map(f => f.example || '示例倷1').join('\t');
  const example2 = fields.map(f => f.example || '示例倷2').join('\t');
  
  return `请粘贴${props.config.entityName}数据（最多20条，不包含标题行）：\n${example1}\n${example2}`;
};

const handlePasteInput = () => {
  // 实时检查粘贴数据的行数
  if (pasteData.value.trim()) {
    const lines = pasteData.value.trim().split('\n');
    if (lines.length > MAX_PASTE_ROWS) {
      
      ElMessage.warning(`粘贴${props.config.entityName}数据超过${MAX_PASTE_ROWS}条，建议使用Excel文件导入`);
    }
  }
};

const handlePasteData = () => {
  console.log("粘贴数据函数被调用");
  if (!pasteData.value.trim()) {
    ElMessage.warning('请先粘贴数据');
    return;
  }
  
  try {
    const { data: parsedData, hasExceededLimit } = parsePasteData(pasteData.value);
    if (parsedData && parsedData.length > 0) {
      // 传递粘贴数据，不包含原始文件，同时传递hasExceededLimit信息
      emit('data-parsed', {
        parsedData,
        originalFile: null,
        hasExceededLimit
      });
    }
  } catch (error: any) {
    emit('error', `${props.config.entityName}粘贴数据解析失败：${error.message}`);
    ElMessage.error(`粘贴数据解析失败：${error.message}`);
  }
};

const parsePasteData = (text: string): { data: ParsedData[], hasExceededLimit: boolean } => {
  const lines = text.trim().split('\n').filter(line => line.trim()); // 过滤空行
  console.log("粘贴数据函数被调用");
  if (lines.length === 0) {
    ElMessage.warning('粘贴的数据为空，请检查');
    return { data: [], hasExceededLimit: false };
  }
  
  // 检查数据量，超过20条时提醒用户并只保留前20条
  let processedLines = lines;
  let hasExceededLimit = false;
  
  if (lines.length > MAX_PASTE_ROWS) {
    processedLines = lines.slice(0, MAX_PASTE_ROWS);
    hasExceededLimit = true;
    
    ElMessage.warning({
      message: `粘贴${props.config.entityName}数据超过${MAX_PASTE_ROWS}条，已自动保留前${MAX_PASTE_ROWS}条数据`,
      duration: 5000,
      showClose: true
    });
  }
  
  const result: ParsedData[] = [];
  const fieldKeys = props.config.templateFields.map(f => f.key);
  
  // 粘贴文本：直接处理所有行作为数据行（不包含标题行）
  for (let i = 0; i < processedLines.length; i++) {
    const line = processedLines[i].trim();
    if (!line) continue;
    
    // 使用Tab分隔字段
    const fields = line.split('\t').map(field => field.trim());
    
    // 检查字段数量
    if (fields.length < 1) {
      ElMessage.warning(`第${i + 1}行${props.config.entityName}数据格式不正确，请检查Tab分隔符`);
      continue;
    }
    
    // 动态构建数据对象
    const entityData: any = {};
    fieldKeys.forEach((key, index) => {
      entityData[key] = fields[index] || '';
    });
    
    // 检查是否为有效数据行（至少有一个字段有值）
    const hasValidData = Object.values(entityData).some(value => 
      value && value.toString().trim() !== '');
    
    if (hasValidData) {
      result.push({
        data: entityData,
        rowIndex: i + 1, // 粘贴文本的行号从1开始
        source: 'paste'
      });
    }
  }
  
  if (result.length === 0) {
    ElMessage.warning(`未解析到有效的${props.config.entityName}数据，请检查格式`);
    return { data: [], hasExceededLimit: false };
  }
  
  // 根据是否超过限制显示不同的成功消息
  if (hasExceededLimit) {
    ElMessage.success(`成功解析前${MAX_PASTE_ROWS}条${props.config.entityName}数据（共${lines.length}条，已自动截断）`);
  } else {
    ElMessage.success(`成功解析${result.length}条${props.config.entityName}数据`);
  }
  console.log("解析粘贴数据过程中是否超过20条", hasExceededLimit);
  return { data: result, hasExceededLimit };
};

const clearPasteData = () => {
  pasteData.value = '';
  ElMessage.info('已清空粘贴数据');
};
</script>

<style scoped>
@import '../../../css/base-styles.css';
@import '../../../css/common-import.css';

/* 组件特有样式 */
.upload-dragger {
  width: 100%;
}

:deep(.el-upload-dragger) {
  border: 2px dashed #d9d9d9;
  border-radius: 6px;
  background: #fafafa;
  transition: all 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
  background: #f0f8ff;
}

:deep(.el-upload-dragger.is-dragover) {
  border-color: #409eff;
  background: #f0f8ff;
}
</style>