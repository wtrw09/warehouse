/**
 * 备份管理API
 * 对应菜单：系统管理 > 备份管理
 * 权限要求：SYSTEM-READ (查看), SYSTEM-EDIT (创建/恢复/删除)
 */
import api from '../base';
import type {
  BackupListResponse
} from '../types/system';

export const backupAPI = {
  /**
   * 创建备份
   * @returns Promise<{message: string, result: any}>
   */
  createBackup: async (): Promise<{message: string, result: any}> => {
    const response = await api.post<{message: string, result: any}>('/api/backup/create');
    return response.data;
  },

  /**
   * 获取备份列表
   * @param params 查询参数
   * @returns Promise<BackupListResponse>
   */
  getBackupList: async (params?: {
    keyword?: string;
    backup_type?: string;
    sort_by?: string;
    sort_order?: string;
    days_back?: number;
  }): Promise<BackupListResponse> => {
    const response = await api.get<BackupListResponse>('/api/backup/list', { params });
    return response.data;
  },

  /**
   * 恢复备份
   * @param filename 备份文件名
   * @param adminPassword 管理员密码
   * @returns Promise<{
   *   message: string;
   *   status: string;
   *   pid: number;
   *   backup_file: string;
   *   status_file: string;
   *   recovery_method: string;
   * }>
   */
  recoverBackup: async (filename: string, adminPassword: string): Promise<{
    message: string;
    status: string;
    pid: number;
    backup_file: string;
    status_file: string;
    recovery_method: string;
  }> => {
    const response = await api.post<{
      message: string;
      status: string;
      pid: number;
      backup_file: string;
      status_file: string;
      recovery_method: string;
    }>(`/api/backup/recover/${encodeURIComponent(filename)}`, {
      admin_password: adminPassword
    });
    return response.data;
  },

  /**
   * 删除备份
   * @param filename 备份文件名
   * @returns Promise<{message: string}>
   */
  deleteBackup: async (filename: string): Promise<{message: string}> => {
    const response = await api.delete<{message: string}>(`/api/backup/${encodeURIComponent(filename)}`);
    return response.data;
  },


};

export default backupAPI;