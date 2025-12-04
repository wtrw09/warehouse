import { PaginationParams, PaginationResult } from './common';

// 供应商管理相关类型
export interface SupplierResponse {
  id: number;
  supplier_name: string;
  supplier_city: string;
  supplier_address: string;
  supplier_contact: string;
  supplier_manager: string;
  supplier_level?: number | null;
  create_time: string;
  update_time: string;
  creator: string;
}

export interface SupplierCreate {
  supplier_name: string;
  supplier_city?: string;
  supplier_address?: string;
  supplier_contact?: string;
  supplier_manager?: string;
  supplier_level?: number | null;
}

export interface SupplierUpdate {
  supplier_name?: string;
  supplier_city?: string;
  supplier_address?: string;
  supplier_contact?: string;
  supplier_manager?: string;
  supplier_level?: number | null;
}

export interface SupplierQueryParams extends PaginationParams {
  search?: string;
  supplier_name?: string;
  supplier_city?: string;
  supplier_address?: string;
  supplier_contact?: string;
  supplier_manager?: string;
  sort_field?: 'id' | 'supplier_name' | 'create_time' | 'update_time';
  sort_asc?: boolean;
}

export interface SupplierPaginationResult extends PaginationResult<SupplierResponse> {}

export interface BatchSupplierDelete {
  supplier_ids: number[];
}

export interface SupplierStatistics {
  total_suppliers: number;
}

export interface SupplierBatchDeleteResult {
  success_count: number;
  failed_count: number;
  failed_suppliers: number[];
  message: string;
}