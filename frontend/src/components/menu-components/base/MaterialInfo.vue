<template>
  <div class="base-management-container">
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
        <p>您没有足够的权限访问器材管理功能。</p>
        <p>需要权限：<el-tag type="danger">BASE-read</el-tag></p>
        <p>请与管理员联系以获取相应权限。</p>
      </template>
    </el-alert>

    <!-- 器材管理内容 -->
    <div v-else class="base-content base-flex-content">
      <!-- 操作栏 -->
      <el-card class="base-operation-card" shadow="hover">
        <div class="base-operation-bar">
          <div class="base-operation-bar__left">
            <el-button 
              type="primary" 
              @click="handleCreate"
              :icon="Plus"
              v-if="hasPermission('BASE-edit')"
            >
              新增器材
            </el-button>
            <el-button 
              type="default" 
              @click="getMaterialList"
              :loading="loading"
              :icon="Refresh"
            >
              刷新
            </el-button>
            <!-- 批量删除按钮 -->
            <el-button 
              v-if="selectedIds.length > 0 && hasPermission('BASE-edit')"
              type="danger" 
              @click="handleBatchDelete" 
              :icon="Delete"
            >
              批量删除 ({{ selectedIds.length }})
            </el-button>
          </div>
          <div class="base-operation-bar__right">
            <!-- 专业筛选下拉框 -->
            <el-select
              filterable
              v-model="queryParams.major_id"
              placeholder="筛选专业"
              clearable
              style="width: 150px;"
              @change="handleMajorChange"
            >
              <el-option
                v-for="major in majors"
                :key="major.id"
                :label="major.major_name"
                :value="major.id"
              />
            </el-select>
            
            <!-- 装备筛选下拉框 -->
            <el-select
              filterable
              v-model="queryParams.equipment_id"
              placeholder="筛选装备"
              clearable
              style="width: 200px;"
              @change="handleSearch"
            >
              <el-option
                v-for="equipment in filteredEquipments"
                :key="equipment.id"
                :label="equipment.equipment_name + (equipment.specification ? '  ' + equipment.specification : '')"
                :value="equipment.id"
              />
            </el-select>
            
            <el-input
              v-model="queryParams.search"
              placeholder="输入搜索关键词，用空格分隔"
              style="width: 320px;"
              clearable
              @input="handleSearch"
              @clear="handleSearch"
            />
          </div>
        </div>
      </el-card>

      <!-- 器材列表 -->
      <el-card class="base-table-card base-table-card--flex" shadow="hover">
        <template #header>
          <div class="base-card-header">
            <el-icon><List /></el-icon>
            <span>器材列表</span>
            <div class="base-card-header__stats" v-if="total > 0">
              <span>总计: {{ total }}</span>
            </div>
          </div>
        </template>

        <!-- 加载状态 -->
        <div v-if="loading" class="base-loading-container">
          <el-skeleton :rows="8" animated />
        </div>

        <!-- 器材表格 -->
        <div v-else class="base-table base-table--auto-height">
          <el-table
            ref="tableRef"
            :data="tableData"
            stripe
            border
            :empty-text="'暂无器材数据'"
            class="base-table"
            @selection-change="handleSelectionChange"
            @sort-change="handleSortChange"
          >
            <el-table-column type="selection" width="55" align="center" />
            <el-table-column 
              prop="material_code" 
              label="器材编码" 
              min-width="120" 
              align="center" 
              fixed="left"
              sortable="custom"
              :sort-orders="['ascending', 'descending']"
            >
            </el-table-column>
            <el-table-column 
              prop="material_name" 
              label="器材名称" 
              width="150" 
              align="center" 
              fixed="left"
              sortable="custom"
              :sort-orders="['ascending', 'descending']"
            >
              <template #default="{ row }">
                <div class="base-cell base-cell-primary">{{ row.material_name }}</div>
              </template>
            </el-table-column>
            <el-table-column prop="material_specification" label="器材规格" width="120" align="center" />
            <el-table-column prop="material_query_code" label="查询码" width="120" align="center" />
                    
            <el-table-column prop="major_name" label="所属专业" width="120" align="center" />
            <el-table-column prop="equipment_name" label="所属装备" width="120" align="center" />
            <el-table-column prop="safety_stock" label="安全库存" width="100" align="center" />
            
            <el-table-column prop="material_wdh" label="长宽高" width="100" align="center" />
            <el-table-column prop="material_desc" label="器材描述" width="150" align="center" />
            <el-table-column 
              v-if="false"
              prop="id" 
              label="ID" 
              width="80" 
              align="center" 
              sortable="custom"
              :sort-orders="['ascending', 'descending']"
            />
            <el-table-column 
              prop="create_time" 
              label="创建时间" 
              width="150" 
              align="center" 
              sortable="custom"
              :sort-orders="['ascending', 'descending']"
            />
            <el-table-column prop="creator" label="创建人" width="100" align="center" />
            <el-table-column label="操作" width="120" align="center" fixed="right" v-if="hasPermission('BASE-edit')">
              <template #default="{ row }">
                <div class="base-action-buttons">
                  <ActionTooltip content="编辑器材">
                    <el-button 
                      type="primary"
                      size="small"
                      @click="handleEdit(row)"
                      :icon="Edit"
                      class="base-button-circle"
                      v-if="hasPermission('BASE-edit')"
                    />
                  </ActionTooltip>
                  <ActionTooltip content="删除器材">
                    <el-button 
                      type="danger"
                      size="small"
                      @click="handleDelete(row)"
                      :icon="Delete"
                      class="base-button-circle"
                      v-if="hasPermission('BASE-edit')"
                    />
                  </ActionTooltip>
                </div>
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

      <!-- 新增/编辑抽屉 -->
      <el-drawer
        :title="dialogTitle"
        v-model="dialogVisible"
        direction="rtl"
        size="900px"
        :before-close="handleDialogClose"
        :modal="true"
        class="base-drawer"
      >
        <div class="base-drawer-body">
          <div class="equipment-select-layout">
            <!-- 左侧：编辑区域 -->
            <div class="edit-section">
              <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
                <el-form-item label="器材编码" prop="material_code">
                  <el-input 
                    v-model="form.material_code" 
                    placeholder="可不用输入，自动生成" 
                    @focus="handleMaterialCodeFocus"
                  />
                </el-form-item>
                
                <el-form-item label="器材名称" prop="material_name">
                  <div style="display: flex; align-items: center; gap: 8px; width: 100%;">
                    <el-input 
                      v-model="form.material_name" 
                      placeholder="请输入器材名称" 
                      @focus="() => {
                          showMaterialCodePanel = false;
                          showEquipmentPanel = false;
                          showMaterialSearchPanel = true;
                        }"
                      style="flex: 1;"
                    />
                    <el-tooltip 
                      content="将常用器材关键字添加到专业描述中，这样下次你输入这个名字时可以自动筛选出专业" 
                      placement="top"
                    >
                      <el-button 
                        type="info" 
                        @click="handleAddDescriptionFromSearch" 
                        class="base-button"
                        size="small"
                      >
                        添加专业描述
                      </el-button>
                    </el-tooltip>
                  </div>
                </el-form-item>
                
                <el-form-item label="器材规格">
                  <el-input v-model="form.material_specification" placeholder="请输入器材规格" />
                </el-form-item>
                
                <el-form-item label="器材描述">
                  <el-input v-model="form.material_desc" placeholder="请输入器材描述" />
                </el-form-item>
                
                <el-form-item label="长宽高">
                  <el-input v-model="form.material_wdh" placeholder="例如：100×50×30" />
                </el-form-item>
                
                <el-form-item label="安全库存">
                  <el-tooltip content="如果设为0，系统将不进行安全库存检测" placement="right">
                    <el-input-number v-model="form.safety_stock" :min="0" placeholder="请输入安全库存" />
                  </el-tooltip>
                </el-form-item>
                
                <el-form-item label="查询码">
                  <el-input v-model="form.material_query_code" placeholder="可自定义查询码，不填则自动生成" />
                </el-form-item>
                
                <el-form-item label="所属专业" prop="major_id">
                  <el-select v-model="form.major_id" placeholder="请选择专业" @change="handleDrawerMajorChange">
                    <el-option
                      v-for="major in majors"
                      :key="major.id"
                      :label="major.major_name"
                      :value="major.id"
                    />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="所属装备" prop="equipment_id">
                  <div class="equipment-selection">
                    <el-input 
                      v-model="selectedEquipmentName" 
                      placeholder="点击右侧选择装备" 
                      readonly 
                      @focus="() => {
                        showMaterialCodePanel = false;
                        showEquipmentPanel = true;
                        showMaterialSearchPanel = false;
                        // 根据当前选择的专业筛选装备
                        equipmentSearchParams.major_id = form.major_id;
                        equipmentSearchParams.page = 1;
                        searchEquipments();
                      }"
                    >
                      <template #append>
                        <el-button @click="clearEquipmentSelection" :icon="Delete" />
                      </template>
                    </el-input>
                  </div>
                </el-form-item>
              </el-form>
            </div>
            
            <!-- 右侧：装备/器材查询区域 -->
            <div class="equipment-search-section" v-show="showEquipmentPanel || showMaterialSearchPanel || showMaterialCodePanel">
              <!-- 装备搜索面板 -->
              <div v-show="showEquipmentPanel">
                <div class="equipment-search-header">
                  <div class="header-row">
                    <h4>选择装备</h4>
                    <div class="search-controls">
                      <el-input
                        v-model="equipmentSearchParams.search"
                        placeholder="搜索装备名称或型号"
                        clearable
                        style="width: 150px;"
                        @input="handleEquipmentSearch"
                        @clear="handleEquipmentSearch"
                      />
                    </div>
                  </div>
                </div>
                
                <div class="equipment-list-container">
                  <div v-if="equipmentLoading" class="loading-container">
                    <el-skeleton :rows="5" animated />
                  </div>
                  
                  <div v-else class="equipment-list">
                    <div 
                      v-for="equipment in searchedEquipments" 
                      :key="equipment.id"
                      class="equipment-item"
                      :class="{ 'selected': form.equipment_id === equipment.id }"
                      @dblclick="selectEquipment(equipment)"
                    >
                      <div class="equipment-name-spec">
                        <span class="equipment-name">{{ equipment.equipment_name }}</span>
                        <span class="equipment-spec">{{ equipment.specification ? `(${equipment.specification})` : '' }}</span>
                      </div>
                      <div class="equipment-major">{{ equipment.major_name || '未分类' }}</div>
                    </div>
                    
                    <div v-if="searchedEquipments.length === 0" class="empty-state">
                      <el-empty description="暂无装备数据" />
                    </div>
                  </div>
                </div>
                
                <div class="equipment-pagination" v-if="equipmentTotal > 0">
                  <el-pagination
                    v-model:current-page="equipmentSearchParams.page"
                    v-model:page-size="equipmentSearchParams.page_size"
                    :total="equipmentTotal"
                    :page-sizes="[10, 20, 50]"
                    layout="prev, pager, next, sizes"
                    small
                    @size-change="handleEquipmentSearch"
                    @current-change="handleEquipmentSearch"
                  />
                </div>
              </div>
              
              <!-- 器材搜索面板 -->
              <div v-show="showMaterialSearchPanel">
                <div class="equipment-search-header">
                  <div class="header-row">
                    <h4>现有器材列表</h4>
                    <div class="search-controls">
                      <el-input
                        v-model="materialSearchParams.search"
                        placeholder="搜索器材名称"
                        clearable
                        style="width: 150px;"
                        @input="handleMaterialSearch"
                        @clear="handleMaterialSearch"
                      />
                    </div>
                  </div>
                </div>
                
                <div class="equipment-list-container">
                  <div v-if="materialSearchLoading" class="loading-container">
                    <el-skeleton :rows="5" animated />
                  </div>
                  
                  <div v-else class="equipment-list">
                    <div 
                      v-for="material in searchedMaterials" 
                      :key="material.id"
                      class="equipment-item"
                      @dblclick="selectMaterial(material)"
                    >
                      <div class="equipment-name-spec">
                        <span class="equipment-name">{{ material.material_name }}</span>
                        <span class="equipment-spec">{{ material.material_specification ? `(${material.material_specification})` : '' }}</span>
                      </div>
                      <div class="equipment-major">{{ material.material_code }} {{ material.major_name ? `(${material.major_name}` : '' }}{{ material.equipment_name ? `-${material.equipment_name})` : (material.major_name ? ')' : '') }}</div>
                    </div>
                    
                    <div v-if="searchedMaterials.length === 0" class="empty-state">
                      <el-empty description="暂无器材数据" />
                    </div>
                  </div>
                </div>
                
                <div class="equipment-pagination" v-if="materialTotal > 0">
                  <el-pagination
                    v-model:current-page="materialSearchParams.page"
                    v-model:page-size="materialSearchParams.page_size"
                    :total="materialTotal"
                    :page-sizes="[10, 20, 50]"
                    layout="prev, pager, next, sizes"
                    small
                    @size-change="handleMaterialSearch"
                    @current-change="handleMaterialSearch"
                  />
                </div>
              </div>
              
              <!-- 器材编码推荐面板 -->
                <div v-show="showMaterialCodePanel">
                  <div class="equipment-search-header">
                    <div class="header-row">
                      <h4>器材编码推荐</h4>
                      <div class="search-controls">
                        <el-input
                          v-model="materialCodeSearchParams.search"
                          placeholder="搜索专业名称或描述"
                          clearable
                          style="width: 150px;"
                          @input="handleMaterialCodeSearch"
                          @clear="handleMaterialCodeSearch"
                        />

                      </div>
                    </div>
                  </div>
                
                <!-- 专业选择区域 -->
                <div class="material-code-level-list-container">                
                  <div v-if="materialCodeLevelLoading" class="loading-container">
                    <el-skeleton :rows="5" animated />
                  </div>
                  
                  <div v-else class="material-code-level-list" style="max-height: 200px; overflow-y: auto;">
                    <div v-if="filteredMaterialCodeLevels.length === 0" class="empty-state">
                      <el-empty description="暂无专业数据" />
                    </div>
                    
                    <div v-else class="material-code-level-items">
                      <div 
                        v-for="level in filteredMaterialCodeLevels" 
                        :key="level.id"
                        class="material-code-level-item"
                        :class="{ 'selected': selectedMaterialCodeLevel?.id === level.id }"
                        @click="selectMaterialCodeLevel(level)"
                      >
                        <div class="level-info">
                          <div class="level-name-code">
                            <span class="level-name">{{ level.sub_major_name }}</span>
                            <span class="level-code">({{ level.sub_major_code }})</span>
                          </div>
                          <div class="major-info">
                            {{ level.major_name }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 专业选择下拉列表 -->
                <div class="professional-selection-container">
                  <div class="professional-selection-header">
                    <h4>专业选择</h4>
                  </div>
                  
                  <div class="professional-selection-form">
                    <el-form label-width="80px">
                      <el-form-item label="一级专业">
                        <el-select 
                          v-model="selectedPrimaryMajor" 
                          placeholder="请选择一级专业"
                          @change="handlePrimaryMajorChange"
                          style="width: 100%;"
                          clearable
                          filterable
                        >
                          <el-option
                            v-for="major in validPrimaryMajors"
                            :key="major.id"
                            :label="major.major_name"
                            :value="major.major_code"
                          />
                        </el-select>
                      </el-form-item>
                      
                      <el-form-item label="二级专业">
                        <el-select 
                          v-model="selectedSecondaryMajor" 
                          placeholder="请先选择一级专业"
                          :disabled="!selectedPrimaryMajor"
                          @change="handleSecondaryMajorChange"
                          style="width: 100%;"
                          clearable
                          filterable
                        >
                          <el-option
                            v-for="major in validSecondaryMajors"
                            :key="major.id"
                            :label="major.sub_major_name"
                            :value="major.sub_major_code"
                          />
                        </el-select>
                        <div v-if="selectedPrimaryMajor && validSecondaryMajors.length === 0" style="color: #909399; font-size: 12px; margin-top: 4px;">
                          该一级专业下暂无二级专业
                        </div>
                      </el-form-item>
                      
                      <el-form-item label="推荐编码">
                        <el-input 
                          v-model="recommendedMaterialCode" 
                          placeholder="请选择两级专业后生成"
                          readonly
                          style="width: 100%;"
                        />
                      </el-form-item>
                    </el-form>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <template #footer>
          <div class="base-drawer-footer">
            <el-button @click="dialogVisible = false" class="base-button">取消</el-button>

            <el-button type="primary" @click="handleSubmit" :loading="dialogLoading" class="base-button">
              确定
            </el-button>
          </div>
        </template>
      </el-drawer>

      <!-- 添加专业描述对话框 -->
      <AddDescriptionDialog
            ref="addDescriptionDialogRef"
            :material-name="form.material_name"
            :search-text="materialCodeSearchParams.search"
            @success="handleAddDescriptionSuccess"
            @close="handleAddDescriptionDialogClose"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, computed, watch, inject, type Ref } from 'vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { 
  Plus, 
  Refresh, 
  List, 
  Edit, 
  Delete
} from '@element-plus/icons-vue';
import { materialAPI } from '@/services/base/material.ts';
import { majorAPI } from '@/services/base/major';
import { subMajorAPI } from '@/services/base/sub_major';
import { equipmentApi } from '@/services/base/equipment';
import type { MaterialResponse, MaterialCreate, MaterialUpdate, MaterialPaginationParams } from '@/services/types/material.ts';
import type { Equipment } from '@/services/types/equipment';

