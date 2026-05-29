<template>
  <div class="base-management-container base-content base-flex-content">
    <!-- 页头 -->
    <el-card class="base-page-header-card" shadow="hover">
      <el-page-header @back="handleBack" class="base-page-header">
        <template #content>
          <div class="base-page-header__content">
            <span class="base-page-header__title">{{ props.readonly ? '查看出库单' : isEdit ? '编辑出库单' : '新增出库单' }} - {{ orderForm.order_number || '新出库单' }}</span>
          </div>
        </template>
      </el-page-header>
    </el-card>

    <!-- 出库单基本信息 -->
    <el-card class="base-form-card" shadow="hover">

      <el-form :model="orderForm" label-width="120px" :rules="orderRules" ref="orderFormRef">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="出库单号" prop="order_number">
              <el-input 
                v-model="orderForm.order_number" 
                :placeholder="isEdit ? '编辑出库单号' : '自动生成'" 
                :disabled="props.readonly"
                @change="handleOrderNumberChange"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="出库日期" prop="outbound_date">
              <el-date-picker
                v-model="orderForm.outbound_date"
                type="date"
                placeholder="选择出库日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                :disabled="props.readonly"
                @change="handleOutboundDateChange"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="客户" prop="customer_id">
              <el-select
                v-model="orderForm.customer_id"
                placeholder="请选择或搜索客户"
                filterable
                remote
                :remote-method="remoteSearchCustomers"
                :loading="customerLoading"
                style="width: 100%"
                :disabled="props.readonly"
                @change="handleCustomerChange"
                @visible-change="bindCustomerScrollListener"
              >
                <el-option
                  v-for="customer in customerOptions"
                  :key="customer.value"
                  :label="customer.label"
                  :value="customer.value"
                />
                <!-- 如果客户已被删除（不在customerOptions中），显示冗余的客户名称 -->
                <el-option
                  v-if="orderForm.customer_id && !customerOptions.some(opt => opt.value === orderForm.customer_id)"
                  :key="orderForm.customer_id"
                  :label="`${originalOrderForm.customer_name || '已删除的客户'}`"
                  :value="orderForm.customer_id"
                  disabled
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="调拨单号" prop="requisition_reference">
              <el-input 
                v-model="orderForm.requisition_reference" 
                placeholder="请输入调拨单号" 
                :disabled="props.readonly"
                @change="handleTransferNumberChange"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="总数量">
              <el-input 
                :value="totalQuantity" 
                placeholder="自动计算" 
                disabled
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="总金额">
              <el-input 
                :value="totalAmount" 
                placeholder="自动计算" 
                disabled
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <!-- 出库明细表格 -->
    <el-card class="base-table-card base-table-card--flex" shadow="hover">
      <template #header>
        <div class="base-card-header" style="height: 20px; line-height: 20px; display: flex; align-items: center; gap: 0;">
          <el-icon><List /></el-icon>
          <span style="height: 20px; display: inline-block; line-height: 20px;margin-right: 10px;">出库明细</span>
          <div class="base-card-header__actions">
            <el-button 
              v-if="!props.readonly"
              type="primary" 
              @click="openMaterialDrawer"
              :icon="Plus"
            >
              添加器材
            </el-button>
            <el-button 
              v-if="!props.readonly && isEdit"
              type="warning" 
              @click="handleForceUpdate"
              :icon="Refresh"
              :loading="updating"
            >
              强制更新
            </el-button>
          </div>
        </div>
      </template>

      <div class="base-table base-table--auto-height">
        <el-table
          :data="paginatedItems"
          stripe
          border
          :empty-text="'暂无出库明细数据'"
          class="base-table"
        >
        <el-table-column 
          type="index" 
          label="序号" 
          width="60" 
          align="center" 
          fixed="left"
        >
          <template #default="{ $index }">
            <span v-memo="[getRealIndex($index)]">{{ getRealIndex($index) + 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column 
          prop="material_code" 
          label="器材编码" 
          width="110" 
          align="center" 
          fixed="left"
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.material_code]">{{ row.material_code }}</span>
          </template>
        </el-table-column>
        <el-table-column 
          prop="material_name" 
          label="器材名称" 
          min-width="100" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.material_name]">{{ row.material_name }}</span>
          </template>
        </el-table-column>
        <el-table-column 
          prop="material_specification" 
          label="器材规格" 
          width="100" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.material_specification]">{{ row.material_specification }}</span>
          </template>
        </el-table-column>
        <el-table-column 
          prop="batch_number" 
          label="批次编码" 
          width="120" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.batch_number]">{{ row.batch_number }}</span>
          </template>
        </el-table-column>
        <!-- 数量列 -->
        <el-table-column 
          prop="quantity" 
          label="数量" 
          width="120" 
          align="center" 
        >
          <template #default="{ row, $index }">
            <el-input-number
              v-model="row.quantity"
              :min="1"
              :precision="0"
              size="small"
              controls-position="right"
              @change="handleQuantityChange(getRealIndex($index))"
              :class="{ 'insufficient-stock': row.batch_id && !checkStockSufficient(row.batch_id, row.quantity, getRealIndex($index)) }"
              style="width: 100%"
              :disabled="props.readonly"
            />
          </template>
        </el-table-column>
        <el-table-column 
          prop="unit" 
          label="单位" 
          width="60" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.unit]">{{ row.unit }}</span>
          </template>
        </el-table-column>
        <el-table-column 
          prop="unit_price" 
          label="单价" 
          width="80" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.unit_price]">
              {{ row.unit_price ? `¥${row.unit_price.toFixed(2)}` : '-' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column 
          prop="bin_name" 
          label="货位" 
          width="100" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.bin_name]">{{ row.bin_name }}</span>
          </template>
        </el-table-column>
        <el-table-column 
          prop="production_date" 
          label="生产日期" 
          width="120" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.production_date]">
              {{ formatDate(row.production_date) }}
            </span>
          </template>
        </el-table-column>
        
        

        <!-- 操作列 -->
        <el-table-column 
          label="操作" 
          width="100" 
          align="center" 
          fixed="right"
          v-if="!props.readonly"
        >
          <template #default="{ $index }">
            <el-button 
              type="danger" 
              size="small" 
              @click="removeItem(getRealIndex($index))"
              :icon="Delete"
              :loading="deleting"
              :disabled="deleting"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
        </el-table>
      </div>

      <!-- 分页器 -->
      <div class="base-pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="orderItems.length"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="currentPage = 1"
          background
        />
      </div>
    </el-card>

    <!-- 操作按钮 -->
    <div class="base-form-actions">
      <el-button @click="handleBack">{{ props.readonly ? '返回' : '取消' }}</el-button>
      <el-button v-if="!props.readonly && !isEdit" type="primary" @click="handleSave" :loading="saving">保存</el-button>
    </div>

    <!-- 器材选择抽屉 -->
    <el-drawer
      v-model="materialDrawerVisible"
      title="选择器材"
      direction="ttb"
      size="80%"
      :before-close="handleDrawerClose"
    >
      <div class="material-drawer-content">
        <!-- 筛选器和定位器材 -->
        <div class="drawer-filter">
          <el-row :gutter="10">
            <el-col :span="12">
              <div style="display: flex; align-items: center; gap: 10px;">
                <label style="min-width: 80px; font-weight: 500; color: #606266;">搜索器材:</label>
                <el-input
                  v-model="materialFilter.keyword"
                  placeholder="输入器材编码、名称、规格搜索"
                  clearable
                  @clear="handleMaterialFilterChange"
                  @input="handleMaterialFilterChange"
                  style="flex: 1;"
                />
              </div>
            </el-col>
            <el-col :span="12">
              <div style="display: flex; align-items: center; gap: 10px;">
                <label style="min-width: 80px; font-weight: 500; color: #606266;">定位器材:</label>
                <el-input
                  v-model="materialLocateCode"
                  placeholder="请输入器材批次编码"
                  clearable
                  @input="handleLocateInputChange"
                  @keyup.enter="handleMaterialLocate"
                  @clear="handleMaterialLocateClear"
                  style="flex: 1;"
                >
                  <template #append>
                    <el-button 
                      :icon="Location" 
                      @click="handleMaterialLocate"
                      :loading="locating"
                    />
                  </template>
                </el-input>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 器材列表 -->
        <div class="drawer-table">
          <el-table
            ref="materialTableRef"
            :data="materialList"
            row-key="detail_id"
            stripe
            border
            height="100%"
            :empty-text="'暂无器材数据'"
            class="base-table"
            @filter-change="handleTableFilterChange"
            :row-class-name="getRowClassName"
          >
            <el-table-column 
              prop="material_code" 
              label="器材编码" 
              width="110" 
              align="center" 
              fixed="left"
            />
            <el-table-column 
              prop="material_name" 
              label="器材名称" 
              min-width="120" 
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
            />
            <el-table-column 
              prop="major_name" 
              label="专业" 
              width="100" 
              align="center"
              :filters="majorFilters"
              :filter-method="filterMajorMethod"
              column-key="major_name"
              filter-multiple
            >
              <template #default="{ row }">
                <el-tag v-if="row.major_name" type="primary" size="small">{{ row.major_name }}</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column 
              prop="equipment_name" 
              label="装备" 
              width="100" 
              align="center"
              :filters="equipmentFilters"
              :filter-method="filterEquipmentMethod"
              column-key="equipment_name"
              filter-multiple
            >
              <template #default="{ row }">
                <el-tag v-if="row.equipment_name" type="success" size="small">{{ row.equipment_name }}</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column 
              prop="unit" 
              label="单位" 
              width="60" 
              align="center" 
            />
            <el-table-column 
              prop="warehouse_name" 
              label="仓库" 
              width="100" 
              align="center" 
            />
            <el-table-column 
              prop="bin_name" 
              label="货位" 
              width="100" 
              align="center" 
            />
            <el-table-column 
              prop="quantity" 
              label="库存数量" 
              width="100" 
              align="center" 
              fixed="right"
            >
              <template #default="{ row }">
                <el-tag :type="getQuantityTagType(getRemainingQuantity(row))">
                  {{ getRemainingQuantity(row) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <!-- 添加操作列 -->
            <el-table-column 
              label="操作" 
              width="180" 
              align="center" 
              fixed="right"
            >
              <template #default="{ row }">
                <el-input-number
                  v-model="row.addQuantity"
                  :min="1"
                  :max="9999"
                  size="small"
                  :class="{ 'quantity-error': row.addQuantity > row.quantity }"
                  style="width: 80px; margin-right: 10px;"
                  placeholder="数量"
                />
                <el-button 
              type="primary" 
              size="small" 
              @click="addMaterialItem(row)"
              :icon="ShoppingCart"
            >
            </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';

// 定义组件属性
interface Props {
  editId?: number | null
  readonly?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  editId: null,
  readonly: false
});
import {
  List, 
  Plus, 
  Delete, 
  ShoppingCart,
  Refresh,
  Location
} from '@element-plus/icons-vue';
import { outboundOrderAPI } from '@/services/material/outbound';
import { customerAPI } from '@/services/base/customer';
import { inventoryDetailAPI } from '@/services/material/inventory_detail';
import type { 
  OutboundOrderCreate,
  OutboundOrderItemCreate
} from '@/services/types/outbound';
import type { InventoryDetailResponse } from '@/services/types/inventory_detail';
import type { CustomerResponse } from '@/services/types/customer';
import { saveDraft, loadDraft, clearDraft, hasDraft, getDraftTimestamp, formatDraftTime } from '@/utils/draftManager';

const isEdit = ref(false);
const orderId = ref<number | null>(null);
const saving = ref(false);
const updating = ref(false);
const deleting = ref(false); // 删除状态锁
const materialDrawerVisible = ref(false);

// 草稿管理相关常量
const DRAFT_KEY = 'outbound_order_draft';

// 草稿数据接口
interface OutboundOrderDraftData {
  orderForm: {
    order_number: string;
    requisition_reference: string;
    customer_id: number | null;
    outbound_date: string;
  };
  orderItems: ExtendedOutboundOrderItem[];
}

// 出库明细（扩展类型以包含显示所需的器材信息）
interface ExtendedOutboundOrderItem extends OutboundOrderItemCreate {
  detail_id?: number;
  material_code?: string;
  material_name?: string;
  material_specification?: string;
  unit_price?: number;
  unit?: string;
  batch_number?: string;
  bin_name?: string;
  equipment_name?: string;
  addQuantity?: number;
  originalQuantity?: number;
}
const orderItems = ref<ExtendedOutboundOrderItem[]>([]);

// 加载出库单详情
const loadOrderDetail = async () => {
  // console.log('loadOrderDetail函数被调用，orderId.value:', orderId.value);
  if (!orderId.value) {
    // console.log('orderId.value为null，函数返回');
    return;
  }
  // console.log('加载出库单详情:', orderId.value);
  try {
    const result = await outboundOrderAPI.getOutboundOrderDetail(orderId.value);
    const { order, items } = result;
    
    // 填充表单数据
    Object.assign(orderForm, {
      order_number: order.order_number,
      requisition_reference: order.requisition_reference || '',
      customer_id: order.customer_id,
      outbound_date: order.create_time.split(' ')[0] // 使用创建日期作为出库日期
    });
    
    // 保存原始值（包括客户名称，用于显示）
    Object.assign(originalOrderForm, {
      ...order,
      customer_name: order.customer_name // 保存客户名称用于显示
    });
    
    // 填充明细数据 - 直接使用出库单详情中的器材信息
    orderItems.value = items.map(item => ({
      detail_id: item.item_id,
      batch_id: item.batch_id,
      material_code: item.material_code,
      material_name: item.material_name,
      material_specification: item.material_specification,
      quantity: item.quantity,
      unit_price: item.unit_price,
      unit: item.unit,
      batch_number: item.batch_number,
      bin_name: item.bin_name,
      equipment_name: item.equipment_name || '',
      addQuantity: item.quantity,
      originalQuantity: item.quantity // 保存原始数量用于变化检查
    }));
    
    // 初始化库存管理变量 - 为已加载的出库明细初始化库存信息
    // 这样在页面加载时，数量输入框就不会显示红色
    stockManagement.value.clear();
    items.forEach(item => {
      stockManagement.value.set(item.batch_id, {
        batch_id: item.batch_id,
        // 在编辑模式下，初始可用库存等于当前出库数量（假设库存充足）
        // 后续打开器材选择抽屉时会重新计算准确的可用库存
        available_quantity: item.quantity,
        original_quantity: item.quantity
      });
    });
    
    // 在编辑模式下，立即加载器材列表并更新库存管理变量为准确值
    if (isEdit.value) {
      await getMaterialList();
      updateStockManagementForEdit();
    }
    
    // 编辑模式下清除草稿（如果有）
    if (hasDraft(DRAFT_KEY)) {
      clearDraft(DRAFT_KEY);
    }
    
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '加载出库单详情失败';
    ElMessage.error(`加载出库单详情失败: ${errorMessage}`);
  }
};


// 出库单表单
const orderForm = reactive({
  order_number: '',
  requisition_reference: '',
  customer_id: null as number | null,
  outbound_date: ''
});

// 出库单表单原始值（用于比较是否真正发生变化）
const originalOrderForm = reactive({
  order_number: '',
  requisition_reference: '',
  customer_id: null as number | null,
  outbound_date: '',
  customer_name: '' // 保存客户名称，用于显示已删除的客户
});

// 筛选选项
const customerOptions = ref<{ value: number; label: string }[]>([]);
// 客户加载状态
const customerLoading = ref(false);
// 搜索防抖定时器
let searchTimer: NodeJS.Timeout | null = null;
// 客户分页状态
const customerPagination = reactive({
  currentPage: 1,
  pageSize: 50,
  totalPages: 0,
  hasMore: true,
  currentSearch: '' // 当前搜索关键字
});
const majorOptions = ref<{ value: number; label: string }[]>([]);
const equipmentOptions = ref<{ value: number; label: string }[]>([]);

// 器材筛选条件
const materialFilter = reactive({
  major_id: undefined as number | number[] | undefined,
  equipment_id: undefined as number | number[] | undefined,
  keyword: ''
});

// 器材列表
const materialList = ref<(InventoryDetailResponse & { addQuantity: number })[]>([]);
const materialFirstPage = ref(1); // 记录当前列表的第一页页码
const materialLastPage = ref(1);  // 记录当前列表的最后一页页码
const materialHasMore = ref(true);
const loadingMoreMaterials = ref(false);
const materialRequestId = ref(0); // 请求 ID，用于防止异步竞态冲突
const MAX_MATERIAL_ITEMS = 100; // 超过100项后修剪前端数据
const highlightedMaterialId = ref<number | null>(null); // 高亮的器材ID
const materialTableRef = ref(); // 器材表格ref

// 定位相关变量
const materialLocateCode = ref(''); // 定位用的批次编号
const locating = ref(false); // 定位加载状态
const isLocatingScroll = ref(false); // 标记是否正在执行定位滚动锁定

// 筛选器变量
const majorFilters = ref<{ text: string; value: string }[]>([]);
const equipmentFilters = ref<{ text: string; value: string }[]>([]);

// 库存管理变量：存储器材batch id和库存数量
interface StockInfo {
  batch_id: number;
  available_quantity: number; // 可用库存数量
  original_quantity: number; // 原始库存数量
}
const stockManagement = ref<Map<number, StockInfo>>(new Map());

// 出库明细分页相关变量
const currentPage = ref(1);
const pageSize = ref(20);

// 计算属性：分页后的出库明细数据
const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return orderItems.value.slice(start, end);
});

