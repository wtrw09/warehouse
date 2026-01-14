<template>
  <div class="database-management-container">
    <!-- 服务器重启状态 -->
    <div v-if="serverRestarting" class="server-restart-container">
      <el-card class="restart-card" shadow="hover">
        <div class="restart-content">
          <el-icon class="restart-icon"><Refresh /></el-icon>
          <h3>服务器重启中</h3>
          <p>数据库恢复操作已完成，服务器正在重启...</p>
          <el-progress :percentage="restartProgress" :status="restartStatus" />
          <p class="restart-tip">请耐心等待，重启完成后将自动跳转回主页面</p>
          <el-button type="primary" @click="checkServerStatus" :loading="checkingServer">
            检查服务器状态
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 权限不足提示 -->
    <el-alert
      v-else-if="!hasBackupReadPermission"
      title="权限不足"
      type="error"
      :closable="false"
      show-icon
    >
      <template #default>
        <p>您没有足够的权限访问数据库管理功能。</p>
        <p>需要权限：<el-tag type="danger">SYSTEM-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 数据库管理内容 -->
    <div v-else class="database-content database-flex-content">
      <!-- 操作栏 -->
      <el-card class="database-operation-card" shadow="hover">
        <div class="database-operation-bar">
          <div class="left-actions">
            <el-button 
              type="primary" 
              @click="handleCreateBackup"
              :disabled="!hasBackupEditPermission"
              :icon="Plus"
            >
              创建备份
            </el-button>
            <el-button 
              type="default" 
              @click="loadBackups"
              :loading="loading"
              :icon="Refresh"
            >
              刷新
            </el-button>
          </div>
          <div class="right-actions">
            <el-text class="search-label">搜索：</el-text>
            <el-input
              v-model="searchParams.search"
              placeholder="请输入备份文件名"
              style="width: 300px;"
              clearable
              @input="debouncedSearch"
              @clear="debouncedSearch"
              @keyup.enter="debouncedSearch"
            />
          </div>
        </div>
      </el-card>

      <!-- 备份列表 -->
      <el-card class="database-table-card database-table-card--flex" shadow="hover">
        <template #header>
          <div class="database-card-header">
            <div class="header-left">
              <el-icon><List /></el-icon>
              <span>备份列表</span>
            </div>
            <div class="header-stats" v-if="statistics">
              <el-tag type="info" size="small">总备份: {{ statistics.total_backups }}</el-tag>
              <el-tag type="warning" size="small">总大小: {{ formatFileSize(statistics.total_size) }}</el-tag>
            </div>
          </div>
        </template>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="database-loading-container">
          <el-skeleton :rows="8" animated />
        </div>
        
        <!-- 错误状态 -->
        <el-alert
          v-else-if="error"
          :title="error"
          type="error"
          show-icon
          :closable="false"
        />
        
        <!-- 备份表格 -->
        <div v-else class="database-table database-table--auto-height">
          <el-table 
            ref="backupTableRef"
            :data="filteredBackupList" 
            stripe 
            border
            :empty-text="'暂无备份数据'"
            @selection-change="handleSelectionChange"
            :default-sort="{ prop: 'create_time', order: 'descending' }"
          >
            <el-table-column type="selection" width="55" align="center" fixed="left" />
            <el-table-column prop="filename" label="文件名" min-width="200" align="center" sortable>
              <template #default="{ row }">
                <div style="word-break: break-all; white-space: normal;">{{ row.filename }}</div>
              </template>
            </el-table-column>
            
            <el-table-column 
              prop="type" 
              label="备份类型" 
              min-width="120" 
              align="center"
              column-key="type"
              :filters="typeFilters"
              :filter-multiple="true"
              :filter-method="filterType"
            >
              <template #default="{ row }">
                <el-tag :type="getTypeTagType(row.type)" effect="light">{{ getTypeDisplayName(row.type) }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="size" label="文件大小" width="120" align="center" sortable>
              <template #default="{ row }">
                {{ row.size }}
              </template>
            </el-table-column>
            
            <el-table-column prop="timestamp" label="创建时间" width="180" align="center" sortable>
              <template #default="{ row }">
                {{ formatTimestamp(row.timestamp) }}
              </template>
            </el-table-column>
            

            
            <el-table-column label="操作" width="100" align="center" fixed="right">
              <template #default="{ row }">
                <el-space>
                  <el-tooltip content="恢复备份" placement="top">
                    <el-button 
                      type="warning"
                      size="small"
                      @click="handleRecover(row)"
                      :disabled="!hasBackupEditPermission || recoveryInProgress"
                      :icon="RefreshLeft"
                      circle
                    />
                  </el-tooltip>
                  <el-tooltip content="删除备份" placement="top">
                    <el-button 
                      type="danger"
                      size="small"
                      @click="handleDelete(row)"
                      :disabled="!hasBackupEditPermission"
                      :icon="Delete"
                      circle
                    />
                  </el-tooltip>
                </el-space>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 统计信息 -->
          <div class="database-statistics">
            <el-space>
              <el-statistic title="总备份数" :value="backupList.length" />
              <el-statistic title="当前显示" :value="filteredBackupList.length" />
              <el-statistic title="选中备份" :value="selectedBackups.length" />
            </el-space>
          </div>
        </div>
      </el-card>
    </div>



    <!-- 恢复确认对话框 -->
    <el-dialog
      v-model="recoverDialog.visible"
      title="恢复数据库备份"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-alert
        title="重要提醒"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>恢复操作将使用选定的备份文件替换当前数据库。</p>
          <p><strong>此操作不可逆，请谨慎操作！</strong></p>
          <p>恢复过程中服务将重启，预计耗时 1-2 分钟。</p>
        </template>
      </el-alert>
      
      <el-form
        ref="recoverFormRef"
        label-width="100px"
        style="margin-top: 20px;"
      >
        <el-form-item label="备份文件">
          <el-text>{{ recoverDialog.filename }}</el-text>
        </el-form-item>
        <el-form-item label="操作确认">
          <el-text type="warning">请确认要恢复此备份文件，恢复操作将重启服务器</el-text>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="recoverDialog.visible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleSaveRecover"
            :loading="recoverDialog.loading"
          >
            确认恢复
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 恢复等待对话框 -->
    <el-dialog
      v-model="waitingDialog.visible"
      title="恢复操作进行中"
      width="500px"
      :close-on-click-modal="false"
      :show-close="false"
    >
      <div class="recovery-waiting">
        <el-result
          icon="info"
          title="恢复操作进行中"
          :sub-title="waitingDialog.message"
        >
          <template #extra>
            <el-progress 
              :percentage="waitingDialog.progress" 
              :status="waitingDialog.status"
              :text-inside="true"
              :stroke-width="20"
            />
            <div style="margin-top: 20px;">
              <el-text type="info">预计等待时间：{{ waitingDialog.estimatedTime }}</el-text>
            </div>
          </template>
        </el-result>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, inject, Ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  Plus, 
  Refresh, 
  List, 
  RefreshLeft,
  Delete
} from '@element-plus/icons-vue';
import { backupAPI } from '../../../services/api';
import type {
  BackupFileInfo
} from '../../../services/types/system';
import type { UserInfo } from '../../../services/types/auth';

