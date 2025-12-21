import { PaginationParams, PaginationResult } from './common';

// 登录记录相关类型
export interface LoginRecordResponse {
  id: number;
  user_id: number;
  username: string;
  ip_address: string;
  user_agent: string;
  login_time: string;
  logout_time: string | null;
  is_active: boolean;
}

export interface LoginRecordQueryParams extends PaginationParams {
  username?: string;
  ip_address?: string;
  start_time?: string;
  end_time?: string;
  search?: string;
}

export interface MyLoginRecordQueryParams extends PaginationParams {
  ip_address?: string;
  start_time?: string;
  end_time?: string;
  search?: string;
}

// 登录记录分页结果接口（使用records字段）
export interface PaginatedLoginRecords {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  records: LoginRecordResponse[];
}

export interface LoginStatisticsSummary {
  total_logins: number;
  active_users: number;
  distinct_ips: number;
  today_logins: number;
  analysis_period_days: number;
}