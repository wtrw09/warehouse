<template>
  <div class="base-management-container base-content base-flex-content">
    <!-- 页头 -->
    <el-card class="base-page-header-card" shadow="hover">
      <el-page-header @back="handleBack" class="base-page-header">
        <template #content>
          <div class="base-page-header__content">
            <span class="base-page-header__title">{{ props.readonly ? '查看入库单' : (isEdit ? '编辑入库单' : '新增入库单') }} - {{ orderForm.order_number || '新入库单' }}</span>
          </div>
        </template>
      </el-page-header>
    </el-card>

    <!-- 入库单基本信息 -->
    <el-card class="base-form-card" shadow="hover">

      <el-form :model="orderForm" label-width="120px" :rules="orderRules" ref="orderFormRef">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="入库单号" prop="order_number">
              <el-input 
                v-model="orderForm.order_number" 
                placeholder="自动生成" 
                @change="handleOrderNumberChange"
                :disabled="props.readonly"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="入库日期" prop="inbound_date">
              <el-date-picker
                v-model="orderForm.inbound_date"
                type="date"
                placeholder="选择入库日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                @change="handleInboundDateChange"
                :disabled="props.readonly"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="供应商" prop="supplier_id">
              <!-- 只读模式：直接显示供应商名称 -->
              <el-input
                v-if="props.readonly"
                :value="orderForm.supplier_name"
                placeholder="供应商名称"
                disabled
                style="width: 100%"
              />
              <!-- 编辑模式：显示下拉选择器 -->
              <el-select
                v-else
                v-model="orderForm.supplier_id"
                placeholder="请选择或搜索供应商"
                filterable
                remote
                :remote-method="remoteSearchSuppliers"
                :loading="supplierLoading"
                style="width: 100%"
                @change="handleSupplierChange"
                @visible-change="bindSupplierScrollListener"
              >
                <!-- 如果当前供应商已被删除，显示为禁用选项 -->
                <el-option
                  v-if="isSupplierDeleted"
                  :key="orderForm.supplier_id"
                  :label="`${orderForm.supplier_name} (已删除)`"
                  :value="orderForm.supplier_id"
                  disabled
                />
                <el-option
                  v-for="supplier in supplierOptions"
                  :key="supplier.value"
                  :label="supplier.label"
                  :value="supplier.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="调拨单号" prop="requisition_reference">
              <el-input 
                v-model="orderForm.requisition_reference" 
                placeholder="请输入调拨单号" 
                @change="handleTransferNumberChange"
                :disabled="props.readonly"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="合同号" prop="contract_reference">
              <el-input 
                v-model="orderForm.contract_reference" 
                placeholder="请输入合同号" 
                @change="handleContractNumberChange"
                :disabled="props.readonly"
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="总数量">
              <el-input 
                :value="totalQuantity" 
                placeholder="自动计算" 
                disabled
              />
            </el-form-item>
          </el-col>
          <el-col :span="6">
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

    <!-- 入库明细表格 -->
    <el-card class="base-table-card base-table-card--flex" shadow="hover">
      <template #header>
        <div class="base-card-header" style="height: 20px; line-height: 20px; display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-icon><List /></el-icon>
            <span style="height: 20px; display: inline-block; line-height: 20px;margin-right: 10px;">入库明细</span>
          </div>
          <el-button v-if="!props.readonly" type="primary" @click="openMaterialDrawer" size="small">
            <el-icon><Plus /></el-icon>
            添加器材
          </el-button>
        </div>
      </template>

      <div class="base-table base-table--auto-height">
        <el-table
          :data="paginatedItems"
          stripe
          border
          :empty-text="'暂无入库明细数据'"
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
          width="120" 
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
          fixed="left"
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
              :class="{ 'error-border': row.quantity <= 0 || !Number.isInteger(row.quantity) }"
              style="width: 100%"
              :disabled="props.readonly"
            />
          </template>
        </el-table-column>
       
        <el-table-column 
          prop="unit_price" 
          label="单价" 
          width="120" 
          align="center" 
        >
          <template #default="{ row, $index }">
            <el-input-number
              v-model="row.unit_price"
              :min="0"
              :precision="3"
              :step="0.001"
              size="small"
              controls-position="right"
              @change="handleUnitPriceChange(getRealIndex($index))"
              :class="{ 'error-border': row.unit_price < 0 || (row.unit_price !== null && row.unit_price.toString().split('.')[1]?.length > 3) }"
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
          prop="amount" 
          label="金额" 
          width="100" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.unit_price, row.quantity]">
              {{ row.unit_price && row.quantity ? `¥${Number((row.unit_price * row.quantity).toFixed(2))}` : '-' }}
            </span>
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
        <el-table-column 
          prop="warehouse_name" 
          label="仓库" 
          width="100" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.warehouse_name]">{{ row.warehouse_name }}</span>
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
          prop="major_name" 
          label="专业" 
          width="80" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.major_name]">{{ row.major_name }}</span>
          </template>
        </el-table-column>
        <el-table-column 
          prop="equipment_name" 
          label="装备" 
          width="80" 
          align="center" 
        >
          <template #default="{ row }">
            <span v-memo="[row.detail_id, row.equipment_name]">{{ row.equipment_name }}</span>
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
          width="160" 
          align="center" 
          fixed="right"
          v-if="!props.readonly"
        >
          <template #default="{ $index, row }">
            <el-button 
              type="primary" 
              size="small" 
              @click="handleEditItem(getRealIndex($index), row)"
              :icon="Edit"
            >
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="removeItem(getRealIndex($index))"
              :icon="Delete"
              :loading="deleting"
              :disabled="deleting"
            >
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
    <div class="base-form-actions" v-if="!isEdit && !props.readonly">
      <el-button @click="handleBack">取消</el-button>
      <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
    </div>

    <!-- 器材选择抽屉（从顶部弹出） -->
    <el-drawer
      v-model="materialDrawerVisible"
      :title="isEditing ? '编辑器材' : '选择器材'"
      direction="ttb"
      size="85%"
      :before-close="handleDrawerClose"
      class="material-select-drawer"
    >
      <div class="material-select-layout">
        <!-- 左侧：器材信息表单 -->
        <div class="material-info-section">
          <div class="material-info-header">
            <h4>器材信息</h4>
          </div>
          <div class="material-info-form">
            <el-form :model="selectedMaterialInfo" label-width="80px">
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-form-item label="器材编码" required>
                    <el-input 
                      v-model="selectedMaterialInfo.material_code" 
                      placeholder="双击器材自动填充" 
                      readonly 
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="器材名称" required>
                    <el-input 
                      v-model="selectedMaterialInfo.material_name" 
                      placeholder="点击输入器材名称" 
                      @click="handleMaterialNameClick"
                      @input="(value: string) => handleMaterialNameInput(value)"
                      :class="{ 'error-border': validationErrors.material_id }"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-form-item label="规格型号">
                    <el-input 
                      v-model="selectedMaterialInfo.material_specification" 
                      placeholder="双击器材自动填充" 
                      readonly 
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="专业装备">
                    <el-input 
                      :value="selectedMaterialInfo.major_name + (selectedMaterialInfo.equipment_name ? ' / ' + selectedMaterialInfo.equipment_name : '')" 
                      placeholder="双击器材自动填充" 
                      readonly 
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-form-item label="数量" required>
                    <el-input-number 
                      v-model="selectedMaterialInfo.quantity" 
                      :min="1" 
                      :precision="0"
                      placeholder="请输入数量" 
                      :class="{ 'error-border': selectedMaterialInfo.quantity === null || selectedMaterialInfo.quantity <= 0 || !Number.isInteger(selectedMaterialInfo.quantity) }"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="单价" required>
                    <el-input-number 
                      v-model="selectedMaterialInfo.unit_price" 
                      :min="0" 
                      :precision="3" 
                      :step="0.001"
                      placeholder="请输入单价" 
                      :class="{ 'error-border': selectedMaterialInfo.unit_price === null || selectedMaterialInfo.unit_price < 0 || (selectedMaterialInfo.unit_price !== null && selectedMaterialInfo.unit_price.toString().split('.')[1]?.length > 3) }"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-form-item label="单位" required>
                    <div class="unit-input-container">
                      <el-input 
                        v-model="selectedMaterialInfo.unit" 
                        placeholder="请输入单位或选择常用单位"
                        @focus="handleUnitInputFocus"
                        @blur="handleUnitInputBlur"
                        @input="handleUnitSearch"
                        style="width: 100%"
                      />
                      <div v-if="showUnitDropdown" class="unit-dropdown">
                        <div class="unit-options">
                          <div 
                            v-for="unit in unitOptions" 
                            :key="unit"
                            class="unit-option"
                            @click="handleUnitSelect(unit)"
                          >
                            {{ unit }}
                          </div>
                          <div 
                            v-if="unitSearchText && !COMMON_UNITS.includes(unitSearchText as any)"
                            class="unit-option custom-unit"
                            @click="addCustomUnit"
                          >
                            <span>添加自定义单位：</span>
                            <strong>{{ unitSearchText }}</strong>
                          </div>
                          <div v-if="unitOptions.length === 0" class="unit-option no-match">
                            无匹配单位
                          </div>
                        </div>
                      </div>
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="货位信息">
                    <el-input 
                      v-model="selectedMaterialInfo.bin_name" 
                      placeholder="点击选择货位" 
                      readonly 
                      @click="handleBinInputClick"
                      :class="{ 'error-border': validationErrors.bin_id }"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="10">
                <el-col :span="13">
                  <el-form-item label="批次号" required>
                    <el-input 
                      v-model="selectedMaterialInfo.batch_number" 
                      placeholder="请输入批次号或使用自动生成" 
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="11">
                  <el-form-item label="生产日期" required>
                    <el-date-picker
                      v-model="selectedMaterialInfo.production_date"
                      type="date"
                      placeholder="选择生产日期"
                      format="YYYY-MM-DD"
                      value-format="YYYY-MM-DD"
                      :default-value="new Date()"
                      style="width: 100%"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </div>

        <!-- 右侧：器材列表/货位列表 -->
        <div class="material-list-section">
          <!-- 筛选区域 -->
          <div class="material-filter-section" v-if="!showBinList">
            <el-row :gutter="20" >
              <el-col :span="8">
                <el-select
                  v-model="materialFilter.major_id"
                  placeholder="选择专业"
                  clearable
                  filterable
                  @change="handleMaterialFilterChange"
                >
                  <el-option
                    v-for="major in majorOptions"
                    :key="major.id"
                    :label="major.major_name"
                    :value="major.id"
                  />
                </el-select>
              </el-col>
              <el-col :span="8" >
                <el-select
                  v-model="materialFilter.equipment_id"
                  placeholder="选择装备"
                  clearable
                  filterable
                  @change="handleMaterialFilterChange"
                >
                  <el-option
                    v-for="equipment in equipmentOptions"
                    :key="equipment.id"
                    :label="equipment.display_name"
                    :value="equipment.id"
                  />
                </el-select>
              </el-col>
              <el-col :span="8">
                <el-input
                  v-model="materialFilter.search"
                  placeholder="搜索器材编码、名称、规格型号"
                  clearable
                  @input="handleMaterialFilterChange"
                  @clear="handleMaterialFilterChange"
                />
              </el-col>
            </el-row>
            
            <!-- 定位器材单独一行 -->
            <el-row :gutter="20" style="margin-top: 12px;">
              <el-col :span="24">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <label style="min-width: 70px; font-weight: 500; color: #606266;">定位器材:</label>
                  <el-input
                    v-model="materialLocateCode"
                    placeholder="请输入器材编码"
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

          <!-- 货位筛选区域 -->
          <div class="material-filter-section" v-if="showBinList">
            <el-row :gutter="20" >
              <el-col :span="12">
                <el-input
                  v-model="binFilter.search"
                  placeholder="搜索货位名称、仓库"
                  clearable
                  @input="handleBinFilterChange"
                  @clear="handleBinFilterChange"
                />
              </el-col>
              <el-col :span="12">
                <el-select
                  v-model="binFilter.warehouse_id"
                  placeholder="选择仓库"
                  clearable
                  filterable
                  @change="handleBinFilterChange"
                >
                  <el-option
                    v-for="warehouse in warehouseOptions"
                    :key="warehouse.id"
                    :label="warehouse.warehouse_name"
                    :value="warehouse.id"
                  />
                </el-select>
              </el-col>
            </el-row>
          </div>

          <!-- 器材列表 -->
          <div class="material-table-section" v-if="!showBinList">
            <el-table
              ref="materialTableRef"
              :data="materialList"
              row-key="id"
              stripe
              border
              height="100%"
              :empty-text="'暂无器材数据'"
              @row-dblclick="handleMaterialDoubleClick"
              :row-class-name="getRowClassName"
              class="material-table"
            >
              <el-table-column prop="material_code" label="器材编码" width="120" align="center" />
              <el-table-column prop="material_name" label="器材名称" width="150" align="center" />
              <el-table-column prop="material_specification" label="规格型号" width="120" align="center" />
              <el-table-column label="专业及装备" width="200" align="center">
                <template #default="{ row }">
                  <div>
                    <div>{{ row.major_name || '未分类' }}</div>
                    <div style="font-size: 12px; color: #999;">{{ row.equipment_name || '未分配' }}</div>
                  </div>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 货位列表 -->
          <div class="material-table-section" v-if="showBinList">
            <el-table
              :data="binList"
              stripe
              border
              height="100%"
              :empty-text="'暂无货位数据'"
              @row-dblclick="handleBinDoubleClick"
              class="material-table"
            >
              <el-table-column prop="bin_name" label="货位名称" width="120" align="center" />
              <el-table-column prop="warehouse_name" label="所属仓库" width="150" align="center" />
              <el-table-column prop="bin_size" label="货位尺寸" width="120" align="center" />
              <el-table-column prop="bin_property" label="货位属性" width="120" align="center" />
              <el-table-column label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="row.empty_label ? 'success' : 'danger'">
                    {{ row.empty_label ? '空闲' : '占用' }}
                  </el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </div>

      <!-- 底部操作按钮 -->
      <div class="material-drawer-footer">
        <el-button type="primary" @click="handleAddMaterial">{{ isEditing ? '确认' : '添加' }}</el-button>
        <el-button @click="handleDrawerClose">关闭</el-button>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { 
  List, 
  Delete,
  Plus,
  Edit,
  Location,
} from '@element-plus/icons-vue';
import { inboundOrderAPI } from '@/services/material/inbound';
import { supplierAPI } from '@/services/base/supplier';
import { materialAPI } from '@/services/base/material';
import { warehouseAPI } from '@/services/base/warehouse';
import { binApi } from '@/services/base/bin';
import { inventoryDetailAPI } from '@/services/material/inventory_detail';
import { COMMON_UNITS } from '@/constants/units';
import { saveDraft, loadDraft, clearDraft, hasDraft, getDraftTimestamp, formatDraftTime } from '@/utils/draftManager';
import type { 
  InboundOrderCreate,
  InboundOrderItemCreate
} from '@/services/types/inbound';
import type { SupplierResponse } from '@/services/types/supplier';
import type { 
  MaterialResponse,
  MajorOption,
  EquipmentOption
} from '@/services/types/material';
import type { BinQueryParams, Bin } from '@/services/types/bin';

