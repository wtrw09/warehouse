<template>
  <div class="import-result-container">
    <!-- 顶部标题区域 -->
    <div class="header-section">
      <h2 class="page-title">导入结果</h2>
      <p class="page-subtitle">{{ config.entityName }}数据导入完成</p>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-section">
      <!-- 成功信息卡片 -->
      <div v-if="result.success_count > 0" class="success-card">
        <div class="card-header success-header">
          <el-icon class="header-icon"><SuccessFilled /></el-icon>
          <span class="header-title">导入成功</span>
        </div>
        <div class="card-content">
          <div class="success-stats">
            <div class="stat-item">
              <div class="stat-value">{{ result.success_count }}</div>
              <div class="stat-label">成功条数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ getSuccessRate() }}</div>
              <div class="stat-label">成功率</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ getImportSpeed() }}</div>
              <div class="stat-label">导入速度</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatImportTime() }}</div>
              <div class="stat-label">导入时间</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 错误信息区域 -->
      <div v-if="result.error_count > 0" class="error-section">
        <!-- 错误文件下载卡片 -->
        <div class="error-file-card">
          <div class="card-header error-header">
            <el-icon class="header-icon"><WarningFilled /></el-icon>
            <span class="header-title">错误处理</span>
          </div>
          <div class="card-content">
            <div class="error-info">
              <p class="error-count">发现 {{ result.error_count }} 个错误</p>
              <div class="error-actions">
                <el-button 
                  v-if="result.has_error_file && result.error_file_name"
                  type="danger" 
                  :icon="Download"
                  @click="downloadErrorFile"
                  :loading="downloadLoading"
                  class="download-btn"
                >
                  下载错误文件
                </el-button>
                <div v-else class="no-file-info">
                  <el-icon><InfoFilled /></el-icon>
                  <span>未生成错误文件</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 错误详情卡片 -->
        <div class="error-details-card">
          <div class="card-header details-header">
            <div class="header-left">
              <el-icon class="header-icon"><PieChart /></el-icon>
              <span class="header-title">错误详情分析</span>
            </div>
            <el-button 
              type="primary"
              size="small" 
              @click="toggleErrorDetails"
              class="toggle-btn"
            >
              <el-icon>
                <ArrowUp v-if="showErrorDetails" />
                <ArrowDown v-else />
              </el-icon>
              {{ showErrorDetails ? '收起详情' : '展开详情' }}
            </el-button>
          </div>

          <!-- 错误详情内容 -->
          <div v-if="showErrorDetails" class="details-content">
            <!-- 错误分类统计 -->
            <div class="error-categories">
              <h4 class="section-title">错误分类</h4>
              <div class="categories-grid">
                <div 
                  v-for="(count, category) in errorCategories" 
                  :key="category" 
                  class="category-item"
                >
                  <el-tag type="danger" effect="dark" class="category-tag">
                    {{ category }}
                  </el-tag>
                  <span class="category-count">{{ count }} 次</span>
                </div>
              </div>
            </div>

            <!-- 错误数据表格 -->
            <div class="error-table-section">
              <h4 class="section-title">错误数据列表</h4>
              <el-table 
                :data="errorTableData" 
                border 
                size="small" 
                max-height="300"
                :row-class-name="getErrorRowClassName"
                class="error-table"
                stripe
              >
                <el-table-column prop="rowIndex" label="行号" width="80" align="center" />
                <el-table-column prop="fieldLabel" label="字段" width="120" />
                <el-table-column prop="errorMessage" label="错误信息" min-width="200" />
                <el-table-column prop="currentValue" label="错误值" width="150" show-overflow-tooltip />
              </el-table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮区域 -->
    <div class="actions-section">
      <el-row :gutter="20" justify="center">
        
        <el-col :xs="24" :sm="12" :md="6" :lg="6">
          <el-button 
            v-if="result.error_count > 0"
            type="warning" 
            size="large"
            @click="retryImport"
            :icon="Refresh"
            class="action-btn"
          >
            重新导入
          </el-button>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6" :lg="6">
          <el-button 
            type="info" 
            size="large"
            @click="importAnother"
            :icon="Plus"
            class="action-btn"
          >
            导入其他文件
          </el-button>
        </el-col>
        
        <el-col :xs="24" :sm="12" :md="6" :lg="6">
          <el-button 
            size="large"
            @click="closeResult"
            :icon="Close"
            class="action-btn"
          >
            关闭
          </el-button>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';
import { 
  SuccessFilled, 
  WarningFilled, 
  Download,
  ArrowUp,
  ArrowDown,
  PieChart,
  Refresh,
  Plus,
  Close,
  InfoFilled
} from '@element-plus/icons-vue';
import { downloadErrorFile as downloadErrorFileUtil } from '@/services/errorHandling';
import type { ImportConfig, BatchImportResult } from '@/services/types/import';

