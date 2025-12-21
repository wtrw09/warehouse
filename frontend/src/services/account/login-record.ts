import api from '../base';
import type {
  LoginRecordResponse,
  LoginRecordQueryParams,
  MyLoginRecordQueryParams,
  PaginatedLoginRecords,
  LoginStatisticsSummary
} from '../types/login-record';

/**
 * 登录记录API服务
 * 对应菜单：账户管理 > 用户登录记录查询
 * 权限要求：AUTH-read (查看所有用户), AUTH-own (查看自己)
 */
export const loginRecordAPI = {
  /**
   * 查询所有用户登录记录（需要AUTH-read权限）
   * @param params 查询参数
   * @returns Promise<PaginatedLoginRecords>
   */
  getLoginRecords: async (params: LoginRecordQueryParams = {}): Promise<PaginatedLoginRecords> => {
    const response = await api.get<PaginatedLoginRecords>('/login-records', { params });
    return response.data;
  },

  /**
   * 获取当前用户自己的登录记录（需要AUTH-own权限）
   * @param params 查询参数
   * @returns Promise<LoginRecordResponse[]>
   */
  getMyLoginRecords: async (params: MyLoginRecordQueryParams = {}): Promise<LoginRecordResponse[]> => {
    const response = await api.get<LoginRecordResponse[]>('/login-records/my', { params });
    return response.data;
  },

  /**
   * 获取登录统计摘要（需要AUTH-read权限）
   * @param days 统计天数，默认90天
   * @returns Promise<LoginStatisticsSummary>
   */
  getLoginStatistics: async (days: number = 90): Promise<LoginStatisticsSummary> => {
    const response = await api.get<LoginStatisticsSummary>('/login-records/stats/summary', {
      params: { days }
    });
    return response.data;
  }
};