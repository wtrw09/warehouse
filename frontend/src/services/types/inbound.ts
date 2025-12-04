import type { PaginationParams, PaginationResult } from './common';

export interface InboundOrderItemCreate {
  material_id: number;
  batch_number: string;
  quantity: number;
  unit_price: number;
  unit: string;
  bin_id?: number | null;
  production_date?: string;
}

export interface InboundOrderCreate {
  order_number: string;
  requisition_reference?: string;
  contract_reference?: string;
  supplier_id: number;
  inbound_date: string;
  items: InboundOrderItemCreate[];
}

export interface InboundOrderItemResponse {
  item_id: number;
  material_id: number;
  material_code: string;
  material_name: string;
  material_specification: string;
  quantity: number;
  unit_price: number;
  unit: string;
  batch_number: string;
  bin_id: number;
  bin_name: string;
  equipment_name?: string;
  production_date?: string;
}

export interface InboundOrderResponse {
  order_id: number;
  order_number: string;
  requisition_reference?: string;
  contract_reference?: string;
  supplier_id: number;
  supplier_name: string;
  total_quantity: number;
  creator: string;
  create_time: string;
  inbound_date: string;
}

export interface InboundOrderDetailResponse {
  order: InboundOrderResponse;
  items: InboundOrderItemResponse[];
}

export interface InboundOrderUpdate {
  requisition_reference?: string;
  contract_reference?: string;
  supplier_id?: number;
  inbound_date?: string;
}

export interface InboundOrderQueryParams extends PaginationParams {
  keyword?: string;
  start_date?: string;
  end_date?: string;
  supplier_id?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface InboundOrderPaginationResult extends PaginationResult<InboundOrderResponse> {}

export interface InboundOrderListResponse {
  total: number;
  data: InboundOrderResponse[];
}

export interface InboundOrderStatistics {
  total_orders: number;
  total_quantity: number;
  total_amount: number;
  supplier_stats: Array<{
    supplier: string;
    count: number;
    quantity: number;
    amount: number;
  }>;
  date_stats: Array<{
    date: string;
    count: number;
    quantity: number;
    amount: number;
  }>;
}

export interface OrderNumberUpdate {
  order_number: string;
}

export interface TransferNumberUpdate {
  requisition_reference: string;
}

export interface SupplierUpdate {
  supplier_id: number;
}

export interface ContractNumberUpdate {
  contract_reference: string;
}

export interface InboundOrderItemUpdate {
  material_id?: number;
  batch_number?: string;
  quantity?: number;
  unit_price?: number;
  unit?: string;
  bin_id?: number | null; // 修改：支持null值，以匹配后端API
  production_date?: string;
}

export interface OrderNumberGenerateResponse {
  order_number: string;
}

export interface SupplierListResponse {
  suppliers: Array<{
    supplier_id: number;
    supplier_name: string;
  }>;
  total: number;
}

export type InboundOrderListResponseType = InboundOrderListResponse;
export type InboundOrderPaginationResponseType = InboundOrderPaginationResult;
export type InboundOrderDetailResponseType = InboundOrderDetailResponse;
export type InboundOrderResponseType = InboundOrderResponse;
export type InboundOrderStatisticsResponseType = InboundOrderStatistics;
export type InboundOrderCreateResponseType = InboundOrderResponse;
export type InboundOrderUpdateResponseType = { message: string; new_order_number?: string; new_transfer_number?: string; new_supplier_id?: number; new_supplier_name?: string; new_contract_number?: string };
export type InboundOrderDateUpdateResponseType = { message: string; updated_fields: { inbound_date: string } };
export type InboundOrderItemResponseType = { message: string; item_id: number };
export type InboundOrderDeleteResponseType = { message: string };
export type OrderNumberGenerateResponseType = OrderNumberGenerateResponse;
export type SupplierListResponseType = SupplierListResponse;