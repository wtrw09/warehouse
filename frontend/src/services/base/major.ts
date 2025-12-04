/**
 * 专业管理API
 * 对应菜单：基础数据 > 专业管理
 * 权限要求：BASE-read (查看), BASE-edit (编辑)
 */
import api from '../base';
import type {
  MajorResponse,
  MajorCreate,
  MajorUpdate,
  MajorQueryParams,
  MajorListResult,
  BatchMajorDelete
} from '../types/major';

export const majorAPI = {
  /**
   * 获取专业列表
   * @param params 查询参数
   * @returns Promise<MajorListResult>
   */
  getMajors: async (params?: MajorQueryParams): Promise<MajorListResult> => {
    const response = await api.get<MajorListResult>('/majors', { params });
    return response.data;
  },
  
  /**
   * 获取单个专业信息
   * @param id 专业ID
   * @returns Promise<MajorResponse>
   */
  getMajor: async (id: number): Promise<MajorResponse> => {
    const response = await api.get<MajorResponse>(`/majors/get/${id}`);
    return response.data;
  },
  
  /**
   * 创建专业
   * @param data 专业数据
   * @returns Promise<MajorResponse>
   */
  createMajor: async (data: MajorCreate): Promise<MajorResponse> => {
    const response = await api.post<MajorResponse>('/majors', data);
    return response.data;
  },
  
  /**
   * 更新专业
   * @param id 专业ID
   * @param data 更新数据
   * @returns Promise<MajorResponse>
   */
  updateMajor: async (id: number, data: MajorUpdate): Promise<MajorResponse> => {
    const response = await api.put<MajorResponse>(`/majors/update/${id}`, data);
    return response.data;
  },
  
  /**
   * 删除专业
   * @param id 专业ID
   * @returns Promise<void>
   */
  deleteMajor: async (id: number): Promise<void> => {
    await api.delete(`/majors/delete/${id}`);
  },
  
  /**
   * 批量删除专业
   * @param data 批量删除数据
   * @returns Promise<void>
   */
  batchDeleteMajors: async (data: BatchMajorDelete): Promise<void> => {
    await api.post('/majors/batch-delete', data);
  }
};

export default majorAPI;