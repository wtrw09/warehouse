<template>
  <div class="base-management-container base-content base-flex-content">
    <!-- 操作栏 -->
    <el-card class="base-operation-card" shadow="hover">
      <div class="base-operation-bar">
        <div class="base-operation-bar__left">
          <el-button 
            type="default" 
            @click="getInventoryTransactions"
            :loading="loading"
            :icon="Refresh"
          >
            刷新
          </el-button>
        </div>
        <div class="base-operation-bar__right">
          <!-- 变更类型筛选下拉框 -->
          <el-select
            v-model="queryParams.change_type"
            placeholder="筛选变更类型"
            clearable
            style="width: 150px;"
            @change="handleSearch"
          >
            <el-option
              v-for="type in changeTypes"
              :key="type.value"
              :label="type.label"
              :value="type.value"
            />
          </el-select>
          
          <!-- 日期范围筛选 -->
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 240px;"
            @change="handleDateRangeChange"
          />
          
          <el-input
            v-model="queryParams.keyword"
            placeholder="输入器材名称、编码、批次号搜索"
            style="width: 320px;"
            clearable
            @clear="handleSearch"
            @input="handleInputSearch"
          />
        </div>
      </div>
    </el-card>

    <!-- 库存流水列表 -->
    <el-card class="base-table-card base-table-card--flex" shadow="hover">
      <template #header>
        <div class="base-card-header">
          <el-icon><List /></el-icon>
          <span>库存变更流水查询</span>
          <div class="base-card-header__stats" v-if="total > 0">
            <span>总计: {{ total }}</span>
          </div>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="base-loading-container">
        <el-skeleton :rows="8" animated />
      </div>

      <!-- 库存流水表格 -->
      <div v-else class="base-table base-table--auto-height">
        <el-table
          ref="tableRef"
          :data="tableData"
          stripe
          border
          :empty-text="'暂无库存流水数据'"
          class="base-table"
          @sort-change="handleSortChange"
        >
          <el-table-column 
            prop="material_code" 
            label="器材编码" 
            width="120" 
            align="center" 
            fixed="left"
          />
          <el-table-column 
            prop="material_name" 
            label="器材名称" 
            min-width="150" 
            align="center" 
            fixed="left"
          />
          <el-table-column 
            prop="batch_number" 
            label="批次号" 
            width="120" 
            align="center" 
          />
          <el-table-column 
            prop="transaction_time" 
            label="操作时间" 
            width="150" 
            align="center" 
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          >
            <template #default="{ row }">
              {{ formatTransactionTime(row.transaction_time) }}
            </template>
          </el-table-column>
          <el-table-column 
            prop="change_type" 
            label="变更类型" 
            width="100" 
            align="center" 
          >
            <template #default="{ row }">
              <el-tag :type="getChangeTypeTagType(row.change_type)">
                {{ getChangeTypeLabel(row.change_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column 
            prop="quantity_change" 
            label="变更数量" 
            width="100" 
            align="center" 
          >
            <template #default="{ row }">
              <span :class="{ 'text-success': row.change_type === ChangeType.IN, 'text-danger': row.change_type === ChangeType.OUT }">
                {{ row.change_type === ChangeType.IN ? '+' : '-' }}{{ row.quantity_change }}
              </span>
            </template>
          </el-table-column>
          <el-table-column 
            prop="quantity_before" 
            label="变更前数量" 
            width="120" 
            align="center" 
          />
          <el-table-column 
            prop="quantity_after" 
            label="变更后数量" 
            width="120" 
            align="center" 
          />
          <el-table-column 
            prop="reference_number" 
            label="关联单据号" 
            width="150" 
            align="center" 
          />
          
          <el-table-column 
            prop="creator" 
            label="操作人" 
            width="100" 
            align="center" 
          />
        </el-table>

        <!-- 分页 -->
        <div class="base-pagination-container">
          <el-pagination
            v-model:current-page="queryParams.page"
            v-model:page-size="queryParams.page_size"
            :page-sizes="[5,10, 20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            :pager-count="7"
            background
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          >
            <template #sizes="{ size }">
              <span>{{ size }}条/页</span>
            </template>
            <template #total="{ total }">
              <span>共 {{ total }} 条</span>
            </template>
            <template #jumper>
              <span>前往</span>
            </template>
          </el-pagination>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue';
import { ElMessage } from 'element-plus';
import { 
  Refresh, 
  List
} from '@element-plus/icons-vue';
import { inventoryTransactionAPI } from '@/services/material/inventory_transaction';
import type { 
  InventoryTransactionResponse, 
  InventoryTransactionQueryParams
} from '@/services/types/inventory_transaction';
import { ChangeType } from '@/services/types/inventory_transaction';

const loading = ref(false);
const tableRef = ref();

const queryParams = reactive<InventoryTransactionQueryParams>({
  page: 1,
  page_size: 10,
  sort_by: 'transaction_time',
  sort_order: 'desc'
});

const dateRange = ref<[string, string] | null>(null);

const tableData = ref<InventoryTransactionResponse[]>([]);
const total = ref(0);

// 防抖搜索定时器
let searchTimer: NodeJS.Timeout | null = null;

// 变更类型选项
const changeTypes = ref([
  { value: ChangeType.IN, label: '入库' },
  { value: ChangeType.OUT, label: '出库' },
  { value: ChangeType.ADJUST, label: '调整' }
]);

// 获取变更类型标签
const getChangeTypeLabel = (type: ChangeType): string => {
  const typeMap = {
    [ChangeType.IN]: '入库',
    [ChangeType.OUT]: '出库',
    [ChangeType.ADJUST]: '调整'
  };
  return typeMap[type] || '未知';
};

// 获取变更类型标签样式
const getChangeTypeTagType = (type: ChangeType): string => {
  const typeMap = {
    [ChangeType.IN]: 'success',
    [ChangeType.OUT]: 'danger',
    [ChangeType.ADJUST]: 'warning'
  };
  return typeMap[type] || 'info';
};

// 格式化交易时间，精确到秒
const formatTransactionTime = (timeString: string): string => {
  if (!timeString) return '';
  
  try {
    // 创建Date对象
    const date = new Date(timeString);
    
    // 格式化为 YYYY-MM-DD HH:mm:ss
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  } catch (error) {
    // 如果解析失败，返回原始字符串
    return timeString;
  }
};
// 获取库存流水列表
const getInventoryTransactions = async () => {
  loading.value = true;
  try {
    const response = await inventoryTransactionAPI.getInventoryTransactions(queryParams);
    tableData.value = response.data;
    total.value = response.total;
    
    // 在数据加载完成后，恢复排序状态
    await nextTick();
    restoreSortState();
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '获取库存流水列表失败';
    ElMessage.error(`获取库存流水列表失败: ${errorMessage}`);
  } finally {
    loading.value = false;
  }
};

// 恢复排序状态
const restoreSortState = () => {
  if (tableRef.value && currentSortProp.value && currentSortOrder.value) {
    // 手动设置表格的排序状态
    tableRef.value.sort(currentSortProp.value, currentSortOrder.value);
  }
};



// 当前排序状态
const currentSortProp = ref<string>('');
const currentSortOrder = ref<'ascending' | 'descending' | null>(null);

// 表头排序处理
const handleSortChange = ({ prop, order }: { prop: string; order: 'ascending' | 'descending' | null }) => {
  // 保存当前排序状态，用于在表格刷新后恢复排序图标
  currentSortProp.value = prop;
  currentSortOrder.value = order;
  
  // 只处理交易时间列的排序
  if (prop === 'transaction_time') {
    if (order) {
      // 有排序方向：升序或降序
      queryParams.sort_by = 'transaction_time';
      queryParams.sort_order = order === 'ascending' ? 'asc' : 'desc';
    } else {
      // 取消排序：重置为默认排序
      queryParams.sort_by = 'transaction_time';
      queryParams.sort_order = 'desc';
    }
    queryParams.page = 1;
    getInventoryTransactions();
  }
};

// 搜索
const handleSearch = () => {
  queryParams.page = 1;
  getInventoryTransactions();
};

// 输入搜索（防抖）
const handleInputSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  
  searchTimer = setTimeout(() => {
    queryParams.page = 1;
    getInventoryTransactions();
  }, 500);
};

// 日期范围变化处理
const handleDateRangeChange = (range: [string, string] | null) => {
  if (range && range.length === 2) {
    queryParams.start_date = range[0];
    queryParams.end_date = range[1];
  } else {
    queryParams.start_date = undefined;
    queryParams.end_date = undefined;
  }
  queryParams.page = 1;
  getInventoryTransactions();
};

// 分页大小变化
const handleSizeChange = (size: number) => {
  queryParams.page_size = size;
  getInventoryTransactions();
};

// 页码变化
const handleCurrentChange = (page: number) => {
  queryParams.page = page;
  getInventoryTransactions();
};

onMounted(() => {
  getInventoryTransactions();
});
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';

/* 使用现代Sass混入 */
@include mixins.table-sort-arrows;

/* 自定义样式 */
.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}
</style>