import axios from 'axios';
import { ElMessage } from 'element-plus';
import router from '../router';

// 定义服务器设置类型
interface ServerSettings {
  ip?: string;
  port?: number;
}

// 获取服务器设置
const getServerBaseURL = (): string => {
  // 在生产环境（Docker容器）中，使用相对路径通过 Nginx 代理访问后端
  // 开发环境判断：必须是 localhost/127.0.0.1 + Vite开发端口
  const isDevelopment = (
    window.location.hostname === 'localhost' || 
    window.location.hostname === '127.0.0.1'
  ) && (
    window.location.port === '5173' ||  // Vite 默认端口
    window.location.port === '3000'     // 常用开发端口
  );
  
  console.log('[BaseURL Debug]', {
    hostname: window.location.hostname,
    port: window.location.port,
    protocol: window.location.protocol,
    href: window.location.href,
    isDevelopment
  });
  
  // 生产环境，强制使用 Nginx 代理
  if (!isDevelopment) {
    console.log('[BaseURL] 生产环境，使用 /api 代理', { hostname: window.location.hostname, port: window.location.port });
    return '/api'; // 生产环境返回 /api，通过 nginx 代理访问后端
  }
  
  // 开发环境下，从本地存储读取配置
  console.log('[BaseURL] 开发环境，从 localStorage 读取配置');
  try {
    const savedSettings = localStorage.getItem('serverSettings');
    if (savedSettings) {
      const parsed: ServerSettings = JSON.parse(savedSettings);
      const ip = parsed.ip || 'localhost';
      const port = parsed.port || 8000;
      const url = `http://${ip}:${port}`;
      console.log('[BaseURL] 使用配置:', url);
      return url;
    }
  } catch (err) {
    console.error('获取服务器设置失败:', err);
  }
  // 开发环境默认值
  console.log('[BaseURL] 使用默认值: http://localhost:8000');
  return 'http://localhost:8000';
};

