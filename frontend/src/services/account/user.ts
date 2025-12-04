import api from '../base';
import type { 
  UserManagementResponse, 
  UserManagementCreate, 
  UserManagementUpdate,
  UserPasswordUpdate,
  UserPasswordReset,
  UserRoleAssign,
  UserQueryParams,
  UserPaginationResult,
  BatchUserRoleAssign,
  BatchOperationResult,
  UserStatistics
} from '../types/user';
import type { UserInfo } from '../../services/types/auth';
/**
 * 用户管理API
 * 对应菜单：账户管理 > 用户管理
 * 权限要求：AUTH-read (查看), AUTH-edit (编辑), AUTH-own (个人)
 */
export const userAPI = {
  /**
   * 获取当前用户信息
   * @returns Promise<UserInfo>
   */
  getCurrentUser: async (): Promise<UserInfo> => {
    const response = await api.get<UserInfo>('/users/me');
    
    // 延迟执行Redis状态检查，避免与登录重定向逻辑冲突
    setTimeout(() => {
      // 使用全局函数启动Redis状态检查
      if (window.startRedisStatusCheck) {
        window.startRedisStatusCheck();
        console.log('通过getCurrentUser启动Redis状态定时检查');
      } else {
        console.warn('全局Redis状态检查函数未定义');
      }
    }, 1000); // 延迟1秒执行，确保登录流程完成
    
    return response.data;
  },

  /**
   * 获取用户列表（分页）
   * @param params 查询参数
   * @returns Promise<UserPaginationResult>
   */
  getUsers: async (params: UserQueryParams = {}): Promise<UserPaginationResult> => {
    const response = await api.get<UserPaginationResult>('/users', { params });
    return response.data;
  },

  /**
   * 获取用户详情
   * @param userId 用户ID
   * @returns Promise<UserManagementResponse>
   */
  getUser: async (userId: number): Promise<UserManagementResponse> => {
    const response = await api.get<UserManagementResponse>(`/users/${userId}`);
    return response.data;
  },

  /**
   * 创建新用户
   * @param userData 用户创建数据
   * @returns Promise<UserManagementResponse>
   */
  createUser: async (userData: UserManagementCreate): Promise<UserManagementResponse> => {
    const response = await api.post<UserManagementResponse>('/users/new', userData);
    return response.data;
  },

  /**
   * 更新用户信息
   * @param userId 用户ID
   * @param userData 用户更新数据
   * @returns Promise<UserManagementResponse>
   */
  updateUser: async (userId: number, userData: UserManagementUpdate): Promise<UserManagementResponse> => {
    const response = await api.put<UserManagementResponse>(`/users/update/${userId}`, userData);
    return response.data;
  },

  /**
   * 用户角色分配
   * @param userId 用户ID
   * @param roleData 角色分配数据
   * @returns Promise<UserManagementResponse>
   */
  assignUserRole: async (userId: number, roleData: UserRoleAssign): Promise<UserManagementResponse> => {
    const response = await api.put<UserManagementResponse>(`/users/${userId}/role`, roleData);
    return response.data;
  },

  /**
   * 删除用户（软删除）
   * @param userId 用户ID
   * @returns Promise<UserManagementResponse>
   */
  deleteUser: async (userId: number): Promise<UserManagementResponse> => {
    const response = await api.delete<UserManagementResponse>(`/users/delete/${userId}`);
    return response.data;
  },

  /**
   * 修改自己的密码
   * @param passwordData 密码更新数据
   * @returns Promise<{message: string}>
   */
  changePassword: async (passwordData: UserPasswordUpdate): Promise<{message: string}> => {
    const response = await api.put<{message: string}>('/users/me/password', passwordData);
    return response.data;
  },

  /**
   * 管理员重置用户密码
   * @param userId 用户ID
   * @param passwordData 密码重置数据
   * @returns Promise<{message: string}>
   */
  resetUserPassword: async (userId: number, passwordData: UserPasswordReset): Promise<{message: string}> => {
    const response = await api.put<{message: string}>(`/users/${userId}/password/reset`, passwordData);
    return response.data;
  },

  /**
   * 批量角色分配
   * @param batchData 批量操作数据
   * @returns Promise<BatchOperationResult>
   */
  batchAssignRole: async (batchData: BatchUserRoleAssign): Promise<BatchOperationResult> => {
    const response = await api.put<BatchOperationResult>('/users/batch/role', batchData);
    return response.data;
  },

  /**
   * 获取用户统计信息
   * @returns Promise<UserStatistics>
   */
  getStatistics: async (): Promise<UserStatistics> => {
    const response = await api.get<UserStatistics>('/users/statistics');
    return response.data;
  }
};