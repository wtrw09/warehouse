import { PaginationResult } from './common';

// 库存器材明细响应模型
export interface InventoryDetailResponse {
  detail_id: number;
  batch_id?: number;
  material_id: number;
  material_code: string;
  material_name: string;
  material_specification?: string;
  batch_number: string;
  quantity: number;
  unit: string;
  unit_price: number;
  supplier_name?: string;
  production_date?: string;
  inbound_date?: string;
  major_id?: number;
  major_name?: string;
  equipment_id?: number;
  equipment_name?: string;
  equipment_specification?: string;
  bin_id: number;
  bin_name: string;
  warehouse_name: string;
  update_time: string;
  last_updated: string;
}

// 库存器材明细分页结果模型
export interface PaginatedInventoryDetailsResponse {
  total: number;
  page: number;
  page_size: number;
  data: InventoryDetailResponse[];
}

// 库存器材明细列表响应模型（不分页）
export interface InventoryDetailsListResponse {
  total: number;
  data: InventoryDetailResponse[];
}



// 库存装备选项响应模型
export interface InventoryEquipmentOption {
  id: number;
  display_name: string;
}

// 库存装备选项集合响应模型
export interface InventoryEquipmentOptionsResponse {
  data: InventoryEquipmentOption[];
  total: number;
}

// 库存器材明细查询参数模型
export interface InventoryDetailsQueryParams {
  page: number;
  page_size: number;
  keyword?: string;
  major_id?: number[];
  equipment_id?: number[];
  warehouse_id?: number;
  bin_id?: number;
  quantity_filter?: 'has_stock' | 'no_stock';
  sort_by?: string;
  sort_order?: string;
}

// 库存器材明细统计信息
export interface InventoryDetailsStatistics {
  total_materials: number;
  distinct_materials: number;
  total_quantity: number;
  distinct_warehouses: number;
  update_time: string;
}

// 库存器材明细分页结果
export interface InventoryDetailPaginationResult extends PaginationResult<InventoryDetailResponse> {
  // 继承PaginationResult的所有属性
}

// 库存器材明细搜索参数（简化版）
export interface InventoryDetailSearchParams {
  search?: string;
  material_code?: string;
  material_name?: string;
  batch_number?: string;
  major_id?: number;
  equipment_id?: number;
  warehouse_id?: number;
  bin_id?: number;
}

// 库存器材明细表单数据（用于筛选）
export interface InventoryDetailFilterForm {
  keyword?: string;
  major_id?: number;
  equipment_id?: number;
  warehouse_id?: number;
  bin_id?: number;
  sort_by: string;
  sort_order: string;
}

// 专业ID选项
export interface MajorIdOption {
  value: number;
  label: string;
}

// 库存专业选项响应模型
export interface InventoryMajorOption {
  id: number;
  major_name: string;
}

// 库存专业选项集合响应模型
export interface InventoryMajorOptionsResponse {
  data: InventoryMajorOption[];
  total_count: number;
}

// 装备ID选项
export interface EquipmentIdOption {
  value: number;
  label: string;
}

// 仓库选项
export interface WarehouseOption {
  value: number;
  label: string;
}

// 货位选项
export interface BinOption {
  value: number;
  label: string;
}

// 排序选项
export interface SortOption {
  value: string;
  label: string;
}