// 计算当前页的真实索引（用于操作原始数组）
const getRealIndex = (pageIndex: number): number => {
  return (currentPage.value - 1) * pageSize.value + pageIndex;
};

// 生成出库单号
const generateOrderNumber = async () => {
  try {
    // 获取当前日期，格式为YYYYMMDD（后端API要求格式）
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const dateStr = `${year}${month}${day}`;
    
    const result = await outboundOrderAPI.generateOutboundOrderNumber(dateStr);
    orderForm.order_number = result.order_number;
  } catch (error: any) {
    // 如果生成失败，显示错误信息而不是自动生成编号
    ElMessage.error(`出库单号生成失败: ${error.response?.data?.message || error.message || '未知错误'}`);
    // 清空出库单号，让用户手动输入或重新生成
    orderForm.order_number = '';
  }
};

// 重置表单
const resetForm = async () => {
  // 新增模式：先检查是否有草稿
  if (hasDraft(DRAFT_KEY)) {
    try {
      // 获取草稿时间戳
      const timestamp = getDraftTimestamp(DRAFT_KEY);
      const timeText = timestamp ? formatDraftTime(timestamp) : '未知时间';
      
      // 询问用户是否恢复草稿
      await ElMessageBox.confirm(
        `检测到未保存的草稿（保存于${timeText}），是否恢复？`,
        '发现草稿',
        {
          confirmButtonText: '恢复草稿',
          cancelButtonText: '放弃草稿',
          type: 'info',
          distinguishCancelAndClose: true
        }
      );
      
      // 用户点击"恢复草稿"按钮，对话框已自动关闭
      const draftData = loadDraft<OutboundOrderDraftData>(DRAFT_KEY);
      if (draftData) {
        // 恢复表单数据
        Object.assign(orderForm, draftData.orderForm);
        // 恢复明细数据
        orderItems.value = draftData.orderItems;
        ElMessage.success('草稿已恢复');
        return; // 恢复草稿后直接返回，不执行后续重置逻辑
      }
    } catch (error) {
      // 用户点击"放弃草稿"或关闭对话框，对话框已自动关闭
      clearDraft(DRAFT_KEY);
      // 继续执行下面的重置逻辑
    }
  }
  
  // 没有草稿或用户选择放弃草稿，执行正常重置逻辑
  // 重置表单数据
  Object.assign(orderForm, {
    order_number: '',
    requisition_reference: '',
    customer_id: null,
    outbound_date: ''
  });
  
  // 清空明细列表
  orderItems.value = [];
  
  // 只有在新增模式时才生成新的出库单号
  if (!isEdit.value) {
    generateOrderNumber();
  }
  
  // 自动填充当天日期
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  orderForm.outbound_date = `${year}-${month}-${day}`;
};

