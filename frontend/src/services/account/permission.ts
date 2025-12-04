import api from '../base';
import type { Permission } from '../types/permission';

/**
 * 权限管理API
 * 对应菜单：账户管理 > 权限管理
 * 权限要求：AUTH-read
 */
export const permissionAPI = {
  /**
   * 获取所有权限列表
   * @returns Promise<Permission[]>
   */
  getPermissions: async (): Promise<Permission[]> => {
    const response = await api.get<Permission[]>('/permissions');
    return response.data;
  }
};