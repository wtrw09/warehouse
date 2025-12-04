/**
 * 供应商管理API
 * 对应菜单：基础数据 > 供应商管理
 * 权限要求：BASE-read (查看), BASE-edit (编辑)
 */
import api from '../base';
import { downloadSupplierErrorFile as downloadSupplierErrorFileUtil } from '../fileDownload';
import type {
  SupplierResponse,
  SupplierCreate,
  SupplierUpdate,
  SupplierQueryParams,
  SupplierPaginationResult,
  BatchSupplierDelete,
  SupplierStatistics,
  SupplierBatchDeleteResult
} from '../types/supplier';
import type { BatchImportResult } from '../types/import';

export const supplierAPI = {
  /**
   * 获取供应商列表
   * @param params 查询参数
   * @returns Promise<SupplierPaginationResult>
   */
  getSuppliers: async (params?: SupplierQueryParams): Promise<SupplierPaginationResult> => {
    const response = await api.get<SupplierPaginationResult>('/suppliers', { params });
    return response.data;
  },
  
  /**
   * 获取供应商统计信息
   * @returns Promise<SupplierStatistics>
   */
  getSupplierStatistics: async (): Promise<SupplierStatistics> => {
    const response = await api.get<SupplierStatistics>('/suppliers/statistics');
    return response.data;
  },
  
  /**
   * 获取单个供应商信息
   * @param id 供应商ID
   * @returns Promise<SupplierResponse>
   */
  getSupplierById: async (id: number): Promise<SupplierResponse> => {
    const response = await api.get<SupplierResponse>(`/suppliers/get/${id}`);
    return response.data;
  },
  
  /**
   * 创建供应商
   * @param data 供应商数据
   * @returns Promise<SupplierResponse>
   */
  createSupplier: async (data: SupplierCreate): Promise<SupplierResponse> => {
    const response = await api.post<SupplierResponse>('/suppliers', data);
    return response.data;
  },
  
  /**
   * 更新供应商
   * @param id 供应商ID
   * @param data 更新数据
   * @returns Promise<SupplierResponse>
   */
  updateSupplier: async (id: number, data: SupplierUpdate): Promise<SupplierResponse> => {
    const response = await api.put<SupplierResponse>(`/suppliers/update/${id}`, data);
    return response.data;
  },
  
  /**
   * 删除供应商
   * @param id 供应商ID
   * @returns Promise<{message: string}>
   */
  deleteSupplier: async (id: number): Promise<{message: string}> => {
    const response = await api.delete<{message: string}>(`/suppliers/delete/${id}`);
    return response.data;
  },
  
  /**
   * 批量删除供应商
   * @param data 供应商ID数组
   * @returns Promise<SupplierBatchDeleteResult>
   */
  batchDeleteSuppliers: async (data: BatchSupplierDelete): Promise<SupplierBatchDeleteResult> => {
    const response = await api.post<SupplierBatchDeleteResult>('/suppliers/batch-delete', data);
    return response.data;
  },

  /**
   * 批量导入供应商
   * @param data 供应商数据数组或FormData
   * @returns Promise<BatchImportResult>
   */
  batchImportSuppliers: async (data: SupplierCreate[] | FormData): Promise<BatchImportResult> => {
    console.log('测试供应商数据:', data);
    if (data instanceof FormData) {
      // 文件上传方式 - 不要手动设置Content-Type，浏览器会自动设置正确的boundary
      const response = await api.post<BatchImportResult>('/suppliers/batch-import', data);
      return response.data;
    } else {
      // JSON数据方式
      const response = await api.post<BatchImportResult>('/suppliers/batch-import-data', data);
      return response.data;
    }
  },

  /**
   * 下载供应商导入模板
   * @returns Promise<Blob>
   */
  downloadSupplierTemplate: async (): Promise<Blob> => {
    const response = await api.get('/suppliers/import-template', {
      responseType: 'blob'
    });
    return response.data;
  },

  /**
   * 下载供应商导入错误文件
   * @param fileName 错误文件名
   * @param downloadFileName 下载时显示的文件名
   * @returns Promise<void>
   */
  downloadSupplierErrorFile: async (
    fileName: string,
    downloadFileName: string = '供应商导入错误数据.xls'
  ): Promise<void> => {
    return downloadSupplierErrorFileUtil(fileName, downloadFileName);
  }
};

export default supplierAPI;