// 监听props.editId和props.readonly变化，设置三种模式
watch([() => props.editId, () => props.readonly], ([newEditId, newReadonly]) => {
  // console.log('props.editId变化:', newEditId, 'props.readonly变化:', newReadonly);
  
  if (newEditId) {
    // 编辑或查看模式
    isEdit.value = true;
    orderId.value = newEditId;
    
    if (newReadonly) {
      // 查看模式：加载详情，表单字段不可编辑
      loadOrderDetail();
    } else {
      // 编辑模式：加载详情，表单字段可编辑
      loadOrderDetail();
    }
  } else {
    // 新建模式
    isEdit.value = false;
    orderId.value = null;
    resetForm();
  }
}, { immediate: true });

// 监听表单数据变化，自动保存草稿（仅新增模式）
watch(() => orderForm, () => {
  if (!isEdit.value) {
    saveDraftDebounced();
  }
}, { deep: true });

// 监听明细数据变化，自动保存草稿（仅新增模式）
watch(() => orderItems.value, () => {
  if (!isEdit.value) {
    saveDraftDebounced();
  }
}, { deep: true });

const orderFormRef = ref();
const orderRules = {
  order_number: [{ required: true, message: '请输入出库单号', trigger: 'change' }],
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  outbound_date: [{ required: true, message: '请选择出库日期', trigger: 'change' }]
};



// 计算总数量
const totalQuantity = computed(() => {
  return orderItems.value.reduce((sum, item) => sum + (item.quantity || 0), 0);
});

// 计算总金额
const totalAmount = computed(() => {
  return orderItems.value.reduce((sum, item) => {
    const amount = (item.quantity || 0) * (item.unit_price || 0);
    return Number((sum + amount).toFixed(3));
  }, 0);
});

// 计算已添加到出库明细的数量
const getAddedQuantity = (batchId: number) => {
  return orderItems.value
    .filter(item => item.batch_id === batchId)
    .reduce((sum, item) => sum + (item.quantity || 0), 0);
};

// 库存管理相关函数

// 初始化库存管理变量（新建出库单模式）
const initStockManagement = () => {
  stockManagement.value.clear();
  
  // 为器材列表中的每个器材初始化库存信息
  materialList.value.forEach(material => {
    if (material.batch_id !== undefined) {
      stockManagement.value.set(material.batch_id, {
        batch_id: material.batch_id,
        available_quantity: material.quantity,
        original_quantity: material.quantity // 添加原始库存
      });
    }
  });
};

// 更新库存管理变量(编辑模式)
const updateStockManagementForEdit = () => {
  stockManagement.value.clear();
  
  // 为器材列表中的器材初始化库存信息
  materialList.value.forEach(material => {
    if (material.batch_id !== undefined) {
      // 编辑模式下由于实时写入数据库，直接使用真实库存
      stockManagement.value.set(material.batch_id!, {
        batch_id: material.batch_id!,
        available_quantity: material.quantity, // 真实可用库存
        original_quantity: material.quantity // 添加原始库存
      });
    }
  });
};

// 添加器材时更新库存管理变量
const updateStockOnAdd = (batchId: number, quantity: number) => {
  const stockInfo = stockManagement.value.get(batchId);
  if (stockInfo) {
    stockInfo.available_quantity -= quantity;
    stockManagement.value.set(batchId, stockInfo);
  }
};

// 删除器材时更新库存管理变量
const updateStockOnRemove = (batchId: number, quantity: number) => {
  const stockInfo = stockManagement.value.get(batchId);
  if (stockInfo) {
    stockInfo.available_quantity += quantity;
    stockManagement.value.set(batchId, stockInfo);
  }
};

// 检查库存是否充足
const checkStockSufficient = (batchId: number, quantity: number, currentIndex?: number): boolean => {
  const stockInfo = stockManagement.value.get(batchId);
  if (!stockInfo) {
    return false;
  }
  
  // 计算当前批次在出库明细中的其他项的总数量（不包括当前正在检查的项）
  const otherItemsQuantity = orderItems.value
    .filter((item, index) => item.batch_id === batchId && index !== currentIndex)
    .reduce((sum, item) => sum + (item.quantity || 0), 0);
  
  // 检查：当前输入数量 + 其他明细项的数量 <= 原始库存
  return (quantity + otherItemsQuantity) <= stockInfo.original_quantity;
};

// 获取可用库存数量
const getAvailableStockQuantity = (batchId: number): number => {
  const stockInfo = stockManagement.value.get(batchId);
  return stockInfo ? stockInfo.available_quantity : 0;
};

// 计算剩余库存数量
const getRemainingQuantity = (material: InventoryDetailResponse) => {
  // 在编辑模式下，使用库存管理变量中的可用库存数量
  if (isEdit.value && material.batch_id !== undefined) {
    return getAvailableStockQuantity(material.batch_id);
  }
  
  // 在新建模式下，使用原始库存减去已添加数量
  if (material.batch_id === undefined) {
    return material.quantity;
  }
  const addedQuantity = getAddedQuantity(material.batch_id);
  return material.quantity - addedQuantity;
};



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

// 草稿自动保存方法
const saveDraftData = () => {
  // 仅在新增模式下保存草稿
  if (!isEdit.value) {
    // 判断是否有有效的用户输入（不仅仅是自动生成的单号和日期）
    const hasValidInput = 
      orderForm.customer_id !== null ||  // 有客户选择
      orderForm.requisition_reference !== '' ||  // 有调拨单号
      orderItems.value.length > 0;  // 有明细数据
    
    // 只有存在有效用户输入时才保存草稿
    if (hasValidInput) {
      const draftData: OutboundOrderDraftData = {
        orderForm: {
          order_number: orderForm.order_number,
          requisition_reference: orderForm.requisition_reference,
          customer_id: orderForm.customer_id,
          outbound_date: orderForm.outbound_date
        },
        orderItems: orderItems.value
      };
      saveDraft(DRAFT_KEY, draftData);
    } else {
      // 没有有效输入，清除可能存在的草稿
      clearDraft(DRAFT_KEY);
    }
  }
};

