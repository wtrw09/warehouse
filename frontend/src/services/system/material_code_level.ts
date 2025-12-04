/**
 * 器材编码分类层级管理API
 * 对应菜单：系统管理 > 器材编码分类层级
 * 权限要求：BASE-read (查看), BASE-edit (编辑)
 */
import api from '../base';
import type {
  MaterialCodeLevelResponse,
  MaterialCodeLevelCreate,
  MaterialCodeLevelUpdate,
  BatchMaterialCodeLevelDelete,
  MaterialCodeLevelStatistics,
  MaterialCodeLevelAddDescription,
  MaterialCodeLevelAddDescriptionResult
} from '../types/material_code_level';

export const materialCodeLevelAPI = {
  /**
   * 获取器材编码分类层级列表（不分页，获取所有数据）
   * @returns Promise<MaterialCodeLevelResponse[]>
   */
  getMaterialCodeLevels: async (): Promise<MaterialCodeLevelResponse[]> => {
    const response = await api.get<MaterialCodeLevelResponse[]>('/material-code-levels/all');
    return response.data;
  },
  
  /**
   * 获取器材编码分类层级统计信息
   * @returns Promise<MaterialCodeLevelStatistics>
   */
  getMaterialCodeLevelStatistics: async (): Promise<MaterialCodeLevelStatistics> => {
    const response = await api.get<MaterialCodeLevelStatistics>('/material-code-levels/statistics');
    return response.data;
  },
  
  /**
   * 获取单个器材编码分类层级信息
   * @param id 层级ID
   * @returns Promise<MaterialCodeLevelResponse>
   */
  getMaterialCodeLevelById: async (id: number): Promise<MaterialCodeLevelResponse> => {
    const response = await api.get<MaterialCodeLevelResponse>(`/material-code-levels/get/${id}`);
    return response.data;
  },
  
  /**
   * 创建器材编码分类层级
   * @param data 层级数据
   * @returns Promise<MaterialCodeLevelResponse>
   */
  createMaterialCodeLevel: async (data: MaterialCodeLevelCreate): Promise<MaterialCodeLevelResponse> => {
    const response = await api.post<MaterialCodeLevelResponse>('/material-code-levels', data);
    return response.data;
  },
  
  /**
   * 更新器材编码分类层级
   * @param id 层级ID
   * @param data 更新数据
   * @returns Promise<MaterialCodeLevelResponse>
   */
  updateMaterialCodeLevel: async (id: number, data: MaterialCodeLevelUpdate): Promise<MaterialCodeLevelResponse> => {
    const response = await api.put<MaterialCodeLevelResponse>(`/material-code-levels/update/${id}`, data);
    return response.data;
  },
  
  /**
   * 删除器材编码分类层级
   * @param id 层级ID
   * @returns Promise<{message: string}>
   */
  deleteMaterialCodeLevel: async (id: number): Promise<{message: string}> => {
    const response = await api.delete<{message: string}>(`/material-code-levels/delete/${id}`);
    return response.data;
  },
  
  /**
   * 批量删除器材编码分类层级
   * @param data 批量删除数据
   * @returns Promise<{message: string, error_ids: number[]}>
   */
  batchDeleteMaterialCodeLevels: async (data: BatchMaterialCodeLevelDelete): Promise<{message: string, error_ids: number[]}> => {
    const response = await api.post<{message: string, error_ids: number[]}>('/material-code-levels/batch-delete', data);
    return response.data;
  },

  /**
   * 通过层级编码和描述字符串向JSON格式description字段插入数据
   * @param data 添加描述数据
   * @returns Promise<MaterialCodeLevelAddDescriptionResult>
   */
  addDescriptionToMaterialCodeLevel: async (data: MaterialCodeLevelAddDescription): Promise<MaterialCodeLevelAddDescriptionResult> => {
    const response = await api.post<MaterialCodeLevelAddDescriptionResult>('/material-code-levels/add-description', data);
    return response.data;
  },

  /**
   * 删除所有器材编码分类层级数据
   * @returns Promise<{message: string}>
   */
  deleteAllMaterialCodeLevels: async (): Promise<{message: string}> => {
    const response = await api.delete<{message: string}>('/material-code-levels/delete-all');
    return response.data;
  },

  /**
   * 根据二级专业数据生成器材编码分类层级数据
   * @returns Promise<{message: string, generated_count: number}>
   */
  generateMaterialCodeLevelsFromSubMajors: async (): Promise<{message: string, generated_count: number}> => {
    const response = await api.post<{message: string, generated_count: number}>('/material-code-levels/generate-from-sub-majors');
    return response.data;
  }
};

export default materialCodeLevelAPI;