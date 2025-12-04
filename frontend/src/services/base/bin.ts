import api from '../base';
import {
  Bin,
  BinCreateRequest,
  BinUpdateRequest,
  BinListResponse,
  BinStatistics,
  BinQueryParams,
  BinBatchDeleteRequest,
  BinBatchDeleteResponse,
  BinPropertiesResponse
} from '../types/bin';

/**
 * 货位管理API服务
 */
export const binApi = {
  /**
   * 获取货位列表（分页）
   * @param params 查询参数
   */
  getBins: async (params?: BinQueryParams): Promise<BinListResponse> => {
    const response = await api.get('/bins', { params });
    return response.data;
  },

  /**
   * 获取货位统计信息
   */
  getStatistics: async (): Promise<BinStatistics> => {
    const response = await api.get('/bins/statistics');
    return response.data;
  },

  /**
   * 获取所有货位属性
   */
  getBinProperties: async (): Promise<BinPropertiesResponse> => {
    const response = await api.get('/bins/properties/all');
    return response.data;
  },

  /**
   * 获取单个货位
   * @param binId 货位ID
   */
  getBin: async (binId: number): Promise<Bin> => {
    const response = await api.get(`/bins/get/${binId}`);
    return response.data;
  },

  /**
   * 创建货位
   * @param data 货位数据
   */
  createBin: async (data: BinCreateRequest): Promise<Bin> => {
    const response = await api.post('/bins', data);
    return response.data;
  },

  /**
   * 更新货位
   * @param binId 货位ID
   * @param data 更新数据
   */
  updateBin: async (binId: number, data: BinUpdateRequest): Promise<Bin> => {
    const response = await api.put(`/bins/update/${binId}`, data);
    return response.data;
  },

  /**
   * 删除货位（软删除）
   * @param binId 货位ID
   */
  deleteBin: async (binId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/bins/delete/${binId}`);
    return response.data;
  },

  /**
   * 批量删除货位
   * @param data 批量删除请求
   */
  batchDelete: async (data: BinBatchDeleteRequest): Promise<BinBatchDeleteResponse> => {
    const response = await api.post('/bins/batch-delete', data);
    return response.data;
  },

  /**
   * 批量导入货位数据
   * @param data 导入数据（FormData或JSON数组）
   * @returns Promise<any>
   */
  batchImport: async (data: FormData | any[]): Promise<any> => {
    if (data instanceof FormData) {
      // 文件上传方式 - 不要手动设置Content-Type，浏览器会自动设置正确的boundary
      const response = await api.post('/bins/batch-import', data);
      return response.data;
    } else {
      // JSON数据方式
      const response = await api.post('/bins/batch-import-data', data);
      return response.data;
    }
  },

  /**
   * 下载货位导入模板
   * @returns Promise<Blob>
   */
  downloadTemplate: async (): Promise<Blob> => {
    const response = await api.get('/bins/import-template', {
      responseType: 'blob'
    });
    return response.data;
  }
};

export default binApi;