// 防抖函数
const debounce = <T extends (...args: any[]) => any>(func: T, delay: number): T => {
  let timeoutId: ReturnType<typeof setTimeout>;
  return ((...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(null, args), delay);
  }) as T;
};

// 防抖保存草稿（500ms）
const saveDraftDebounced = debounce(saveDraftData, 500);

// 获取客户列表（支持传参和追加模式）
const getCustomers = async (searchKeyword?: string, append: boolean = false) => {
  try {
    // 如果不是追加模式，重置分页状态
    if (!append) {
      customerPagination.currentPage = 1;
      customerPagination.currentSearch = searchKeyword || '';
    }
    
    // 根据是否搜索设置不同的参数
    const params: any = {
      page: customerPagination.currentPage,
      page_size: customerPagination.pageSize,
      sort_field: 'update_time', // 按更新时间排序，显示最近使用的
      sort_asc: false // 降序排列
    };
    
    // 如果有搜索关键字，添加search参数
    if (searchKeyword && searchKeyword.trim()) {
      params.search = searchKeyword.trim();
      params.page_size = 50; // 搜索时显示50条
    }
    
    const result = await customerAPI.getCustomers(params);
    
    // 更新分页信息
    customerPagination.totalPages = result.total_pages;
    customerPagination.hasMore = customerPagination.currentPage < result.total_pages;
    
    // 根据模式处理数据：追加或替换
    const newOptions = result.data.map((customer: CustomerResponse) => ({
      value: customer.id,
      label: customer.customer_name
    }));
    
    if (append) {
      // 追加模式：合并数据，去重
      const existingIds = new Set(customerOptions.value.map(opt => opt.value));
      const uniqueNewOptions = newOptions.filter(opt => !existingIds.has(opt.value));
      customerOptions.value = [...customerOptions.value, ...uniqueNewOptions];
    } else {
      // 替换模式：直接赋值
      customerOptions.value = newOptions;
    }
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '获取客户列表失败';
  }
};

// 远程搜索客户（带防抖）
const remoteSearchCustomers = (query: string) => {
  // 清除之前的定时器
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  
  // 如果查询为空，加载初始列表
  if (!query || !query.trim()) {
    getCustomers();
    return;
  }
  
  // 设置加载状态
  customerLoading.value = true;
  
  // 防抖：300ms后执行搜索
  searchTimer = setTimeout(async () => {
    try {
      await getCustomers(query);
    } finally {
      customerLoading.value = false;
    }
  }, 300);
};

// 触底加载更多客户（优化：防止滚动跳动）
const loadMoreCustomers = async () => {
  // 如果正在加载或没有更多数据，直接返回
  if (customerLoading.value || !customerPagination.hasMore) {
    return;
  }
  
  // 获取当前滚动容器
  const scrollContainer = document.querySelector('.el-select-dropdown__wrap') as HTMLElement;
  if (!scrollContainer) return;
  
  // 保存加载前的滚动位置和内容高度
  const scrollTopBefore = scrollContainer.scrollTop;
  const scrollHeightBefore = scrollContainer.scrollHeight;
  
  try {
    customerLoading.value = true;
    // 页码+1
    customerPagination.currentPage++;
    // 使用当前搜索关键字，并以追加模式加载
    await getCustomers(customerPagination.currentSearch, true);
    
    // 等待DOM更新完成
    await nextTick();
    
    // 计算新增内容的高度
    const scrollHeightAfter = scrollContainer.scrollHeight;
    const heightDiff = scrollHeightAfter - scrollHeightBefore;
    
    // 恢复滚动位置（补偿新增高度）
    if (heightDiff > 0) {
      scrollContainer.scrollTop = scrollTopBefore + heightDiff;
    }
  } catch (error) {
    // 加载失败，回退页码
    customerPagination.currentPage--;
  } finally {
    customerLoading.value = false;
  }
};

// 客户下拉框滚动事件处理
const handleCustomerScroll = (event: Event) => {
  const target = event.target as HTMLElement;
  const { scrollTop, scrollHeight, clientHeight } = target;
  
  // 触底加载：离底部还有15px时触发
  if (scrollTop + clientHeight >= scrollHeight - 15) {
    loadMoreCustomers();
  }
};

// 绑定客户下拉框滚动监听
const bindCustomerScrollListener = () => {
  nextTick(() => {
    // 获取 el-select 的下拉框 DOM
    const selectDropdown = document.querySelector('.el-select-dropdown__wrap');
    if (selectDropdown) {
      selectDropdown.removeEventListener('scroll', handleCustomerScroll);
      selectDropdown.addEventListener('scroll', handleCustomerScroll);
    }
  });
};

// 获取专业列表
const getMajors = async () => {
  try {
    const result = await inventoryDetailAPI.getMajorOptionsFromInventory();
    majorOptions.value = result.data.map((major: any) => ({
      value: major.id,
      label: major.major_name
    }));
    // 生成专业筛选器
    generateMajorFilters();
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '获取专业列表失败';
    ElMessage.error(`获取专业列表失败: ${errorMessage}`);
  }
};

// 获取装备列表
const getEquipments = async () => {
  try {
    const result = await inventoryDetailAPI.getEquipmentOptionsFromInventory();
    equipmentOptions.value = result.data.map((equipment: any) => ({
      value: equipment.id,
      label: equipment.display_name
    }));
    // 生成装备筛选器
    generateEquipmentFilters();
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '获取装备列表失败';
    ElMessage.error(`获取装备列表失败: ${errorMessage}`);
  }
};

// 生成专业筛选器
const generateMajorFilters = () => {
  majorFilters.value = majorOptions.value.map(option => ({
    text: option.label,
    value: option.label
  }));
};

// 生成装备筛选器
const generateEquipmentFilters = () => {
  equipmentFilters.value = equipmentOptions.value.map(option => ({
    text: option.label,
    value: option.label
  }));
};

// 根据专业获取装备列表
const getEquipmentsByMajor = async (majorId: number) => {
  try {
    const response = await inventoryDetailAPI.getEquipmentOptionsFromInventory([majorId]);
    equipmentOptions.value = response.data.map((item: any) => ({
      value: item.id,
      label: item.display_name
    }));
    // 更新装备筛选器
    generateEquipmentFilters();
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '获取装备列表失败';
    ElMessage.error(`获取装备列表失败: ${errorMessage}`);
  }
};

// 获取器材列表
const getMaterialList = async (page = 1, mode: 'replace' | 'append' | 'prepend' = 'replace') => {
  if (loadingMoreMaterials.value && mode !== 'replace') return;
  
  // 生成当前请求的唯一 ID
  const currentId = ++materialRequestId.value;
  
  try {
    loadingMoreMaterials.value = true;
    const pageSize = 10;
    
    // 构建查询参数
    const params = {
      page: page,
      page_size: pageSize,
      keyword: materialFilter.keyword,
      major_id: Array.isArray(materialFilter.major_id) ? materialFilter.major_id : 
                materialFilter.major_id !== undefined ? [materialFilter.major_id] : undefined,
      equipment_id: Array.isArray(materialFilter.equipment_id) ? materialFilter.equipment_id : 
                   materialFilter.equipment_id !== undefined ? [materialFilter.equipment_id] : undefined,
      quantity_filter: 'has_stock' as 'has_stock' // 只显示有库存的器材
    };
    
    const response = await inventoryDetailAPI.getInventoryDetails(params);
    
    // 如果在请求期间有新的 replace 请求发起，则丢弃当前过期请求的结果
    if (currentId !== materialRequestId.value && mode === 'replace') {
      return;
    }

    const newData = response.data.map(item => ({
      ...item,
      addQuantity: item.quantity > 0 ? 1 : 0
    }));

    const tableEl = materialTableRef.value?.$el;
    const scrollWrapper = tableEl?.querySelector('.el-scrollbar__wrap') || tableEl?.querySelector('.el-table__body-wrapper');
    
    // 记录加载前的滚动高度，用于向上加载时的位置补偿
    const oldScrollHeight = scrollWrapper?.scrollHeight || 0;
    const oldScrollTop = scrollWrapper?.scrollTop || 0;

    if (mode === 'append') {
      // 向下追加：如果超过限制，删除顶部
      if (materialList.value.length + newData.length > MAX_MATERIAL_ITEMS) {
        // 智能修剪：检查高亮项是否在准备删除的 20 项内
        const highlightedIndex = materialList.value.findIndex(item => (item.detail_id || item.batch_id) === highlightedMaterialId.value);
        if (highlightedIndex === -1 || highlightedIndex >= 20) {
          materialList.value.splice(0, 20);
          materialFirstPage.value += 2;
        }
      }
      materialList.value = [...materialList.value, ...newData];
      materialLastPage.value = page;
    } else if (mode === 'prepend') {
      // 向上追加：如果超过限制，删除底部
      if (materialList.value.length + newData.length > MAX_MATERIAL_ITEMS) {
        // 智能修剪：检查高亮项是否在底部的 20 项内
        const highlightedIndex = materialList.value.findIndex(item => (item.detail_id || item.batch_id) === highlightedMaterialId.value);
        if (highlightedIndex === -1 || highlightedIndex < materialList.value.length - 20) {
          materialList.value.splice(-20);
          materialLastPage.value -= 2;
        }
      }
      materialList.value = [...newData, ...materialList.value];
      materialFirstPage.value = page;
      
      // 向上加载后需要补偿滚动位置
      nextTick(() => {
        if (scrollWrapper) {
          const newScrollHeight = scrollWrapper.scrollHeight;
          scrollWrapper.scrollTop = oldScrollTop + (newScrollHeight - oldScrollHeight);
        }
      });
    } else {
      // 替换
      materialList.value = newData;
      materialFirstPage.value = page;
      materialLastPage.value = page;
    }
    
    // 如果是最后一页，更新 hasMore
    if (mode !== 'prepend') {
      materialHasMore.value = newData.length === pageSize;
    }
    
    // 增量更新库存管理变量
    if (mode === 'replace') {
      if (isEdit.value) {
        updateStockManagementForEdit();
      } else {
        initStockManagement();
      }
    } else {
      // 追加模式下增量添加库存信息
      newData.forEach(material => {
        if (material.batch_id !== undefined && !stockManagement.value.has(material.batch_id)) {
          // 编辑模式和新建模式都直接使用真实库存
          // 编辑模式下由于实时写入数据库，后端返回的就是真实可用库存
          stockManagement.value.set(material.batch_id, {
            batch_id: material.batch_id,
            available_quantity: material.quantity,
            original_quantity: material.quantity
          });
        }
      });
    }
  } catch (error: any) {
    const errorMessage = error.response?.data?.message || error.message || '获取器材列表失败';
    ElMessage.error(`获取器材列表失败: ${errorMessage}`);
  } finally {
    loadingMoreMaterials.value = false;
  }
};