// 草稿管理相关常量
const DRAFT_KEY = 'inbound_order_draft';

// 草稿数据接口
interface InboundOrderDraftData {
  orderForm: {
    order_number: string;
    requisition_reference: string;
    contract_reference: string;
    supplier_id: number | null;
    supplier_name: string;
    inbound_date: string;
  };
  orderItems: ExtendedInboundOrderItem[];
}

// 定义props
const props = defineProps<{
  editId?: number | null
  readonly?: boolean
}>();

const isEdit = ref(false);
const orderId = ref<number | null>(null);
const saving = ref(false);
const deleting = ref(false); // 删除状态锁

// 入库单表单
const orderForm = reactive({
  order_number: '',
  requisition_reference: '',
  contract_reference: '',
  supplier_id: null as number | null,
  supplier_name: '', // 供应商名称（冗余字段，用于显示已删除的供应商）
  inbound_date: ''
});

// 入库单表单原始值（用于比较是否真正发生变化）
const originalOrderForm = reactive({
  order_number: '',
  requisition_reference: '',
  contract_reference: '',
  supplier_id: null as number | null,
  supplier_name: '', // 供应商名称（冗余字段）
  inbound_date: ''
});

const orderFormRef = ref();
const orderRules = {
  order_number: [{ required: true, message: '请输入入库单号', trigger: 'change' }],
  supplier_id: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  inbound_date: [{ required: true, message: '请选择入库日期', trigger: 'change' }]
};

// 入库明细（扩展类型以包含显示所需的器材信息）
interface ExtendedInboundOrderItem extends Omit<InboundOrderItemCreate, 'bin_id'> {
  item_id?: number;
  material_code?: string;
  material_name?: string;
  material_specification?: string;
  major_name?: string;
  equipment_name?: string;
  warehouse_name?: string;
  bin_name?: string;
  originalQuantity?: number;
  originalUnitPrice?: number;
  bin_id?: number | null; // 修改：支持null值，以匹配后端API
}
const orderItems = ref<ExtendedInboundOrderItem[]>([]);

// 筛选选项
const supplierOptions = ref<{ value: number; label: string }[]>([]);
// 供应商加载状态
const supplierLoading = ref(false);
// 搜索防抖定时器
let searchTimer: NodeJS.Timeout | null = null;
// 供应商分页状态
const supplierPagination = reactive({
  currentPage: 1,
  pageSize: 50,
  totalPages: 0,
  hasMore: true,
  currentSearch: '' // 当前搜索关键字
});

// 判断当前供应商是否已被删除
const isSupplierDeleted = computed(() => {
  if (!orderForm.supplier_id || !orderForm.supplier_name) {
    return false;
  }
  // 检查供应商选项中是否包含当前供应商ID
  return !supplierOptions.value.some(option => option.value === orderForm.supplier_id);
});

// 器材选择抽屉相关数据
const materialDrawerVisible = ref(false);

// 器材筛选条件
const materialFilter = reactive({
  major_id: undefined as number | undefined,
  equipment_id: undefined as number | undefined,
  search: ''
});

// 器材定位相关变量
const materialLocateCode = ref(''); // 定位用的器材编码
const locating = ref(false); // 定位加载状态
const highlightedMaterialId = ref<number | null>(null); // 高亮的器材ID
const isLocatingScroll = ref(false); // 标记是否正在执行定位滚动锁定
const materialTableRef = ref(); // 器材表格ref

// 货位筛选条件
const binFilter = reactive({
  search: '',
  warehouse_id: null
});

// 器材列表数据
const materialList = ref<MaterialResponse[]>([]);
const materialFirstPage = ref(1); // 记录当前列表的第一页页码
const materialLastPage = ref(1);  // 记录当前列表的最后一页页码
const materialHasMore = ref(true);
const loadingMoreMaterials = ref(false);
const MAX_MATERIAL_ITEMS = 50; // 超过50项后修剪前端数据，防止卡顿
const materialRequestId = ref(0); // 请求 ID，用于防止异步竞态冲突

// 货位列表
const binList = ref<Bin[]>([]);

// 仓库选项
const warehouseOptions = ref<{id: number, warehouse_name: string}[]>([]);

// 是否显示货位列表
const showBinList = ref(false);

// 专业选项
const majorOptions = ref<MajorOption[]>([]);

// 装备选项
const equipmentOptions = ref<EquipmentOption[]>([]);

// 选中的器材信息
const selectedMaterialInfo = reactive({
  material_id: 0,
  material_code: '',
  material_name: '',
  material_specification: '',
  major_name: '',
  equipment_name: '',
  quantity: null as number | null,
  unit: '',
  unit_price: null as number | null,
  batch_number: '',
  bin_id: null as number | null, // 支持null值，表示未选择货位
  bin_name: '',
  production_date: ''
});

