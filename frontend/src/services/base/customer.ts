/**
 * 客户管理API
 * 对应菜单：基础数据 > 客户管理
 * 权限要求：BASE-read (查看), BASE-edit (编辑)
 */
import api from '../base';
import { downloadCustomerErrorFile as downloadCustomerErrorFileUtil } from '../fileDownload';
import type {
  CustomerResponse,
  CustomerCreate,
  CustomerUpdate,
  CustomerQueryParams,
  CustomerPaginationResult,
  BatchCustomerDelete,
  CustomerStatistics,
  BatchDeleteResult
} from '../types/customer';

export const customerAPI = {
  /**
   * 获取客户列表
   * @param params 查询参数
   * @returns Promise<CustomerPaginationResult>
   */
  getCustomers: async (params?: CustomerQueryParams): Promise<CustomerPaginationResult> => {
    const response = await api.get<CustomerPaginationResult>('/customers', { params });
    return response.data;
  },
  
  /**
   * 获取客户统计信息
   * @returns Promise<CustomerStatistics>
   */
  getCustomerStatistics: async (): Promise<CustomerStatistics> => {
    const response = await api.get<CustomerStatistics>('/customers/statistics');
    return response.data;
  },
  
  /**
   * 获取单个客户信息
   * @param id 客户ID
   * @returns Promise<CustomerResponse>
   */
  getCustomerById: async (id: number): Promise<CustomerResponse> => {
    const response = await api.get<CustomerResponse>(`/customers/get/${id}`);
    return response.data;
  },
  
  /**
   * 创建客户
   * @param data 客户数据
   * @returns Promise<CustomerResponse>
   */
  createCustomer: async (data: CustomerCreate): Promise<CustomerResponse> => {
    const response = await api.post<CustomerResponse>('/customers', data);
    return response.data;
  },
  
  /**
   * 更新客户
   * @param id 客户ID
   * @param data 更新数据
   * @returns Promise<CustomerResponse>
   */
  updateCustomer: async (id: number, data: CustomerUpdate): Promise<CustomerResponse> => {
    const response = await api.put<CustomerResponse>(`/customers/update/${id}`, data);
    return response.data;
  },
  
  /**
   * 删除客户
   * @param id 客户ID
   * @returns Promise<{message: string}>
   */
  deleteCustomer: async (id: number): Promise<{message: string}> => {
    const response = await api.delete<{message: string}>(`/customers/delete/${id}`);
    return response.data;
  },
  
  /**
   * 批量删除客户
   * @param data 客户ID数组
   * @returns Promise<BatchDeleteResult>
   */
  batchDeleteCustomers: async (data: BatchCustomerDelete): Promise<BatchDeleteResult> => {
    const response = await api.post<BatchDeleteResult>('/customers/batch-delete', data);
    return response.data;
  },
  
  /**
   * 下载客户导入模板
   * @returns Promise<Blob>
   */
  downloadCustomerTemplate: async (): Promise<Blob> => {
    const response = await api.get('/customers/import-template', {
      responseType: 'blob'
    });
    return response.data;
  },
  
  /**
   * 批量导入客户数据
   * @param data 导入数据（FormData或JSON数组）
   * @returns Promise<any>
   */
  batchImportCustomers: async (data: FormData | any[]): Promise<any> => {
    if (data instanceof FormData) {
      // 文件上传方式 - 不要手动设置Content-Type，浏览器会自动设置正确的boundary
      const response = await api.post('/customers/batch-import', data);
      return response.data;
    } else {
      // JSON数据方式
      const response = await api.post('/customers/batch-import-data', data);
      return response.data;
    }
  },

  /**
   * 下载客户导入错误文件
   * @param fileName 错误文件名
   * @param downloadFileName 下载时显示的文件名
   * @returns Promise<void>
   */
  downloadCustomerErrorFile: async (
    fileName: string,
    downloadFileName: string = '客户导入错误数据.xls'
  ): Promise<void> => {
    return downloadCustomerErrorFileUtil(fileName, downloadFileName);
  }
};

export default customerAPI;