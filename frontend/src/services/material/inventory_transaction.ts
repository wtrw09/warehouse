import api from '../base';
import type {
  InventoryTransactionQueryParams,
  InventoryTransactionPaginationResult,
  InventoryTransactionListResponse,
  InventoryTransactionDetailResponse,
  InventoryTransactionCreateParams,
  InventoryTransactionUpdateParams,
  InventoryTransactionResponse,
  InventoryTransactionStatistics,
  ChangeType,
  ReferenceType
} from '../types/inventory_transaction';

/**
 * 库存变更流水管理API
 */
export const inventoryTransactionAPI = {
  /**
   * 获取库存变更流水分页列表
   * @param params 查询参数
   * @returns 分页结果
   */
  getInventoryTransactions: async (params: InventoryTransactionQueryParams): Promise<InventoryTransactionPaginationResult> => {
    const response = await api.get<InventoryTransactionPaginationResult>('/inventory-transactions', { params });
    return response.data;
  },

  /**
   * 获取所有库存变更流水列表（不分页）
   * @param params 查询参数
   * @returns 列表结果
   */
  getAllInventoryTransactions: async (params: {
    keyword?: string;
    start_date?: string;
    end_date?: string;
    material_id?: number;
    batch_id?: number;
    change_type?: ChangeType;
    reference_type?: ReferenceType;
    sort_by?: string;
    sort_order?: string;
  } = {}): Promise<InventoryTransactionListResponse> => {
    const response = await api.get<InventoryTransactionListResponse>('/inventory-transactions/all', { params });
    return response.data;
  },

  /**
   * 获取单个库存变更流水记录详情
   * @param transactionId 流水ID
   * @returns 详情响应
   */
  getInventoryTransactionById: async (transactionId: number): Promise<InventoryTransactionDetailResponse> => {
    const response = await api.get<InventoryTransactionDetailResponse>(`/inventory-transactions/get/${transactionId}`);
    return response.data;
  },

  /**
   * 创建库存变更流水记录
   * @param data 创建参数
   * @returns 创建的记录
   */
  createInventoryTransaction: async (data: InventoryTransactionCreateParams): Promise<InventoryTransactionResponse> => {
    const response = await api.post<InventoryTransactionResponse>('/inventory-transactions', data);
    return response.data;
  },

  /**
   * 获取库存变更统计信息
   * @param params 统计参数
   * @returns 统计信息
   */
  getStatistics: async (params: {
    material_id?: number;
    batch_id?: number;
    start_date?: string;
    end_date?: string;
  } = {}): Promise<InventoryTransactionStatistics> => {
    const response = await api.get<InventoryTransactionStatistics>('/inventory-transactions/statistics', { params });
    return response.data;
  }
};

// 导出枚举类型
export { ChangeType, ReferenceType };

// 导出类型别名
export type {
  InventoryTransactionQueryParams,
  InventoryTransactionPaginationResult,
  InventoryTransactionListResponse,
  InventoryTransactionDetailResponse,
  InventoryTransactionCreateParams,
  InventoryTransactionUpdateParams,
  InventoryTransactionResponse,
  InventoryTransactionStatistics
};