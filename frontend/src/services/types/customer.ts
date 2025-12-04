import { PaginationParams, PaginationResult } from './common';

// 客户管理相关类型
export interface CustomerResponse {
  id: number;
  customer_name: string;
  customer_city: string;
  customer_address: string;
  customer_contact: string;
  customer_manager: string;
  customer_level?: string | null;
  create_time: string;
  update_time: string;
  creator: string;
}

export interface CustomerCreate {
  customer_name: string;
  customer_city: string;
  customer_address: string;
  customer_contact: string;
  customer_manager: string;
  customer_level?: string | null;
}

export interface CustomerUpdate {
  customer_name?: string;
  customer_city?: string;
  customer_address?: string;
  customer_contact?: string;
  customer_manager?: string;
  customer_level?: string | null;
}

export interface CustomerQueryParams extends PaginationParams {
  search?: string;
  customer_name?: string;
  customer_city?: string;
  customer_address?: string;
  customer_contact?: string;
  customer_manager?: string;
  sort_field?: 'id' | 'customer_name' | 'create_time' | 'update_time';
  sort_asc?: boolean;
}

export interface CustomerPaginationResult extends PaginationResult<CustomerResponse> {}

export interface BatchCustomerDelete {
  customer_ids: number[];
}

export interface CustomerStatistics {
  total_customers: number;
  customers_by_city: {
    city: string;
    count: number;
  }[];
}

export interface BatchDeleteResult {
  success_count: number;
  failed_count: number;
  failed_customers: number[];
  message: string;
}