// Props
interface Props {
  config: ImportConfig;
  result: BatchImportResult;
}

const props = defineProps<Props>();

// Emits
const emit = defineEmits<{
  'view-data': [];
  'retry-import': [];
  'import-another': [];
  'close': [];
}>();

// Refs
const showErrorDetails = ref(false);
const downloadLoading = ref(false);

// Computed
const errorTableData = computed(() => {
  return props.result.errors?.map(error => ({
    rowIndex: error.row_index,
    fieldLabel: getFieldLabel(error.field),
    errorMessage: error.error_message,
    currentValue: formatValue(error.raw_data?.[error.field])
  })) || [];
});

const errorCategories = computed(() => {
  const categories: Record<string, number> = {};
  props.result.errors?.forEach(error => {
    const category = getErrorCategory(error.error_message);
    categories[category] = (categories[category] || 0) + 1;
  });
  return categories;
});

// Methods
const formatImportTime = (): string => {
  return new Date(props.result.import_time).toLocaleString();
};

const getImportSpeed = (): string => {
  const speed = props.result.success_count / 1;
  return `${speed.toFixed(1)} 条/秒`;
};

const getSuccessRate = (): string => {
  const rate = (props.result.success_count / props.result.total_count) * 100;
  return `${rate.toFixed(1)}%`;
};

const getFieldLabel = (fieldKey: string): string => {
  const field = props.config.templateFields.find(f => f.key === fieldKey);
  return field?.label || fieldKey;
};

const formatValue = (value: any): string => {
  if (value === null || value === undefined) return '';
  return String(value);
};

const getErrorCategory = (errorMessage: string): string => {
  if (errorMessage.includes('不能为空')) return '必填项缺失';
  if (errorMessage.includes('已存在')) return '重复数据';
  if (errorMessage.includes('长度')) return '格式错误';
  if (errorMessage.includes('格式')) return '格式错误';
  return '其他错误';
};

const toggleErrorDetails = () => {
  showErrorDetails.value = !showErrorDetails.value;
};

const downloadErrorFile = async () => {
  // 后端返回的是error_file_name，需要构造完整的下载URL
  let fileName = props.result.error_file_name;
  
  if (!fileName) {
    ElMessage.warning('错误文件不存在');
    return;
  }
  
  downloadLoading.value = true;
  try {
    console.log('调用前输入名称:', fileName);
    await downloadErrorFileUtil(
        fileName, 
        `${props.config.entityName}导入错误数据.xls`,
        props.config.entityKey
      );
  } catch (error: any) {
    ElMessage.error(`下载失败：${error.message}`);
  } finally {
    downloadLoading.value = false;
  }
};


const retryImport = () => {
  emit('retry-import');
};

const importAnother = () => {
  emit('import-another');
};

const closeResult = () => {
  emit('close');
};

const getErrorRowClassName = ({ rowIndex }: { rowIndex: number }): string => {
  return rowIndex % 2 === 0 ? 'even-row' : 'odd-row';
};
</script>

<style scoped>
.import-result-container {
  max-width: 100%;
  margin: 0 auto;
  padding: 24px;
  background: #f8f9fa;
}

/* 头部样式 */
.header-section {
  text-align: center;
  margin-bottom: 12px;
}

/* 主要内容区域 */
.content-section {
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #1f2937;
  margin-top: 0px;
  padding-top: 0px;
  margin-bottom: 8px;
}

.page-subtitle {
  font-size: 16px;
  color: #6b7280;
  margin: 0;
}

/* 卡片通用样式 */
.success-card,
.error-file-card,
.error-details-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
  overflow: hidden;
}

.card-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 12px;
}

.success-header {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.error-header {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.details-header {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-icon {
  font-size: 24px;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
}

.card-content {
  padding: 24px;
}

/* 成功统计样式 */
.success-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #059669;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
}

/* 错误信息样式 */
.error-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.error-count {
  font-size: 16px;
  color: #374151;
  margin: 0;
  font-weight: 500;
}

.download-btn {
  padding: 12px 24px;
  font-weight: 600;
}

.no-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #6b7280;
}

/* 错误详情样式 */
.details-content {
  padding-top: 0;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 16px;
}

.error-categories {
  margin-bottom: 32px;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.category-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.category-tag {
  font-weight: 600;
}

.category-count {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.error-table-section {
  margin-top: 24px;
}

.error-table {
  border-radius: 8px;
  overflow: hidden;
}

/* 操作按钮样式 */
.actions-section {
  margin-top: 16px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.action-btn {
  width: 100%;
  padding: 16px;
  font-weight: 600;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .import-result-container {
    padding: 16px;
  }
  
  .success-stats {
    grid-template-columns: 1fr;
  }
  
  .error-info {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .categories-grid {
    grid-template-columns: 1fr;
  }
  
  .details-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>