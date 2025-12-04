/**
 * 二级专业管理API
 * 对应菜单：基础数据 > 二级专业管理
 * 权限要求：BASE-read (查看), BASE-edit (编辑)
 */
import api from '../base';
import type {
  SubMajorResponse,
  SubMajorCreate,
  SubMajorUpdate,
  SubMajorQueryParams,
  SubMajorListResult,
  BatchSubMajorDelete,
  SubMajorStatistics,
  SubMajorAddDescription,
  SubMajorAddDescriptionResult
} from '../types/sub_major';

export const subMajorAPI = {
  /**
   * 获取二级专业列表
   * @param params 查询参数
   * @returns Promise<SubMajorListResult>
   */
  getSubMajors: async (params?: SubMajorQueryParams): Promise<SubMajorListResult> => {
    const response = await api.get<SubMajorListResult>('/sub-majors', { params });
    return response.data;
  },
  
  /**
   * 获取单个二级专业信息
   * @param id 二级专业ID
   * @returns Promise<SubMajorResponse>
   */
  getSubMajor: async (id: number): Promise<SubMajorResponse> => {
    const response = await api.get<SubMajorResponse>(`/sub-majors/get/${id}`);
    return response.data;
  },
  
  /**
   * 获取二级专业统计信息
   * @returns Promise<SubMajorStatistics>
   */
  getSubMajorStatistics: async (): Promise<SubMajorStatistics> => {
    const response = await api.get<SubMajorStatistics>('/sub-majors/statistics');
    return response.data;
  },
  
  /**
   * 创建二级专业
   * @param data 二级专业数据
   * @returns Promise<SubMajorResponse>
   */
  createSubMajor: async (data: SubMajorCreate): Promise<SubMajorResponse> => {
    const response = await api.post<SubMajorResponse>('/sub-majors', data);
    return response.data;
  },
  
  /**
   * 更新二级专业
   * @param id 二级专业ID
   * @param data 更新数据
   * @returns Promise<SubMajorResponse>
   */
  updateSubMajor: async (id: number, data: SubMajorUpdate): Promise<SubMajorResponse> => {
    console.log('更新二级专业数据:', data);
    const response = await api.put<SubMajorResponse>(`/sub-majors/update/${id}`, data);
    return response.data;
  },
  
  /**
   * 删除二级专业
   * @param id 二级专业ID
   * @returns Promise<void>
   */
  deleteSubMajor: async (id: number): Promise<void> => {
    await api.delete(`/sub-majors/delete/${id}`);
  },
  
  /**
   * 批量删除二级专业
   * @param data 批量删除数据
   * @returns Promise<void>
   */
  batchDeleteSubMajors: async (data: BatchSubMajorDelete): Promise<void> => {
    await api.post('/sub-majors/batch-delete', data);
  },

  /**
   * 向二级专业添加描述项
   * @param data 添加描述数据
   * @returns Promise<SubMajorAddDescriptionResult>
   */
  addDescriptionToSubMajor: async (data: SubMajorAddDescription): Promise<SubMajorAddDescriptionResult> => {
    const response = await api.post<SubMajorAddDescriptionResult>('/sub-majors/add-description', data);
    return response.data;
  }
};

export default subMajorAPI;