import type { MajorResponse } from '@/services/types/major';
import type { SubMajorResponse } from '@/services/types/sub_major';
import ActionTooltip from './ActionTooltip.vue';
import AddDescriptionDialog from './AddDescriptionDialog.vue';

interface Major {
  id: number;
  major_name: string;
}

const loading = ref(false);
const dialogVisible = ref(false);
const dialogLoading = ref(false);
const dialogTitle = ref('');
const formRef = ref<FormInstance>();
const tableRef = ref();
const selectedIds = ref<number[]>([]);

const queryParams = reactive<MaterialPaginationParams>({
  page: 1,
  page_size: 10,
  sort_field: 'id',
  sort_asc: true
});

const form = reactive({
  id: 0,
  material_code: '',
  material_name: '',
  material_specification: '',
  material_desc: '',
  material_wdh: '',
  safety_stock: 0,
  material_query_code: '',
  major_id: undefined as number | undefined,
  equipment_id: undefined as number | undefined
});

// 临时保存的数据
const tempFormData = ref<typeof form | null>(null)
const lastMenuType = ref<'create' | 'edit' | null>(null)
// 保存原始数据用于比较
const originalFormData = ref<typeof form | null>(null)

const rules: FormRules = {
  material_code: [{ required: true, message: '请输入器材编码', trigger: ['blur', 'change'] }],
  material_name: [{ required: true, message: '请输入器材名称', trigger: ['blur', 'change'] }]
};