// 处理器材筛选变化（关键词搜索）
let searchTimeout: NodeJS.Timeout | null = null;
const handleMaterialFilterChange = async () => {
  // 如果输入了搜索内容，自动清空定位器材输入框
  if (materialFilter.keyword) {
    materialLocateCode.value = '';
    highlightedMaterialId.value = null;
  }
  
  // 防抖处理，避免频繁请求
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  searchTimeout = setTimeout(() => {
    getMaterialList();
  }, 500);
};

// 监听专业筛选变化，实现级联筛选
const handleMajorFilterChange = async (values: string[]) => {
  if (!values || values.length === 0) {
    // 当取消专业筛选时，重置装备筛选并获取所有器材
    materialFilter.major_id = undefined;
    materialFilter.equipment_id = undefined;
    // 重新生成装备筛选器（显示所有装备）
    await getEquipments();
    await getMaterialList();
    return;
  }
  
  // 由于后端API不支持多选，这里只取第一个选中的专业
  const selectedMajor = majorOptions.value.find(opt => opt.label === values[0]);
  if (selectedMajor) {
    materialFilter.major_id = selectedMajor.value;
    materialFilter.equipment_id = undefined;
    
    // 根据专业获取对应的装备列表
    await getEquipmentsByMajor(selectedMajor.value);
    // 重新获取器材清单
    await getMaterialList();
  }
};

// 监听装备筛选变化
const handleEquipmentFilterChange = async (values: string[]) => {
  if (!values || values.length === 0) {
    // 当取消装备筛选时，重置装备筛选条件
    materialFilter.equipment_id = undefined;
    await getMaterialList();
    return;
  }
  
  // 由于后端API不支持多选，这里只取第一个选中的装备
  const selectedEquipment = equipmentOptions.value.find(opt => opt.label === values[0]);
  if (selectedEquipment) {
    materialFilter.equipment_id = selectedEquipment.value;
    await getMaterialList();
  }
};

// 处理表格筛选变化事件
const handleTableFilterChange = (filters: any) => {
  // 处理专业筛选变化
  if (filters.major_name && filters.major_name.length > 0) {
    handleMajorFilterChange(filters.major_name);
  } else {
    // 清除专业筛选状态
    materialFilter.major_id = undefined;
    materialFilter.equipment_id = undefined;
    // 重新获取所有装备和器材
    getEquipments().then(() => getMaterialList());
  }
  
  // 处理装备筛选变化
  if (filters.equipment_name && filters.equipment_name.length > 0) {
    handleEquipmentFilterChange(filters.equipment_name);
  } else {
    // 清除装备筛选状态
    materialFilter.equipment_id = undefined;
    getMaterialList();
  }
};

// 清除表格筛选状态
const clearTableFilters = () => {
  // 清除筛选条件
  materialFilter.major_id = undefined;
  materialFilter.equipment_id = undefined;
  materialFilter.keyword = '';
  
  // 重新获取所有装备和器材
  getEquipments().then(() => getMaterialList());
};

// 专业字段筛选函数 - 处理专业筛选变化
const filterMajorMethod = (values: string[], row: any) => {
  // 只进行本地筛选，不调用API
  if (!values || values.length === 0) {
    return true; // 显示所有行
  }
  
  return values.includes(row.major_name);
};

// 装备字段筛选函数 - 处理装备筛选变化
const filterEquipmentMethod = (values: string[], row: any) => {
  // 只进行本地筛选，不调用API
  if (!values || values.length === 0) {
    return true; // 显示所有行
  }
  
  return values.includes(row.equipment_name);
};

// 加载更多器材
const loadMoreMaterials = () => {
  if (materialHasMore.value && !loadingMoreMaterials.value) {
    getMaterialList(materialLastPage.value + 1, 'append');
  }
};

// 加载前一页器材
const loadPreviousMaterials = () => {
  if (materialFirstPage.value > 1 && !loadingMoreMaterials.value) {
    getMaterialList(materialFirstPage.value - 1, 'prepend');
  }
};

// 滚动事件处理函数
const handleTableScroll = (event: any) => {
  const { scrollTop, scrollHeight, clientHeight } = event.target;
  
  // 触底加载下一页
  if (scrollTop + clientHeight >= scrollHeight - 15) {
    loadMoreMaterials();
  }
  
  // 触顶加载前一页
  if (scrollTop <= 5) {
    loadPreviousMaterials();
  }
};

// 初始化表格滚动监听（用于无限滚动）
const initTableScroll = () => {
  // 使用递归重试确保 DOM 已挂载
  const tryInit = (count = 0) => {
    if (count > 10) return; // 最多重试 10 次
    
    nextTick(() => {
      if (!materialTableRef.value) {
        setTimeout(() => tryInit(count + 1), 200);
        return;
      }
      
      const tableEl = materialTableRef.value.$el;
      // Element Plus 3.x 滚动容器可能是 .el-scrollbar__wrap 或 .el-table__body-wrapper
      const scrollWrapper = tableEl.querySelector('.el-scrollbar__wrap') || 
                           tableEl.querySelector('.el-table__body-wrapper');
      
      if (scrollWrapper) {
        scrollWrapper.removeEventListener('scroll', handleTableScroll);
        scrollWrapper.addEventListener('scroll', handleTableScroll);
      } else {
        setTimeout(() => tryInit(count + 1), 200);
      }
    });
  };
  tryInit();
};

// 器材定位输入变化处理
const handleLocateInputChange = (value: string) => {
  if (value) {
    // 如果输入了定位码，自动清空器材搜索框
    materialFilter.keyword = '';
    highlightedMaterialId.value = null;
  }
};

// 器材定位处理
const handleMaterialLocate = async () => {
  if (!materialLocateCode.value || !materialLocateCode.value.trim()) {
    ElMessage.warning('请输入批次编号');
    return;
  }

  try {
    locating.value = true;
    const pageSize = 10;
    
    // 调用定位接口
    const result = await inventoryDetailAPI.locate({
      batch_number: materialLocateCode.value,
      page_size: pageSize
    });
    
    if (result.target_page !== null) {
      isLocatingScroll.value = true;
      
      // 清除筛选条件，显示全部器材
      materialFilter.keyword = '';
      materialFilter.major_id = undefined;
      materialFilter.equipment_id = undefined;
      
      // 使用定位返回的页码进行加载
      await getMaterialList(result.target_page);
      
      // 如果定位的器材在页面后半部分，则多加载一页
      if (result.position !== null) {
        const positionInPage = ((result.position - 1) % 10) + 1;
        if (positionInPage > 5 && materialHasMore.value) {
          await getMaterialList(result.target_page + 1, 'append');
        }
      }
      
      if (result.found && result.detail_id) {
        // 先设置高亮
        highlightedMaterialId.value = result.detail_id;
        
        // 等待 DOM 完全渲染后再滚动
        await nextTick();
        await nextTick(); // 双重 nextTick 确保 DOM 完全更新
        
        const targetDetailId = result.detail_id;
        // 延迟一小段时间，确保表格渲染和高亮样式都已应用
        setTimeout(() => {
          scrollToTargetMaterial(targetDetailId);
          ElMessage.success(`已定位到: ${result.material_name} (位置: ${result.position})`);
          
          // 等待平滑滚动完成后解除锁定
          setTimeout(() => {
            isLocatingScroll.value = false;
          }, 800);
        }, 100);

        // 20秒后移除高亮
        setTimeout(() => {
          if (highlightedMaterialId.value === targetDetailId) {
            highlightedMaterialId.value = null;
          }
        }, 20000);
      } else {
        isLocatingScroll.value = false;
        ElMessage.info('已返回第1页');
      }
    } else {
      ElMessage.warning(`未找到批次编号: ${materialLocateCode.value}`);
    }
  } catch (error: any) {
    isLocatingScroll.value = false;
    const errorMessage = error.response?.data?.detail || error.message || '定位失败';
    ElMessage.error(`器材定位失败: ${errorMessage}`);
  } finally {
    locating.value = false;
  }
};