// 响应式数据
const backupList = ref<BackupFileInfo[]>([]);
const selectedBackups = ref<BackupFileInfo[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const statistics = ref<any | null>(null);
const recoveryInProgress = ref(false);

// 表格引用
const backupTableRef = ref();

// 备份类型筛选器
const typeFilters = ref<{ text: string; value: string }[]>([]);

// 搜索参数
const searchParams = ref<any>({
  search: '',
  backup_type: undefined
});

// 防抖计时器
let searchDebounceTimer: number | null = null;

// 防抖搜索函数
const debouncedSearch = () => {
  if (searchDebounceTimer) {
    clearTimeout(searchDebounceTimer);
  }
  
  searchDebounceTimer = window.setTimeout(() => {
    // 搜索逻辑已经通过filteredBackupList计算属性自动处理
    // 这里只需要确保计算属性重新计算
    nextTick(() => {
      // 强制触发计算属性更新
    });
  }, 300); // 300ms防抖延迟
};



// 恢复确认对话框
const recoverDialog = ref({
  visible: false,
  loading: false,
  filename: ''
});

const recoverFormRef = ref<any>();

// 恢复等待对话框
const waitingDialog = ref({
  visible: false,
  message: '请等待服务重启...',
  progress: 0,
  status: 'success' as any,
  estimatedTime: '1-2分钟'
});

// 服务器重启状态相关
const serverRestarting = ref(false);
const restartProgress = ref(0);
const restartStatus = ref<'success' | 'exception' | 'warning' | undefined>(undefined);
const checkingServer = ref(false);
const serverCheckTimer = ref<NodeJS.Timeout | null>(null);
const maxServerCheckAttempts = 30; // 最大检查次数
const serverCheckAttempts = ref(0);

// 获取当前用户信息（从父组件注入）
const currentUser = inject<Ref<UserInfo | null>>('currentUser') || ref<UserInfo | null>(null);

// 计算属性：检查是否有SYSTEM-read权限
const hasBackupReadPermission = computed(() => {
  if (!currentUser.value || !currentUser.value.permissions) {
    return false;
  }
  console.log("当前用户权限",currentUser.value.permissions);
  return currentUser.value.permissions.includes('SYSTEM-read');
});

// 计算属性：检查是否有SYSTEM-edit权限
const hasBackupEditPermission = computed(() => {
  if (!currentUser.value || !currentUser.value.permissions) {
    return false;
  }
  return currentUser.value.permissions.includes('SYSTEM-edit');
});

// 格式化时间戳
const formatTimestamp = (timestamp: string): string => {
  if (!timestamp) return '-';
  const date = new Date(timestamp);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 获取备份类型显示名称
const getTypeDisplayName = (type: string): string => {
  const typeMap: Record<string, string> = {
    'daily': '每日备份',
    'monthly': '月度归档',
    'user_full': '用户全量备份'
  };
  return typeMap[type] || type;
};

// 获取备份类型标签样式
const getTypeTagType = (type: string): string => {
  const typeMap: Record<string, string> = {
    'daily': 'primary',
    'monthly': 'warning',
    'user_full': 'success'
  };
  return typeMap[type] || 'info';
};

// 加载备份列表
const loadBackups = async () => {
  if (!hasBackupReadPermission.value) {
    ElMessage.warning('您没有足够的权限访问备份列表');
    return;
  }

  loading.value = true;
  error.value = null;
  
  try {
    const response = await backupAPI.getBackupList(searchParams.value);
    backupList.value = response.backups;
    
    // 提取备份类型用于筛选
    const uniqueTypes = [...new Set(response.backups.map((backup: any) => backup.type))];
    typeFilters.value = uniqueTypes.map(type => ({
      text: getTypeDisplayName(type as string),
      value: type as string
    }));
    
  } catch (err: any) {
    console.error('加载备份列表失败:', err);
    
    if (err.response?.status === 403) {
      error.value = '权限不足，无法访问数据库管理功能';
      ElMessage.error('权限不足，请与管理员联系');
    } else if (err.response?.status === 401) {
      error.value = '身份验证失败，请重新登录';
      console.error('认证失败:', err.response?.data?.detail || '请重新登录');
    } else {
      error.value = err.response?.data?.detail || '加载备份列表失败';
      ElMessage.error(error.value || '加载备份列表失败');
    }
  } finally {
    loading.value = false;
  }
};

// 加载统计信息（暂不实现）
const loadStatistics = async () => {
  // 统计信息功能暂不实现
  statistics.value = null;
};

// 计算属性：过滤后的备份列表
const filteredBackupList = computed(() => {
    if (!searchParams.value.search || !searchParams.value.search.trim()) {
      return backupList.value;
    }
    
    const keywords = (searchParams.value.search || '').trim().toLowerCase().split(/\s+/);
    
    return backupList.value.filter(backup => {
      const searchText = `${backup.filename}`.toLowerCase();
      return keywords.every((keyword: string) => searchText.includes(keyword));
    });
  });



// 备份类型筛选方法
const filterType = (value: string, row: BackupFileInfo) => {
    return row.type === value;
  };



// 选择变化处理
const handleSelectionChange = (selection: BackupFileInfo[]) => {
  selectedBackups.value = selection;
};

// 创建备份
const handleCreateBackup = async () => {
  if (!hasBackupEditPermission.value) {
    ElMessage.warning('您没有足够的权限创建备份');
    return;
  }
  
  try {
    await backupAPI.createBackup();
    ElMessage.success('备份创建成功');
    loadBackups();
    loadStatistics();
  } catch (err: any) {
    console.error('创建备份失败:', err);
    ElMessage.error(err.response?.data?.detail || '创建备份失败');
  }
};



// 恢复备份
const handleRecover = (backup: BackupFileInfo) => {
  if (!hasBackupEditPermission.value) {
    ElMessage.warning('您没有足够的权限恢复备份');
    return;
  }
  
  if (recoveryInProgress.value) {
    ElMessage.warning('当前已有恢复操作在进行中，请等待完成');
    return;
  }
  
  recoverDialog.value.filename = backup.filename;
  recoverDialog.value.visible = true;
};

// 保存恢复操作
const handleSaveRecover = async () => {
  try {
    recoverDialog.value.loading = true;
    
    // 调用真实的恢复备份API（不传递管理员密码）
    await backupAPI.recoverBackup(recoverDialog.value.filename, '');
    
    ElMessage.success('恢复操作已开始，服务器正在重启...');
    recoverDialog.value.visible = false;
    recoveryInProgress.value = true;
    
    // 显示服务器重启状态页面
    serverRestarting.value = true;
    restartProgress.value = 0;
    restartStatus.value = undefined;
    serverCheckAttempts.value = 0;
    
    // 开始检查服务器状态
    startServerStatusCheck();
    
  } catch (err: any) {
    console.error('恢复备份失败:', err);
    ElMessage.error(err.response?.data?.detail || '恢复备份失败');
  } finally {
    recoverDialog.value.loading = false;
  }
};

// 开始检查服务器状态
const startServerStatusCheck = () => {
  if (serverCheckTimer.value) {
    clearTimeout(serverCheckTimer.value);
  }
  
  const checkServer = async () => {
    checkingServer.value = true;
    
    try {
      // 尝试调用一个简单的API来检查服务器状态
      await backupAPI.getBackupList({});
      
      // 服务器已恢复
      restartProgress.value = 100;
      restartStatus.value = 'success';
      
      ElMessage.success('服务器重启完成，已恢复正常');
      
      // 延迟2秒后返回主页面
      setTimeout(() => {
        serverRestarting.value = false;
        recoveryInProgress.value = false;
        loadBackups();
      }, 2000);
      
    } catch (err: any) {
      // 服务器仍在重启中
      serverCheckAttempts.value++;
      
      // 更新进度（基于尝试次数）
      restartProgress.value = Math.min(serverCheckAttempts.value * 3, 90);
      
      if (serverCheckAttempts.value >= maxServerCheckAttempts) {
        // 超过最大尝试次数，显示错误
        restartProgress.value = 100;
        restartStatus.value = 'exception';
        ElMessage.error('服务器重启超时，请手动检查服务器状态');
        checkingServer.value = false;
        return;
      }
      
      // 继续检查
      serverCheckTimer.value = setTimeout(checkServer, 2000);
    } finally {
      checkingServer.value = false;
    }
  };
  
  // 延迟1秒后开始第一次检查
  serverCheckTimer.value = setTimeout(checkServer, 1000);
};

// 手动检查服务器状态
const checkServerStatus = () => {
  if (serverCheckTimer.value) {
    clearTimeout(serverCheckTimer.value);
  }
  startServerStatusCheck();
};


// 删除备份
const handleDelete = async (backup: BackupFileInfo) => {
  if (!hasBackupEditPermission.value) {
    ElMessage.warning('您没有足够的权限删除备份');
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除备份文件 "${backup.filename}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    await backupAPI.deleteBackup(backup.filename);
    ElMessage.success('备份删除成功');
    loadBackups();
    loadStatistics();
    
  } catch (err: any) {
    if (err === 'cancel') {
      return;
    }
    console.error('删除备份失败:', err);
    ElMessage.error(err.response?.data?.detail || '删除备份失败');
  }
};

// 组件挂载时加载数据
onMounted(() => {
  if (hasBackupReadPermission.value) {
    loadBackups();
    loadStatistics();
  }
});
</script>

<style scoped>
.database-management-container {
  padding: 20px;
}

.database-flex-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.database-operation-card {
  margin-bottom: 0;
}

.database-operation-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.database-operation-bar .left-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.database-operation-bar .right-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.search-label {
  font-weight: 500;
  color: var(--el-text-color-regular);
}

.database-table-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.database-table-card--flex {
  min-height: 400px;
}

.database-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.database-card-header .header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.database-card-header .header-stats {
  display: flex;
  gap: 8px;
}

.database-loading-container {
  padding: 20px;
}

.database-table {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.database-table--auto-height {
  min-height: 300px;
}

.database-statistics {
  margin: 20px 0;
  padding: 16px;
  background-color: var(--el-fill-color-light);
  border-radius: var(--el-border-radius-base);
}



.recovery-waiting {
  text-align: center;
}

/* 服务器重启状态页面样式 */
.server-restart-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  padding: 40px 20px;
}

.restart-card {
  width: 100%;
  max-width: 500px;
  text-align: center;
}

.restart-content {
  padding: 30px;
}

.restart-icon {
  font-size: 64px;
  color: var(--el-color-primary);
  margin-bottom: 20px;
}

.restart-content h3 {
  margin-bottom: 15px;
  color: var(--el-text-color-primary);
}

.restart-content p {
  margin-bottom: 20px;
  color: var(--el-text-color-regular);
}

.restart-tip {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-top: 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .database-operation-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .database-operation-bar .left-actions,
  .database-operation-bar .right-actions {
    justify-content: center;
  }
  
  .database-card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .server-restart-container {
    padding: 20px 10px;
  }
  
  .restart-content {
    padding: 20px;
  }
  
  .restart-icon {
    font-size: 48px;
  }
}
</style>