// 创建 axios 实例
// 注意：baseURL 不在这里设置，而是在请求拦截器中动态设置
const api = axios.create({
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  },
  // 正确序列化数组参数，使用 repeat 格式：major_id=1&major_id=2
  paramsSerializer: {
    serialize: (params) => {
      const parts: string[] = [];
      Object.keys(params).forEach(key => {
        const value = params[key];
        if (value === null || value === undefined) {
          return;
        }
        if (Array.isArray(value)) {
          // 数组参数：major_id=1&major_id=2
          value.forEach(item => {
            if (item !== null && item !== undefined) {
              parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(item)}`);
            }
          });
        } else {
          parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
        }
      });
      return parts.join('&');
    }
  }
});

// 请求拦截器 - 动态更新baseURL并添加token
api.interceptors.request.use(
  (config: any) => {
    // 动态设置 baseURL
    const newBaseURL = getServerBaseURL();
    config.baseURL = newBaseURL;
    
    // 添加 token
    if (!config.headers) {
      config.headers = {};
    }
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // 如果是 FormData，删除 Content-Type，让浏览器自动设置（包含 boundary）
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
      // console.log('[Request Interceptor] 检测到 FormData，已移除 Content-Type');
    }
    
    // 详细调试信息
    console.log('[Request Interceptor]', {
      method: config.method?.toUpperCase(),
      baseURL: config.baseURL,
      url: config.url,
      fullURL: config.baseURL + config.url,
      isFormData: config.data instanceof FormData,
      headers: config.headers
    });
    
    return config;
  },
  (error: any) => {
    console.error('[Request Interceptor Error]', error);
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理网络错误和认证错误
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: any) => {
    // 处理网络连接错误（服务器不可用）
    if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
      console.error('服务器连接失败:', error.message);
      
      // 只显示错误提示，不清除token，不跳转登录页
      // 网络错误可能是临时的，不应该强制用户退出登录
      ElMessage.error('网络连接失败，请检查网络或稍后重试');
      
      return Promise.reject(error);
    }
    
    // 处理服务器内部错误（500系列）
    if (error.response?.status >= 500) {
      console.error('服务器内部错误:', error.response?.status, error.response?.data);
      
      // 检查是否应该本地处理错误（不显示全局错误消息）
      const handleErrorLocally = error.config?.headers?.['x-handle-error-locally'] === 'true';
      
      // 检查错误类型，只对特定的认证相关错误进行退出处理
      const errorDetail = error.response?.data?.detail || '';
      const errorCode = error.response?.headers?.['x-error-code'] || '';
      
      // 只有认证相关的500错误才需要退出登录
      const isAuthError = errorDetail.includes('认证') || 
                         errorDetail.includes('token') || 
                         errorDetail.includes('session') ||
                         errorDetail.includes('用户') ||
                         errorDetail.includes('登录') ||
                         errorDetail.includes('密码') ||
                         errorDetail.includes('令牌') ||
                         errorCode.includes('AUTH') ||
                         errorCode.includes('SESSION') ||
                         errorCode.includes('TOKEN') ||
                         errorCode.includes('USER');
      
      if (isAuthError && !window.location.pathname.includes('/login')) {
        // 清除token
        localStorage.removeItem('token');
        
        // 显示认证错误提示
        ElMessage.error('认证错误，请重新登录');
        
        // 跳转到登录页面
        router.push('/login');
      } else if (!handleErrorLocally) {
        // 只有在不需要本地处理错误的情况下，才显示全局错误消息
        ElMessage.error('服务器内部错误，请稍后重试或联系管理员');
      }
      
      return Promise.reject(error);
    }
    
    if (error.response?.status === 401) {
      const originalRequest = error.config;
      
      // 排除登录和刷新令牌请求
      if (originalRequest.url.includes('/login') || originalRequest.url.includes('/refresh-token')) {
        // 清除token并跳转到登录页
        localStorage.removeItem('token');
        // 直接跳转到登录页，让Login.vue组件处理错误显示
        router.push('/login');
        return Promise.reject(error);
      }
      
      // 检查错误详情，判断是令牌过期还是会话过期
      const errorDetail = error.response?.data?.detail || '';
      const errorCode = error.response?.headers?.['x-error-code'] || 'UNKNOWN_ERROR';
      
      if (errorDetail.includes('令牌已过期') || errorDetail.includes('会话已过期') || 
          errorCode.includes('SESSION') || errorCode.includes('EXPIRED')) {
        
        console.log(`检测到认证过期 [${errorCode}]:`, errorDetail);
        
        // 尝试刷新令牌
        try {
          const refreshResponse = await api.post('/refresh-token');
          const newToken = refreshResponse.data.access_token;
          
          // 更新本地存储的token
          localStorage.setItem('token', newToken);
          
          // 更新原请求的Authorization头
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          
          console.log('令牌刷新成功，重试原请求');
          
          // 重试原请求
          return api(originalRequest);
        } catch (refreshError: any) {
          // 刷新失败，记录错误信息到控制台
          const refreshErrorDetail = refreshError.response?.data?.detail || '令牌刷新失败';
          const refreshErrorCode = refreshError.response?.headers?.['x-error-code'] || 'REFRESH_FAILED';
          
          // 根据错误码记录不同的错误信息
          let errorMessage = '认证已过期，请重新登录';
          
          switch (refreshErrorCode) {
            case 'SESSION_NOT_FOUND':
              errorMessage = '会话不存在，可能已超时或用户已登出';
              break;
            case 'SESSION_INACTIVE':
              errorMessage = '会话已失效，用户可能已在其他设备登录';
              break;
            case 'SESSION_EXPIRED':
              errorMessage = '会话已过期，请重新登录';
              break;
            case 'USER_DISABLED':
              errorMessage = '您的账户已被禁用，请联系管理员';
              break;
            case 'USER_NOT_FOUND':
              errorMessage = '用户不存在，请联系管理员';
              break;
            case 'INVALID_USER_IDENTITY':
              errorMessage = '用户身份验证失败，请重新登录';
              break;
            default:
              errorMessage = refreshErrorDetail;
          }
          
          // 仅记录错误到控制台，避免与后端错误消息重复显示
          console.error('令牌刷新失败:', errorMessage, refreshErrorDetail);
          
          // 清除token并跳转到登录页
          localStorage.removeItem('token');
          router.push('/login');
          return Promise.reject(refreshError);
        }
      } else {
        // 其他401错误，显示详细的错误信息
        let errorMessage = '认证失败，请重新登录';
        
        switch (errorCode) {
          case 'USER_DISABLED':
            errorMessage = '您的账户已被禁用，请联系管理员';
            break;
          case 'USER_NOT_FOUND':
            errorMessage = '用户不存在，请联系管理员';
            break;
          default:
            errorMessage = errorDetail;
        }
        
        // 使用Element Plus消息组件显示错误信息
        ElMessage.error(errorMessage);
        
        localStorage.removeItem('token');
        router.push('/login');
        return Promise.reject(error);
      }
    }
    
    return Promise.reject(error);
  }
);

export default api;
export { getServerBaseURL };