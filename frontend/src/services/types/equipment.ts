// 装备相关类型定义
export interface Equipment {
  id: number;
  equipment_name: string;
  specification?: string;
  major_id?: number;
  major_name?: string;
  creator: string;
  create_time: string;
  update_time: string;
}

export interface EquipmentCreateRequest {
  equipment_name: string;
  specification?: string;
  major_id?: number;
}

export interface EquipmentUpdateRequest {
  equipment_name?: string;
  specification?: string;
  major_id?: number;
}

export interface EquipmentListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  data: Equipment[];
}

export interface EquipmentStatistics {
  total_count: number;
  major_count: Record<string, number>;
}

export interface EquipmentQueryParams {
  search?: string;
  major_id?: number;
  major_name?: string;
  page?: number;
  page_size?: number;
  sort_field?: string;
  sort_asc?: boolean;
}

export interface EquipmentBatchDeleteRequest {
  ids: number[];
}

export interface EquipmentBatchDeleteResponse {
  message: string;
  success_count: number;
  total_count: number;
}