<template>
  <div class="import-progress">
    <div class="progress-header">
      <h4>{{ config.entityName }}数据导入进度</h4>
      <div class="progress-status" :class="statusClass">
        {{ getStatusText() }}
      </div>
    </div>
    
    <!-- 进度条 -->
    <div class="progress-bar-section">
      <el-progress 
        :percentage="progress.percentage" 
        :status="getProgressStatus()"
        :stroke-width="12"
        :show-text="true"
      >
        <template #default="{ percentage }">
          <span class="progress-text">{{ percentage }}%</span>
        </template>
      </el-progress>
      
      <div class="progress-info">
        <span>{{ progress.current }} / {{ progress.total }}</span>
        <span class="progress-message">{{ progress.message }}</span>
      </div>
    </div>
    

    
    <!-- 导入完成提示 -->
    <div v-if="progress.status === 'completed'" class="completion-notice">
      <el-alert
        title="导入任务已完成"
        type="success"
        description="请点击下方按钮查看详细结果"
        show-icon
        :closable="false"
      />
    </div>
    
    <!-- 详细进度信息 -->
    <div v-if="showDetails" class="progress-details">
      <div class="details-header">
        <span>详细进度</span>
        <el-button 
          type="text" 
          size="small" 
          @click="toggleDetails"
        >
          {{ showDetails ? '收起' : '展开' }}
        </el-button>
      </div>
      
      <div class="details-content">
        <div class="detail-item">
          <span class="detail-label">开始时间：</span>
          <span class="detail-value">{{ formatTime(startTime) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">已用时间：</span>
          <span class="detail-value">{{ getElapsedTime() }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">预计剩余：</span>
          <span class="detail-value">{{ getEstimatedTime() }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">处理速度：</span>
          <span class="detail-value">{{ getProcessingSpeed() }}</span>
        </div>
      </div>
    </div>
    

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
// 移除了不需要的ElMessage和ElMessageBox导入

import type { ImportConfig, ImportProgress } from '@/services/types/import';

// Props
interface Props {
  config: ImportConfig;
  progress: ImportProgress;
}

const props = defineProps<Props>();


// Refs
const showDetails = ref(false);
// 移除了cancelling相关状态

const startTime = ref<Date | null>(null);
const progressTimer = ref<number | null>(null);

// Computed
const statusClass = computed(() => {
  return {
    'status-uploading': props.progress.status === 'uploading',
    'status-parsing': props.progress.status === 'parsing',
    'status-validating': props.progress.status === 'validating',
    'status-importing': props.progress.status === 'importing',
    'status-completed': props.progress.status === 'completed',
    'status-error': props.progress.status === 'error'
  };
});

// Methods
const getStatusText = (): string => {
  switch (props.progress.status) {
    case 'uploading':
      return '正在上传文件...';
    case 'parsing':
      return '正在解析数据...';
    case 'validating':
      return '正在验证数据...';
    case 'importing':
      return '正在导入数据...';
    case 'completed':
      return '导入完成';
    case 'error':
      return '导入失败';
    default:
      return '准备中...';
  }
};

const getProgressStatus = () => {
  if (props.progress.status === 'error') return 'exception';
  if (props.progress.status === 'completed') return 'success';
  return undefined;
};

const toggleDetails = () => {
  showDetails.value = !showDetails.value;
};

const formatTime = (time: Date | null): string => {
  if (!time) return '--';
  return time.toLocaleTimeString();
};

const getElapsedTime = (): string => {
  if (!startTime.value) return '--';
  const elapsed = Date.now() - startTime.value.getTime();
  const seconds = Math.floor(elapsed / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) {
    return `${hours}小时${minutes % 60}分钟`;
  } else if (minutes > 0) {
    return `${minutes}分钟${seconds % 60}秒`;
  } else {
    return `${seconds}秒`;
  }
};

const getEstimatedTime = (): string => {
  if (props.progress.percentage === 0 || !startTime.value) return '--';
  
  const elapsed = Date.now() - startTime.value.getTime();
  const estimatedTotal = (elapsed / props.progress.percentage) * 100;
  const remaining = estimatedTotal - elapsed;
  
  if (remaining <= 0) return '即将完成';
  
  const remainingSeconds = Math.floor(remaining / 1000);
  const remainingMinutes = Math.floor(remainingSeconds / 60);
  
  if (remainingMinutes > 0) {
    return `约${remainingMinutes}分钟`;
  } else {
    return `约${remainingSeconds}秒`;
  }
};

const getProcessingSpeed = (): string => {
  if (!startTime.value || props.progress.current === 0) return '--';
  
  const elapsed = Date.now() - startTime.value.getTime();
  const speed = (props.progress.current / elapsed) * 1000; // 每秒处理数量
  
  if (speed < 1) {
    return `${(speed * 60).toFixed(1)}条/分钟`;
  } else {
    return `${speed.toFixed(1)}条/秒`;
  }
};


// Watchers
watch(() => props.progress.status, (newStatus) => {
  if (newStatus === 'uploading' && !startTime.value) {
    startTime.value = new Date();
  }
  
  if (newStatus === 'completed' || newStatus === 'error') {
    if (progressTimer.value) {
      clearInterval(progressTimer.value);
      progressTimer.value = null;
    }
  }
});

// Lifecycle
onMounted(() => {
  // 启动进度更新定时器
  progressTimer.value = window.setInterval(() => {
    // 强制重新计算时间相关的computed属性
  }, 1000);
});

onUnmounted(() => {
  if (progressTimer.value) {
    clearInterval(progressTimer.value);
  }
});
</script>

<style scoped>
@import '../../../css/base-styles.css';
@import '../../../css/common-import.css';



/* 完成提示样式 */
.completion-notice {
  margin: 20px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  /* 移除了不需要的样式 */
}



/* 组件特有样式，覆盖或补充通用样式 */
</style>