import type { PaginationParams, PaginationResult } from './common';

/** 库存变更类型枚举 */
export enum ChangeType {
  IN = 'IN',      // 入库
  OUT = 'OUT',    // 出库
  ADJUST = 'ADJUST'  // 调整
}

/** 关联单据类型枚举 */
export enum ReferenceType {
  INBOUND = 'inbound',      // 入库单
  OUTBOUND = 'outbound',    // 出库单
  STOCKTAKE = 'stocktake'  // 盘点单
}

/** 创建库存变更流水记录参数 */
export interface InventoryTransactionCreateParams {
  material_id: number;
  batch_id: number;
  change_type: ChangeType;
  quantity_change: number;
  quantity_before: number;
  quantity_after: number;
  reference_type: ReferenceType;
  reference_id?: number;
  creator: string;
}

/** 更新库存变更流水记录参数 */
export interface InventoryTransactionUpdateParams {
  material_id?: number;
  batch_id?: number;
  change_type?: ChangeType;
  quantity_change?: number;
  quantity_before?: number;
  quantity_after?: number;
  reference_type?: ReferenceType;
  reference_id?: number;
  creator?: string;
}

/** 库存变更流水记录响应 */
export interface InventoryTransactionResponse {
  transaction_id: number;
  material_id: number;
  material_code?: string;
  material_name?: string;
  material_specification?: string;
  batch_id: number;
  batch_number?: string;
  change_type: ChangeType;
  quantity_change: number;
  quantity_before: number;
  quantity_after: number;
  reference_number?: string;
  creator: string;
  transaction_time: string;
}

/** 库存变更流水查询参数 */
export interface InventoryTransactionQueryParams extends PaginationParams {
  keyword?: string;
  start_date?: string;
  end_date?: string;
  material_id?: number;
  batch_id?: number;
  change_type?: ChangeType;
  reference_type?: ReferenceType;
  sort_by?: string;
  sort_order?: string;
}

/** 库存变更流水分页结果 */
export interface InventoryTransactionPaginationResult extends PaginationResult<InventoryTransactionResponse> {
}

/** 库存变更流水列表响应（不分页） */
export interface InventoryTransactionListResponse {
  data: InventoryTransactionResponse[];
}

/** 库存变更统计信息 */
export interface InventoryTransactionStatistics {
  total_in: number;
  total_out: number;
  total_adjust: number;
  net_change: number;
  transaction_count: number;
}

/** 库存变更流水详情响应 */
export interface InventoryTransactionDetailResponse {
  transaction: InventoryTransactionResponse;
}

/** 库存变更流水API响应类型别名 */
export type InventoryTransactionGetResponse = InventoryTransactionPaginationResult;
export type InventoryTransactionGetAllResponse = InventoryTransactionListResponse;
export type InventoryTransactionGetByIdResponse = InventoryTransactionDetailResponse;
export type InventoryTransactionCreateResponse = InventoryTransactionResponse;
export type InventoryTransactionStatisticsResponse = InventoryTransactionStatistics;