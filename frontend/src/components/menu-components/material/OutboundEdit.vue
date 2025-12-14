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
                placeholder="选择客户"
                filterable
                style="width: 100%"
                :disabled="props.readonly"
                @change="handleCustomerChange"
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
          </div>
        </div>
      </template>

      <div class="base-table base-table--auto-height">
        <el-table
          :data="orderItems"
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
        />
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
          min-width="100" 
          align="center" 
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
              @change="handleQuantityChange($index)"
              :class="{ 'insufficient-stock': row.batch_id && !checkStockSufficient(row.batch_id, row.quantity) }"
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
          prop="bin_name" 
          label="货位" 
          width="100" 
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
              @click="removeItem($index)"
              :icon="Delete"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
        </el-table>
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
      size="60%"
      :before-close="handleDrawerClose"
    >
      <div class="material-drawer-content">
        <!-- 筛选器 -->
        <div class="drawer-filter">
          <el-row :gutter="10">
            <el-col :span="24">
              <el-input
                v-model="materialFilter.keyword"
                placeholder="输入器材编码、名称、规格搜索"
                clearable
                @clear="handleMaterialFilterChange"
                @input="handleMaterialFilterChange"
              />
            </el-col>
          </el-row>
        </div>

        <!-- 器材列表 -->
        <div class="drawer-table">
          <el-table
            :data="materialList"
            stripe
            border
            height="250"
            :empty-text="'暂无器材数据'"
            class="base-table"
            @filter-change="handleTableFilterChange"
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
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { ElMessage } from 'element-plus';

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
  ShoppingCart
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

const isEdit = ref(false);
const orderId = ref<number | null>(null);
const saving = ref(false);
const materialDrawerVisible = ref(false);

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
      stockManagement.value.set(item.item_id, {
        batch_id: item.batch_id,
        // 在编辑模式下，初始可用库存等于当前出库数量（假设库存充足）
        // 后续打开器材选择抽屉时会重新计算准确的可用库存
        available_quantity: item.quantity,
        original_quantity: item.quantity
      });
    });
    
    // 在编辑模式下，加载器材列表后更新库存管理变量为准确值
    if (isEdit.value) {
      await getMaterialList();
      updateStockManagementForEdit();
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
const resetForm = () => {
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
    console.log('进入新建模式，重置表单');
    resetForm();
  }
}, { immediate: true });

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
    return sum + (item.quantity * (item.unit_price || 0));
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

