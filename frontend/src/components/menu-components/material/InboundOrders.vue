<template>
  <div class="base-management-container base-content base-flex-content">
    <!-- 操作栏 -->
    <el-card class="base-operation-card" shadow="hover">
      <div class="base-operation-bar">
        <div class="base-operation-bar__left">
          <el-button 
            type="default" 
            @click="getInboundOrders"
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
            新增入库单
          </el-button>
          <el-button 
            type="success" 
            @click="handlePrintMaterialLedger" 
            :disabled="selectedOrders.length === 0"
            :icon="Printer"
          >
            打印分类账页
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
            placeholder="输入入库单号、供应商搜索"
            style="width: 320px;"
            clearable
            @clear="handleSearch"
            @input="handleInputSearch"
          />
        </div>
      </div>
    </el-card>

    <!-- 入库单列表 -->
    <el-card class="base-table-card base-table-card--flex" shadow="hover">
      <template #header>
        <div class="base-card-header">
          <el-icon><List /></el-icon>
          <span>入库单列表</span>
          <div class="base-card-header__stats" v-if="total > 0">
            <span>总计: {{ total }}</span>
          </div>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="base-loading-container">
        <el-skeleton :rows="8" animated />
      </div>

      <!-- 入库单表格 -->
      <div v-else class="base-table base-table--auto-height">
        <el-table
          ref="tableRef"
          :data="tableData"
          stripe
          border
          :empty-text="'暂无入库单数据'"
          class="base-table"
          @sort-change="handleSortChange"
          @selection-change="handleSelectionChange"
        >
          <el-table-column 
            type="selection" 
            width="55" 
            align="center" 
            fixed="left"
          />
          <el-table-column 
            prop="order_number" 
            label="入库单号" 
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
            prop="supplier_name" 
            label="供应商" 
            min-width="120" 
            align="center"
            :filters="supplierFilters"
            :filter-method="filterSupplier"
            column-key="supplier_name"
          />
          
          <el-table-column 
            prop="contract_reference" 
            label="合同号" 
            width="150" 
            align="center" 
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
            width="230" 
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
              <el-dropdown class="action-dropdown" split-button type="success" size="small" @click="() => handleExportInboundOrderExcel(row)">
                <el-icon><Printer /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="() => handlePrintInboundOrderPdf(row)">
                      <el-icon><Document /></el-icon>
                      导出PDF
                    </el-dropdown-item>
                    <el-dropdown-item @click="() => handleExportInboundOrderExcel(row)">
                      <el-icon><DocumentCopy /></el-icon>
                      导出Excel
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
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
import { ref, reactive, onMounted, onActivated, nextTick, h } from 'vue';
import { ElMessage, ElMessageBox, ElNotification, ElProgress } from 'element-plus';
import { 
  Refresh, 
  List,
  Plus,
  Edit,
  Delete,
  View,
  Printer,
  Document,
  DocumentCopy
} from '@element-plus/icons-vue';
import { inboundOrderAPI } from '@/services/material/inbound';
import type { 
  InboundOrderResponse, 
  InboundOrderQueryParams
} from '@/services/types/inbound';


const loading = ref(false);
const tableRef = ref();
const dateRange = ref<string[]>([]);

const queryParams = reactive<InboundOrderQueryParams>({
  page: 1,
  page_size: 10,
  sort_by: 'create_time',
  sort_order: 'desc'
});

const tableData = ref<InboundOrderResponse[]>([]);
const total = ref(0);

// 选择功能
const selectedOrders = ref<InboundOrderResponse[]>([]);

// 防抖搜索定时器
let searchTimer: NodeJS.Timeout | null = null;

// 筛选选项
const supplierOptions = ref<{ value: number; label: string }[]>([]);
const supplierFilters = ref<{ text: string; value: string }[]>([]);

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

// 获取供应商列表（从入库单中获取去重供应商）
const getSuppliers = async () => {
  try {
    const result = await inboundOrderAPI.getInboundOrderSuppliers();
    supplierOptions.value = result.suppliers.map((supplier) => ({
      value: supplier.supplier_id,
      label: supplier.supplier_name
    }));
    
    // 设置表格筛选器选项
    supplierFilters.value = result.suppliers.map((supplier) => ({
      text: supplier.supplier_name,
      value: supplier.supplier_name
    }));
  } catch (error: any) {
    // 全局拦截器已经处理了401等错误，这里只记录错误不重复显示
    console.error('获取供应商列表失败:', error);
  }
};

// 供应商筛选方法
const filterSupplier = (value: string, row: InboundOrderResponse) => {
  return row.supplier_name === value;
};

