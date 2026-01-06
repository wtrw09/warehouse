<template>
  <div class="base-management-container base-content base-flex-content">
    <!-- 操作栏 -->
    <el-card class="base-operation-card" shadow="hover">
      <div class="base-operation-bar">
        <div class="base-operation-bar__left">
          <el-button 
            type="default" 
            @click="getInventoryDetails"
            :loading="loading"
            :icon="Refresh"
          >
            刷新
          </el-button>
          <el-button 
            type="primary" 
            @click="handleExportExcel"
            :loading="exportLoading"
            :icon="Download"
          >
            导出Excel
          </el-button>
        </div>
        <div class="base-operation-bar__right">
            
          <el-checkbox 
            v-model="hideZeroStock" 
            @change="handleHideZeroStockChange"
            style="margin-right: 10px;"
          >
            隐藏无库存器材
          </el-checkbox>
          <!-- 专业筛选下拉框 -->
          <el-select
            v-model="queryParams.major_id"
            placeholder="筛选专业"
            clearable
            filterable
            multiple
            collapse-tags
            collapse-tags-tooltip
            style="width: 200px;"
            @change="handleSearch"
          >
            <el-option
              v-for="major in majorOptions"
              :key="major.value"
              :label="major.label"
              :value="major.value"
            />
          </el-select>
          
          <!-- 仓库筛选下拉框 -->
          <el-select
            v-model="queryParams.warehouse_id"
            placeholder="筛选仓库"
            clearable
            filterable
            style="width: 150px;"
            @change="handleSearch"
          >
            <el-option
              v-for="warehouse in warehouseOptions"
              :key="warehouse.value"
              :label="warehouse.label"
              :value="warehouse.value"
            />
          </el-select>
         
          
          <el-input
            v-model="queryParams.keyword"
            placeholder="输入器材名称、编码、批次号搜索"
            style="width: 280px;"
            clearable
            @clear="handleSearch"
            @input="handleInputSearch"
          />
        </div>
      </div>
    </el-card>

    <!-- 库存器材明细列表 -->
    <el-card class="base-table-card base-table-card--flex" shadow="hover">
      <template #header>
        <div class="base-card-header">
          <el-icon><List /></el-icon>
          <span>库存器材明细</span>
          <div class="base-card-header__stats" v-if="total > 0">
            <span>总计: {{ total }}</span>
          </div>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="base-loading-container">
        <el-skeleton :rows="8" animated />
      </div>

      <!-- 库存器材明细表格 -->
      <div v-else class="base-table base-table--auto-height">
        <el-table
          ref="tableRef"
          :data="tableData"
          stripe
          border
          :empty-text="'暂无库存器材明细数据'"
          class="base-table"
          @sort-change="handleSortChange"
        >
          <el-table-column 
            prop="material_code" 
            label="器材编码" 
            width="120" 
            align="center" 
            fixed="left"
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column 
            prop="material_name" 
            label="器材名称" 
            min-width="150" 
            align="center" 
            fixed="left"
          />
          <el-table-column 
            prop="material_specification" 
            label="器材规格" 
            width="100" 
            align="center" 
          />
          <el-table-column 
            prop="batch_number" 
            label="批次编码" 
            width="120" 
            align="center" 
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column 
            prop="quantity" 
            label="库存数量" 
            width="90" 
            align="center" 
          >
            <template #default="{ row }">
              <el-tag :type="getQuantityTagType(row.quantity)">
                {{ row.quantity }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column 
            prop="unit" 
            label="单位" 
            width="60" 
            align="center" 
          />
          <el-table-column 
            prop="unit_price" 
            label="单价" 
            width="80" 
            align="center" 
          >
            <template #default="{ row }">
              {{ row.unit_price ? `¥${row.unit_price.toFixed(2)}` : '-' }}
            </template>
          </el-table-column>
          <el-table-column 
            prop="warehouse_name" 
            label="仓库名称" 
            width="120" 
            align="center" 
          />
          <el-table-column 
            prop="bin_name" 
            label="货位名称" 
            width="120" 
            align="center" 
          />
          <el-table-column 
            prop="supplier_name" 
            label="供应商" 
            width="120" 
            align="center" 
          />
          <el-table-column 
            prop="production_date" 
            label="生产日期" 
            width="120" 
            align="center" 
          >
            <template #default="{ row }">
              {{ formatDate(row.production_date) }}
            </template>
          </el-table-column>
          <el-table-column 
            prop="inbound_date" 
            label="入库日期" 
            width="120" 
            align="center" 
          >
            <template #default="{ row }">
              {{ formatDate(row.inbound_date) }}
            </template>
          </el-table-column>
          <el-table-column 
            prop="last_updated" 
            label="上次更新日期" 
            width="120" 
            align="center" 
          >
            <template #default="{ row }">
              {{ formatDate(row.last_updated) }}
            </template>
          </el-table-column>
          <el-table-column 
            prop="major_name" 
            label="专业名称" 
            width="120" 
            align="center" 
          />
          <el-table-column 
            prop="equipment_name" 
            label="装备名称" 
            width="120" 
            align="center" 
          />
          <el-table-column 
            prop="equipment_specification" 
            label="装备型号" 
            width="120" 
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
  List,
  Download
} from '@element-plus/icons-vue';
import { inventoryDetailAPI } from '@/services/material/inventory_detail';
import { warehouseAPI } from '@/services/base/warehouse';
import type { 
  InventoryDetailResponse, 
  InventoryDetailsQueryParams,
} from '@/services/types/inventory_detail';
import type { WarehouseResponse } from '@/services/types/warehouse';


const loading = ref(false);
const exportLoading = ref(false);
const tableRef = ref();
const hideZeroStock = ref(true); // 默认隐藏无库存器材