const tableData = ref<MaterialResponse[]>([]);
const total = ref(0);
const majors = ref<Major[]>([]);
const equipments = ref<Equipment[]>([]);

// 装备选择相关变量
const showEquipmentPanel = ref(false);
const equipmentLoading = ref(false);
const searchedEquipments = ref<Equipment[]>([]);
const equipmentTotal = ref(0);

const equipmentSearchParams = reactive({
  search: '',
  major_id: undefined as number | undefined,
  page: 1,
  page_size: 10
});

// 器材名称搜索相关变量
const showMaterialSearchPanel = ref(false);
const materialSearchLoading = ref(false);
const searchedMaterials = ref<MaterialResponse[]>([]);
const materialTotal = ref(0);

const materialSearchParams = reactive({
  search: '',
  page: 1,
  page_size: 10
});

// 器材编码推荐相关变量
const showMaterialCodePanel = ref(false);
const materialCodeLevelLoading = ref(false);
const selectedMaterialCodeLevel = ref<MajorResponse | SubMajorResponse | null>(null);

// 添加专业描述相关变量
const addDescriptionDialogRef = ref();

// 权限检查相关
const currentUser = inject<Ref<any | null>>('currentUser') || ref<any | null>(null)

/**
 * 检查当前用户是否拥有指定权限
 * @param permission 权限名称字符串，如 'BASE-read', 'BASE-edit'
 * @returns boolean - 用户是否拥有该权限
 */
