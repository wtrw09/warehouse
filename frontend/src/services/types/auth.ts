// 认证相关类型
export interface Credentials {
  username: string;
  password: string;
}

export interface UserData extends Credentials {
  invitation_code?: string;
}

export interface LoginResponse {
  access_token: string;
  [key: string]: any;
}

export interface UserInfo {
  id: number;
  username: string;
  role_id: number;
  roleName: string;
  permissions: string[];
  roles: string[];
  [key: string]: any;
}