// 更新库存管理变量（编辑模式）
const updateStockManagementForEdit = () => {
  stockManagement.value.clear();
  
  // 首先为出库明细中的所有器材初始化库存信息
  orderItems.value.forEach(item => {
    if (item.batch_id !== undefined) {
      // 初始可用库存等于当前出库数量（假设库存充足）
      stockManagement.value.set(item.batch_id, {
        batch_id: item.batch_id,
        available_quantity: item.quantity,
        original_quantity: item.quantity // 添加原始库存
      });
    }
  });
  
  // 然后为器材列表中的器材更新准确的库存信息
  materialList.value.forEach(material => {
    if (material.batch_id !== undefined) {
      // 获取当前出库单中该器材的数量
      const orderItemQuantity = orderItems.value
        .filter(item => item.batch_id === material.batch_id)
        .reduce((sum, item) => sum + (item.quantity || 0), 0);
      
      // 可用库存 = 真实库存 + 当前出库单中的数量
      const availableQuantity = material.quantity + orderItemQuantity;
      
      stockManagement.value.set(material.batch_id!, {
        batch_id: material.batch_id!,
        available_quantity: availableQuantity,
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
const checkStockSufficient = (batchId: number, quantity: number): boolean => {
  const stockInfo = stockManagement.value.get(batchId);
  console.log('库存信息:', batchId, stockInfo?.available_quantity, '原始库存:', stockInfo?.original_quantity, '输入数量', quantity);
  if (!stockInfo) {
    return false;
  }
  // 检查输入数量是否超过可用库存，并且不能超过原始库存
  return quantity <= stockInfo.original_quantity;
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

// 获取客户列表
const getCustomers = async () => {
  try {
    const result = await customerAPI.getCustomers();
    customerOptions.value = result.data.map((customer: CustomerResponse) => ({
      value: customer.id,
      label: customer.customer_name
    }));
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '获取客户列表失败';
    ElMessage.error(`获取客户列表失败: ${errorMessage}`);
  }
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
const getMaterialList = async () => {
  try {
    // 根据搜索框内容动态设置page_size：搜索框为空时显示5项，有输入时显示20项
    const pageSize = materialFilter.keyword ? 20 : 5;
    
    // 构建查询参数
    const params = {
      page: 1,
      page_size: pageSize,
      keyword: materialFilter.keyword,
      major_id: Array.isArray(materialFilter.major_id) ? materialFilter.major_id : 
                materialFilter.major_id !== undefined ? [materialFilter.major_id] : undefined,
      equipment_id: Array.isArray(materialFilter.equipment_id) ? materialFilter.equipment_id : 
                   materialFilter.equipment_id !== undefined ? [materialFilter.equipment_id] : undefined,
      quantity_filter: 'has_stock' as 'has_stock' // 只显示有库存的器材
    };
    
    const response = await inventoryDetailAPI.getInventoryDetails(params);
    // 为每个器材添加数量输入框，根据实际库存设置合理的默认值
    materialList.value = response.data.map(item => ({
      ...item,
      addQuantity: item.quantity > 0 ? 1 : 0  // 有库存时默认1，无库存时默认0
    }));
    
    // 初始化库存管理变量
    if (isEdit.value) {
      updateStockManagementForEdit();
    } else {
      initStockManagement();
    }
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '获取器材列表失败';
    ElMessage.error(`获取器材列表失败: ${errorMessage}`);
  }
};

// 处理器材筛选变化（关键词搜索）
let searchTimeout: NodeJS.Timeout | null = null;
const handleMaterialFilterChange = async () => {
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
      
      // 检查合并后的数量是否超过库存
      // 计算可用库存：实际库存 + 已出库数量（如果是编辑模式）
      const stockInfo = stockManagement.value.get(material.batch_id!);
      const maxAllowedQuantity = stockInfo ? stockInfo.original_quantity : material.quantity;
      
      if (newQuantity > maxAllowedQuantity) {
        ElMessage.error(`合并后数量 ${newQuantity} 超过可用库存 ${maxAllowedQuantity}，无法添加`);
        return;
      }
      
      // 显示合并提示
      ElMessage.success(`已存在相同批次号器材，数量已合并：${existingItem.quantity} + ${material.addQuantity} = ${newQuantity}`);
      
      // 如果是编辑模式，实时更新明细项数量
      if (isEdit.value && orderId.value && material.batch_id !== undefined) {
        try {
          await outboundOrderAPI.updateOutboundOrderItem(orderId.value, material.batch_id, {
            quantity: newQuantity
          });
        } catch (error: any) {
          // 显示具体的错误原因
          const errorMessage = error.response?.data?.message || error.message || '器材数量更新失败';
          ElMessage.error(`器材数量更新失败: ${errorMessage}`);
          return;
        }
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
          await outboundOrderAPI.addOutboundOrderItem(orderId.value, {
            batch_id: material.batch_id,
            quantity: material.addQuantity
          });
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
  const item = orderItems.value[index];
  
  // 如果是编辑模式，调用API删除明细项
  if (isEdit.value && orderId.value && item.batch_id) {
    try {
      await outboundOrderAPI.deleteOutboundOrderItem(orderId.value, item.batch_id);
      ElMessage.success('明细项删除成功');
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = detail.message || '明细项删除失败';
        
        // 如果有问题器材列表，添加到错误信息中
        if (detail.problematic_items && detail.problematic_items.length > 0) {
          errorMessage += '\n\n无法删除明细项，原因：\n';
          detail.problematic_items.forEach((problem: any) => {
            errorMessage += `- ${problem.reason || '未知原因'}\n`;
          });
        }
        
        ElMessage.error(errorMessage);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '明细项删除失败';
        ElMessage.error(`明细项删除失败: ${errorMessage}`);
      }
      return;
    }
  }
  
  // 更新库存管理变量（恢复删除的数量）
  if (item.batch_id) {
    updateStockOnRemove(item.batch_id, item.quantity);
  }
  
  orderItems.value.splice(index, 1);
};



// 定义事件
const emit = defineEmits<{
  back: []
  saved: []
}>();

// 返回出库单列表
const handleBack = () => {
  // 触发返回事件
  emit('back');
};

// 出库单号变更处理（实时保存）
const handleOrderNumberChange = async () => {
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

// 出库日期变更处理（实时保存）
const handleOutboundDateChange = async () => {
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
      await outboundOrderAPI.updateOutboundOrderItem(orderId.value, item.batch_id, {
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
  border-color: #f56c6c !important;
  box-shadow: 0 0 0 1px #f56c6c !important;
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
  }
  
  .drawer-table {
    flex: 1;
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
</style>