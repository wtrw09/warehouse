import { PaginationResult } from './common';

// 器材创建模式
export interface MaterialCreate {
  material_code: string;
  material_name: string;
  material_specification?: string;
  material_desc?: string;
  material_wdh?: string;
  safety_stock?: number;
  equipment_id?: number;
}

// 器材更新模式
export interface MaterialUpdate {
  material_code?: string;
  material_name?: string;
  material_specification?: string;
  material_desc?: string;
  material_wdh?: string;
  safety_stock?: number;
  equipment_id?: number;
}

// 器材响应模式
export interface MaterialResponse {
  id: number;
  material_code: string;
  material_name: string;
  material_specification?: string;
  material_desc?: string;
  material_wdh?: string;
  safety_stock?: number;
  material_query_code?: string;
  major_id?: number;
  major_name?: string;
  equipment_id?: number;
  equipment_name?: string;
  creator?: string;
  create_time?: string;
  update_time?: string;
}

// 器材查询参数
export interface MaterialQueryParams {
  material_code?: string;
  material_name?: string;
  material_specification?: string;
  material_desc?: string;
  material_wdh?: string;
  safety_stock?: number;
  major_id?: number;
  major_name?: string;
  equipment_id?: number;
  equipment_name?: string;
  creator?: string;
  search?: string;
  sort_field?: string;
  sort_asc?: boolean;
}

// 器材分页参数
export interface MaterialPaginationParams {
  page: number;
  page_size: number;
  material_code?: string;
  material_name?: string;
  material_specification?: string;
  material_desc?: string;
  material_wdh?: string;
  safety_stock?: number;
  major_id?: number;
  major_name?: string;
  equipment_id?: number;
  equipment_name?: string;
  creator?: string;
  search?: string;
  sort_field?: string;
  sort_asc?: boolean;
}

// 器材分页结果
export interface MaterialPaginationResult extends PaginationResult<MaterialResponse> {
  // 继承PaginationResult的所有属性，data属性已包含在泛型中
}

// 器材列表响应
export interface MaterialListResponse {
  data: MaterialResponse[];
  total: number;
}

// 器材统计信息
export interface MaterialStatistics {
  total_count: number;
  major_count: Record<string, number>;
  equipment_count: Record<string, number>;
}

// 批量删除器材
export interface BatchMaterialDelete {
  ids: number[];
}

// 批量导入结果
export interface MaterialBatchImportResult {
  success_count: number;
  error_count: number;
  errors: string[];
}

// 器材表单数据（用于创建和编辑）
export interface MaterialFormData {
  material_code: string;
  material_name: string;
  material_specification?: string;
  material_desc?: string;
  material_wdh?: string;
  safety_stock?: number;
  equipment_id?: number;
}

// 器材搜索参数（简化版，用于组件搜索）
export interface MaterialSearchParams {
  search?: string;
  material_code?: string;
  material_name?: string;
  equipment_id?: number;
  major_id?: number;
}

// 器材选择项（用于下拉选择）
export interface MaterialOption {
  value: number;
  label: string;
  material_code: string;
  material_name: string;
}

// 装备选项（用于专业下的装备选择）
export interface EquipmentOption {
  id: number;
  display_name: string;
}

// 装备选项响应
export interface EquipmentOptionsResponse {
  data: EquipmentOption[];
}

// 专业选项
export interface MajorOption {
  id: number;
  major_name: string;
}

// 专业选项集合响应模型
export interface MajorOptionsResponse {
  data: MajorOption[];
  total_count: number;
}