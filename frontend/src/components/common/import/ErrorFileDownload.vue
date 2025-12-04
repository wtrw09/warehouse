<template>
  <div class="error-file-download">
    <div class="download-container">
      <h2>错误文件下载</h2>
      <div class="download-status" v-if="loading">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>正在下载错误文件，请稍候...</span>
      </div>
      <div class="download-error" v-else-if="error">
        <el-alert
          :title="error"
          type="error"
          show-icon
          :closable="false"
        />
        <div class="retry-section">
          <el-button type="primary" @click="retryDownload">
            重试下载
          </el-button>
          <el-button @click="goBack">返回</el-button>
        </div>
      </div>
      <div class="download-success" v-else-if="success">
        <el-alert
          title="文件下载成功"
          type="success"
          show-icon
          :closable="false"
        />
        <div class="success-actions">
          <el-button @click="goBack">返回</el-button>
        </div>
      </div>
      <div class="manual-download" v-else>
        <p>如果自动下载未开始，请点击下方按钮手动下载：</p>
        <el-button type="primary" @click="startDownload">
          手动下载错误文件
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { downloadErrorFile } from '@/services/errorHandling'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref('')
const success = ref(false)

const startDownload = async () => {
  const fileName = route.query.fileName as string
  const entityType = route.query.entityType as string || 'supplier'
  
  if (!fileName) {
    error.value = '缺少文件名参数'
    return
  }

  try {
    loading.value = true
    error.value = ''
    
    await downloadErrorFile(
      fileName,
      '导入错误数据.xls',
      entityType
    )
    
    success.value = true
  } catch (err: any) {
    error.value = `下载失败：${err.message}`
    ElMessage.error(`下载失败：${err.message}`)
  } finally {
    loading.value = false
  }
}

const retryDownload = () => {
  error.value = ''
  startDownload()
}

const goBack = () => {
  router.back()
}

onMounted(() => {
  // 页面加载时自动开始下载
  startDownload()
})
</script>

<style scoped>
.error-file-download {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  padding: 20px;
}

.download-container {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  text-align: center;
  max-width: 500px;
  width: 100%;
}

.download-container h2 {
  margin-bottom: 30px;
  color: #303133;
  font-size: 24px;
}

.download-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-icon {
  font-size: 48px;
  color: #409eff;
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.download-error,
.download-success {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.retry-section,
.success-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.manual-download {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.manual-download p {
  color: #606266;
  margin: 0;
}
</style>