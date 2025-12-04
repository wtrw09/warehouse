import api from '../base';
import {
  Equipment,
  EquipmentCreateRequest,
  EquipmentUpdateRequest,
  EquipmentListResponse,
  EquipmentStatistics,
  EquipmentQueryParams,
  EquipmentBatchDeleteRequest,
  EquipmentBatchDeleteResponse
} from '../types/equipment';

/**
 * 装备管理API服务
 */
export const equipmentApi = {
  /**
   * 获取装备列表（分页）
   * @param params 查询参数
   */
  getEquipments: async (params?: EquipmentQueryParams): Promise<EquipmentListResponse> => {
    const response = await api.get('/equipments', { params });
    return response.data;
  },

  /**
   * 获取装备统计信息
   */
  getStatistics: async (): Promise<EquipmentStatistics> => {
    const response = await api.get('/equipments/statistics');
    return response.data;
  },

  /**
   * 获取所有装备列表（不分页）
   */
  getAllEquipments: async (): Promise<{ data: Equipment[]; total: number }> => {
    const response = await api.get('/equipments/all');
    return response.data;
  },

  /**
   * 获取单个装备
   * @param equipmentId 装备ID
   */
  getEquipment: async (equipmentId: number): Promise<Equipment> => {
    const response = await api.get(`/equipments/get/${equipmentId}`);
    return response.data;
  },

  /**
   * 创建装备
   * @param data 装备数据
   */
  createEquipment: async (data: EquipmentCreateRequest): Promise<Equipment> => {
    
    const response = await api.post('/equipments', data);
    console.log('调用完成:');
    return response.data;
  },

  /**
   * 更新装备
   * @param equipmentId 装备ID
   * @param data 更新数据
   */
  updateEquipment: async (equipmentId: number, data: EquipmentUpdateRequest): Promise<Equipment> => {
    const response = await api.put(`/equipments/update/${equipmentId}`, data);
    return response.data;
  },

  /**
   * 删除装备（软删除）
   * @param equipmentId 装备ID
   */
  deleteEquipment: async (equipmentId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/equipments/delete/${equipmentId}`);
    return response.data;
  },

  /**
   * 批量删除装备
   * @param data 批量删除请求
   */
  batchDelete: async (data: EquipmentBatchDeleteRequest): Promise<EquipmentBatchDeleteResponse> => {
    const response = await api.post('/equipments/batch-delete', data);
    return response.data;
  }
};

export default equipmentApi;