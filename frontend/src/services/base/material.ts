import api from '../base';
import type { 
  MaterialCreate, 
  MaterialUpdate, 
  MaterialResponse,
  MaterialPaginationParams,
  MaterialPaginationResult,
  MaterialListResponse,
  MaterialStatistics,
  BatchMaterialDelete,
  MaterialBatchImportResult,
  EquipmentOptionsResponse,
  MajorOptionsResponse
} from '../types/material';

/**
 * 器材管理API接口
 */
export const materialAPI = {
  /**
   * 分页获取器材列表
   */
  async getMaterials(params: MaterialPaginationParams): Promise<MaterialPaginationResult> {
    const response = await api.get<MaterialPaginationResult>('/materials', { params });
    return response.data;
  },

  /**
   * 获取所有器材列表（不分页）
   */
  async getAllMaterials(): Promise<MaterialListResponse> {
    const response = await api.get<MaterialListResponse>('/materials/all');
    return response.data;
  },

  /**
   * 获取单个器材详情
   */
  async getMaterial(id: number): Promise<MaterialResponse> {
    const response = await api.get<MaterialResponse>(`/materials/get/${id}`);
    return response.data;
  },

  /**
   * 创建器材
   */
  async createMaterial(data: MaterialCreate): Promise<MaterialResponse> {
    const response = await api.post<MaterialResponse>('/materials/', data);
    return response.data;
  },

  /**
   * 更新器材
   */
  async updateMaterial(id: number, data: MaterialUpdate): Promise<MaterialResponse> {
    const response = await api.put<MaterialResponse>(`/materials/update/${id}`, data);
    return response.data;
  },

  /**
   * 删除器材（软删除）
   */
  async deleteMaterial(id: number): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/materials/delete/${id}`);
    return response.data;
  },

  /**
   * 批量删除器材
   */
  async batchDeleteMaterials(data: BatchMaterialDelete): Promise<{
    success_count: number;
    error_count: number;
    errors: string[];
  }> {
    const response = await api.post('/materials/batch-delete', data);
    return response.data;
  },

  /**
   * 获取器材统计信息
   */
  async getMaterialStatistics(): Promise<MaterialStatistics> {
    const response = await api.get<MaterialStatistics>('/materials/statistics');
    return response.data;
  },

  /**
   * 批量导入器材
   */
  async batchImportMaterials(file: File): Promise<MaterialBatchImportResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    // 不要手动设置Content-Type，浏览器会自动设置正确的boundary
    const response = await api.post<MaterialBatchImportResult>('/materials/batch-import', formData);
    return response.data;
  },



  /**
   * 下载导入模板
   */
  async downloadImportTemplate(): Promise<Blob> {
    const response = await api.get('/materials/import-template', {
      responseType: 'blob'
    });
    return response.data;
  },

  /**
   * 下载错误文件
   */
  async downloadErrorFile(): Promise<Blob> {
    const response = await api.get('/materials/download-error-file', {
      responseType: 'blob'
    });
    return response.data;
  },

  /**
   * 根据多个专业ID获取装备选项
   */
  async getEquipmentOptionsByMajors(majorIds: number[]): Promise<EquipmentOptionsResponse> {
    const params = majorIds && majorIds.length > 0 ? { major_ids: majorIds } : {};
    const response = await api.get<EquipmentOptionsResponse>('/materials/equipment-options', {
      params,
      paramsSerializer: (params) => {
        // 手动序列化参数，确保数组参数正确传递
        const parts: string[] = [];
        Object.keys(params).forEach(key => {
          const value = params[key];
          if (Array.isArray(value)) {
            value.forEach(v => parts.push(`${key}=${encodeURIComponent(v)}`));
          } else {
            parts.push(`${key}=${encodeURIComponent(value)}`);
          }
        });
        return parts.join('&');
      }
    });
    return response.data;
  },

  /**
   * 获取器材表中所有准专业的合集（不重复）
   */
  async getMajorOptions(): Promise<MajorOptionsResponse> {
    const response = await api.get<MajorOptionsResponse>('/materials/major-options');
    return response.data;
  }
};

export default materialAPI;