// 获取入库单列表
const getInboundOrders = async () => {
  loading.value = true;
  try {
    const response = await inboundOrderAPI.getInboundOrders(queryParams);
    tableData.value = response.data;
    total.value = response.total;
    
    // 在数据加载完成后，恢复排序状态
    await nextTick();
    restoreSortState();
  } catch (error: any) {
    const errorMessage = error.response?.data?.message || error.message || '获取入库单列表失败';
    ElMessage.error(`获取入库单列表失败: ${errorMessage}`);
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
  getInboundOrders();
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
  getInboundOrders();
};

// 搜索
const handleSearch = () => {
  queryParams.page = 1;
  getInboundOrders();
};

// 输入搜索（防抖）
const handleInputSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  
  searchTimer = setTimeout(() => {
    queryParams.page = 1;
    getInboundOrders();
  }, 500);
};

// 分页大小变化
const handleSizeChange = (size: number) => {
  queryParams.page_size = size;
  getInboundOrders();
};

// 页码变化
const handleCurrentChange = (page: number) => {
  queryParams.page = page;
  getInboundOrders();
};

// 定义事件
const emit = defineEmits<{
  add: []
  view: [id: number]
  edit: [id: number]
}>();

// 新增入库单
const handleAdd = () => {
  // 触发新增事件
  emit('add');
};

// 查看入库单
const handleView = (row: InboundOrderResponse) => {
  // 触发查看事件
  emit('view', row.order_id);
};

// 编辑入库单
const handleEdit = (row: InboundOrderResponse) => {
  // 触发编辑事件
  emit('edit', row.order_id);
};

// 选择事件处理
const handleSelectionChange = (selection: InboundOrderResponse[]) => {
  selectedOrders.value = selection;
};

// 打印入库单
const handlePrintInboundOrderPdf = async (row: InboundOrderResponse) => {
  // 创建Notification实例
  let notification: any = null;
  
  const createNotification = (percentage: number, status: 'success' | 'exception' | undefined = undefined) => {
    if (notification) {
      notification.close();
    }
    notification = ElNotification({
      title: '导出入库单',
      message: h('div', { style: 'width: 100%' }, [
        h('p', { style: 'margin-bottom: 10px' }, 
          percentage < 100 
            ? `正在导出入库单 ${row.order_number} 的文件...`
            : status === 'success' 
              ? `入库单 ${row.order_number} 的文件导出成功`
              : `导出入库单 ${row.order_number} 的文件失败`
        ),
        h(ElProgress, {
          percentage: percentage,
          status: status,
          strokeWidth: 6,
          showText: false
        })
      ]),
      duration: 0, // 不会自动关闭
      showClose: false, // 隐藏关闭按钮
      position: 'top-right',
      customClass: 'print-notification'
    });
  };

  try {
    // 初始通知
    createNotification(0);
    
    // 更新进度到50%
    createNotification(50);

    const blob = await inboundOrderAPI.printInboundOrder(row.order_number);
     
    // 更新进度到100%并显示成功状态
    createNotification(100, 'success');

    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `入库单_${row.order_number}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    // 延迟关闭通知并显示成功消息
    setTimeout(() => {
      if (notification) {
        notification.close();
      }
      ElMessage.success('入库单PDF下载成功');
    }, 500);
  } catch (error: any) {
    // 更新进度为错误状态
    createNotification(100, 'exception');
    
    const errorMessage = error.response?.data?.message || error.message || '打印入库单失败';
    
    // 延迟关闭通知并显示错误消息
    setTimeout(() => {
      if (notification) {
        notification.close();
      }
      ElMessage.error(`打印入库单失败: ${errorMessage}`);
    }, 1000);
  }
};

// 导出入库单Excel
const handleExportInboundOrderExcel = async (row: InboundOrderResponse) => {
  // 创建Notification实例
  let notification: any = null;
  
  const createNotification = (percentage: number, status: 'success' | 'exception' | undefined = undefined) => {
    if (notification) {
      notification.close();
    }
    notification = ElNotification({
      title: '导出入库单',
      message: h('div', { style: 'width: 100%' }, [
        h('p', { style: 'margin-bottom: 10px' }, 
          percentage < 100 
            ? `正在导出入库单 ${row.order_number} 的文件...`
            : status === 'success' 
              ? `入库单 ${row.order_number} 的文件导出成功`
              : `导出入库单 ${row.order_number} 的文件失败`
        ),
        h(ElProgress, {
          percentage: percentage,
          status: status,
          strokeWidth: 6,
          showText: false
        })
      ]),
      duration: 0, // 不会自动关闭
      showClose: false, // 隐藏关闭按钮
      position: 'top-right',
      customClass: 'print-notification'
    });
  };

  try {
    // 初始通知
    createNotification(0);
    
    // 更新进度到50%
    createNotification(50);

    const blob = await inboundOrderAPI.generateInboundOrderExcel(row.order_number);
     
    // 更新进度到100%并显示成功状态
    createNotification(100, 'success');

    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `入库单_${row.order_number}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    // 延迟关闭通知并显示成功消息
    setTimeout(() => {
      if (notification) {
        notification.close();
      }
      ElMessage.success('入库单Excel下载成功');
    }, 500);
  } catch (error: any) {
    // 更新进度为错误状态
    createNotification(100, 'exception');
    
    const errorMessage = error.response?.data?.message || error.message || '导出入库单Excel失败';
    
    // 延迟关闭通知并显示错误消息
    setTimeout(() => {
      if (notification) {
        notification.close();
      }
      ElMessage.error(`导出入库单Excel失败: ${errorMessage}`);
    }, 1000);
  }
};

