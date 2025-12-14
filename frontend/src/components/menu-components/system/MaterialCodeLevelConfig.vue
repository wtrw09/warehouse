<template>
  <div class="base-management-container material-code-level-config">
    <!-- 权限不足提示 -->
    <el-alert
      v-if="!hasReadPermission"
      title="权限不足"
      type="error"
      :closable="false"
      show-icon
    >
      <template #default>
        <p>您没有足够的权限访问器材编码分类层级管理功能。</p>
        <p>需要权限：<el-tag type="danger">BASE-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 器材编码分类层级管理内容 -->
    <div v-else class="base-content">
      

      <!-- 器材编码规则说明 -->
      <el-card class="base-info-card" shadow="hover">
        <template #header>
          <div class="base-card-header">
            <div class="header-left">
              <el-icon><InfoFilled /></el-icon>
              <span>器材编码规则说明</span>
            </div>
          </div>
        </template>
        
        <div class="code-rule-info">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="编码格式">10位专业代码+顺序编号</el-descriptions-item>
            <el-descriptions-item label="编码结构">
              <div class="code-structure">
                <div class="code-segment">
                  <span class="segment-label">1-2位：</span>
                  <span class="segment-desc">一级专业代码</span>
                </div>
                <div class="code-segment-separator"></div>
                <div class="code-segment">
                  <span class="segment-label">3-4位：</span>
                  <span class="segment-desc">二级专业代码</span>
                </div>
                <div class="code-segment-separator"></div>
                <div class="code-segment">
                  <span class="segment-label">5-10位：</span>
                  <span class="segment-desc">顺序编号</span>
                </div>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="示例">
              <el-tag type="success" size="large">AB12345678</el-tag>
              <span style="margin-left: 8px; color: #666;">其中：AB=一级专业代码，12=二级专业代码，345678=顺序编号</span>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-card>

      <!-- 操作栏 -->
      <el-card class="base-operation-card" shadow="hover">
        <div class="base-operation-bar">
          <div class="base-operation-bar__left">
            <el-button 
              type="primary" 
              @click="handleRegenerate"
              :disabled="!hasEditPermission"
              :icon="Refresh"
            >
              重新生成
            </el-button>
            <el-button 
              type="primary" 
              @click="handleModifyMajorInfo"
              :disabled="!hasEditPermission"
              :icon="Edit"
            >
              修改专业信息
            </el-button>
            <el-button 
              type="default" 
              @click="handleRefresh"
              :loading="loading"
              :icon="Refresh"
            >
              刷新
            </el-button>
          </div>
          <div class="base-operation-bar__right">
            <el-text class="search-label">搜索：</el-text>
            <el-input
              v-model="searchKeyword"
              placeholder="请输入分类名称或编码"
              style="width: 300px;"
              clearable
              @input="handleSearch"
              @clear="handleSearch"
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </el-card>
      
      <!-- 器材编码分类层级列表 -->
      <el-card class="base-table-card" shadow="hover">
        <template #header>
          <div class="base-card-header">
            <div class="header-left">
              <el-icon><List /></el-icon>
              <span>器材编码分类层级列表</span>
            </div>
            <div class="base-card-header__stats">
              <span>总计：{{ data.length }} 条记录</span>
            </div>
          </div>
        </template>
        
        <!-- 加载状态 -->
        <div v-if="loading" class="base-loading-container">
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
        
        <!-- 器材编码分类层级表格 -->
        <div v-else class="base-table">
          <el-table 
            :data="filteredData" 
            stripe 
            border
            height="calc(100vh - 370px)"
            :empty-text="'暂无器材编码分类层级数据'"
            :default-sort="{ prop: 'level_code', order: 'ascending' }"
            @sort-change="handleSortChange"
          >
            <el-table-column prop="level_code" label="层级编码" width="100" align="center" sortable />
            
            <el-table-column 
              prop="level_name" 
              label="分类名称" 
              min-width="150" 
              align="center" 
              sortable
            >
              <template #default="{ row }">
                <el-tag type="primary" effect="dark">{{ row.level_name }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="code" label="分类编码" width="120" align="center" />
            
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
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
            
            <el-table-column prop="createdAt" label="创建时间" width="180" align="center" sortable>
              <template #default="{ row }">
                <el-text type="info" size="small">
                  {{ formatDate(row.createdAt) }}
                </el-text>
              </template>
            </el-table-column>
            
            <el-table-column prop="updatedAt" label="更新时间" width="180" align="center" sortable>
              <template #default="{ row }">
                <el-text type="info" size="small">
                  {{ formatDate(row.updatedAt) }}
                </el-text>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>

    <!-- 重新生成确认对话框 -->
    <el-dialog
      v-model="regenerateDialogVisible"
      title="重新生成确认"
      width="400px"
      :close-on-click-modal="false"
    >
      <span>确定要重新生成器材编码分类层级数据吗？这将删除现有数据并从二级专业重新生成。</span>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleRegenerateDialogClose">取消</el-button>
          <el-button 
            type="primary" 
            @click="confirmRegenerate" 
            :loading="regenerateLoading"
          >
            确定
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Search, Refresh, Edit, List, InfoFilled } from '@element-plus/icons-vue';
import { materialCodeLevelAPI } from '../../../services/system/material_code_level';
import { useUserStore } from '../../../stores/user';
import { useMenuStore } from '../../../stores/menu';
import { usePermission } from '../../../composables/usePermission';
import { useRouter } from 'vue-router';

// 响应式数据
const loading = ref(false);
const error = ref(null);
const data = ref([]);
const searchKeyword = ref('');
const regenerateDialogVisible = ref(false);
const regenerateLoading = ref(false);

