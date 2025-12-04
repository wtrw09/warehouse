import api from '../base';
import type {
  PaginatedInventoryDetailsResponse,
  InventoryDetailsListResponse,
  InventoryMajorOptionsResponse,
  InventoryEquipmentOptionsResponse,
  InventoryDetailsQueryParams,
  InventoryDetailsStatistics
} from '../types/inventory_detail';
import type {
  BatchCodeGenerateRequest,
  BatchCodeGenerateResponse
} from '../types/batch_code';

/**
 * 库存器材明细管理API
 */
export const inventoryDetailAPI = {
  /**
   * 分页查询库存器材明细
   */
  getInventoryDetails: async (params: InventoryDetailsQueryParams): Promise<PaginatedInventoryDetailsResponse> => {
    // 过滤掉空数组参数，避免发送无效筛选条件
    const filteredParams = { ...params };
    if (filteredParams.major_id && filteredParams.major_id.length === 0) {
      delete filteredParams.major_id;
    }
    if (filteredParams.equipment_id && filteredParams.equipment_id.length === 0) {
      delete filteredParams.equipment_id;
    }
    
    const response = await api.get<PaginatedInventoryDetailsResponse>('/inventory-details/', { params: filteredParams });
    return response.data;
  },

  /**
   * 获取全部库存器材明细（不分页）
   */
  getAllInventoryDetails: async (params: {
    keyword?: string;
    major_id?: number[];
    equipment_id?: number[];
    warehouse_id?: number;
    bin_id?: number;
    sort_by?: string;
    sort_order?: string;
  } = {}): Promise<InventoryDetailsListResponse> => {
    const response = await api.get<InventoryDetailsListResponse>('/inventory-details/all', { params });
    return response.data;
  },

  /**
   * 获取库存器材所属专业选项集合
   */
  getMajorOptionsFromInventory: async (): Promise<InventoryMajorOptionsResponse> => {
    const response = await api.get<InventoryMajorOptionsResponse>('/inventory-details/major-options');
    return response.data;
  },

  getEquipmentOptionsFromInventory: async (majorIds?: number[]): Promise<InventoryEquipmentOptionsResponse> => {
    const params = majorIds ? { major_ids: majorIds.join(',') } : {};
    const response = await api.get<InventoryEquipmentOptionsResponse>('/inventory-details/equipment-options', {
      params
    });
    return response.data;
  },

  /**
   * 获取库存器材明细统计信息
   */
  getInventoryDetailsStatistics: async (): Promise<InventoryDetailsStatistics> => {
    const response = await api.get<InventoryDetailsStatistics>('/inventory-details/statistics');
    return response.data;
  },

  /**
   * 导出库存器材明细数据到Excel
   */
  exportInventoryDetails: async (params: Omit<InventoryDetailsQueryParams, 'page' | 'page_size'>): Promise<Blob> => {
    // 过滤掉空数组参数，避免发送无效筛选条件
    const filteredParams = { ...params };
    if (filteredParams.major_id && filteredParams.major_id.length === 0) {
      delete filteredParams.major_id;
    }
    if (filteredParams.equipment_id && filteredParams.equipment_id.length === 0) {
      delete filteredParams.equipment_id;
    }
    
    const response = await api.get('/inventory-details/export-excel', {
      params: filteredParams,
      responseType: 'blob'
    });
    return response.data;
  },

  /**
   * 生成批次编码
   */
  generateBatchCode: async (request: BatchCodeGenerateRequest): Promise<BatchCodeGenerateResponse> => {
    const response = await api.post<BatchCodeGenerateResponse>('/inventory-details/generate-batch-code', request);
    return response.data;
  }
};