// 单位选择相关变量
const allUnitOptions = ref<string[]>([...COMMON_UNITS]); // 完整的单位列表（保持最近使用的顺序）
const showUnitDropdown = ref(false);
const unitSearchText = ref('');

// 计算属性：根据搜索文本过滤单位选项
const unitOptions = computed(() => {
  if (unitSearchText.value) {
    // 根据搜索文本过滤
    const filtered = allUnitOptions.value.filter(unit => 
      unit.includes(unitSearchText.value)
    );
    
    // 如果过滤后为空，从COMMON_UNITS中查找
    if (filtered.length === 0) {
      return COMMON_UNITS.filter(unit => 
        unit.includes(unitSearchText.value)
      );
    }
    
    return filtered;
  }
  // 没有搜索文本时，显示完整列表
  return allUnitOptions.value;
});

// 编辑状态管理
const editingIndex = ref<number | null>(null);
const isEditing = ref(false);

// 错误状态管理
const validationErrors = reactive({
  material_id: false,
  bin_id: false
});

// 入库明细分页相关变量
const currentPage = ref(1);
const pageSize = ref(20);

// 计算属性：分页后的入库明细数据
const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return orderItems.value.slice(start, end);
});

// 计算当前页的真实索引（用于操作原始数组）
const getRealIndex = (pageIndex: number): number => {
  return (currentPage.value - 1) * pageSize.value + pageIndex;
};