// 滚动到目标器材
const scrollToTargetMaterial = (detailId: number) => {
  if (!materialTableRef.value) return;
  
  const index = materialList.value.findIndex(item => item.detail_id === detailId);
  if (index === -1) return;
  
  const tableEl = materialTableRef.value.$el;
  const tableBody = tableEl.querySelector('.el-table__body-wrapper');
  
  if (tableBody) {
    const rows = tableBody.querySelectorAll('.el-table__row');
    if (rows[index]) {
      rows[index].scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  }
};

// 清除定位
const handleMaterialLocateClear = async () => {
  highlightedMaterialId.value = null;
  materialLocateCode.value = '';
  await getMaterialList(1);
  
  nextTick(() => {
    if (materialTableRef.value) {
      const tableEl = materialTableRef.value.$el;
      const scrollWrapper = tableEl.querySelector('.el-scrollbar__wrap') || 
                           tableEl.querySelector('.el-table__body-wrapper');
      if (scrollWrapper) {
        scrollWrapper.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }
  });
};

// 获取表格行类名（用于高亮）
const getRowClassName = ({ row }: { row: any }) => {
  return row.detail_id === highlightedMaterialId.value ? 'highlighted-row' : '';
};

// 打开器材选择抽屉
const openMaterialDrawer = () => {
  // 查看模式下不允许打开器材选择抽屉
  if (props.readonly) {
    ElMessage.warning('查看模式下不允许添加器材');
    return;
  }
  
  materialDrawerVisible.value = true;
  // 清除筛选状态，确保每次打开都是全新的筛选
  clearTableFilters();
  
  // 初始化器材列表滚动监听
  initTableScroll();
};

// 关闭抽屉
const handleDrawerClose = (done: () => void) => {
  done()
};

// 添加器材到出库明细
const addMaterialItem = async (material: InventoryDetailResponse & { addQuantity: number }) => {
  try {
    // 验证数量
    if (!material.addQuantity || material.addQuantity <= 0) {
      ElMessage.warning('请输入有效的数量');
      return;
    }
    
    // 检查输入数量是否超过实际库存
    if (material.addQuantity > material.quantity) {
      ElMessage.error(`输入数量 ${material.addQuantity} 超过实际库存 ${material.quantity}，请重新输入`);
      return;
    }
    
    // 检查是否已存在相同批次编号的器材
    const existingItemIndex = orderItems.value.findIndex(item => 
      item.batch_id === material.batch_id
    );
    
    if (existingItemIndex !== -1) {
      // 如果已存在，则合并数量（删除新项，把数量加到现有项上）
      const existingItem = orderItems.value[existingItemIndex];
      const newQuantity = existingItem.quantity + material.addQuantity;
      
      // 检查库存是否充足
      const stockInfo = stockManagement.value.get(material.batch_id!);
      const availableStock = stockInfo ? stockInfo.original_quantity : material.quantity;
      
      if (isEdit.value) {
        // 编辑模式：只检查新增数量是否超过真实库存（已出库的数量已在数据库中）
        if (material.addQuantity > availableStock) {
          ElMessage.error(`新增数量 ${material.addQuantity} 超过可用库存 ${availableStock}，无法添加`);
          return;
        }
      } else {
        // 新建模式：检查合并后总数量是否超过真实库存
        if (newQuantity > availableStock) {
          ElMessage.error(`合并后数量 ${newQuantity} 超过可用库存 ${availableStock}，无法添加`);
          return;
        }
      }
      
      // 如果是编辑模式，实时更新明细项数量
      if (isEdit.value && orderId.value && existingItem.detail_id !== undefined) {
        try {
          await outboundOrderAPI.updateOutboundOrderItem(orderId.value, existingItem.detail_id, {
            batch_id: material.batch_id,
            quantity: newQuantity
          });
          
          // 后端更新成功后再显示合并提示
          ElMessage.success(`已存在相同批次号器材，数量已合并：${existingItem.quantity} + ${material.addQuantity} = ${newQuantity}`);
        } catch (error: any) {
          // 优先处理detail字段中的详细信息
          if (error.response?.data?.detail) {
            const detail = error.response.data.detail;
            let errorMessage = '器材数量更新失败';
            
            // 判断detail是字符串还是对象
            if (typeof detail === 'string') {
              // detail是字符串，直接显示
              errorMessage = detail;
            } else if (typeof detail === 'object' && detail !== null) {
              // detail是对象，处理message字段和problematic_items
              errorMessage = detail.message || '器材数量更新失败';
              
              // 如果有问题器材列表，添加到错误信息中
              if (detail.problematic_items && detail.problematic_items.length > 0) {
                errorMessage += '\n\n无法更新数量，原因：\n';
                detail.problematic_items.forEach((problem: any) => {
                  errorMessage += `- ${problem.reason || '未知原因'}\n`;
                });
              }
            }
            
            ElMessage.error(errorMessage);
          } else {
            // 如果没有detail字段，使用原来的逻辑
            const errorMessage = error.response?.data?.message || error.message || '器材数量更新失败';
            ElMessage.error(`器材数量更新失败: ${errorMessage}`);
          }
          return;
        }
      } else {
        // 新建模式下直接显示合并提示
        ElMessage.success(`已存在相同批次号器材，数量已合并：${existingItem.quantity} + ${material.addQuantity} = ${newQuantity}`);
      }
      
      // 更新现有项的数量（相当于删除新项，把数量加到现有项上）
      orderItems.value[existingItemIndex].quantity = newQuantity;
      
      // 更新库存管理变量（减去新增的数量）
      updateStockOnAdd(material.batch_id!, material.addQuantity);
    } else {
      // 如果不存在，则添加新项
      // 检查batch_id是否存在
      if (material.batch_id === undefined) {
        ElMessage.error('批次ID不存在，无法添加器材');
        return;
      }
      
      const newItem: ExtendedOutboundOrderItem = {
        batch_id: material.batch_id,
        quantity: material.addQuantity,
        detail_id: material.detail_id,
        material_code: material.material_code,
        material_name: material.material_name,
        material_specification: material.material_specification,
        unit_price: material.unit_price,
        unit: material.unit,
        batch_number: material.batch_number,
        bin_name: material.bin_name,
        equipment_name: material.equipment_name,
        addQuantity: material.addQuantity
      };
      
      // 如果是编辑模式，调用API添加明细项
      if (isEdit.value && orderId.value) {
        // 检查batch_id是否存在
        if (material.batch_id === undefined) {
          ElMessage.error('批次ID不存在，无法添加器材');
          return;
        }
        
        try {
          const result = await outboundOrderAPI.addOutboundOrderItem(orderId.value, {
            batch_id: material.batch_id,
            quantity: material.addQuantity
          });
          
          // 将后端返回的item_id赋值给newItem.detail_id
          newItem.detail_id = result.item_id;
        } catch (error: any) {
          // 显示具体的错误原因
          const errorMessage = error.response?.data?.message || error.message || '器材添加失败';
          ElMessage.error(`器材添加失败: ${errorMessage}`);
          return;
        }
      }
      
      // 添加到明细列表
      orderItems.value.push(newItem);
      
      // 更新库存管理变量（减去新增的数量）
      updateStockOnAdd(material.batch_id!, material.addQuantity);
      
      console.log('添加明细项:', newItem);
    }
    
    // 重置数量输入框
    material.addQuantity = 1;
    
    ElMessage.success('器材添加成功');
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '添加器材失败';
    ElMessage.error(`添加器材失败: ${errorMessage}`);
  }
};

// 删除出库明细项
const removeItem = async (index: number) => {
  // 如果正在删除中，直接返回（按钮已禁用，这里做二次防护）
  if (deleting.value) {
    return;
  }
  
  const item = orderItems.value[index];
  
  // 如果是编辑模式，调用API删除明细项
  if (isEdit.value && orderId.value && item.detail_id) {
    try {
      deleting.value = true;
      await outboundOrderAPI.deleteOutboundOrderItem(orderId.value, item.detail_id);
      
      // API删除成功后，执行本地删除
      // 更新库存管理变量（恢复删除的数量）
      if (item.batch_id) {
        updateStockOnRemove(item.batch_id, item.quantity);
      }
      
      orderItems.value.splice(index, 1);
      
      // 删除后调整页码，确保当前页有效
      adjustPageAfterDelete();
      
      ElMessage.success('明细项删除成功');
    } catch (error: any) {
      // 处理后端返回的错误信息（当前API返回字符串格式）
      const errorMessage = error.response?.data?.detail 
        || error.response?.data?.message 
        || error.message 
        || '明细项删除失败';
      ElMessage.error(errorMessage);
    } finally {
      deleting.value = false;
    }
  } else {
    // 新增模式：直接在前端移除
    // 更新库存管理变量（恢复删除的数量）
    if (item.batch_id) {
      updateStockOnRemove(item.batch_id, item.quantity);
    }
    
    orderItems.value.splice(index, 1);
    
    // 删除后调整页码，确保当前页有效
    adjustPageAfterDelete();
  }
};

// 删除后调整页码
const adjustPageAfterDelete = () => {
  // 计算删除后的总页数
  const totalPages = Math.ceil(orderItems.value.length / pageSize.value);
  
  // 如果当前页超出了总页数，调整到最后一页
  if (currentPage.value > totalPages && totalPages > 0) {
    currentPage.value = totalPages;
  }
  
  // 如果删除后没有数据，重置到第1页
  if (orderItems.value.length === 0) {
    currentPage.value = 1;
  }
};



// 定义事件
const emit = defineEmits<{
  back: []
  saved: []
}>();

// 返回出库单列表
const handleBack = () => {
  // 新增模式：草稿已自动保存，直接返回即可
  // 下次进入新建页面时会提示恢复草稿
  emit('back');
};

// 出库单号变更处理（实时保存）
const handleOrderNumberChange = async () => {
  // 如果是由日期变更触发的单号更新，不执行后续逻辑
  if (isDateTriggeringOrderNumber.value) {
    return;
  }
  
  if (isEdit.value && orderId.value && orderForm.order_number) {
    // 检查出库单号是否真的发生了更改
    if (orderForm.order_number === originalOrderForm.order_number) {
      // 出库单号没有变化，不需要调用API
      return;
    }
    
    try {
      await outboundOrderAPI.updateOrderNumber(orderId.value, { order_number: orderForm.order_number });
      // 更新成功后，保存当前出库单号作为新的原始值
      originalOrderForm.order_number = orderForm.order_number;
      ElMessage.success('出库单号更新成功');
    } catch (error: any) {
      // 显示具体的错误原因
      const errorMessage = error.response?.data?.message || error.message || '出库单号更新失败';
      ElMessage.error(`出库单号更新失败: ${errorMessage}`);
    }
  }
};

// 客户变更处理（实时保存）
const handleCustomerChange = async () => {
  if (isEdit.value && orderId.value && orderForm.customer_id) {
    // 检查客户是否真的发生了更改
    if (orderForm.customer_id === originalOrderForm.customer_id) {
      // 客户没有变化，不需要调用API
      return;
    }
    
    try {
      await outboundOrderAPI.updateCustomer(orderId.value, { customer_id: orderForm.customer_id });
      // 更新成功后，保存当前客户作为新的原始值
      originalOrderForm.customer_id = orderForm.customer_id;
      ElMessage.success('客户信息更新成功');
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = detail.message || '客户信息更新失败';
        
        // 如果有问题器材列表，添加到错误信息中
        if (detail.problematic_items && detail.problematic_items.length > 0) {
          errorMessage += '\n\n无法更新客户信息，原因：\n';
          detail.problematic_items.forEach((problem: any) => {
            errorMessage += `- ${problem.reason || '未知原因'}\n`;
          });
        }
        
        ElMessage.error(errorMessage);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '客户信息更新失败';
        ElMessage.error(`客户信息更新失败: ${errorMessage}`);
      }
    }
  }
};

// 调拨单号变更处理（实时保存）
const handleTransferNumberChange = async () => {
  if (isEdit.value && orderId.value) {
    // 检查调拨单号是否真的发生了更改
    if (orderForm.requisition_reference === originalOrderForm.requisition_reference) {
      // 调拨单号没有变化，不需要调用API
      return;
    }
    
    try {
      await outboundOrderAPI.updateTransferNumber(orderId.value, { requisition_reference: orderForm.requisition_reference || '' });
      // 更新成功后，保存当前调拨单号作为新的原始值
      originalOrderForm.requisition_reference = orderForm.requisition_reference || '';
      ElMessage.success('调拨单号更新成功');
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = detail.message || '调拨单号更新失败';
        
        // 如果有问题器材列表，添加到错误信息中
        if (detail.problematic_items && detail.problematic_items.length > 0) {
          errorMessage += '\n\n无法更新调拨单号，原因：\n';
          detail.problematic_items.forEach((problem: any) => {
            errorMessage += `- ${problem.reason || '未知原因'}\n`;
          });
        }
        
        ElMessage.error(errorMessage);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '调拨单号更新失败';
        ElMessage.error(`调拨单号更新失败: ${errorMessage}`);
      }
    }
  }
};

