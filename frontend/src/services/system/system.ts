/**
 * 系统配置管理API
 * 对应菜单：系统管理 > 系统配置
 * 权限要求：BASE-read (查看), BASE-edit (编辑)
 */
import api from '../base';
import type {
  SystemConfigResponse,
  SystemConfigUpdate,
  SystemConfigListResponse
} from '../types/system';

export const systemAPI = {
  config: {
 /**
 * 获取系统配置
 * @returns Promise<SystemConfigListResponse>
 */
getSystemConfig: async (): Promise<SystemConfigListResponse> => {
  const response = await api.get<SystemConfigListResponse>('/system/config');
  return response.data;
},

    /**
     * 更新系统配置
     * @param data 更新数据
     * @returns Promise<SystemConfigResponse>
     */
    updateSystemConfig: async (data: SystemConfigUpdate): Promise<SystemConfigResponse> => {
      const response = await api.put<SystemConfigResponse>(`/system/config/${encodeURIComponent(data.config_key)}`, {
        config_value: data.config_value
      });
      return response.data;
    },

    /**
     * 获取系统初始化状态
     * @returns Promise<{initialized: boolean, init_time: string, init_version: string}>
     */
    getSystemInitStatus: async (): Promise<{initialized: boolean, init_time: string, init_version: string}> => {
      const response = await api.get<{initialized: boolean, init_time: string, init_version: string}>('/system/init/status');
      return response.data;
    },

    /**
     * 初始化系统配置
     * @returns Promise<{message: string, init_time: string, status: string}>
     */
    initializeSystem: async (): Promise<{message: string, init_time: string, status: string}> => {
      const response = await api.post<{message: string, init_time: string, status: string}>('/system/init');
      return response.data;
    },

    /**
     * 测试Redis服务器状态
     * @returns Promise<{status: string, message: string}>
     */
    testRedisStatus: async (): Promise<{
      status: string;
      message: string;
      redis_available: boolean;
      fallback_active: boolean;
      fallback_sessions_count?: number;
      auth_strategy?: string;
      redis_version?: string;
      connected_clients?: number;
      used_memory?: string;
    }> => {
      const response = await api.get<{
        status: string;
        message: string;
        redis_available: boolean;
        fallback_active: boolean;
        fallback_sessions_count?: number;
        auth_strategy?: string;
        redis_version?: string;
        connected_clients?: number;
        used_memory?: string;
      }>('/system/redis/status');
      return response.data;
    }
  }
};

export default systemAPI;