<template>
  <div class="major-management-container">
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
        <p>您没有足够的权限访问专业管理功能。</p>
        <p>需要权限：<el-tag type="danger">BASE-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 专业管理内容 -->
    <div v-else class="major-management-content">
      <!-- 选项卡切换 -->
      <el-card class="major-tabs-card" shadow="hover">
        <el-tabs v-model="activeTab" type="card" @tab-click="handleTabChange">
          <el-tab-pane label="一级专业管理" name="major">
            <template #label>
              <span class="tab-label">
                <el-icon><List /></el-icon>
                一级专业管理
              </span>
            </template>
          </el-tab-pane>
          <el-tab-pane label="二级专业管理" name="subMajor">
            <template #label>
              <span class="tab-label">
                <el-icon><List /></el-icon>
                二级专业管理
              </span>
            </template>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <!-- 组件内容容器 -->
      <div class="component-container">
        <MajorInfo v-if="activeTab === 'major'" key="major" />
        <SubMajorInfo v-if="activeTab === 'subMajor'" key="subMajor" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { List } from '@element-plus/icons-vue';
import { usePermission } from '../../../composables/usePermission';
import MajorInfo from './MajorInfo.vue';
import SubMajorInfo from './SubMajorInfo.vue';

// 权限检查
const { hasPermission } = usePermission();

// 响应式数据
const activeTab = ref<'major' | 'subMajor'>('major');

// 选项卡切换处理
const handleTabChange = (tab: any) => {
  activeTab.value = tab.paneName as 'major' | 'subMajor';
};

// 默认激活一级专业管理
onMounted(() => {
  activeTab.value = 'major';
});
</script>

<style scoped>
.major-management-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.major-management-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0px;
}

.major-tabs-card {
  margin-bottom: 0;
}

.major-tabs-card :deep(.el-card__body) {
  padding: 0;
}

.major-tabs-card :deep(.el-tabs) {
  padding: 0 0 0 0;
}

.major-tabs-card :deep(.el-tabs__header) {
  margin: 0;
}

.major-tabs-card :deep(.el-tabs__item) {
  height: 40px;
  line-height: 40px;
  font-size: 14px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

.component-container {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.component-container > * {
  flex: 1;
  min-height: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .major-tabs-card :deep(.el-tabs) {
    padding: 0 12px;
  }
  
  .major-tabs-card :deep(.el-tabs__item) {
    font-size: 12px;
    padding: 0 12px;
  }
  
  .tab-label {
    gap: 4px;
  }
}
</style>