const hasPermission = (permission: string): boolean => {
  if (!currentUser.value || !currentUser.value.permissions) {
    // 如果没有用户信息或权限信息，尝试从localStorage获取
    const userData = localStorage.getItem('userData')
    if (userData) {
      try {
        const parsedUserData = JSON.parse(userData)
        return parsedUserData.permissions?.includes(permission) || false
      } catch (err) {
        console.error('解析用户数据失败:', err)
      }
    }
    return false
  }
  return currentUser.value.permissions.includes(permission)
}

const materialCodeSearchParams = reactive({
  search: '',
  page: 1,
  page_size: 10
});

// 处理器材编码输入框获取焦点事件
const handleMaterialCodeFocus = async () => {
  if (dialogTitle.value === '编辑器材' && form.material_code) {
    // 编辑模式下，根据当前器材编码解析并填充专业数据
    try {
      // 显示器材编码面板
      showMaterialCodePanel.value = true;
      showEquipmentPanel.value = false;
      showMaterialSearchPanel.value = false;
      
      // 解析器材编码（假设编码格式为：一级专业代码 + 二级专业代码 + 序列号）
      const materialCode = form.material_code;
      
      // 确保专业数据已加载
      if (primaryMajors.value.length === 0 || secondaryMajors.value.length === 0) {
        await loadAllMaterialCodeLevels();
      }
      
      // 尝试匹配一级专业（一般为1-2位）
      let matchedPrimary = null;
      let matchedSecondary = null;
      
      // 遍历所有一级专业，找到匹配的
      for (const primary of primaryMajors.value) {
        if (primary.major_code && materialCode.startsWith(primary.major_code)) {
          matchedPrimary = primary;
          
          // 尝试匹配二级专业
          const remainingCode = materialCode.substring(primary.major_code.length);
          
          // 遍历此一级专业下的所有二级专业
          for (const secondary of secondaryMajors.value) {
            if (secondary.major_id === primary.id && 
                secondary.sub_major_code && 
                remainingCode.startsWith(secondary.sub_major_code)) {
              matchedSecondary = secondary;
              break;
            }
          }
          break;
        }
      }
      
      // 填充专业选择
      if (matchedPrimary) {
        selectedPrimaryMajor.value = matchedPrimary.major_code;
        
        // 加载二级专业
        await handlePrimaryMajorChange();
        
        if (matchedSecondary) {
          selectedSecondaryMajor.value = matchedSecondary.sub_major_code;
          // 选中对应的二级专业项
          selectedMaterialCodeLevel.value = matchedSecondary;
        }
        
        // 生成推荐编码
        await generateRecommendedMaterialCode();
      }
    } catch (error) {
      console.error('解析器材编码失败:', error);
    }
  } else {
    // 新建模式下，保持原有行为
    showMaterialCodePanel.value = true;
    showEquipmentPanel.value = false;
    showMaterialSearchPanel.value = false;
  }
};

// 监听器材名称变化，自动填充到右侧搜索框
watch(() => form.material_name, (newValue, oldValue) => {
  // 只在新建模式下自动填充和搜索
  if (dialogTitle.value === '新增器材' && newValue && newValue !== oldValue) {
    // 填充到器材搜索框
    materialSearchParams.search = newValue;
    // 填充到专业搜索框
    materialCodeSearchParams.search = newValue;
    
    // 如果当前显示的是器材搜索面板，则自动执行搜索
    if (showMaterialSearchPanel.value) {
      handleMaterialSearch();
    }
    // 如果当前显示的是专业搜索面板，则自动执行搜索
    if (showMaterialCodePanel.value) {
      handleMaterialCodeSearch();
    } else {
      // 即使专业搜索面板没有显示，也执行专业搜索，但不自动跳转面板
      handleMaterialCodeSearch();
    }
    // 不再自动跳转到器材编码推荐面板，保持当前面板状态
  }
});

// 专业选择相关变量
const primaryMajors = ref<MajorResponse[]>([]);
const secondaryMajors = ref<SubMajorResponse[]>([]);
const selectedPrimaryMajor = ref<string>('');
const selectedSecondaryMajor = ref<string>('');
const recommendedMaterialCode = ref<string>('');

// 计算属性：过滤有效的一级专业（同时具有code和name）
const validPrimaryMajors = computed(() => {
  return primaryMajors.value.filter(m => m.major_code && m.major_name);
});

// 计算属性：过滤有效的二级专业（同时具有code和name）
const validSecondaryMajors = computed(() => {
  const result = secondaryMajors.value.filter(m => m.sub_major_code && m.sub_major_name);
  // console.log('validSecondaryMajors 计算属性被调用，原始数据数量:', secondaryMajors.value.length, '有效数据数量:', result.length);
  return result;
});

// 计算属性：获取选中的装备名称
const selectedEquipmentName = computed(() => {
  if (!form.equipment_id) return '';
  const equipment = equipments.value.find(eq => eq.id === form.equipment_id);
  return equipment ? equipment.equipment_name : '';
});

// 计算属性：根据选择的专业筛选装备
const filteredEquipments = computed(() => {
  if (!queryParams.major_id) {
    return equipments.value;
  }
  return equipments.value.filter(eq => eq.major_id === queryParams.major_id);
});

// 计算属性：根据搜索条件筛选二级专业数据
const filteredMaterialCodeLevels = computed(() => {
  const searchTerm = materialCodeSearchParams.search.trim().toLowerCase();
  
  if (!searchTerm) {
    // 如果没有搜索条件，显示所有二级专业数据
    return secondaryMajors.value;
  }
  
  // 根据搜索条件过滤二级专业数据
  const filteredLevels = secondaryMajors.value.filter(subMajor => 
    subMajor.sub_major_name?.toLowerCase().includes(searchTerm) ||
    subMajor.sub_major_code?.toLowerCase().includes(searchTerm) ||
    // 同时搜索对应的一级专业名称
    (subMajor.major_name && subMajor.major_name.toLowerCase().includes(searchTerm)) ||
    // 搜索专业描述字段
    (subMajor.description && subMajor.description.toLowerCase().includes(searchTerm))
  );
  
  return filteredLevels;
});