// 标记：是否由出库日期变更触发的单号更新（防止递归）
const isDateTriggeringOrderNumber = ref(false);

// 出库日期变更处理（实时保存）
const handleOutboundDateChange = async () => {
  // 同步更新出库单号中的日期部分
  if (orderForm.outbound_date && orderForm.order_number) {
    updateOrderNumberDate(orderForm.outbound_date);
  }
  
  if (isEdit.value && orderId.value && orderForm.outbound_date) {
    // 检查出库日期是否真的发生了更改
    if (orderForm.outbound_date === originalOrderForm.outbound_date) {
      // 出库日期没有变化，不需要调用API
      return;
    }
    
    try {
      // 调用更新出库单创建时间的API
      await outboundOrderAPI.updateCreateTime(orderId.value, { 
        create_time: orderForm.outbound_date + ' 00:00:00' 
      });
      // 更新成功后，保存当前出库日期作为新的原始值
      originalOrderForm.outbound_date = orderForm.outbound_date;
      ElMessage.success('出库日期已更新');
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = detail.message || '出库日期更新失败';
        
        // 如果有问题器材列表，添加到错误信息中
        if (detail.problematic_items && detail.problematic_items.length > 0) {
          errorMessage += '\n\n无法更新出库日期，原因：\n';
          detail.problematic_items.forEach((problem: any) => {
            errorMessage += `- ${problem.reason || '未知原因'}\n`;
          });
        }
        
        ElMessage.error(errorMessage);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '出库日期更新失败';
        ElMessage.error(`出库日期更新失败: ${errorMessage}`);
      }
    }
  }
};

// 更新出库单号中的日期部分
const updateOrderNumberDate = async (newDate: string) => {
  if (!orderForm.order_number || isDateTriggeringOrderNumber.value) {
    return;
  }
  
  // 出库单号格式: CK20231225-001
  // 匹配格式: CK + 8位数字(YYYYMMDD) + - + 3位数字
  const orderNumberPattern = /^(CK)(\d{8})(-.+)$/;
  const match = orderForm.order_number.match(orderNumberPattern);
  
  if (match) {
    // 将日期格式从 YYYY-MM-DD 转换为 YYYYMMDD
    const dateStr = newDate.replace(/-/g, '');
    
    // 检查日期格式是否正确（8位数字）
    if (dateStr.length === 8 && /^\d{8}$/.test(dateStr)) {
      try {
        // 设置标记，防止触发handleOrderNumberChange
        isDateTriggeringOrderNumber.value = true;
        
        // 调用后端API重新生成出库单号，避免重复单号
        const response = await outboundOrderAPI.generateOutboundOrderNumber(dateStr);
        const newOrderNumber = response.order_number;
        
        orderForm.order_number = newOrderNumber;
        
        // 如果是编辑模式，需要调用API将新单号写入数据库
        if (isEdit.value && orderId.value) {
          try {
            await outboundOrderAPI.updateOrderNumber(orderId.value, { order_number: newOrderNumber });
            // 数据库更新成功后，同步更新原始值
            originalOrderForm.order_number = newOrderNumber;
            ElMessage.success('出库单号已更新');
          } catch (updateError: any) {
            // 数据库更新失败，恢复原单号
            const updateErrorMessage = updateError.response?.data?.message || updateError.message || '出库单号写入数据库失败';
            ElMessage.error(`出库单号更新失败: ${updateErrorMessage}`);
            // 恢复原单号
            orderForm.order_number = originalOrderForm.order_number;
          }
        } else {
          // 新增模式，只更新前端表单
          originalOrderForm.order_number = newOrderNumber;
        }
        
        // 延迟重置标记
        setTimeout(() => {
          isDateTriggeringOrderNumber.value = false;
        }, 100);
      } catch (error: any) {
        // 如果API调用失败，显示错误但不影响日期更新
        console.error('重新生成出库单号失败:', error);
        const errorMessage = error.response?.data?.message || error.message || '重新生成出库单号失败';
        ElMessage.warning(`出库单号更新失败: ${errorMessage}，请手动修改`);
        
        // 重置标记
        isDateTriggeringOrderNumber.value = false;
      }
    }
  }
};


