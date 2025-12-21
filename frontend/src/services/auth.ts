import api from './base';
import type { Credentials, UserData, LoginResponse, UserInfo } from './types/auth';

/**
 * 认证相关API
 * 对应菜单：登录/注册功能
 */
export const authAPI = {
  /**
   * 用户登录
   * @param credentials 登录凭证
   * @returns Promise<LoginResponse>
   */
  login: async (credentials: Credentials): Promise<LoginResponse> => {
    // 创建FormData对象来提交表单数据
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await api.post<LoginResponse>('/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
  },
  
  /**
   * 获取当前用户信息
   * @returns Promise<UserInfo>
   */
  getCurrentUser: async (): Promise<UserInfo> => {
    const response = await api.get<UserInfo>('/users/me');
    return response.data;
  },
  
  /**
   * 用户登出
   */
  logout: async (): Promise<void> => {
    try {
      await api.post('/logout');
    } finally {
      localStorage.removeItem('token');
    }
  },
  
  /**
   * 用户注册
   * @param userData 用户注册数据
   * @returns Promise<any>
   */
  register: async (userData: UserData): Promise<any> => {
    // 创建FormData对象来提交表单数据
    const formData = new FormData();
    formData.append('username', userData.username);
    formData.append('password', userData.password);
    if (userData.invitation_code) {
      formData.append('invitation_code', userData.invitation_code);
    }
    
    const response = await api.post('/register', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data;
  }
};