// 打印器材分类账页
const handlePrintMaterialLedger = async () => {
  if (selectedOrders.value.length === 0) {
    ElMessage.warning('请先选择要打印的入库单');
    return;
  }

  // 创建Notification实例
  let notification: any = null;
  
  const createNotification = (percentage: number, status: 'success' | 'exception' | undefined = undefined, currentIndex: number = 0, currentOrderNumber: string = '') => {
    if (notification) {
      notification.close();
    }
    
    let messageText = '';
    if (percentage < 100) {
      if (currentIndex > 0) {
        messageText = `正在生成第 ${currentIndex}/${selectedOrders.value.length} 个账页: ${currentOrderNumber}`;
      } else {
        messageText = `正在批量生成 ${selectedOrders.value.length} 个器材分类账页...`;
      }
    } else {
      messageText = status === 'success' 
        ? `成功生成 ${selectedOrders.value.length} 个器材分类账页`
        : `批量生成器材分类账页失败`;
    }
    
    notification = ElNotification({
      title: '批量生成器材分类账页',
      message: h('div', { style: 'width: 100%' }, [
        h('p', { style: 'margin-bottom: 10px' }, messageText),
        h(ElProgress, {
          percentage: percentage,
          status: status,
          strokeWidth: 6,
          showText: false
        })
      ]),
      duration: 0, // 不会自动关闭
      showClose: false, // 隐藏关闭按钮
      position: 'top-right', // 改为右上角显示
      customClass: 'print-notification'
    });
  };

  try {
    // 初始通知
    createNotification(0);
    
    // 批量打印选中的入库单
    for (let i = 0; i < selectedOrders.value.length; i++) {
      const order = selectedOrders.value[i];
      
      // 更新进度条显示当前处理进度
      const progress = Math.round((i / selectedOrders.value.length) * 100);
      createNotification(progress, undefined, i + 1, order.order_number);

      const blob = await inboundOrderAPI.printMaterialLedger(order.order_number);
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `器材分类账页${order.order_number}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      // 添加延迟，避免同时下载多个文件导致浏览器阻塞
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    // 更新进度到100%并显示成功状态
    createNotification(100, 'success');
    
    // 延迟关闭通知并显示成功消息
    setTimeout(() => {
      if (notification) {
        notification.close();
      }
      ElMessage.success(`成功打印 ${selectedOrders.value.length} 个器材分类账页`);
    }, 500);
  } catch (error: any) {
    // 更新进度为错误状态
    createNotification(100, 'exception');
    
    const errorMessage = error.response?.data?.message || error.message || '打印器材分类账页失败';
    
    // 延迟关闭通知并显示错误消息
    setTimeout(() => {
      if (notification) {
        notification.close();
      }
      ElMessage.error(`打印器材分类账页失败: ${errorMessage}`);
    }, 1000);
  }
};

// 删除入库单
const handleDelete = async (row: InboundOrderResponse) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除入库单 "${row.order_number}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    // 调用删除API
    await inboundOrderAPI.deleteInboundOrder(row.order_id);
    ElMessage.success('删除成功');
    getInboundOrders();
  } catch (error: any) {
    // 显示具体的错误原因
    if (error.message === 'cancel') {
      return; // 用户取消操作，不显示错误
    }
    
    // 优先处理detail字段中的详细信息
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      let errorMessage = detail.message || '删除失败';
      
      // 如果有问题器材列表，添加到错误信息中
      if (detail.problematic_items && detail.problematic_items.length > 0) {
        detail.problematic_items.forEach((item: any) => {
          errorMessage += `- ${item.material_name} (批次: ${item.batch_number}, 出库单数量: ${item.outbound_count}`;
          // 如果有关联的出库单号，显示出来
          if (item.outbound_order_numbers && item.outbound_order_numbers.length > 0) {
            errorMessage += `, 关联出库单: ${item.outbound_order_numbers.join(', ')}`;
          }
          errorMessage += ')\n';
        });
      }
      
      ElMessage.error(errorMessage);
    } else {
      // 如果没有detail字段，使用原来的逻辑
      const errorMessage = error.response?.data?.message || error.message || '删除失败';
      ElMessage.error(`删除失败: ${errorMessage}`);
    }
  }
};

onMounted(async () => {
  await getSuppliers();
  await getInboundOrders();
});

// 暴露方法给父组件
defineExpose({
  getInboundOrders
});

// 组件激活时刷新数据（从 keep-alive 缓存中恢复时）
onActivated(async () => {
  // 刷新数据以获取最新内容
  await getInboundOrders();
});
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';

/* 使用现代Sass混入 */
@include mixins.table-sort-arrows;

/* 操作列下拉菜单样式 */
.action-dropdown {
  margin: 0 4px;
  vertical-align: middle;
}
</style>