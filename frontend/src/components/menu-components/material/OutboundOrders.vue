<template>
  <div class="base-management-container base-content base-flex-content">
    <!-- 操作栏 -->
    <el-card class="base-operation-card" shadow="hover">
      <div class="base-operation-bar">
        <div class="base-operation-bar__left">
          <el-button 
            type="default" 
            @click="getOutboundOrders"
            :loading="loading"
            :icon="Refresh"
          >
            刷新
          </el-button>
          <el-button 
            type="primary" 
            @click="handleAdd"
            :icon="Plus"
          >
            新增出库单
          </el-button>
        </div>
        <div class="base-operation-bar__right">
          <!-- 日期范围筛选 -->
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            @change="handleDateRangeChange"
            style="width: 240px; margin-right: 10px;"
          />
          
          <el-input
            v-model="queryParams.keyword"
            placeholder="输入出库单号、客户、调拨单号搜索"
            style="width: 320px;"
            clearable
            @clear="handleSearch"
            @input="handleInputSearch"
          />
        </div>
      </div>
    </el-card>

    <!-- 出库单列表 -->
    <el-card class="base-table-card base-table-card--flex" shadow="hover">
      <template #header>
        <div class="base-card-header">
          <el-icon><List /></el-icon>
          <span>出库单列表</span>
          <div class="base-card-header__stats" v-if="total > 0">
            <span>总计: {{ total }}</span>
          </div>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="base-loading-container">
        <el-skeleton :rows="8" animated />
      </div>

      <!-- 出库单表格 -->
      <div v-else class="base-table base-table--auto-height">
        <el-table
          ref="tableRef"
          :data="tableData"
          stripe
          border
          :empty-text="'暂无出库单数据'"
          class="base-table"
          @sort-change="handleSortChange"
        >
          <el-table-column 
            prop="order_number" 
            label="出库单号" 
            width="150" 
            align="center" 
            fixed="left"
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column 
            prop="total_quantity" 
            label="总数量" 
            width="100" 
            align="center" 
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          />
          <el-table-column 
            prop="customer_name" 
            label="客户名称" 
            min-width="120" 
            align="center"
            :filters="customerFilters"
            :filter-method="filterCustomer"
            column-key="customer_name"
          />
          
          <el-table-column 
            prop="requisition_reference" 
            label="调拨单号" 
            width="150" 
            align="center" 
          />
          
          <el-table-column 
            prop="creator" 
            label="创建人" 
            width="100" 
            align="center" 
          />
          <el-table-column 
            prop="create_time" 
            label="创建时间" 
            width="160" 
            align="center" 
            sortable="custom"
            :sort-orders="['ascending', 'descending']"
          >
            <template #default="{ row }">
              {{ formatDateTime(row.create_time) }}
            </template>
          </el-table-column>
          
          <!-- 操作列 -->
          <el-table-column 
            label="操作" 
            width="260" 
            align="center" 
            fixed="right"
          >
            <template #default="{ row }">
              <el-button 
                type="info" 
                size="small" 
                @click="handleView(row)"
                :icon="View"
              >
              </el-button>
              <el-button 
                type="primary" 
                size="small" 
                @click="handleEdit(row)"
                :icon="Edit"
              >
              </el-button>
              <el-button 
                type="success" 
                size="small" 
                @click="handleExportPDF(row)"
                :icon="Printer"
              >
              </el-button>
              <el-button 
                type="danger" 
                size="small" 
                @click="handleDelete(row)"
                :icon="Delete"
              >
              </el-button>
            </template>
          </el-table-column>
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
import { ref, reactive, onMounted, nextTick, h } from 'vue';
import { ElMessage, ElMessageBox, ElNotification, ElProgress } from 'element-plus';
import { 
  Refresh, 
  List,
  Plus,
  Edit,
  Delete,
  View,
  Printer
} from '@element-plus/icons-vue';
import { outboundOrderAPI } from '@/services/material/outbound';
import type { 
  OutboundOrderResponse, 
  OutboundOrderQueryParams
} from '@/services/types/outbound';


const loading = ref(false);
const tableRef = ref();
const dateRange = ref<string[]>([]);

const queryParams = reactive<OutboundOrderQueryParams>({
  page: 1,
  page_size: 10,
  sort_by: 'create_time',
  sort_order: 'desc'
});

const tableData = ref<OutboundOrderResponse[]>([]);
const total = ref(0);

// 防抖搜索定时器
let searchTimer: NodeJS.Timeout | null = null;

// 筛选选项
const customerOptions = ref<{ value: number; label: string }[]>([]);
const customerFilters = ref<{ text: string; value: string }[]>([]);

// 格式化日期时间
const formatDateTime = (dateString: string): string => {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  } catch (error) {
    return dateString;
  }
};

// 获取客户列表（从出库单中获取去重客户）
const getCustomers = async () => {
  try {
    const result = await outboundOrderAPI.getOutboundOrderCustomers();
    customerOptions.value = result.customers.map((customer) => ({
      value: customer.customer_id,
      label: customer.customer_name
    }));
    
    // 设置表格筛选器选项
    customerFilters.value = result.customers.map((customer) => ({
      text: customer.customer_name,
      value: customer.customer_name
    }));
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '获取客户列表失败';
    ElMessage.error(`获取客户列表失败: ${errorMessage}`);
  }
};

