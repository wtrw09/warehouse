import type { PaginationParams, PaginationResult } from './common';

export interface OutboundOrderItemCreate {
  batch_id: number;
  quantity: number;
}

export interface OutboundOrderCreate {
  order_number: string;
  requisition_reference?: string;
  customer_id: number;
  items: OutboundOrderItemCreate[];
}

export interface OutboundOrderItemResponse {
  item_id: number;
  material_id: number;
  material_code: string;
  material_name: string;
  material_specification: string;
  quantity: number;
  unit_price: number;
  unit: string;
  batch_id: number;
  batch_number: string;
  bin_id: number;
  bin_name: string;
  equipment_name?: string;
}

export interface OutboundOrderResponse {
  order_id: number;
  order_number: string;
  requisition_reference?: string;
  customer_id: number;
  customer_name: string;
  total_quantity: number;
  creator: string;
  create_time: string;
}

export interface OutboundOrderDetailResponse {
  order: OutboundOrderResponse;
  items: OutboundOrderItemResponse[];
}

export interface OutboundOrderUpdate {
  requisition_reference?: string;
  customer_id?: number;
}

export interface OutboundOrderQueryParams extends PaginationParams {
  keyword?: string;
  start_date?: string;
  end_date?: string;
  customer_id?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface OutboundOrderPaginationResult extends PaginationResult<OutboundOrderResponse> {}

export interface OutboundOrderListResponse {
  total: number;
  data: OutboundOrderResponse[];
}

export interface OutboundOrderStatistics {
  total_orders: number;
  total_quantity: number;
  total_amount: number;
  customer_stats: Array<{
    customer_name: string;
    order_count: number;
    total_quantity: number;
    total_amount: number;
  }>;
  date_stats: Array<{
    date: string;
    order_count: number;
    total_quantity: number;
    total_amount: number;
  }>;
}

export interface OrderNumberUpdate {
  order_number: string;
}

export interface TransferNumberUpdate {
  requisition_reference: string;
}

export interface CustomerUpdate {
  customer_id: number;
}

export interface CreateTimeUpdate {
  create_time: string;
}

export interface OutboundOrderItemUpdate {
  batch_id?: number;
  quantity?: number;
}

export interface OutboundOrderItemBatchDelete {
  item_ids: number[];
}

export interface BatchDeleteResponse {
  success: boolean;
  deleted_count: number;
  message: string;
}

export interface OrderNumberGenerateResponse {
  order_number: string;
}

export interface CustomerListResponse {
  customers: Array<{
    customer_id: number;
    customer_name: string;
  }>;
  total: number;
}

export type OutboundOrderListResponseType = OutboundOrderListResponse;
export type OutboundOrderPaginationResponseType = OutboundOrderPaginationResult;
export type OutboundOrderDetailResponseType = OutboundOrderDetailResponse;
export type OutboundOrderResponseType = OutboundOrderResponse;
export type OutboundOrderStatisticsResponseType = OutboundOrderStatistics;
export type OutboundOrderCreateResponseType = OutboundOrderResponse;
export type OutboundOrderUpdateResponseType = { message: string; new_order_number?: string; new_transfer_number?: string; new_customer_id?: number; new_customer_name?: string };
export type OutboundOrderCreateTimeUpdateResponseType = { message: string; updated_fields: { create_time: string } };
export type OutboundOrderItemResponseType = OutboundOrderItemResponse;
export type OutboundOrderDeleteResponseType = { message: string };
export type BatchDeleteResponseType = BatchDeleteResponse;
export type OrderNumberGenerateResponseType = OrderNumberGenerateResponse;
export type CustomerListResponseType = CustomerListResponse;