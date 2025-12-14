// 货位相关类型定义
export interface Bin {
  id: number;
  bin_name: string;
  bin_size?: string;
  bin_property?: string;
  warehouse_id: number;
  warehouse_name: string;
  empty_label: boolean;
  bar_code?: string;
  creator: string;
  create_time: string;
  update_time: string;
}

export interface BinCreateRequest {
  bin_name: string;
  bin_size?: string | null;
  bin_property?: string | null;
  warehouse_id: number;
  empty_label: boolean;
  bar_code?: string | null;
}

export interface BinUpdateRequest {
  bin_name?: string;
  bin_size?: string | null;
  bin_property?: string | null;
  warehouse_id?: number;
  empty_label?: boolean;
  bar_code?: string | null;
}

export interface BinListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  data: Bin[];
}

export interface BinStatistics {
  total_bins: number;
  bins_by_warehouse: Array<{
    warehouse_id: number;
    warehouse_name: string;
    count: number;
  }>;
  bins_by_property: Array<{
    property: string;
    count: number;
  }>;
}

export interface BinQueryParams {
  search?: string;
  bin_name?: string;
  warehouse_id?: number;
  warehouse_name?: string;
  bin_property?: string;
  empty_label?: boolean;
  sort_field?: 'id' | 'bin_name' | 'warehouse_name' | 'bin_property' | 'empty_label' | 'create_time' | 'update_time';
  sort_asc?: boolean;
  page?: number;
  page_size?: number;
}

export interface BinBatchDeleteRequest {
  bin_ids: number[];
}

export interface BinBatchDeleteResponse {
  message: string;
}

export interface BinPropertiesResponse {
  properties: string[];
}