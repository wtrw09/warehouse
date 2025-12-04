import api from '../base';
import type { 
  PaginationParams, 
  PaginationResult
} from '../types/common';
import type {
  RoleResponse,
  RoleWithPermissions,
  RoleCreate,
  RoleUpdate,
  UpdateRolePermissions
} from '../types/role';

/**
 * 角色管理API
 * 对应菜单：账户管理 > 角色管理
 * 查看权限要求：AUTH-read
 * 编辑权限要求：AUTH-edit
 */
export const roleAPI = {
  /**
   * 获取角色列表（分页）
   * @param params 分页参数
   * @returns Promise<PaginationResult<RoleWithPermissions>>
   */
  getRoles: async (params: PaginationParams = {}): Promise<PaginationResult<RoleWithPermissions>> => {
    const response = await api.get<PaginationResult<RoleWithPermissions>>('/roles', { params });
    return response.data;
  },
  
  /**
   * 获取单个角色详情
   * @param roleId 角色ID
   * @returns Promise<RoleWithPermissions>
   */
  getRole: async (roleId: number): Promise<RoleWithPermissions> => {
    const response = await api.get<RoleWithPermissions>(`/roles/${roleId}`);
    return response.data;
  },
  
  /**
   * 创建新角色
   * @param roleData 角色创建数据
   * @returns Promise<RoleResponse>
   */
  createRole: async (roleData: RoleCreate): Promise<RoleResponse> => {
    const response = await api.post<RoleResponse>('/roles/new', roleData);
    return response.data;
  },
  
  /**
   * 更新角色信息
   * @param roleId 角色ID
   * @param roleData 角色更新数据
   * @returns Promise<RoleResponse>
   */
  updateRole: async (roleId: number, roleData: RoleUpdate): Promise<RoleResponse> => {
    const response = await api.put<RoleResponse>(`/roles/update/${roleId}`, roleData);
    return response.data;
  },
  
  /**
   * 更新角色权限
   * @param roleId 角色ID
   * @param permissions 权限更新数据
   * @returns Promise<RoleWithPermissions>
   */
  updateRolePermissions: async (roleId: number, permissions: UpdateRolePermissions): Promise<RoleWithPermissions> => {
    const response = await api.put<RoleWithPermissions>(`/roles/${roleId}/permissions`, permissions);
    return response.data;
  },
  
  /**
   * 删除角色
   * @param roleId 角色ID
   * @returns Promise<RoleResponse>
   */
  deleteRole: async (roleId: number): Promise<RoleResponse> => {
    const response = await api.delete<RoleResponse>(`/roles/delete/${roleId}`);
    return response.data;
  }
};