// 获取器材列表
const getMaterialList = async () => {
  loading.value = true;
  try {
    const response = await materialAPI.getMaterials(queryParams);
    tableData.value = response.data;
    total.value = response.total;
    
    // 在数据加载完成后，恢复排序状态
    await nextTick();
    restoreSortState();
  } catch (error) {
    ElMessage.error('获取器材列表失败');
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

// 获取专业列表
const getMajorList = async () => {
  try {
    const response = await majorAPI.getMajors();
    majors.value = response.data;
  } catch (error) {
    ElMessage.error('获取专业列表失败');
  }
};

// 获取装备列表
const getEquipmentList = async () => {
  try {
    const response = await equipmentApi.getAllEquipments();
    equipments.value = response.data;
  } catch (error) {
    ElMessage.error('获取装备列表失败');
  }
};

// 搜索装备列表（分页）
const searchEquipments = async () => {
  equipmentLoading.value = true;
  try {
    const response = await equipmentApi.getEquipments(equipmentSearchParams);
    searchedEquipments.value = response.data;
    equipmentTotal.value = response.total;
  } catch (error) {
    ElMessage.error('搜索装备失败');
  } finally {
    equipmentLoading.value = false;
  }
};

// 处理装备搜索
const handleEquipmentSearch = () => {
  equipmentSearchParams.page = 1;
  searchEquipments();
};

// 搜索器材列表（分页）
const searchMaterials = async () => {
  materialSearchLoading.value = true;
  try {
    const response = await materialAPI.getMaterials(materialSearchParams);
    searchedMaterials.value = response.data;
    materialTotal.value = response.total;
  } catch (error) {
    ElMessage.error('搜索器材失败');
  } finally {
    materialSearchLoading.value = false;
  }
};

// 处理器材搜索
const handleMaterialSearch = () => {
  materialSearchParams.page = 1;
  searchMaterials();
};

// 选择器材（双击读取信息到左侧）
const selectMaterial = (material: MaterialResponse) => {
  // 将器材信息读取到左侧表单
  form.material_code = material.material_code;
  form.material_name = material.material_name;
  form.material_specification = material.material_specification || '';
  form.material_desc = material.material_desc || '';
  form.material_wdh = material.material_wdh || '';
  form.safety_stock = material.safety_stock || 0;
  form.material_query_code = material.material_query_code || '';
  form.equipment_id = material.equipment_id;
  form.major_id = material.major_id;
  // 不关闭器材搜索面板，保持显示
};


// 选择装备
const selectEquipment = (equipment: Equipment) => {
  form.equipment_id = equipment.id;
};

// 清除装备选择
const clearEquipmentSelection = () => {
  form.equipment_id = undefined;
  form.major_id = undefined;
};

// 刷新页面数据
const refreshAllData = () => {
  getMaterialList();
  getMajorList();
  getEquipmentList();
};

// 当前排序状态
const currentSortProp = ref<string>('');
const currentSortOrder = ref<'ascending' | 'descending' | null>(null);

// 表头排序处理
const handleSortChange = ({ prop, order }: { prop: string; order: 'ascending' | 'descending' | null }) => {
  // 保存当前排序状态，用于在表格刷新后恢复排序图标
  currentSortProp.value = prop;
  currentSortOrder.value = order;
  
  if (prop) {
    const fieldMap: Record<string, string> = {
      'id': 'id',
      'material_code': 'material_code',
      'material_name': 'material_name',
      'create_time': 'create_time',
      'update_time': 'update_time'
    }
    
    const sortField = fieldMap[prop]
    if (sortField) {
      if (order) {
        // 有排序方向：升序或降序
        queryParams.sort_field = sortField as 'id' | 'material_code' | 'material_name' | 'create_time' | 'update_time'
        queryParams.sort_asc = order === 'ascending'
      } else {
        // 取消排序：重置为默认排序
        queryParams.sort_field = 'id'
        queryParams.sort_asc = true
      }
      queryParams.page = 1
      getMaterialList()
    }
  }
}

// 专业选择变化处理
const handleMajorChange = () => {
  // 清除装备筛选下拉框中选中的内容
  queryParams.equipment_id = undefined;
  
  // 更新装备搜索的专业筛选
  equipmentSearchParams.major_id = queryParams.major_id;
  equipmentSearchParams.page = 1;
  searchEquipments();
  
  // 更新器材查询参数的专业筛选并刷新器材表格
  queryParams.page = 1;
  getMaterialList();
};

// drawer中专业选择变化处理
const handleDrawerMajorChange = () => {
  // 清除已选择的装备
  form.equipment_id = undefined;
  
  // 更新装备搜索的专业筛选（仅影响drawer中的装备搜索）
  equipmentSearchParams.major_id = form.major_id;
  equipmentSearchParams.page = 1;
  
  // 自动切换到装备选择界面
  showEquipmentPanel.value = true;
  showMaterialSearchPanel.value = false;
  showMaterialCodePanel.value = false;
  
  // 搜索装备（显示筛选专业后的装备）
  searchEquipments();
};

// 搜索
const handleSearch = () => {
  queryParams.page = 1;
  getMaterialList();
};

// 分页大小变化
const handleSizeChange = (size: number) => {
  queryParams.page_size = size;
  getMaterialList();
};

// 页码变化
const handleCurrentChange = (page: number) => {
  queryParams.page = page;
  getMaterialList();
};

// 表格选择变化
const handleSelectionChange = (selection: MaterialResponse[]) => {
  selectedIds.value = selection.map(item => item.id);
};

// 新增器材
const handleCreate = () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有创建器材的权限');
    return;
  }
  dialogTitle.value = '新增器材';
  
  // 检查是否是同一个菜单类型
  if (lastMenuType.value === 'create' && tempFormData.value) {
    // 恢复之前的数据
    Object.assign(form, tempFormData.value);
  } else {
    resetForm();
    // 保存原始数据用于比较
    originalFormData.value = { ...form };
  }
  
  // 初始化面板显示状态 - 确保显示器材搜索面板
  showMaterialCodePanel.value = false;
  showEquipmentPanel.value = false;
  showMaterialSearchPanel.value = true; 
  
  // 重置搜索参数
  equipmentSearchParams.search = '';
  equipmentSearchParams.major_id = form.major_id; // 使用左侧已有的专业筛选
  equipmentSearchParams.page = 1;
  materialSearchParams.search = '';
  materialSearchParams.page = 1;
  materialCodeSearchParams.search = '';
  materialCodeSearchParams.page = 1;
  
  lastMenuType.value = 'create';
  dialogVisible.value = true;
  
  // 加载装备搜索数据
  searchEquipments();
  // 新增器材时自动加载器材列表数据
  searchMaterials();
  // 新增器材时自动加载器材编码层级数据
  loadAllMaterialCodeLevels();
};

