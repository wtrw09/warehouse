import { PaginationParams, PaginationResult } from './common';

// 仓库管理相关类型
export interface WarehouseResponse {
  id: number;
  warehouse_name: string;
  warehouse_city: string;
  warehouse_address: string;
  warehouse_contact: string;
  warehouse_manager: string;
  creator: string;
  create_time: string;
  update_time: string;
}

export interface WarehouseCreate {
  warehouse_name: string;
  warehouse_city: string;
  warehouse_address: string;
  warehouse_contact: string;
  warehouse_manager: string;
}

export interface WarehouseUpdate {
  warehouse_name?: string;
  warehouse_city?: string;
  warehouse_address?: string;
  warehouse_contact?: string;
  warehouse_manager?: string;
}

export interface WarehouseQueryParams extends PaginationParams {
  warehouse_name?: string;
  warehouse_city?: string;
  warehouse_manager?: string;
}

export interface WarehousePaginationResult extends PaginationResult<WarehouseResponse> {}

export interface BatchWarehouseDelete {
  warehouse_ids: number[];
}

export interface WarehouseStatistics {
  total_warehouses: number;
  warehouses_by_city: {
    city: string;
    count: number;
  }[];
  recent_creations: number;
}