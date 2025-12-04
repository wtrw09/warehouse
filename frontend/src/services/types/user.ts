import { PaginationParams, PaginationResult } from './common';

// 用户管理相关类型
export interface UserManagementResponse {
  id: number;
  username: string;
  role_id: number;
  role_name: string;
  department?: string;
  create_time: string;
  update_time: string;
}

export interface UserManagementCreate {
  username: string;
  password: string;
  role_id: number | undefined;
  department?: string;
}

export interface UserManagementUpdate {
  username?: string;
  role_id?: number;
  department?: string;
}

export interface UserPasswordUpdate {
  old_password: string;
  new_password: string;
}

export interface UserPasswordReset {
  new_password: string;
}

export interface UserRoleAssign {
  role_id: number;
}

export interface UserQueryParams extends PaginationParams {
  role_id?: number;
}

export interface UserPaginationResult extends PaginationResult<UserManagementResponse> {}

export interface BatchUserRoleAssign {
  user_ids: number[];
  role_id: number;
}

export interface BatchOperationResult {
  success_count: number;
  failed_count: number;
  failed_users: number[];
  message: string;
}

export interface UserStatistics {
  total_users: number;
  users_by_role: {
    role_id: number;
    role_name: string;
    user_count: number;
  }[];
  recent_registrations: number;
}