// 编辑器材
const handleEdit = (row: MaterialResponse) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有编辑器材的权限');
    return;
  }
  dialogTitle.value = '编辑器材';
  
  // 检查是否是同一个菜单类型
  if (lastMenuType.value === 'edit' && tempFormData.value) {
    // 恢复之前的数据
    Object.assign(form, tempFormData.value);
  } else {
    Object.assign(form, {
      id: row.id,
      material_code: row.material_code,
      material_name: row.material_name,
      material_specification: row.material_specification || '',
      material_desc: row.material_desc || '',
      material_wdh: row.material_wdh || '',
      safety_stock: row.safety_stock || 0,
      material_query_code: row.material_query_code || '',
      major_id: row.major_id,
      equipment_id: row.equipment_id
    });
    // 保存原始数据用于比较
    originalFormData.value = { ...form };
  }
  
  // 初始化面板显示状态 - 确保显示器材搜索面板
  showMaterialCodePanel.value = false;
  showEquipmentPanel.value = false;
  showMaterialSearchPanel.value = true; // 编辑器材时先显示器材搜索面板
  
  // 重置搜索参数
  equipmentSearchParams.search = '';
  equipmentSearchParams.major_id = form.major_id; // 使用左侧已有的专业筛选
  equipmentSearchParams.page = 1;
  materialSearchParams.search = '';
  materialSearchParams.page = 1;
  materialCodeSearchParams.search = '';
  materialCodeSearchParams.page = 1;
  
  lastMenuType.value = 'edit';
  dialogVisible.value = true;
  
  // 加载装备搜索数据
  searchEquipments();
  // 编辑器材时自动加载器材列表数据
  searchMaterials();
  // 编辑器材时自动加载器材编码层级数据
  loadAllMaterialCodeLevels();
};