const queryParams = reactive<InventoryDetailsQueryParams>({
  page: 1,
  page_size: 10,
  sort_by: 'material_code',
  sort_order: 'asc',
  major_id: [],
  warehouse_id: undefined,
  keyword: undefined
});

const tableData = ref<InventoryDetailResponse[]>([]);
const total = ref(0);

// 防抖搜索定时器
let searchTimer: NodeJS.Timeout | null = null;

// 筛选选项
const majorOptions = ref<{ value: number; label: string }[]>([]);
const warehouseOptions = ref<{ value: number; label: string }[]>([]);

// 格式化日期
const formatDate = (dateString: string): string => {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
  } catch (error) {
    return dateString;
  }
};

// 获取库存数量标签样式
const getQuantityTagType = (quantity: number): string => {
  if (quantity > 0) {
    return 'success';
  } else {
    return 'danger';
  }
};

// 获取专业选项集合
const getMajorOptions = async () => {
  try {
    const response = await inventoryDetailAPI.getMajorOptionsFromInventory();
    
    // 直接使用返回的专业选项数据
    majorOptions.value = response.data.map((option) => ({
      value: option.id,
      label: option.major_name
    }));
  } catch (error: any) {
    const errorMessage = error.response?.data?.message || error.message || '获取专业选项集合失败';
    ElMessage.error(`获取专业选项集合失败: ${errorMessage}`);
  }
};

// 获取仓库列表
const getWarehouses = async () => {
  try {
    const warehouses = await warehouseAPI.getAllWarehouses();
    // 将仓库数据转换为下拉框选项格式
    warehouseOptions.value = warehouses.map((warehouse: WarehouseResponse) => ({
      value: warehouse.id,
      label: warehouse.warehouse_name
    }));
  } catch (error: any) {
    const errorMessage = error.response?.data?.message || error.message || '获取仓库列表失败';
    ElMessage.error(`获取仓库列表失败: ${errorMessage}`);
  }
};

// 获取库存器材明细列表
const getInventoryDetails = async () => {
  loading.value = true;
  try {
    const response = await inventoryDetailAPI.getInventoryDetails(queryParams);
    tableData.value = response.data;
    total.value = response.total;
    
    // 在数据加载完成后，恢复排序状态
    await nextTick();
    restoreSortState();
  } catch (error: any) {
    const errorMessage = error.response?.data?.message || error.message || '获取库存器材明细列表失败';
    ElMessage.error(`获取库存器材明细列表失败: ${errorMessage}`);
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
  
  // 处理排序
  if (order) {
    // 有排序方向：升序或降序
    queryParams.sort_by = prop;
    queryParams.sort_order = order === 'ascending' ? 'asc' : 'desc';
  } else {
    // 取消排序：重置为默认排序
    queryParams.sort_by = 'material_code';
    queryParams.sort_order = 'asc';
  }
  queryParams.page = 1;
  getInventoryDetails();
};

// 处理隐藏无库存器材的复选框变化
const handleHideZeroStockChange = () => {
  // 通过后端API的quantity_filter参数来实现
  if (hideZeroStock.value) {
    // 隐藏无库存器材，只显示有库存的器材
    queryParams.quantity_filter = 'has_stock';
  } else {
    // 显示所有器材（包括库存为0的）
    queryParams.quantity_filter = undefined;
  }
  queryParams.page = 1;
  getInventoryDetails();
};

// 搜索
const handleSearch = () => {
  queryParams.page = 1;
  getInventoryDetails();
};

// 输入搜索（防抖）
const handleInputSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  
  searchTimer = setTimeout(() => {
    queryParams.page = 1;
    getInventoryDetails();
  }, 500);
};

// 分页大小变化
const handleSizeChange = (size: number) => {
  queryParams.page_size = size;
  getInventoryDetails();
};

// 页码变化
const handleCurrentChange = (page: number) => {
  queryParams.page = page;
  getInventoryDetails();
};

// 导出Excel
const handleExportExcel = async () => {
  exportLoading.value = true;
  try {
    // 构建导出参数，使用当前的筛选条件，但不包含分页参数
    const exportParams = {
      keyword: queryParams.keyword,
      major_id: queryParams.major_id,
      equipment_id: queryParams.equipment_id,
      warehouse_id: queryParams.warehouse_id,
      bin_id: queryParams.bin_id,
      quantity_filter: queryParams.quantity_filter,
      sort_by: queryParams.sort_by,
      sort_order: queryParams.sort_order
    };
    
    const blob = await inventoryDetailAPI.exportInventoryDetails(exportParams);
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    
    // 从响应头中提取文件名，如果没有则使用默认文件名
    const timestamp = new Date().toLocaleString('zh-CN', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false 
    }).replace(/[\/\s:]/g, '-').replace('--', '-');
    link.download = `库存器材明细-${timestamp}.xlsx`;
    
    // 触发下载
    document.body.appendChild(link);
    link.click();
    
    // 清理
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    ElMessage.success('导出成功');
  } catch (error: any) {
    const errorMessage = error.response?.data?.message || error.message || '导出Excel失败';
    ElMessage.error(`导出Excel失败: ${errorMessage}`);
  } finally {
    exportLoading.value = false;
  }
};

onMounted(async () => {
  await getMajorOptions();
  await getWarehouses();
  
  // 初始化时应用隐藏无库存器材的默认设置
  if (hideZeroStock.value) {
    queryParams.quantity_filter = 'has_stock';
  } else {
    queryParams.quantity_filter = undefined;
  }
  
  await getInventoryDetails();
});
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';

/* 使用现代Sass混入 */
@include mixins.table-sort-arrows;
</style>