// 数量变更处理（实时更新）
const handleQuantityChange = async (index: number) => {
  if (isEdit.value && orderId.value && orderItems.value[index]) {
    const item = orderItems.value[index];
    
    // 检查数量是否真的发生了更改
    if (item.originalQuantity !== undefined && item.quantity === item.originalQuantity) {
      // 数量没有变化，不需要调用API
      return;
    }
    
    try {
      await outboundOrderAPI.updateOutboundOrderItem(orderId.value, item.detail_id!, {
        batch_id: item.batch_id,
        quantity: item.quantity
      });
      
      // 更新成功后，保存当前数量作为新的原始数量
      item.originalQuantity = item.quantity;
      
      ElMessage.success('数量更新成功');
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = '数量更新失败';
        
        // 判断detail是字符串还是对象
        if (typeof detail === 'string') {
          // detail是字符串，直接显示
          errorMessage = detail;
        } else if (typeof detail === 'object' && detail !== null) {
          // detail是对象，处理message字段和problematic_items
          errorMessage = detail.message || '数量更新失败';
          
          // 如果有问题器材列表，添加到错误信息中
          if (detail.problematic_items && detail.problematic_items.length > 0) {
            errorMessage += '\n\n无法更新数量，原因：\n';
            detail.problematic_items.forEach((problem: any) => {
              errorMessage += `- ${problem.reason || '未知原因'}\n`;
            });
          }
        }
        
        ElMessage.error(errorMessage);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '数量更新失败';
        ElMessage.error(`数量更新失败: ${errorMessage}`);
      }
    }
  }
};

// 强制更新冗余字段
const handleForceUpdate = async () => {
  if (!orderId.value) {
    ElMessage.warning('无法获取出库单ID');
    return;
  }
  
  try {
    await ElMessageBox.confirm(
      '此操作将根据入库明细表更新出库明细中的器材编码、名称、规格、单价、单位等字段，是否继续？',
      '确认强制更新',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    );
    
    updating.value = true;
    const result = await outboundOrderAPI.updateRedundantFields(orderId.value);
    
    if (result.success) {
      ElMessage.success(result.message);
      
      // 如果有未找到的批次，显示警告
      if (result.not_found_batches && result.not_found_batches.length > 0) {
        ElMessage.warning(`以下批次ID未找到对应的入库明细: ${result.not_found_batches.join(', ')}`);
      }
      
      // 重新加载出库单详情以显示更新后的数据
      await loadOrderDetail();
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      const errorMessage = error.response?.data?.message || error.message || '强制更新失败';
      ElMessage.error(`强制更新失败: ${errorMessage}`);
    }
  } finally {
    updating.value = false;
  }
};

// 保存出库单
const handleSave = async () => {
  // 验证表单
  if (!orderFormRef.value) return;
  
  // 验证表单 - 确保出库单号、日期及客户不能为空
  const valid = await orderFormRef.value.validate();
  if (!valid) {
    ElMessage.warning('请填写必填字段：出库单号、出库日期、客户');
    return;
  }
  
  // 验证明细
  if (orderItems.value.length === 0) {
    ElMessage.warning('请至少添加一条出库明细');
    return;
  }
  
  try {
    
    saving.value = true;
    // 构建出库单数据 - 只包含API需要的字段
    const orderData: OutboundOrderCreate = {
      ...orderForm,
      customer_id: orderForm.customer_id || 0, // 确保customer_id不为null
      items: orderItems.value.map(item => ({
        batch_id: item.batch_id,
        quantity: item.quantity
      }))
    };
    console.log("提交的器材出库信息：", orderData);
    
    if (isEdit.value && orderId.value) {
    } else {
      // 新增出库单
      await outboundOrderAPI.createOutboundOrder(orderData);
      ElMessage.success('出库单创建成功');
      // 保存成功后清除草稿
      clearDraft(DRAFT_KEY);
    }
    
    // 保存成功后立即触发保存事件
    emit('saved');
    
  } catch (error: any) {
    // 优先处理detail字段中的详细信息
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      let errorMessage = '保存出库单失败';
      
      // 处理detail为对象的情况
      if (typeof detail === 'object') {
        errorMessage = detail.message || errorMessage;
        
        // 如果有问题器材列表，添加到错误信息中
        if (detail.problematic_items && detail.problematic_items.length > 0) {
          errorMessage += '\n\n无法保存出库单，原因：\n';
          detail.problematic_items.forEach((problem: any) => {
            errorMessage += `- ${problem.reason || '未知原因'}\n`;
          });
        }
      } 
      // 处理detail为字符串的情况
      else if (typeof detail === 'string') {
        errorMessage = detail;
      }
      
      ElMessage.error(errorMessage);
    } else {
      // 如果没有detail字段，使用原来的逻辑
      ElMessage.error(error.response?.data?.message || '保存出库单失败');
    }
  } finally {
    saving.value = false;
  }
};

// 初始化数据
const initData = async () => {
  await getCustomers();
  await getMajors();
  await getEquipments();
};

// 组件挂载时初始化数据
onMounted(() => {
  initData();
});
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';

/* 数量输入框错误样式 */
.quantity-error {
  :deep(.el-input__wrapper) {
    border-color: #f56c6c !important;
    box-shadow: 0 0 0 1px #f56c6c !important;
  }
}

/* 库存不足标红样式 */
.insufficient-stock {
  color: #f56c6c !important;
  font-weight: bold;
}

:deep(.el-input-number.insufficient-stock .el-input__wrapper) {
  border: 1px solid #f56c6c !important;
  box-shadow: 0 0 0 1px #f56c6c inset !important;
}

/* 确保聚焦状态下也显示红色边框 */
:deep(.el-input-number.insufficient-stock .el-input__wrapper:hover),
:deep(.el-input-number.insufficient-stock .el-input__wrapper:focus),
:deep(.el-input-number.insufficient-stock.is-focus .el-input__wrapper) {
  border: 1px solid #f56c6c !important;
  box-shadow: 0 0 0 1px #f56c6c inset !important;
}

/* 使用现代Sass混入 */
@include mixins.table-sort-arrows;




.base-form-actions {
  margin-top: 5px;
  margin-bottom: 5px;
  text-align: center;
  
  .el-button {
    margin: 0 10px;
  }
}

.material-drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  
  .drawer-filter {
    margin-bottom: 20px;
    flex-shrink: 0; // 防止筛选器被压缩
  }
  
  .drawer-table {
    flex: 1;
    min-height: 0; // 关键：让flex子元素能正确计算高度
    display: flex;
    flex-direction: column;
    
    :deep(.el-table) {
      flex: 1;
      display: flex;
      flex-direction: column;
      
      .el-table__inner-wrapper {
        flex: 1;
        display: flex;
        flex-direction: column;
      }
      
      .el-table__body-wrapper {
        flex: 1;
        overflow-y: auto;
      }
    }
  }
}

/* 选择器材对话框标题样式 - 移除默认padding和margin */
:deep(.el-drawer__header) {
  margin-bottom: 0 !important;
}

:deep(.el-drawer__title) {
  margin: 0 !important;
  padding: 0 !important;
}

/* 器材定位高亮样式 - 增强视觉效果并覆盖斑马纹 */
:deep(.el-table__row.highlighted-row) {
  background: linear-gradient(90deg, #ffd700 0%, #fff9e6 50%, #ffffff 100%) !important;
  border-left: 4px solid #ff6b00 !important;
  box-shadow: 0 0 15px rgba(255, 107, 0, 0.3) !important;
  animation: highlight-pulse 1s ease-in-out infinite;
  position: relative;
  z-index: 10 !important;
}

/* 确保高亮行的单元格背景也被覆盖 */
:deep(.el-table__row.highlighted-row > td) {
  background: transparent !important;
  font-weight: 600 !important;
  color: #333 !important;
}

/* 覆盖斑马纹样式 */
:deep(.el-table--striped .el-table__row.highlighted-row.el-table__row--striped > td) {
  background: transparent !important;
}

@keyframes highlight-pulse {
  0%, 100% { 
    background: linear-gradient(90deg, #ffd700 0%, #fff9e6 50%, #ffffff 100%);
  }
  50% { 
    background: linear-gradient(90deg, #ffed4e 0%, #fffbf0 50%, #ffffff 100%);
  }
}
</style>