// 删除器材
const handleDelete = async (row: MaterialResponse) => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有删除器材的权限');
    return;
  }
  try {
    await ElMessageBox.confirm(`确定要删除器材"${row.material_name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    await materialAPI.deleteMaterial(row.id)
    ElMessage.success('删除成功')
    // 删除后清除所有选中状态，让用户重新选择
    selectedIds.value = []
    getMaterialList();
  } catch (error) {
    // 用户取消删除
  }
};

// 批量删除
const handleBatchDelete = async () => {
  if (!hasPermission('BASE-edit')) {
    ElMessage.warning('没有批量删除器材的权限');
    return;
  }
  if (selectedIds.value.length === 0) return;
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 个器材吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    await materialAPI.batchDeleteMaterials({ ids: selectedIds.value });
    ElMessage.success('批量删除成功');
    selectedIds.value = [];
    getMaterialList();
  } catch (error) {
    // 用户取消删除
  }
};

// 清空右侧组件内容
const clearRightPanelContent = () => {
  // 清空专业选择相关变量
  selectedMaterialCodeLevel.value = null;
  selectedPrimaryMajor.value = '';
  selectedSecondaryMajor.value = '';
  recommendedMaterialCode.value = '';
  
  // 清空搜索相关变量
  materialCodeSearchParams.search = '';
  equipmentSearchParams.search = '';
  materialSearchParams.search = '';
  
  // 清空搜索结果
  searchedEquipments.value = [];
  searchedMaterials.value = [];
  
  // 重置面板显示状态
  showMaterialCodePanel.value = false;
  showEquipmentPanel.value = false;
  showMaterialSearchPanel.value = false;
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  
  try {
    await formRef.value.validate();
    dialogLoading.value = true;
    
    if (dialogTitle.value === '新增器材') {
      const createData: MaterialCreate = {
        material_code: form.material_code,
        material_name: form.material_name
      };
      
      // 只有当字段有实际值时才包含可选字段
      if (form.material_specification) {
        createData.material_specification = form.material_specification;
      }
      if (form.material_desc) {
        createData.material_desc = form.material_desc;
      }
      if (form.material_wdh) {
        createData.material_wdh = form.material_wdh;
      }
      if (form.safety_stock !== undefined && form.safety_stock !== null) {
        createData.safety_stock = form.safety_stock;
      }
      // 只有当equipment_id有值时才包含该字段
      if (form.equipment_id !== undefined && form.equipment_id !== null) {
        createData.equipment_id = form.equipment_id;
      }
      
      console.log('提交的创建数据:', createData);
      await materialAPI.createMaterial(createData);
      ElMessage.success('新增成功');
    } else {
      const updateData: MaterialUpdate = {
        material_code: form.material_code,
        material_name: form.material_name
      };
      
      // 包含所有可选字段，即使为空值也要发送给后端
      updateData.material_specification = form.material_specification;
      updateData.material_desc = form.material_desc;
      updateData.material_wdh = form.material_wdh;
      updateData.safety_stock = form.safety_stock;
      
      // 始终包含equipment_id字段，即使为undefined或null
      updateData.equipment_id = form.equipment_id;
      
      console.log('提交的更新数据:', updateData);
      await materialAPI.updateMaterial(form.id, updateData);
      ElMessage.success('更新成功');
    }
    
    // 清除临时保存的数据
    tempFormData.value = null
    lastMenuType.value = null
    originalFormData.value = null
    
    // 清空右侧组件内容
    clearRightPanelContent();
    
    dialogVisible.value = false;
    getMaterialList();
  } catch (error: any) {
    // 显示具体的错误信息给用户
    if (error.response?.data?.detail) {
      // 使用后端返回的具体错误信息
      ElMessage.error(error.response.data.detail);
    } else if (error.message) {
      // 使用错误对象的message
      ElMessage.error(error.message);
    } else {
      // 默认错误信息
      ElMessage.error('操作失败，请重试');
    }
  } finally {
    dialogLoading.value = false;
  }
};

// 处理对话框关闭
const handleDialogClose = (done: () => void) => {
  // 检查是否有真正的数据修改
  const hasRealChanges = originalFormData.value && (
    form.material_code !== originalFormData.value.material_code ||
    form.material_name !== originalFormData.value.material_name ||
    form.material_specification !== originalFormData.value.material_specification ||
    form.material_desc !== originalFormData.value.material_desc ||
    form.material_wdh !== originalFormData.value.material_wdh ||
    form.safety_stock !== originalFormData.value.safety_stock ||
    form.material_query_code !== originalFormData.value.material_query_code ||
    form.major_id !== originalFormData.value.major_id ||
    form.equipment_id !== originalFormData.value.equipment_id
  )
  
  if (hasRealChanges) {
    // 有真正的数据修改，自动保存并提示用户
    tempFormData.value = { ...form }
    ElMessage.success('编辑信息已保存')
    done()
  } else {
    // 没有真正的数据修改，直接关闭
    tempFormData.value = null
    done()
  }
};

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields();
  }
  Object.assign(form, {
    id: 0,
    material_code: '',
    material_name: '',
    material_specification: '',
    material_desc: '',
    material_wdh: '',
    safety_stock: 0,
    material_query_code: '',
    major_id: undefined,
    equipment_id: undefined
  });
};


// 加载所有专业数据（分别从一级专业和二级专业API获取）
const loadAllMaterialCodeLevels = async () => {
  try {
    materialCodeLevelLoading.value = true;
    
    // 分别从一级专业和二级专业API获取数据
    const [primaryResponse, secondaryResponse] = await Promise.all([
      majorAPI.getMajors(),
      subMajorAPI.getSubMajors()
    ]);
    
    // 设置一级专业数据
    primaryMajors.value = primaryResponse.data || [];
    
    // 设置二级专业数据
    secondaryMajors.value = secondaryResponse.data || [];
    
    // 调试：查看获取的专业数据
    // console.log("一级专业数据:", primaryMajors.value);
    // console.log("二级专业数据:", secondaryMajors.value);
    
    // 数据加载完成后，显示器材编码推荐面板
    showMaterialCodePanel.value = true;
    // 隐藏其他面板
    showEquipmentPanel.value = false;
    showMaterialSearchPanel.value = false;
    
    // console.log("一级专业数据数量:", primaryMajors.value.length);
    // console.log("二级专业数据数量:", secondaryMajors.value.length);
  } catch (error) {
    // console.error('加载专业数据失败:', error);
    ElMessage.error('加载专业数据失败');
  } finally {
    materialCodeLevelLoading.value = false;
  }
};

// 处理器材编码搜索
const handleMaterialCodeSearch = async () => {
  try {
    materialCodeLevelLoading.value = true;
    
    const searchTerm = materialCodeSearchParams.search.trim();
    
    if (!searchTerm) {
      // 如果搜索词为空，重新加载所有二级专业数据
      await loadAllMaterialCodeLevels();
      return;
    }
    
    // 从后端API搜索二级专业数据
    // console.log('搜索专业:', searchTerm);
    const response = await subMajorAPI.getSubMajors({ 
      search: searchTerm 
    });
    
    // 更新二级专业列表
    secondaryMajors.value = response.data || [];
    
    // console.log('搜索专业完成，找到', secondaryMajors.value.length, '个结果', secondaryMajors.value);
    
  } catch (error) {
    // console.error('搜索专业失败:', error);
    ElMessage.error('搜索专业失败');
  } finally {
    materialCodeLevelLoading.value = false;
  }
};

// 选择专业层级
const selectMaterialCodeLevel = (level: MajorResponse | SubMajorResponse) => {
  selectedMaterialCodeLevel.value = level;
  
  // 根据选择的专业类型设置相应的专业选择
  if ('major_code' in level) {
    // 一级专业
    selectedPrimaryMajor.value = level.major_code;
    selectedSecondaryMajor.value = '';
    
    // 触发一级专业变化处理
    handlePrimaryMajorChange();
  } else if ('sub_major_code' in level) {
    // 二级专业
    const parentMajor = primaryMajors.value.find(major => major.id === level.major_id);
    if (parentMajor) {
      selectedPrimaryMajor.value = parentMajor.major_code;
      selectedSecondaryMajor.value = level.sub_major_code;
      
      // 直接生成推荐编码，不触发一级专业变化处理（避免清空二级专业选择）
      generateRecommendedMaterialCode();
    }
  }
  
  // 生成推荐器材编码
  generateRecommendedMaterialCode();
};



// 处理添加专业描述对话框关闭
const handleAddDescriptionDialogClose = () => {
  // 对话框关闭时的处理
};

// 处理添加专业描述成功
const handleAddDescriptionSuccess = async () => {
  // 刷新器材编码分类层级数据
  await loadAllMaterialCodeLevels();
};

// 处理从搜索框添加专业描述
const handleAddDescriptionFromSearch = () => {
  // 将器材名称复制到对话框的描述名称输入框
  const materialName = form.material_name.trim();
  if (materialName) {
    // 打开添加专业描述对话框，并传递器材名称
    addDescriptionDialogRef.value?.open();
    
    // 这里需要稍后处理对话框打开后的自动填充
    // 由于对话框是异步打开的，我们需要在对话框打开后设置描述名称
    // 这需要在AddDescriptionDialog组件中添加相应的支持
  } else {
    ElMessage.warning('请先输入器材名称');
  }
};
// 生成推荐器材编码
const generateRecommendedMaterialCode = async () => {
  if (!selectedPrimaryMajor.value) {
    recommendedMaterialCode.value = '';
    return;
  }
  
  try {
    // 获取一级专业代码
    const primaryItem = primaryMajors.value.find(item => item.major_code === selectedPrimaryMajor.value);
    if (!primaryItem || !primaryItem.major_code) {
      recommendedMaterialCode.value = '';
      return;
    }
    
    const primaryCode = primaryItem.major_code;
    
    // 获取二级专业代码
    let secondaryCode = '';
    if (selectedSecondaryMajor.value) {
      const secondaryItem = secondaryMajors.value.find(item => item.sub_major_code === selectedSecondaryMajor.value);
      if (secondaryItem && secondaryItem.sub_major_code) {
        // 直接使用二级专业的代码字段
        secondaryCode = secondaryItem.sub_major_code;
      }
    }
    
    // 构建前2位编码：一级专业代码 + 二级专业代码
    const prefix = primaryCode + secondaryCode;
    
    // 获取现有器材列表，查找相同前缀的编码
    const response = await materialAPI.getMaterials({
      page: 1,
      page_size: 1000, // 获取足够多的数据来查找最大序列号
      search: prefix
    });
    
    const materials = response.data || [];
    
    // 查找相同前缀的编码，获取最大序列号
    let maxSequence = 0;
    materials.forEach((material: MaterialResponse) => {
      if (material.material_code.startsWith(prefix)) {
        const sequenceStr = material.material_code.substring(prefix.length); // 去掉前缀后的序列号部分
        const sequence = parseInt(sequenceStr, 10);
        if (!isNaN(sequence) && sequence > maxSequence) {
          maxSequence = sequence;
        }
      }
    });
    
    // 生成新的序列号（取未使用的最小值）
    const newSequence = maxSequence + 1;
    const sequenceStr = newSequence.toString().padStart(10 - prefix.length, '0'); // 动态计算序列号位数
    
    // 生成完整的10位器材编码
    recommendedMaterialCode.value = prefix + sequenceStr;
    
    // 自动填充到器材编码输入框
    form.material_code = recommendedMaterialCode.value;
    
  } catch (error) {
    // console.error( '生成推荐器材编码失败:', error);
    ElMessage.error('生成推荐器材编码失败');
    recommendedMaterialCode.value = '';
  }
};


// 处理一级专业选择变化
const handlePrimaryMajorChange = async () => {
  selectedSecondaryMajor.value = '';
  
  if (selectedPrimaryMajor.value) {
    // 根据选择的一级专业ID加载对应的二级专业
    const primaryItem = primaryMajors.value.find(item => item.major_code === selectedPrimaryMajor.value);
    // console.log('选中的一级专业:', primaryItem);
    if (primaryItem && primaryItem.id) {
      try {
        // 设置到表单的所属专业中
        form.major_id = primaryItem.id;
        
        // 根据一级专业ID获取对应的二级专业
        const response = await subMajorAPI.getSubMajors({ major_id: primaryItem.id });
        
        // 强制重置为空数组再赋值，触发Vue响应式更新
        secondaryMajors.value = [];
        await nextTick();
        secondaryMajors.value = response.data || [];
        
        // console.log('加载二级专业数据成功，数量:', secondaryMajors.value.length);
        console.log('二级专业数据详情:', JSON.parse(JSON.stringify(secondaryMajors.value)));
        
        // 检查有效数据
        const validData = secondaryMajors.value.filter(m => m.sub_major_code && m.sub_major_name);
        // console.log('有效的二级专业数据数量:', validData.length);
        if (validData.length > 0) {
          // console.log('第一条有效数据:', validData[0]);
        }
      } catch (error) {
        // console.error('加载二级专业数据失败:', error);
        ElMessage.error('加载二级专业数据失败');
        secondaryMajors.value = [];
      }
    } else {
      // console.log('未找到一级专业或缺少ID');
      secondaryMajors.value = [];
    }
  } else {
    // 清空表单的所属专业
    form.major_id = undefined;
    secondaryMajors.value = [];
  }
  
  // 生成推荐器材编码
  generateRecommendedMaterialCode();
};

// 处理二级专业选择变化
const handleSecondaryMajorChange = () => {
  // 生成推荐器材编码
  generateRecommendedMaterialCode();
};






onMounted(() => {
  refreshAllData();
});
</script>

<style scoped lang="scss">
@use '../../../css/base-styles-mixin.scss' as mixins;
@import '../../../css/base-styles.css';

/* 使用现代Sass混入 */
@include mixins.table-sort-arrows;

/* 装备选择布局样式 */
.equipment-select-layout {
  display: flex;
  height: 100%;
  gap: 20px;
}

.edit-section {
  flex: 1;
  min-width: 0;
}

.equipment-search-section {
  width: 250px;
  border-left: 1px solid #e4e7ed;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.equipment-search-header {
  margin-bottom: 20px;
  
  .header-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 15px;
    
    h4 {
      margin: 0;
      color: #303133;
      font-size: 16px;
      font-weight: 600;
      white-space: nowrap;
    }
    
    .search-controls {
      display: flex;
      gap: 10px;
      align-items: center;
    }
  }
}

.equipment-list-container {
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
}

.equipment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.equipment-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #409eff;
    background-color: #f5f7fa;
  }
  
  &.selected {
    border-color: #409eff;
    background-color: #ecf5ff;
  }
  
  .equipment-name {
    font-weight: 600;
    color: #303133;
    margin-bottom: 4px;
  }
  
  .equipment-spec {
    font-size: 12px;
    color: #909399;
    margin-bottom: 2px;
  }
  
  .equipment-major {
    font-size: 12px;
    color: #67c23a;
  }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.equipment-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.equipment-selection {
  .el-input {
    cursor: pointer;
    
    &:hover {
      .el-input__inner {
        border-color: #409eff;
      }
    }
  }
}

.loading-container {
  padding: 20px;
}

/* 专业列表样式 */
.material-code-level-list-container {
  margin-bottom: 20px;
}

.material-code-level-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.material-code-level-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #409eff;
    background-color: #f5f7fa;
  }
  
  &.selected {
    border-color: #409eff;
    background-color: #ecf5ff;
  }
  
  .level-info {
    .level-name-code {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .level-name {
        font-weight: 600;
        color: #303133;
        font-size: 14px;
      }
      
      .level-code {
        font-size: 12px;
        color: #909399;
        margin-left: 8px;
      }
    }
  }
}

/* 器材搜索面板样式 */
.material-search-panel {
  width: 200px;
  border-left: 1px solid #e4e7ed;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.material-search-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .panel-title {
    color: #303133;
    font-size: 16px;
    font-weight: 600;
  }
}

.material-search-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.material-list {
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
  margin-top: 15px;
}

.material-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 8px;
  
  &:hover {
    border-color: #409eff;
    background-color: #f5f7fa;
  }
  
  .material-name {
    font-weight: 600;
    color: #303133;
    margin-bottom: 4px;
  }
  
  .material-spec {
    font-size: 12px;
    color: #909399;
    margin-bottom: 2px;
  }
  
  .material-code {
    font-size: 12px;
    color: #67c23a;
  }
}

.material-pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 器材编码推荐面板样式 */
.material-code-panel {
  width: 300px;
  border-left: 1px solid #e4e7ed;
  padding-left: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.material-code-header {
  margin-bottom: 20px;
  
  .panel-title {
    color: #303133;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 15px;
  }
  
  .search-input {
    margin-bottom: 15px;
  }
}

.material-code-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.material-code-list {
  flex: 1;
  overflow-y: auto;
  max-height: 300px;
  margin-bottom: 20px;
}

.material-code-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-bottom: 8px;
  
  &:hover {
    border-color: #409eff;
    background-color: #f5f7fa;
  }
  
  &.selected {
    border-color: #409eff;
    background-color: #ecf5ff;
  }
  
  .level-code {
    font-weight: 600;
    color: #303133;
    margin-bottom: 4px;
  }
  
  .major-code {
    font-size: 12px;
    color: #67c23a;
  }
}

.major-selection-section {
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
  
  .section-title {
    font-size: 14px;
    font-weight: 600;
    color: #303133;
    margin-bottom: 15px;
  }
  
  .major-selectors {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .selector-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
    
    label {
      font-size: 12px;
      color: #606266;
      font-weight: 500;
    }
  }
  
  .recommended-code {
    margin-top: 15px;
    padding: 12px;
    background-color: #f0f9ff;
    border: 1px solid #91d5ff;
    border-radius: 4px;
    
    .code-label {
      font-size: 12px;
      color: #606266;
      margin-bottom: 8px;
    }
    
    .code-value {
      font-family: 'Courier New', monospace;
      font-size: 14px;
      font-weight: 600;
      color: #1890ff;
    }
  }
  
  .apply-button {
    margin-top: 15px;
    width: 100%;
  }
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #909399;
  font-size: 14px;
}

/* 专业选择列表样式 - 类似装备选择列表 */
.material-code-level-list-container {
  flex: 1;
  overflow-y: auto;
  max-height: 400px;
  margin-top: 15px;
}

.material-code-level-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.material-code-level-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #409eff;
    background-color: #f5f7fa;
  }
  
  &.selected {
    border-color: #409eff;
    background-color: #ecf5ff;
  }
  
  .level-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .level-name {
    font-weight: 600;
    color: #303133;
    font-size: 14px;
    margin-bottom: 2px;
  }
  
  .level-code {
    font-size: 12px;
    color: #909399;
  }
  
  .major-info {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
  }
  
  .level-name {
    font-weight: 600;
    color: #303133;
    font-size: 14px;
    margin-bottom: 4px;
  }
  
  .level-code {
    font-size: 12px;
    color: #909399;
  }
}
</style>