// 获取路由实例
const router = useRouter();

// 用户权限检查
const userStore = useUserStore();
const { hasPermission } = usePermission();

// 计算属性：检查是否有BASE-read权限
const hasReadPermission = computed(() => {
  return hasPermission('BASE-read');
});

// 计算属性：检查是否有BASE-edit权限
const hasEditPermission = computed(() => {
  return hasPermission('BASE-edit');
});

// 计算属性：过滤后的数据
const filteredData = computed(() => {
  if (!searchKeyword.value.trim()) {
    return data.value;
  }
  
  const keywords = searchKeyword.value.trim().toLowerCase().split(/\s+/);
  
  return data.value.filter(item => {
    const searchText = `${item.level_name} ${item.code} ${item.description || ''}`.toLowerCase();
    return keywords.every(keyword => searchText.includes(keyword));
  });
});

// 处理修改专业信息
const handleModifyMajorInfo = async () => {
  if (!hasEditPermission.value) {
    ElMessage.warning('您没有权限修改专业信息');
    return;
  }
  
  try {
    const menuStore = useMenuStore();
    
    console.log('开始跳转到专业信息管理页面...');
    
    // 1. 先展开父级菜单"1"（基础数据）
    menuStore.openMenu('1');
    console.log('已展开父菜单 1');
    
    // 2. 通过事件总线或直接操作来触发菜单切换
    // 使用 nextTick 确保菜单状态更新后再跳转
    await nextTick();
    
    // 3. 强制跳转并触发组件切换
    if (router.currentRoute.value.query.menu === '1-5') {
      // 如果当前已经在目标页面，先跳转到其他页面再跳回来
      await router.replace({ path: '/', query: { menu: 'default' } });
      await nextTick();
    }
    
    await router.replace({ 
      path: '/', 
      query: { menu: '1-5' } 
    });
    
    console.log('路由跳转完成');
    
    // 4. 显示成功提示
    ElMessage.success('已跳转到专业信息管理页面');
    
  } catch (error) {
    console.error('跳转失败:', error);
    ElMessage.error('页面跳转失败');
  }
};

// 处理重新生成
const handleRegenerate = () => {
  if (!hasEditPermission.value) {
    ElMessage.warning('您没有权限执行此操作');
    return;
  }
  regenerateDialogVisible.value = true;
};

// 确认重新生成
const confirmRegenerate = async () => {
  regenerateLoading.value = true;
  try {
    const result = await materialCodeLevelAPI.generateMaterialCodeLevelsFromSubMajors();
    ElMessage.success(result.message || '重新生成成功');
    regenerateDialogVisible.value = false;
    await fetchData();
  } catch (error) {
    ElMessage.error(error.message || '重新生成失败');
  } finally {
    regenerateLoading.value = false;
  }
};

// 处理重新生成对话框关闭
const handleRegenerateDialogClose = () => {
  regenerateDialogVisible.value = false;
};

// 处理刷新
const handleRefresh = async () => {
  await fetchData();
  ElMessage.success('数据已刷新');
};

// 处理搜索
const handleSearch = () => {
  // 使用客户端过滤，不需要重新加载数据
};

// 处理排序变化
const handleSortChange = ({ prop, order }) => {
  // 实现排序逻辑
  if (prop && order) {
    data.value.sort((a, b) => {
      if (order === 'ascending') {
        return a[prop] > b[prop] ? 1 : -1;
      } else {
        return a[prop] < b[prop] ? 1 : -1;
      }
    });
  }
};

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (err) {
    return dateString;
  }
};

// 获取数据
const fetchData = async () => {
  if (!hasReadPermission.value) {
    ElMessage.warning('您没有足够的权限访问器材编码分类层级数据');
    return;
  }

  loading.value = true;
  error.value = null;
  
  try {
    const response = await materialCodeLevelAPI.getMaterialCodeLevels();
    data.value = response || [];
    console.log('获取到的数据:', data.value); // 添加调试信息
  } catch (err) {
    console.error('获取器材编码分类层级数据失败:', err);
    error.value = err.response?.data?.detail || '获取数据失败';
    ElMessage.error(error.value);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  // 如果有权限，自动加载数据
  if (hasReadPermission.value) {
    fetchData();
  }
});

// 解析描述字段为字符串数组
const parseDescription = (description) => {
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
</script>

<style src="../../../css/base-styles.css"></style>
<style scoped>
/* 器材编码分类层级管理组件特定样式 */

/* 移除组件外部间隙 */
.material-code-level-config {
  padding: 0;
}

/* 移除卡片之间的间隙 */
.base-content {
  gap: 0 !important;
}

/* 确保搜索标签对齐 */
.search-label {
  margin-right: 8px;
  font-weight: 500;
}

/* 器材编码规则说明样式 */
.base-info-card {
  margin-bottom: 0;
}

.code-rule-info {
  padding: 10px 0;
}

.code-structure {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0;
}

.code-segment {
  display: flex;
  align-items: center;
  gap: 8px;
}

.code-segment-separator {
  width: 40px;
  flex-shrink: 0;
}

.segment-label {
  font-weight: 600;
  color: #409eff;
  min-width: 60px;
}

.segment-desc {
  color: #606266;
}

/* 自适应表格高度 */
.base-table {
  height: 100%;
}

/* 确保表格容器自适应 */
.base-table-card {
  height: calc(100vh - 320px);
  min-height: 400px;
  display: flex;
  flex-direction: column;
}

.base-table-card .el-card__body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.base-table-card .base-table {
  flex: 1;
}
</style>