// 客户筛选方法
const filterCustomer = (value: string, row: OutboundOrderResponse) => {
  return row.customer_name === value;
};

// 获取出库单列表（导出该方法供父组件调用）
const getOutboundOrders = async () => {
  loading.value = true;
  try {
    const response = await outboundOrderAPI.getOutboundOrders(queryParams);
    tableData.value = response.data;
    total.value = response.total;
    
    // 在数据加载完成后，恢复排序状态
    await nextTick();
    restoreSortState();
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '获取出库单列表失败';
    ElMessage.error(`获取出库单列表失败: ${errorMessage}`);
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
    queryParams.sort_by = 'create_time';
    queryParams.sort_order = 'desc';
  }
  queryParams.page = 1;
  getOutboundOrders();
};

// 处理日期范围变化
const handleDateRangeChange = (dates: string[]) => {
  if (dates && dates.length === 2) {
    queryParams.start_date = dates[0];
    queryParams.end_date = dates[1];
  } else {
    queryParams.start_date = undefined;
    queryParams.end_date = undefined;
  }
  queryParams.page = 1;
  getOutboundOrders();
};

// 搜索
const handleSearch = () => {
  queryParams.page = 1;
  getOutboundOrders();
};

// 输入搜索（防抖）
const handleInputSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  
  searchTimer = setTimeout(() => {
    queryParams.page = 1;
    getOutboundOrders();
  }, 500);
};

// 分页大小变化
const handleSizeChange = (size: number) => {
  queryParams.page_size = size;
  getOutboundOrders();
};

// 页码变化
const handleCurrentChange = (page: number) => {
  queryParams.page = page;
  getOutboundOrders();
};

// 定义事件
const emit = defineEmits<{
  add: []
  view: [id: number]
  edit: [id: number]
}>();

// 新增出库单
const handleAdd = () => {
  // 触发新增事件
  emit('add');
};

// 查看出库单
const handleView = (row: OutboundOrderResponse) => {
  // 触发查看事件
  emit('view', row.order_id);
};

// 编辑出库单
const handleEdit = (row: OutboundOrderResponse) => {
  // 触发编辑事件
  emit('edit', row.order_id);
};

// 创建Notification实例
const createNotification = (progress: number, status?: 'success' | 'exception', message?: string) => {
  const notificationMessage = message || `正在生成出库单PDF... ${progress}%`;
  
  return ElNotification({
    title: 'PDF生成进度',
    message: h('div', [
      h('p', { style: 'margin: 0 0 8px 0;' }, notificationMessage),
      h(ElProgress, {
        percentage: progress,
        status: status,
        strokeWidth: 8,
        style: 'margin: 0;'
      })
    ]),
    duration: 0,
    showClose: false,
    position: 'top-right', // 改为右上角显示
    offset: 80
  });
};

// 导出出库单PDF
const handleExportPDF = async (row: OutboundOrderResponse) => {
  let notification: any = null;
  
  try {
    // 创建Notification实例，显示0%进度
    notification = createNotification(0, undefined, `正在生成出库单 ${row.order_number} 的PDF文件...`);
    
    // 模拟进度更新：0% -> 50%
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // 更新现有通知，而不是创建新通知
    if (notification) {
      notification.close();
    }
    notification = createNotification(50, undefined, `正在生成出库单 ${row.order_number} 的PDF文件...`);
    
    // 调用PDF导出API
    const pdfBlob = await outboundOrderAPI.generateOutboundOrderPDF(row.order_number);
    
    // 更新进度到100%，显示成功状态
    if (notification) {
      notification.close();
    }
    notification = createNotification(100, 'success', `出库单 ${row.order_number} 的PDF文件生成成功！`);
    
    // 创建下载链接
    const url = window.URL.createObjectURL(pdfBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `出库单_${row.order_number}.pdf`;
    
    // 触发下载
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // 清理URL
    window.URL.revokeObjectURL(url);
    
    // 延迟1秒后关闭通知
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    if (notification) {
      notification.close();
    }
    
    // 显示最终成功消息
    ElMessage.success('PDF文件生成成功，正在下载...');
  } catch (error: any) {
    // 显示错误状态
    if (notification) {
      notification.close();
      notification = createNotification(100, 'exception', `出库单 ${row.order_number} 的PDF文件生成失败！`);
      
      // 延迟2秒后关闭错误通知
      await new Promise(resolve => setTimeout(resolve, 2000));
      notification.close();
    }
    
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || 'PDF导出失败';
    ElMessage.error(`PDF导出失败: ${errorMessage}`);
  }
};

// 删除出库单
const handleDelete = async (row: OutboundOrderResponse) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除出库单 "${row.order_number}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    // 调用删除API
    await outboundOrderAPI.deleteOutboundOrder(row.order_id);
    ElMessage.success('删除成功');
    getOutboundOrders();
  } catch (error: any) {
    if (error !== 'cancel') {
      // 显示具体的错误原因
      const errorMessage = error.response?.data?.message || error.message || '删除失败';
      ElMessage.error(`删除失败: ${errorMessage}`);
    }
  }
};

onMounted(async () => {
  await getCustomers();
  await getOutboundOrders();
});

// 暴露方法给父组件
defineExpose({
  getOutboundOrders
});
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';

/* 使用现代Sass混入 */
@include mixins.table-sort-arrows;
</style>