// 草稿自动保存方法
const saveDraftData = () => {
  // 仅在新增模式下保存草稿
  if (!isEdit.value) {
    // 判断是否有有效的用户输入（不仅仅是自动生成的单号和日期）
    const hasValidInput = 
      orderForm.supplier_id !== null ||  // 有供应商选择
      orderForm.requisition_reference !== '' ||  // 有调拨单号
      orderForm.contract_reference !== '' ||  // 有合同号
      orderItems.value.length > 0;  // 有明细数据
    
    // 只有存在有效用户输入时才保存草稿
    if (hasValidInput) {
      const draftData: InboundOrderDraftData = {
        orderForm: {
          order_number: orderForm.order_number,
          requisition_reference: orderForm.requisition_reference,
          contract_reference: orderForm.contract_reference,
          supplier_id: orderForm.supplier_id,
          supplier_name: orderForm.supplier_name,
          inbound_date: orderForm.inbound_date
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

// 计算总数量
const totalQuantity = computed(() => {
  return orderItems.value.reduce((sum, item) => sum + (item.quantity || 0), 0);
});

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


// 获取供应商列表（支持传参和追加模式）
const getSuppliers = async (searchKeyword?: string, append: boolean = false) => {
  try {
    // 如果不是追加模式，重置分页状态
    if (!append) {
      supplierPagination.currentPage = 1;
      supplierPagination.currentSearch = searchKeyword || '';
    }
    
    // 根据是否搜索设置不同的参数
    const params: any = {
      page: supplierPagination.currentPage,
      page_size: supplierPagination.pageSize,
      sort_field: 'update_time', // 按更新时间排序，显示最近使用的
      sort_asc: false // 降序排列
    };
    
    // 如果有搜索关键字，添加search参数
    if (searchKeyword && searchKeyword.trim()) {
      params.search = searchKeyword.trim();
      params.page_size = 50; // 搜索时显示50条
    }
    
    const result = await supplierAPI.getSuppliers(params);
    
    // 更新分页信息
    supplierPagination.totalPages = result.total_pages;
    supplierPagination.hasMore = supplierPagination.currentPage < result.total_pages;
    
    // 根据模式处理数据：追加或替换
    const newOptions = result.data.map((supplier: SupplierResponse) => ({
      value: supplier.id,
      label: supplier.supplier_name
    }));
    
    if (append) {
      // 追加模式：合并数据，去重
      const existingIds = new Set(supplierOptions.value.map(opt => opt.value));
      const uniqueNewOptions = newOptions.filter(opt => !existingIds.has(opt.value));
      supplierOptions.value = [...supplierOptions.value, ...uniqueNewOptions];
    } else {
      // 替换模式：直接赋值
      supplierOptions.value = newOptions;
    }
  } catch (error: any) {
    // 全局拦截器已经处理了401等错误，这里只记录错误不重复显示
    console.error('获取供应商列表失败:', error);
  }
};

// 远程搜索供应商（带防抖）
const remoteSearchSuppliers = (query: string) => {
  // 清除之前的定时器
  if (searchTimer) {
    clearTimeout(searchTimer);
  }
  
  // 如果查询为空，加载初始列表
  if (!query || !query.trim()) {
    getSuppliers();
    return;
  }
  
  // 设置加载状态
  supplierLoading.value = true;
  
  // 防抖：300ms后执行搜索
  searchTimer = setTimeout(async () => {
    try {
      await getSuppliers(query);
    } finally {
      supplierLoading.value = false;
    }
  }, 300);
};

// 触底加载更多供应商（优化：防止滚动跳动）
const loadMoreSuppliers = async () => {
  // 如果正在加载或没有更多数据，直接返回
  if (supplierLoading.value || !supplierPagination.hasMore) {
    return;
  }
  
  // 获取当前滚动容器
  const scrollContainer = document.querySelector('.el-select-dropdown__wrap') as HTMLElement;
  if (!scrollContainer) return;
  
  // 保存加载前的滚动位置和内容高度
  const scrollTopBefore = scrollContainer.scrollTop;
  const scrollHeightBefore = scrollContainer.scrollHeight;
  
  try {
    supplierLoading.value = true;
    // 页码+1
    supplierPagination.currentPage++;
    // 使用当前搜索关键字，并以追加模式加载
    await getSuppliers(supplierPagination.currentSearch, true);
    
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
    console.error('加载更多供应商失败:', error);
    // 加载失败，回退页码
    supplierPagination.currentPage--;
  } finally {
    supplierLoading.value = false;
  }
};

// 供应商下拉框滚动事件处理
const handleSupplierScroll = (event: Event) => {
  const target = event.target as HTMLElement;
  const { scrollTop, scrollHeight, clientHeight } = target;
  
  // 触底加载：离底部还有15px时触发
  if (scrollTop + clientHeight >= scrollHeight - 15) {
    loadMoreSuppliers();
  }
};

// 绑定供应商下拉框滚动监听
const bindSupplierScrollListener = () => {
  nextTick(() => {
    // 获取 el-select 的下拉框 DOM
    const selectDropdown = document.querySelector('.el-select-dropdown__wrap');
    if (selectDropdown) {
      selectDropdown.removeEventListener('scroll', handleSupplierScroll);
      selectDropdown.addEventListener('scroll', handleSupplierScroll);
    }
  });
};

// 移除明细项
const removeItem = async (index: number) => {
  // 如果正在删除中，直接返回（按钮已禁用，这里做二次防护）
  if (deleting.value) {
    return;
  }
  
  const item = orderItems.value[index];
  console.log("判断当前模式是否为编辑模式",isEdit.value,orderId.value,item.item_id);
  if (isEdit.value && orderId.value && item.item_id) {
    // 编辑模式：调用后端API删除明细项
    console.log("删除明细项",orderId.value, item.item_id);
    try {
      deleting.value = true;
      await inboundOrderAPI.deleteInboundOrderItem(orderId.value, item.item_id);
      orderItems.value.splice(index, 1);
      
      // 删除后调整页码，确保当前页有效
      adjustPageAfterDelete();
      
      ElMessage.success('明细项删除成功');
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = '删除明细项失败';
        
        // 判断detail是字符串还是对象
        if (typeof detail === 'string') {
          // detail是字符串，直接显示
          errorMessage = detail;
        } else if (typeof detail === 'object' && detail !== null) {
          // detail是对象，处理message字段和problematic_items
          errorMessage = detail.message || '删除明细项失败';
          
          // 如果有问题器材列表，显示详细信息
          if (detail.problematic_items && detail.problematic_items.length > 0) {
            errorMessage += '\n\n无法删除明细项，原因：\n';
            detail.problematic_items.forEach((problem: any) => {
              errorMessage += `- ${problem.reason || '未知原因'}\n`;
            });
          }
        }
        
        ElMessage.error(errorMessage);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '删除明细项失败';
        ElMessage.error(`删除明细项失败: ${errorMessage}`);
      }
    } finally {
      deleting.value = false;
    }
  } else {
    // 新增模式：直接在前端移除
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

// 编辑明细项
const handleEditItem = (index: number, row: ExtendedInboundOrderItem) => {
  // 设置编辑状态
  editingIndex.value = index;
  isEditing.value = true;
  
  // 将选中项信息填充到器材选择抽屉
  selectedMaterialInfo.material_id = row.material_id;
  selectedMaterialInfo.material_code = row.material_code || '';
  selectedMaterialInfo.material_name = row.material_name || '';
  selectedMaterialInfo.material_specification = row.material_specification || '';
  selectedMaterialInfo.major_name = row.major_name || '';
  selectedMaterialInfo.equipment_name = row.equipment_name || '';
  selectedMaterialInfo.quantity = row.quantity;
  selectedMaterialInfo.unit = row.unit || '';
  selectedMaterialInfo.unit_price = row.unit_price;
  selectedMaterialInfo.batch_number = row.batch_number || '';
  selectedMaterialInfo.bin_id = row.bin_id || null; // 修改：将默认值从0改为null，表示未选择货位
  selectedMaterialInfo.bin_name = row.bin_name || '';
  selectedMaterialInfo.production_date = row.production_date || '';
  
  // 打开器材选择抽屉
  materialDrawerVisible.value = true;
  
  // 清除错误状态
  clearValidationErrors();
};

// 打开器材选择抽屉
const openMaterialDrawer = async () => {
  materialDrawerVisible.value = true;
  
  // 清空左侧表单数据
  resetSelectedMaterialInfo();
  
  // 自动设置生产日期为入库日期（如果有入库日期），否则使用当天
  if (orderForm.inbound_date) {
    selectedMaterialInfo.production_date = orderForm.inbound_date;
  } else {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    selectedMaterialInfo.production_date = `${year}-${month}-${day}`;
  }
  
  await getMaterialList();
  await getMajors();
  await getEquipments();
  
  // 初始化器材列表滚动监听
  initTableScroll();
};

// 关闭抽屉
const handleDrawerClose = () => {
  materialDrawerVisible.value = false;
  // 重置筛选条件
  materialFilter.major_id = undefined;
  materialFilter.equipment_id = undefined;
  materialFilter.search = '';
  
  // 重置编辑状态
  if (isEditing.value) {
    isEditing.value = false;
    editingIndex.value = null;
    resetSelectedMaterialInfo();
  }
};

// 单位选择相关方法
const handleUnitSelect = (unit: string) => {
  selectedMaterialInfo.unit = unit;
  showUnitDropdown.value = false;
  unitSearchText.value = '';
  // 更新unitOptions，将使用的单位插入到最前面
  updateUnitOptions(unit);
};

const handleUnitInputFocus = () => {
  showUnitDropdown.value = true;
  unitSearchText.value = ''; // 清空搜索文本，显示完整列表
};

const handleUnitInputBlur = () => {
  // 延迟关闭下拉框，以便点击选项时能正常触发
  setTimeout(() => {
    showUnitDropdown.value = false;
    // 如果用户直接输入了单位（没有选择下拉项），也更新unitOptions
    if (selectedMaterialInfo.unit && selectedMaterialInfo.unit.trim()) {
      updateUnitOptions(selectedMaterialInfo.unit.trim());
    }
  }, 300);
};

const handleUnitSearch = (value: string) => {
  unitSearchText.value = value;
  // 过滤逻辑由计算属性unitOptions自动处理
};

const addCustomUnit = () => {
  if (unitSearchText.value && !COMMON_UNITS.includes(unitSearchText.value as any)) {
    selectedMaterialInfo.unit = unitSearchText.value;
    // 更新unitOptions，将自定义单位插入到最前面
    updateUnitOptions(unitSearchText.value);
    unitSearchText.value = '';
    showUnitDropdown.value = false;
  }
};

// 更新单位选项，将使用的单位移到最前面
const updateUnitOptions = (unit: string) => {
  if (!unit) return;
  
  // 从当前的allUnitOptions中移除该单位（如果存在）
  const index = allUnitOptions.value.indexOf(unit);
  if (index > -1) {
    allUnitOptions.value.splice(index, 1);
  }
  
  // 将该单位插入到最前面
  allUnitOptions.value.unshift(unit);
};

// 获取专业列表
const getMajors = async () => {
  try {
    const result = await materialAPI.getMajorOptions();
    majorOptions.value = result.data;
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '获取专业列表失败';
    ElMessage.error(`获取专业列表失败: ${errorMessage}`);
  }
};

// 获取装备列表
const getEquipments = async () => {
  try {
    // 专业ID为空时，让后端API自动处理
    const majorIds = materialFilter.major_id ? [materialFilter.major_id] : [];
    console.log('专业号:', majorIds);
    const result = await materialAPI.getEquipmentOptionsByMajors(majorIds);
    equipmentOptions.value = result.data;
    console.log('装备列表:', equipmentOptions.value);
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
    
    const params = {
      search: materialFilter.search,
      major_id: materialFilter.major_id,
      equipment_id: materialFilter.equipment_id,
      page: page,
      page_size: pageSize,
      sort_field: 'material_code',
      sort_asc: true
    };
    
    const result = await materialAPI.getMaterials(params);
    
    // 如果在请求期间有新的 replace 请求发起，则丢弃当前过期请求的结果
    if (currentId !== materialRequestId.value && mode === 'replace') {
      console.log('丢弃过期的器材列表请求:', currentId);
      return;
    }

    const newData = result.data;
    const tableEl = materialTableRef.value?.$el;
    const scrollWrapper = tableEl?.querySelector('.el-scrollbar__wrap') || tableEl?.querySelector('.el-table__body-wrapper');
    
    // 记录加载前的滚动高度，用于向上加载时的位置补偿
    const oldScrollHeight = scrollWrapper?.scrollHeight || 0;
    const oldScrollTop = scrollWrapper?.scrollTop || 0;

    if (mode === 'append') {
      // 向下追加：如果超过限制，删除顶部
      if (materialList.value.length + newData.length > MAX_MATERIAL_ITEMS) {
        // 智能修剪：检查高亮项是否在准备删除的 20 项内
        const highlightedIndex = materialList.value.findIndex(item => item.id === highlightedMaterialId.value);
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
        const highlightedIndex = materialList.value.findIndex(item => item.id === highlightedMaterialId.value);
        if (highlightedIndex === -1 || highlightedIndex < materialList.value.length - 20) {
          materialList.value.splice(-20);
          materialLastPage.value -= 2;
        }
      }
      materialList.value = [...newData, ...materialList.value];
      materialFirstPage.value = page;
      
      // 关键：向上加载后需要补偿滚动位置，防止跳动
      nextTick(() => {
        if (scrollWrapper) {
          const newScrollHeight = scrollWrapper.scrollHeight;
          scrollWrapper.scrollTop = oldScrollTop + (newScrollHeight - oldScrollHeight);
        }
      });
    } else {
      // 替换（搜索或定位）
      materialList.value = newData;
      materialFirstPage.value = page;
      materialLastPage.value = page;
    }
    
    // 如果是最后一页，更新 hasMore
    if (mode !== 'prepend') {
      materialHasMore.value = newData.length === pageSize;
    }
    
  } catch (error: any) {
    const errorMessage = error.response?.data?.message || error.message || '获取器材列表失败';
    ElMessage.error(`获取器材列表失败: ${errorMessage}`);
  } finally {
    loadingMoreMaterials.value = false;
  }
};

// 筛选条件变化处理
const handleMaterialFilterChange = async () => {
  // 如果输入了搜索内容，自动清空定位器材输入框
  if (materialFilter.search) {
    materialLocateCode.value = '';
  }

  // 只有当专业发生变化时才重新获取装备列表并清空装备筛选条件
  // 避免装备选择时也被清空
  const currentMajorId = materialFilter.major_id;
  
  // 如果专业发生变化，重新获取装备列表并清空装备筛选条件
  if (currentMajorId !== undefined) {
    // 只有在专业确实发生变化时才清空装备筛选
    // 这里我们通过检查是否需要重新获取装备列表来判断
    await getEquipments();
  }
  
  // 清除高亮
  highlightedMaterialId.value = null;
  // 总是重新获取器材列表
  getMaterialList();
};

// 器材定位输入变化处理
const handleLocateInputChange = (value: string) => {
  if (value) {
    // 如果输入了定位码，自动清空器材搜索框
    materialFilter.search = '';
  }
};

// 器材定位处理
const handleMaterialLocate = async () => {
  try {
    locating.value = true;
    // 强制使用与 getMaterialList 一致的 pageSize: 10
    const pageSize = 10;
    
    // 调用定位接口
    const result = await materialAPI.locate({
      material_code: materialLocateCode.value,
      page_size: pageSize
    });
    
    if (result.target_page !== null) {
      // 标记开始定位滚动，锁定滚动监听
      isLocatingScroll.value = true;
      
      // 重新获取器材列表（清除筛选条件，显示全部器材）
      materialFilter.major_id = undefined;
      materialFilter.equipment_id = undefined;
      materialFilter.search = '';
      
      // 使用定位返回的页码进行加载
      await getMaterialList(result.target_page);
      
      // 优化：如果定位的器材在页面后半部分，则多加载一页支撑滚动
      if (result.position !== null) {
        const positionInPage = ((result.position - 1) % 10) + 1;
        if (positionInPage > 5 && materialHasMore.value) {
          await getMaterialList(result.target_page + 1, 'append');
        }
      }
      
      if (result.found && result.material) {
        await nextTick();
        
        const targetMaterial = result.material;
        scrollToTargetMaterial(targetMaterial.id);
        
        // 设置高亮
        highlightedMaterialId.value = targetMaterial.id;
        ElMessage.success(`已定位到: ${targetMaterial.material_name} (位置: ${result.position})`);
        
        // 等待平滑滚动完成后解除锁定（通常 800ms 足够）
        setTimeout(() => {
          isLocatingScroll.value = false;
        }, 800);

        // 20秒后移除高亮
        setTimeout(() => {
          if (highlightedMaterialId.value === targetMaterial.id) {
            highlightedMaterialId.value = null;
          }
        }, 20000);
      } else {
        isLocatingScroll.value = false;
        ElMessage.info('已返回第1页');
      }
    } else {
      ElMessage.warning(`未找到器材编码: ${materialLocateCode.value}`);
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
const scrollToTargetMaterial = (materialId: number) => {
  if (!materialTableRef.value) return;
  
  // 找到目标器材在当前列表中的索引
  const index = materialList.value.findIndex(item => item.id === materialId);
  if (index === -1) return;
  
  // 获取表格的DOM元素
  const tableEl = materialTableRef.value.$el;
  const tableBody = tableEl.querySelector('.el-table__body-wrapper');
  
  if (tableBody) {
    // 获取所有行元素
    const rows = tableBody.querySelectorAll('.el-table__row');
    if (rows[index]) {
      // 滚动到目标行
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
  // 等待数据加载完成
  await getMaterialList(1);
  
  // 强制滚动到最顶部
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
const getRowClassName = ({ row }: { row: MaterialResponse }) => {
  return row.id === highlightedMaterialId.value ? 'highlighted-row' : '';
};

// 处理货位筛选条件变化
const handleBinFilterChange = () => {
  getBins();
};

// 点击货位输入框
const handleBinInputClick = () => {
  showBinList.value = true;
  // 清除错误状态
  clearValidationErrors();
  // 获取仓库列表
  getWarehouses();
  // 获取货位列表
  getBins();
};

// 点击器材名称输入框
const handleMaterialNameClick = () => {
  showBinList.value = false;
  // 清除错误状态
  clearValidationErrors();
  // 确保器材列表显示
  getMaterialList();
};

// 处理器材名称输入
const handleMaterialNameInput = (value: string) => {
  // 将输入内容同步到搜索框
  materialFilter.search = value
  // 触发搜索
  handleMaterialFilterChange()
}

// 双击货位行
const handleBinDoubleClick = async (row: any) => {
  try {
    // 获取完整的货位信息，包括仓库名称
    const binResponse = await binApi.getBin(row.id);
    
    selectedMaterialInfo.bin_id = binResponse.id;
    selectedMaterialInfo.bin_name = binResponse.bin_name;
    
    // 清除错误状态
    clearValidationErrors();
    // 关闭货位列表，显示器材列表
    showBinList.value = false;
    
    // 显示成功消息
    ElMessage.success(`已选择货位: ${binResponse.bin_name} (仓库: ${binResponse.warehouse_name})`);
  } catch (error) {
    console.error('获取货位详情失败:', error);
    ElMessage.error('获取货位信息失败，请重试');
  }
};

// 获取仓库列表
const getWarehouses = async () => {
  try {
    warehouseOptions.value = await warehouseAPI.getAllWarehouses();
  } catch (error) {
    console.error('获取仓库列表失败:', error);
  }
};

// 获取货位列表
const getBins = async () => {
  try {
    const params: BinQueryParams = {
      search: binFilter.search,
      warehouse_id: binFilter.warehouse_id || undefined
    };
    const response = await binApi.getBins(params);
    binList.value = response.data || [];
  } catch (error) {
    console.error('获取货位列表失败:', error);
  }
};

// 生成批次编码
const generateBatchCode = async (material: MaterialResponse) => {
    try {
      // 使用入库日期作为批次日期（如果有入库日期），否则使用当天日期
      let batchDate: string;
      if (orderForm.inbound_date) {
        batchDate = orderForm.inbound_date;
      } else {
        const now = new Date();
        batchDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
      }
      
      // 检查器材明细中是否已经有相同器材ID的记录
      const existingItems = orderItems.value.filter(item => item.material_id === material.id);
      
      // 如果有相同器材ID的记录，需要获取不同的批次编码
      if (existingItems.length > 0) {
        // 获取所有现有批次编码的流水号
        const existingSequences = existingItems.map(item => {
          const batchCode = item.batch_number;
          if (batchCode && batchCode.includes('-')) {
            const parts = batchCode.split('-');
            const sequencePart = parts[parts.length - 1];
            
            // 检查批次编码格式是否正确（器材编码-日期+流水号）
            // 正确的流水号应该是3位数字
            if (sequencePart.length === 3 && /^\d{3}$/.test(sequencePart)) {
              const sequence = parseInt(sequencePart);
              return isNaN(sequence) ? 0 : sequence;
            } else {
              // 如果批次编码格式错误，尝试从最后3位提取流水号
              const lastThreeChars = sequencePart.slice(-3);
              if (/^\d{3}$/.test(lastThreeChars)) {
                const sequence = parseInt(lastThreeChars);
                return isNaN(sequence) ? 0 : sequence;
              }
            }
          }
          return 0;
        }).filter(seq => seq > 0);
        
        // 获取最大的流水号，然后加1
        const maxSequence = existingSequences.length > 0 ? Math.max(...existingSequences) : 0;
        const nextSequence = maxSequence + 1;
        
        // 使用入库日期生成批次编码（保持与后端API一致的格式）
        const [year, month, day] = batchDate.split('-');
        const sequenceStr = String(nextSequence).padStart(3, '0');
        
        // 生成正确的批次编码格式：器材编码-年月日+流水号
        const correctBatchCode = `${material.material_code}-${year}${month}${day}${sequenceStr}`;
        
        // 检查是否有错误的批次编码需要修复
        const hasInvalidBatchCodes = existingItems.some(item => {
          const batchCode = item.batch_number;
          if (batchCode && batchCode.includes('-')) {
            const parts = batchCode.split('-');
            const sequencePart = parts[parts.length - 1];
            // 如果流水号部分长度超过3位，说明格式错误
            return sequencePart.length > 3;
          }
          return false;
        });
        
        // 如果检测到错误的批次编码，显示警告信息
        if (hasInvalidBatchCodes) {
          console.warn('检测到错误的批次编码格式，已自动修复为正确格式');
        }
        
        return correctBatchCode;
      } else {
        // 如果没有相同器材ID的记录，正常调用后端API
        const batchResponse = await inventoryDetailAPI.generateBatchCode({
          material_id: material.id,
          batch_date: batchDate
        });
        
        return batchResponse.batch_code;
      }
    } catch (error) {
      console.error('生成批次编码失败:', error);
      // 如果API调用失败，使用前端备用方案，优先使用入库日期
      let dateStr: string;
      if (orderForm.inbound_date) {
        dateStr = orderForm.inbound_date.replace(/-/g, '');
      } else {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        dateStr = `${year}${month}${day}`;
      }
      const sequence = '002';
      ElMessage.warning('批次编码生成失败，使用备用方案');
      return `${material.material_code}-${dateStr}${sequence}`;
  }
};

  // 双击器材添加到入库明细
  const handleMaterialDoubleClick = async (material: MaterialResponse) => {
    // 填充左侧表单数据
    selectedMaterialInfo.material_id = material.id;
    selectedMaterialInfo.material_code = material.material_code;
    selectedMaterialInfo.material_name = material.material_name;
    selectedMaterialInfo.material_specification = material.material_specification || '';
    selectedMaterialInfo.major_name = material.major_name || '';
    selectedMaterialInfo.equipment_name = material.equipment_name || '';
    
    // 执行批次编码生成
    selectedMaterialInfo.batch_number = await generateBatchCode(material);
  
  // 清除错误状态
  clearValidationErrors();
  
  // 显示成功消息
  ElMessage.success(`已选择器材: ${material.material_name}`);
};



// 手动添加器材（通过底部按钮）
const handleAddMaterial = async () => {
  if (!selectedMaterialInfo.material_id) {
    ElMessage.warning('请先选择器材');
    return;
  }
  
  // 验证器材ID是否存在且名称匹配
  validationErrors.material_id = false;
  try {
    const materialResponse = await materialAPI.getMaterial(selectedMaterialInfo.material_id);
    if (!materialResponse || !materialResponse.id) {
      validationErrors.material_id = true;
      ElMessage.error('器材ID不存在，请重新选择器材');
      return;
    }
    
    // 验证器材名称是否匹配
    if (materialResponse.material_name !== selectedMaterialInfo.material_name) {
      validationErrors.material_id = true;
      ElMessage.error('器材名称与ID不匹配，请重新选择器材');
      return;
    }
  } catch (error: any) {
    validationErrors.material_id = true;
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '器材ID验证失败';
    ElMessage.error(`器材ID验证失败: ${errorMessage}，请检查器材ID是否正确`);
    return;
  }
  
  // 验证货位ID是否存在
  validationErrors.bin_id = false;
  if (selectedMaterialInfo.bin_id) {
    try {
      const binResponse = await binApi.getBin(selectedMaterialInfo.bin_id);
      if (!binResponse || !binResponse.id) {
        validationErrors.bin_id = true;
        ElMessage.error('货位ID不存在，请重新选择货位');
        return;
      }
    } catch (error: any) {
      validationErrors.bin_id = true;
      // 显示具体的错误原因
      const errorMessage = error.response?.data?.message || error.message || '货位ID验证失败';
      ElMessage.error(`货位ID验证失败: ${errorMessage}，请检查货位ID是否正确`);
      return;
    }
  }
 
  // 验证必填字段
  if (selectedMaterialInfo.quantity === null || selectedMaterialInfo.quantity <= 0) {
    ElMessage.warning('请输入有效的数量');
    return;
  }
  
  if (!selectedMaterialInfo.unit) {
    ElMessage.warning('请输入单位');
    return;
  }
  
  if (selectedMaterialInfo.unit_price === null || selectedMaterialInfo.unit_price < 0) {
    ElMessage.warning('请输入有效的单价');
    return;
  }
  
  // 创建新的器材项
  const newItem: ExtendedInboundOrderItem = {
    material_id: selectedMaterialInfo.material_id,
    material_code: selectedMaterialInfo.material_code,
    material_name: selectedMaterialInfo.material_name,
    material_specification: selectedMaterialInfo.material_specification,
    major_name: selectedMaterialInfo.major_name,
    equipment_name: selectedMaterialInfo.equipment_name,
    quantity: selectedMaterialInfo.quantity || 0, // 处理 null 值，默认为 0
    unit: selectedMaterialInfo.unit || '', // 确保 unit 不是 undefined
    unit_price: selectedMaterialInfo.unit_price || 0, // 处理 null 值，默认为 0
    batch_number: selectedMaterialInfo.batch_number,
    bin_id: selectedMaterialInfo.bin_id || null, // 修改：确保未选择货位时提交null而不是0
    warehouse_name: selectedMaterialInfo.bin_id ? await getWarehouseNameByBinId(selectedMaterialInfo.bin_id) : '',
    bin_name: selectedMaterialInfo.bin_name || '',
    production_date: selectedMaterialInfo.production_date || ''
  };
  
  // 判断是编辑模式还是添加模式
  if (isEditing.value && editingIndex.value !== null) {
    // 编辑模式：更新现有项
    const originalItem = orderItems.value[editingIndex.value];
    orderItems.value[editingIndex.value] = newItem;
    
    // 如果是编辑模式且存在订单ID，调用后端API更新器材信息
    if (isEdit.value && orderId.value && originalItem.item_id) {
      try {
        await inboundOrderAPI.updateInboundOrderItem(orderId.value, originalItem.item_id, {
          material_id: newItem.material_id,
          quantity: newItem.quantity,
          unit: newItem.unit,
          unit_price: newItem.unit_price,
          batch_number: newItem.batch_number,
          bin_id: newItem.bin_id,
          production_date: newItem.production_date
        });
        ElMessage.success(`已更新器材: ${selectedMaterialInfo.material_name}`);
      } catch (error: any) {
        // 优先处理detail字段中的详细信息
        if (error.response?.data?.detail) {
          const detail = error.response.data.detail;
          let errorMessage = '器材更新失败';
          
          // 判断detail是字符串还是对象
          if (typeof detail === 'string') {
            // detail是字符串，直接显示
            errorMessage = detail;
          } else if (typeof detail === 'object' && detail !== null) {
            // detail是对象，处理message字段和problematic_items
            errorMessage = detail.message || '器材更新失败';
            
            // 如果有问题器材列表，添加到错误信息中
            if (detail.problematic_items && detail.problematic_items.length > 0) {
              errorMessage += '\n\n无法更新器材，原因：\n';
              detail.problematic_items.forEach((problem: any) => {
                errorMessage += `- ${problem.reason || '未知原因'}\n`;
              });
            }
          }
          
          ElMessage.error(errorMessage);
          
          // 如果更新失败，恢复原始数据
          orderItems.value[editingIndex.value] = originalItem;
          return;
        } else {
          // 如果没有detail字段，使用原来的逻辑
          const errorMessage = error.response?.data?.message || error.message || '器材更新失败';
          ElMessage.error(`器材更新失败: ${errorMessage}`);
          
          // 如果更新失败，恢复原始数据
          orderItems.value[editingIndex.value] = originalItem;
          return;
        }
      }
    } else {
      ElMessage.success(`已更新器材: ${selectedMaterialInfo.material_name}`);
    }
    
    // 重置编辑状态
    isEditing.value = false;
    editingIndex.value = null;
    
    // 编辑模式：清空选中信息，保持抽屉打开
    resetSelectedMaterialInfo();
  } else {
    // 添加模式：检查是否已存在相同批次号的器材
    const existingItemIndex = orderItems.value.findIndex(item => 
      item.material_id === newItem.material_id && 
      item.batch_number === newItem.batch_number
    );
    
    if (existingItemIndex !== -1) {
      // 存在相同批次号的器材，进行合并
      const existingItem = orderItems.value[existingItemIndex];
      const originalQuantity = existingItem.quantity;
      const newQuantity = originalQuantity + newItem.quantity;
      
      // 更新现有器材的数量
      existingItem.quantity = newQuantity;
      
      // 如果是编辑模式且存在订单ID，调用后端API更新器材数量
      if (isEdit.value && orderId.value && existingItem.item_id) {
        try {
          await inboundOrderAPI.updateInboundOrderItem(orderId.value, existingItem.item_id, {
            quantity: newQuantity,
            unit_price: existingItem.unit_price
          });
          ElMessage.success(`发现相同批次器材，已自动合并`);
        } catch (error: any) {
          // 如果更新失败，恢复原始数量
          existingItem.quantity = originalQuantity;
          
          // 优先处理detail字段中的详细信息
          if (error.response?.data?.detail) {
            const detail = error.response.data.detail;
            let errorMessage = '器材合并失败';
            
            if (typeof detail === 'string') {
              errorMessage = detail;
            } else if (typeof detail === 'object' && detail !== null) {
              errorMessage = detail.message || '器材合并失败';
              
              if (detail.problematic_items && detail.problematic_items.length > 0) {
                errorMessage += '\n\n无法合并器材，原因：\n';
                detail.problematic_items.forEach((problem: any) => {
                  errorMessage += `- ${problem.reason || '未知原因'}\n`;
                });
              }
            }
            
            ElMessage.error(errorMessage);
          } else {
            const errorMessage = error.response?.data?.message || error.message || '器材合并失败';
            ElMessage.error(`器材合并失败: ${errorMessage}`);
          }
          return;
        }
      } else {
        ElMessage.success(`发现相同批次器材，已自动合并`);
      }
      
      // 合并模式：清空选中信息，保持抽屉打开
      resetSelectedMaterialInfo();
      // 无论新增还是编辑模式，都保持抽屉打开，用户可以继续添加其他器材
    } else {
      // 不存在相同批次号的器材，正常添加
      if (isEdit.value && orderId.value) {
        // 编辑模式下添加器材：直接调用后端API添加器材信息
        try {
          const response = await inboundOrderAPI.addInboundOrderItem(orderId.value, {
            material_id: newItem.material_id,
            quantity: newItem.quantity,
            unit: newItem.unit,
            unit_price: newItem.unit_price,
            batch_number: newItem.batch_number,
            bin_id: newItem.bin_id,
            production_date: newItem.production_date
          });
          
          // 将后端返回的item_id添加到器材项中
          newItem.item_id = response.item_id;
          orderItems.value.push(newItem);
          ElMessage.success(`已添加器材: ${selectedMaterialInfo.material_name}`);
          
          // 编辑模式：清空选中信息，保持抽屉打开
          resetSelectedMaterialInfo();
        } catch (error: any) {
          // 优先处理detail字段中的详细信息
          if (error.response?.data?.detail) {
            const detail = error.response.data.detail;
            let errorMessage = '器材添加失败';
            
            // 判断detail是字符串还是对象
            if (typeof detail === 'string') {
              // detail是字符串，直接显示
              errorMessage = detail;
            } else if (typeof detail === 'object' && detail !== null) {
              // detail是对象，处理message字段和problematic_items
              errorMessage = detail.message || '器材添加失败';
              
              // 如果有问题器材列表，添加到错误信息中
              if (detail.problematic_items && detail.problematic_items.length > 0) {
                errorMessage += '\n\n无法添加器材，原因：\n';
                detail.problematic_items.forEach((problem: any) => {
                  errorMessage += `- ${problem.reason || '未知原因'}\n`;
                });
              }
            }
            
            ElMessage.error(errorMessage);
          } else {
            // 如果没有detail字段，使用原来的逻辑
            const errorMessage = error.response?.data?.message || error.message || '器材添加失败';
            ElMessage.error(`器材添加失败: ${errorMessage}`);
          }
          return;
        }
      } else {
        // 新增入库单模式：添加到器材列表，等待统一提交保存
        orderItems.value.push(newItem);
        ElMessage.success(`已添加器材: ${selectedMaterialInfo.material_name}`);
        
        // 新增模式：清空选中信息，但保持抽屉打开
        // 用户可以继续添加其他器材
        resetSelectedMaterialInfo();
      }
    }
  }
};

  // 清空选中器材信息
  const resetSelectedMaterialInfo = () => {
    selectedMaterialInfo.material_id = 0;
    selectedMaterialInfo.material_code = '';
    selectedMaterialInfo.material_name = '';
    selectedMaterialInfo.material_specification = '';
    selectedMaterialInfo.major_name = '';
    selectedMaterialInfo.equipment_name = '';
    selectedMaterialInfo.quantity = null;
    selectedMaterialInfo.unit = '';
    selectedMaterialInfo.unit_price = null;
    selectedMaterialInfo.batch_number = '';
    selectedMaterialInfo.bin_id = null; // 修改：将默认值从0改为null，表示未选择货位
    selectedMaterialInfo.bin_name = '';
    
    // 清除错误状态
    validationErrors.material_id = false;
    validationErrors.bin_id = false;
  };

  // 清除错误状态
  const clearValidationErrors = () => {
    validationErrors.material_id = false;
    validationErrors.bin_id = false;
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

// 处理数量变化（带防抖的实时更新）
const handleQuantityChange = debounce(async (index: number) => {
  // console.log(`数量变化: 第${index}行, 新数量: ${orderItems.value[index].quantity}`);
  if (isEdit.value && orderId.value && orderItems.value[index]) {
    const item = orderItems.value[index];
    
    // 检查数量是否真的发生了更改
    if (item.originalQuantity !== undefined && item.quantity === item.originalQuantity) {
      // 数量没有变化，不需要调用API
      return;
    }
    
    try {
      await inboundOrderAPI.updateInboundOrderItem(orderId.value, item.item_id!, {
        quantity: item.quantity,
        unit_price: item.unit_price || 0
      });
      
      // 更新成功后，保存当前数量作为新的原始数量
      item.originalQuantity = item.quantity;
      
      ElMessage.success(`数量更新成功: 第${index + 1}行, 新数量: ${item.quantity}`);
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = detail.message || '数量更新失败';
        
        // 判断detail是字符串还是对象
        if (typeof detail === 'string') {
          // detail是字符串，直接显示
          errorMessage = detail;
        } else if (detail.problematic_items && detail.problematic_items.length > 0) {
          // 如果有问题器材列表，添加到错误信息中
          errorMessage += '\n\n无法更新数量，原因：\n';
          detail.problematic_items.forEach((problem: any) => {
            errorMessage += `- ${problem.reason || '未知原因'}\n`;
          });
        }
        
        ElMessage.error(`数量更新失败: ${errorMessage}`);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '数量更新失败';
        ElMessage.error(`数量更新失败: ${errorMessage}`);
      }
    }
  }
}, 500); // 500ms防抖延迟

// 处理单价变化（带防抖的实时更新）
const handleUnitPriceChange = debounce(async (index: number) => {
  if (isEdit.value && orderId.value && orderItems.value[index]) {
    const item = orderItems.value[index];
    
    // 检查单价是否真的发生了更改
    if (item.originalUnitPrice !== undefined && item.unit_price === item.originalUnitPrice) {
      // 单价没有变化，不需要调用API
      return;
    }
    
    try {
      await inboundOrderAPI.updateInboundOrderItem(orderId.value, item.item_id!, {
        quantity: item.quantity,
        unit_price: item.unit_price || 0
      });
      
      // 更新成功后，保存当前单价作为新的原始单价
      item.originalUnitPrice = item.unit_price;
      
      ElMessage.success(`单价更新成功: 第${index + 1}行, 新单价: ${item.unit_price}`);
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = detail.message || '单价更新失败';
        
        // 判断detail是字符串还是对象
        if (typeof detail === 'string') {
          // detail是字符串，直接显示
          errorMessage = detail;
        } else if (detail.problematic_items && detail.problematic_items.length > 0) {
          // 如果有问题器材列表，添加到错误信息中
          errorMessage += '\n\n无法更新单价，原因：\n';
          detail.problematic_items.forEach((problem: any) => {
            errorMessage += `- ${problem.reason || '未知原因'}\n`;
          });
        }
        
        ElMessage.error(`单价更新失败: ${errorMessage}`);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '单价更新失败';
        ElMessage.error(`单价更新失败: ${errorMessage}`);
      }
    }
  }
}, 500); // 500ms防抖延迟




// 计算总金额
const totalAmount = computed(() => {
  return orderItems.value.reduce((sum, item) => {
    const amount = (item.quantity || 0) * (item.unit_price || 0);
    return Number((sum + amount).toFixed(3));
  }, 0);
});

// 定义事件
const emit = defineEmits<{
  back: []
  saved: []
}>();

// 返回入库单列表
const handleBack = () => {
  // 新增模式：草稿已自动保存，直接返回即可
  // 下次进入新建页面时会提示恢复草稿
  emit('back');
};

// 入库单号变更处理（实时保存）
const handleOrderNumberChange = async () => {
  // 如果是由日期变更触发的单号更新，不执行后续逻辑
  if (isDateTriggeringOrderNumber.value) {
    return;
  }
  
  if (isEdit.value && orderId.value && orderForm.order_number) {
    // 检查入库单号是否真的发生了更改
    if (orderForm.order_number === originalOrderForm.order_number) {
      // 入库单号没有变化，不需要调用API
      return;
    }
    
    try {
      await inboundOrderAPI.updateOrderNumber(orderId.value, { order_number: orderForm.order_number });
      // 更新成功后，保存当前入库单号作为新的原始值
      originalOrderForm.order_number = orderForm.order_number;
      ElMessage.success('入库单号更新成功');
    } catch (error: any) {
      // 显示具体的错误原因
      const errorMessage = error.response?.data?.message || error.message || '入库单号更新失败';
      ElMessage.error(`入库单号更新失败: ${errorMessage}`);
    }
  }
};

// 供应商变更处理（实时保存）
const handleSupplierChange = async () => {
  if (isEdit.value && orderId.value && orderForm.supplier_id) {
    // 检查供应商是否真的发生了更改
    if (orderForm.supplier_id === originalOrderForm.supplier_id) {
      // 供应商没有变化，不需要调用API
      return;
    }
    
    try {
      await inboundOrderAPI.updateSupplier(orderId.value, { supplier_id: orderForm.supplier_id });
      // 更新成功后，保存当前供应商作为新的原始值
      originalOrderForm.supplier_id = orderForm.supplier_id;
      ElMessage.success('供应商更新成功');
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = detail.message || '供应商更新失败';
        
        // 如果有问题器材列表，添加到错误信息中
        if (detail.problematic_items && detail.problematic_items.length > 0) {
          errorMessage += '\n\n无法更新供应商，原因：\n';
          detail.problematic_items.forEach((problem: any) => {
            errorMessage += `- ${problem.reason || '未知原因'}\n`;
          });
        }
        
        ElMessage.error(errorMessage);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '供应商更新失败';
        ElMessage.error(`供应商更新失败: ${errorMessage}`);
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
      await inboundOrderAPI.updateTransferNumber(orderId.value, { requisition_reference: orderForm.requisition_reference || '' });
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

// 合同号变更处理（实时保存）
const handleContractNumberChange = async () => {
  if (isEdit.value && orderId.value) {
    // 检查合同号是否真的发生了更改
    if (orderForm.contract_reference === originalOrderForm.contract_reference) {
      // 合同号没有变化，不需要调用API
      return;
    }
    
    try {
      await inboundOrderAPI.updateContractNumber(orderId.value, { contract_reference: orderForm.contract_reference || '' });
      // 更新成功后，保存当前合同号作为新的原始值
      originalOrderForm.contract_reference = orderForm.contract_reference || '';
      ElMessage.success('合同号更新成功');
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = detail.message || '合同号更新失败';
        
        // 如果有问题器材列表，添加到错误信息中
        if (detail.problematic_items && detail.problematic_items.length > 0) {
          errorMessage += '\n\n无法更新合同号，原因：\n';
          detail.problematic_items.forEach((problem: any) => {
            errorMessage += `- ${problem.reason || '未知原因'}\n`;
          });
        }
        
        ElMessage.error(errorMessage);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '合同号更新失败';
        ElMessage.error(`合同号更新失败: ${errorMessage}`);
      }
    }
  }
};

// 标记：是否由入库日期变更触发的单号更新（防止递归）
const isDateTriggeringOrderNumber = ref(false);

// 入库日期变更处理（实时保存）
const handleInboundDateChange = async () => {
  // 同步更新入库单号中的日期部分
  if (orderForm.inbound_date && orderForm.order_number) {
    updateOrderNumberDate(orderForm.inbound_date);
  }
  
  if (isEdit.value && orderId.value && orderForm.inbound_date) {
    // 检查入库日期是否真的发生了更改
    if (orderForm.inbound_date === originalOrderForm.inbound_date) {
      // 入库日期没有变化，不需要调用API
      return;
    }
    
    try {
      // 将日期转换为datetime格式（添加时间部分）
      const createTime = `${orderForm.inbound_date}T00:00:00`;
      await inboundOrderAPI.updateCreateTime(orderId.value, { create_time: createTime });
      // 更新成功后，保存当前入库日期作为新的原始值
      originalOrderForm.inbound_date = orderForm.inbound_date;
      ElMessage.success('入库日期更新成功');
    } catch (error: any) {
      // 优先处理detail字段中的详细信息
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        let errorMessage = detail || detail.message || '入库日期更新失败';
        
        // 如果有问题器材列表，添加到错误信息中
        if (detail.problematic_items && detail.problematic_items.length > 0) {
          errorMessage += '\n\n无法更新入库日期，原因：\n';
          detail.problematic_items.forEach((problem: any) => {
            errorMessage += `- ${problem.reason || '未知原因'}\n`;
          });
        }
        
        ElMessage.error(errorMessage);
      } else {
        // 如果没有detail字段，使用原来的逻辑
        const errorMessage = error.response?.data?.message || error.message || '入库日期更新失败';
        ElMessage.error(`入库日期更新失败: ${errorMessage}`);
      }
    }
  }
};

// 更新入库单号中的日期部分
const updateOrderNumberDate = async (newDate: string) => {
  if (!orderForm.order_number || isDateTriggeringOrderNumber.value) {
    return;
  }
  
  // 入库单号格式: RK20231225-001
  // 匹配格式: RK + 8位数字(YYYYMMDD) + - + 3位数字
  const orderNumberPattern = /^(RK)(\d{8})(-.+)$/;
  const match = orderForm.order_number.match(orderNumberPattern);
  
  if (match) {
    // 将日期格式从 YYYY-MM-DD 转换为 YYYYMMDD
    const dateStr = newDate.replace(/-/g, '');
    
    // 检查日期格式是否正确（8位数字）
    if (dateStr.length === 8 && /^\d{8}$/.test(dateStr)) {
      try {
        // 设置标记，防止触发handleOrderNumberChange
        isDateTriggeringOrderNumber.value = true;
        
        // 调用后端API重新生成入库单号，避免重复单号
        const response = await inboundOrderAPI.generateInboundOrderNumber(dateStr);
        const newOrderNumber = response.order_number;
        
        orderForm.order_number = newOrderNumber;
        
        // 如果是编辑模式，需要调用API将新单号写入数据库
        if (isEdit.value && orderId.value) {
          try {
            await inboundOrderAPI.updateOrderNumber(orderId.value, { order_number: newOrderNumber });
            // 数据库更新成功后，同步更新原始值
            originalOrderForm.order_number = newOrderNumber;
            ElMessage.success('入库单号已更新');
          } catch (updateError: any) {
            // 数据库更新失败，恢复原单号
            const updateErrorMessage = updateError.response?.data?.message || updateError.message || '入库单号写入数据库失败';
            ElMessage.error(`入库单号更新失败: ${updateErrorMessage}`);
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
        console.error('重新生成入库单号失败:', error);
        const errorMessage = error.response?.data?.message || error.message || '重新生成入库单号失败';
        ElMessage.warning(`入库单号更新失败: ${errorMessage}，请手动修改`);
        
        // 重置标记
        isDateTriggeringOrderNumber.value = false;
      }
    }
  }
};


// 保存入库单
const handleSave = async () => {
  try {
    // 验证表单
    if (!orderFormRef.value) return;
    
    const valid = await orderFormRef.value.validate();
    if (!valid) return;
    
    // 验证明细
    if (orderItems.value.length === 0) {
      ElMessage.warning('请至少添加一条入库明细');
      return;
    }
    
    saving.value = true;
    
    // 构建入库单数据
    const orderData: InboundOrderCreate = {
      ...orderForm,
      supplier_id: orderForm.supplier_id || 0, // 确保supplier_id不为null
      items: orderItems.value.map(item => ({
        material_id: item.material_id,
        quantity: item.quantity,
        unit: item.unit,
        unit_price: item.unit_price,
        batch_number: item.batch_number,
        bin_id: item.bin_id,
        production_date: item.production_date
      }))
    };
    
    if (isEdit.value && orderId.value) {
      // 编辑模式下，各个字段已经通过实时更新函数自动保存
      // 这里只需要显示成功消息即可
      ElMessage.success('入库单信息已通过实时更新保存');
    } else {
      // 新增入库单
      console.log('入库单创建数据:', orderData);
      await inboundOrderAPI.createInboundOrder(orderData);
      ElMessage.success('入库单创建成功');
      // 保存成功后清除草稿
      clearDraft(DRAFT_KEY);
  }
  
  // 触发保存成功事件
  emit('saved');
  } catch (error: any) {
    // 优化错误处理逻辑，确保能够正确显示后端返回的详细错误信息
    let errorMessage = '保存失败';
    
    if (error.response?.data) {
      const responseData = error.response.data;
      
      // 优先处理detail字段
      if (responseData.detail) {
        const detail = responseData.detail;
        
        // 判断detail是字符串还是对象
        if (typeof detail === 'string') {
          // detail是字符串，直接显示
          errorMessage = detail;
        } else if (typeof detail === 'object' && detail !== null) {
          // detail是对象，处理message字段和problematic_items
          errorMessage = detail.message || '保存失败';
          
          // 如果有问题器材列表，添加到错误信息中
          if (detail.problematic_items && detail.problematic_items.length > 0) {
            errorMessage += '\n\n无法保存入库单，原因：\n';
            detail.problematic_items.forEach((problem: any) => {
              errorMessage += `- ${problem.reason || '未知原因'}\n`;
            });
          }
        }
      } else if (responseData.message) {
        // 如果没有detail字段，但有message字段
        errorMessage = responseData.message;
      } else {
        // 如果只有简单的错误信息
        errorMessage = '保存失败，请检查数据是否正确';
      }
    } else if (error.message) {
      // 使用错误对象的message
      errorMessage = error.message;
    }
    
    // 显示详细的错误信息
    ElMessage.error(errorMessage);
  } finally {
    saving.value = false;
  }
};

// 初始化数据
const initData = async () => {
  await getSuppliers();
  
  // 如果是编辑模式，加载入库单详情
  if (isEdit.value && orderId.value) {
    try {
      const response = await inboundOrderAPI.getInboundOrderDetail(orderId.value);
      // 赋值订单基本信息，包括supplier_name
      Object.assign(orderForm, response.order);
      // 保存原始值，包括supplier_name
      Object.assign(originalOrderForm, response.order);
      
      // 为每个明细项获取仓库名称和专业名称
      const itemsWithAdditionalInfo = await Promise.all(
        response.items.map(async (item) => {
          let warehouse_name = '';
          let major_name = '';
          
          // 根据货位ID获取仓库名称
          if (item.bin_id) {
            warehouse_name = await getWarehouseNameByBinId(item.bin_id);
          }
          
          // 根据器材ID获取专业名称
          if (item.material_id) {
            try {
              const materialDetail = await materialAPI.getMaterial(item.material_id);
              major_name = materialDetail.major_name || '';
            } catch (error) {
              console.error('获取器材专业信息失败:', error);
            }
          }
          
          return {
            item_id: item.item_id, // 添加item_id字段
            material_id: item.material_id,
            material_code: item.material_code,
            material_name: item.material_name,
            material_specification: item.material_specification,
            batch_number: item.batch_number,
            quantity: item.quantity,
            unit_price: item.unit_price,
            unit: item.unit,
            bin_id: item.bin_id,
            bin_name: item.bin_name,
            equipment_name: item.equipment_name || '',
            warehouse_name: warehouse_name,
            major_name: major_name,
            production_date: item.production_date,
            originalQuantity: item.quantity, // 保存原始数量
            originalUnitPrice: item.unit_price // 保存原始单价
          };
        })
      );
      
      orderItems.value = itemsWithAdditionalInfo;
      
      // 编辑模式下清除草稿（如果有）
      if (hasDraft(DRAFT_KEY)) {
        clearDraft(DRAFT_KEY);
      }
    } catch (error: any) {
      // 显示具体的错误原因
      const errorMessage = error.response?.data?.message || error.message || '加载入库单详情失败';
      ElMessage.error(`加载入库单详情失败: ${errorMessage}`);
    }
  } else {
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
        const draftData = loadDraft<InboundOrderDraftData>(DRAFT_KEY);
        if (draftData) {
          // 恢复表单数据
          Object.assign(orderForm, draftData.orderForm);
          // 恢复明细数据
          orderItems.value = draftData.orderItems;
          ElMessage.success('草稿已恢复');
        } else {
          // 草稿加载失败，继续正常流程
          orderForm.order_number = await generateOrderNumber();
          orderForm.inbound_date = new Date().toISOString().split('T')[0];
        }
      } catch (error) {
        // 用户点击"放弃草稿"或关闭对话框，对话框已自动关闭
        clearDraft(DRAFT_KEY);
        // 继续正常流程
        orderForm.order_number = await generateOrderNumber();
        orderForm.inbound_date = new Date().toISOString().split('T')[0];
      }
    } else {
      // 没有草稿，正常生成入库单号
      orderForm.order_number = await generateOrderNumber();
      orderForm.inbound_date = new Date().toISOString().split('T')[0];
    }
  }
};

// 生成入库单号
const generateOrderNumber = async (): Promise<string> => {
  try {
    // 获取当前日期，格式为YYYYMMDD
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const dateStr = `${year}${month}${day}`;
    
    // 调用API生成入库单号
    const response = await inboundOrderAPI.generateInboundOrderNumber(dateStr);
    return response.order_number;
  } catch (error: any) {
    // 显示具体的错误原因
    const errorMessage = error.response?.data?.message || error.message || '生成入库单号失败';
    ElMessage.error(`生成入库单号失败: ${errorMessage}，使用默认单号`);
    
    // 如果API调用失败，使用默认的生成逻辑
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const dateStr = `${year}${month}${day}`;
    const serialNumber = String(Math.floor(Math.random() * 999) + 1).padStart(3, '0');
    
    return `RK${dateStr}-${serialNumber}`;
  }
};

// 根据货位ID获取仓库名称
const getWarehouseNameByBinId = async (binId: number): Promise<string> => {
  try {
    const binResponse = await binApi.getBin(binId);
    return binResponse.warehouse_name || '';
  } catch (error) {
    console.error('获取仓库名称失败:', error);
    return '';
  }
};

// 监听props.editId的变化
watch(() => props.editId, (newEditId: number | null | undefined) => {
  if (newEditId) {
    isEdit.value = true;
    orderId.value = newEditId;
    initData();
  } else {
    // 新增模式
    isEdit.value = false;
    orderId.value = null;
    initData();
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
        console.log('器材列表滚动监听器绑定成功');
      } else {
        setTimeout(() => tryInit(count + 1), 200);
      }
    });
  };
  tryInit();
};

// 监听货位/器材列表切换，确保切换回来时能重新绑定
watch(() => showBinList.value, (newVal) => {
  if (!newVal && materialDrawerVisible.value) {
    initTableScroll();
  }
});

// 滚动事件处理函数
const handleTableScroll = (event: any) => {
  // 如果正在程序化滚动定位，屏蔽滚动加载逻辑，防止“落地跳页”
  if (isLocatingScroll.value) return;

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

/* 错误边框样式 */
.error-border {
  :deep(.el-input__wrapper) {
    border-color: #f56c6c !important;
    box-shadow: 0 0 0 1px #f56c6c !important;
  }
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

/* 器材选择抽屉样式 */
.material-select-layout {
  display: flex;
  flex: 1; /* 自动填充剩余空间 */
  min-height: 0; /* 允许 flex 项目缩小，防止溢出 */
  gap: 20px;
  margin-bottom: 10px; /* 减少底部间距 */
}

.material-info-section {
  flex: 0 0 600px; /* 固定宽度600px */
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 防止内容溢出 */
}

.material-info-header {
  margin-bottom: 20px;
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 10px;
  flex-shrink: 0; /* 防止头部被压缩 */
}

.material-info-header h4 {
  margin: 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.material-info-form {
  flex: 1;
  overflow-y: auto;
  min-height: 0; /* 防止内容溢出 */
}

.material-list-section {
  flex: 1; /* 占据剩余空间，空间不够时自动缩小 */
  min-width: 400px; /* 设置最小宽度，防止缩得太小 */
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 0; /* 防止内容溢出 */
}

.material-filter-section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  flex-shrink: 0; /* 防止筛选区域被压缩 */
}

.material-table-section {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0; /* 防止内容溢出 */
}

.material-table {
  width: 100%;
  flex: 1; /* 表格占据剩余空间 */
  min-height: 0; /* 防止内容溢出 */
}

.material-drawer-footer {
  margin-top: 0; /* 移除自动边距 */
  text-align: center;
  padding: 10px 0; /* 减少上下边距 */
  border-top: 1px solid #e9ecef;
  background: #fff;
  position: sticky;
  bottom: 0;
  z-index: 10;
  flex-shrink: 0; /* 防止按钮区域被压缩 */
}

/* 确保抽屉内容区域有足够的空间 */
:deep(.el-drawer__body) {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px 20px 0 20px; /* 移除底部内边距，因为 footer 已经有边距了 */
}

/* 调整抽屉整体布局 */
.material-drawer-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 20px;
}

/* 表单样式优化 */
:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f5f7fa;
  border-color: #e4e7ed;
}

:deep(.el-input.is-disabled .el-input__inner) {
  color: #c0c4cc;
}

/* 选择器材对话框标题样式 - 移除默认padding和margin */
:deep(.el-drawer__header) {
  margin-bottom: 0 !important;
}

:deep(.el-drawer__title) {
  margin: 0 !important;
  padding: 0 !important;
}

/* 单位选择组件样式 */
.unit-input-container {
  position: relative;
  width: 100%;
}

.unit-dropdown {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  z-index: 2000;
  max-height: 150px;
  overflow-y: auto;
  margin-bottom: 2px;
}

.unit-options {
  padding: 5px 0;
}

.unit-option {
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.3s;
  font-size: 14px;
  color: #606266;
}

.unit-option:hover {
  background-color: #f5f7fa;
}

.unit-option.custom-unit {
  background-color: #f0f9ff;
  border-top: 1px solid #e4e7ed;
  color: #409eff;
}

.unit-option.custom-unit:hover {
  background-color: #ecf5ff;
}

.unit-option.custom-unit strong {
  font-weight: 600;
}

.unit-option.no-match {
  color: #c0c4cc;
  font-style: italic;
  cursor: default;
}

.unit-option.no-match:hover {
  background-color: transparent;
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