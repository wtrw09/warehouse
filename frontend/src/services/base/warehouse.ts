/**
 * 仓库管理API
 * 对应菜单：基础数据 > 仓库配置
 * 权限要求：BASE-read (查看), BASE-edit (编辑)
 */
import api from '../base';
import type {
  WarehouseResponse,
  WarehouseCreate,
  WarehouseUpdate,
  WarehouseQueryParams,
  WarehousePaginationResult,
  BatchWarehouseDelete,
  WarehouseStatistics
} from '../types/warehouse';

export const warehouseAPI = {
  /**
   * 获取仓库列表
   * @param params 查询参数
   * @returns Promise<any>
   */
  getWarehouses: async (params?: WarehouseQueryParams): Promise<WarehousePaginationResult> => {
    const response = await api.get<WarehousePaginationResult>('/warehouses', { params });
    return response.data;
  },
  
  /**
   * 获取所有仓库数据（不分页）
   * @returns Promise<WarehouseResponse[]>
   */
  getAllWarehouses: async (): Promise<WarehouseResponse[]> => {
    const response = await api.get<WarehouseResponse[]>('/warehouses/all');
    return response.data;
  },
  
  /**
   * 获取仓库统计信息
   * @returns Promise<any>
   */
  getWarehouseStatistics: async (): Promise<WarehouseStatistics> => {
    const response = await api.get<WarehouseStatistics>('/warehouses/statistics');
    return response.data;
  },
  
  /**
   * 获取单个仓库信息
   * @param id 仓库ID
   * @returns Promise<any>
   */
  getWarehouseById: async (id: number): Promise<WarehouseResponse> => {
    const response = await api.get<WarehouseResponse>(`/warehouses/get/${id}`);
    return response.data;
  },
  
  /**
   * 创建仓库
   * @param data 仓库数据
   * @returns Promise<any>
   */
  createWarehouse: async (data: WarehouseCreate): Promise<WarehouseResponse> => {
    const response = await api.post<WarehouseResponse>('/warehouses', data);
    return response.data;
  },
  
  /**
   * 更新仓库
   * @param id 仓库ID
   * @param data 更新数据
   * @returns Promise<any>
   */
  updateWarehouse: async (id: number, data: WarehouseUpdate): Promise<WarehouseResponse> => {
    const response = await api.put<WarehouseResponse>(`/warehouses/update/${id}`, data);
    return response.data;
  },
  
  /**
   * 删除仓库
   * @param id 仓库ID
   * @returns Promise<any>
   */
  deleteWarehouse: async (id: number): Promise<WarehouseResponse> => {
    const response = await api.delete<WarehouseResponse>(`/warehouses/delete/${id}`);
    return response.data;
  },
  
  /**
   * 批量删除仓库
   * @param warehouse_ids 仓库ID数组
   * @returns Promise<any>
   */
  batchDeleteWarehouses: async (data: BatchWarehouseDelete): Promise<{message: string}> => {
    const response = await api.post<{message: string}>('/warehouses/batch-delete', data);
    return response.data;
  },
  
  /**
   * 下载仓库导入模板
   * @returns Promise<Blob>
   */
  downloadWarehouseTemplate: async (): Promise<Blob> => {
    const response = await api.get('/warehouses/import-template', {
      responseType: 'blob'
    });
    return response.data;
  },
  
  /**
   * 批量导入仓库数据
   * @param data 导入数据（FormData或JSON数组）
   * @returns Promise<any>
   */
  batchImportWarehouses: async (data: FormData | any[]): Promise<any> => {
    if (data instanceof FormData) {
      // 文件上传方式 - 不要手动设置Content-Type，浏览器会自动设置正确的boundary
      const response = await api.post('/warehouses/batch-import', data);
      return response.data;
    } else {
      // JSON数据方式
      const response = await api.post('/warehouses/batch-import-data', data);
      return response.data;
    }
  }
};

export default warehouseAPI;