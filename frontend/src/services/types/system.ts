/**
 * 系统配置相关类型定义
 */

/**
 * 系统配置项响应类型
 */
export interface SystemConfigResponse {
  /** 配置键 */
  config_key: string;
  /** 配置值 */
  config_value: string;
  /** 配置类型 (string, int, bool) */
  config_type: string;
  /** 配置描述 */
  description?: string;
  /** 是否受保护 */
  is_protected?: boolean;
  /** 创建时间 */
  created_at?: string;
  /** 更新时间 */
  updated_at?: string;
}

/**
 * 系统状态响应类型
 */
export interface SystemStatusResponse {
  /** 系统是否已初始化 */
  initialized: boolean;
  /** 初始化时间 */
  init_time?: string;
  /** 初始化版本号 */
  init_version?: string;
}

/**
 * 系统配置列表响应类型
 */
export interface SystemConfigListResponse {
  /** 配置列表 */
  configs: SystemConfigResponse[];
  /** 配置总数 */
  total: number;
}

/**
 * 系统配置更新类型
 */
export interface SystemConfigUpdate {
  /** 配置键 */
  config_key: string;
  /** 配置值 */
  config_value: string;
}

/**
 * 系统初始化请求类型
 */
export interface SystemInitializeRequest {
  /** 初始化版本 */
  version?: string;
  /** 初始化备注 */
  remark?: string;
}

/**
 * 系统配置批量更新类型
 */
export interface SystemConfigBatchUpdate {
  /** 配置更新列表 */
  configs: SystemConfigUpdate[];
}

/**
 * 系统配置API响应类型
 */
export interface SystemConfigApiResponse<T = any> {
  /** 状态码 */
  code: number;
  /** 消息 */
  message: string;
  /** 数据 */
  data?: T;
}

/**
 * 系统配置错误响应类型
 */
export interface SystemConfigErrorResponse {
  /** 错误详情 */
  detail: string;
  /** 错误码 */
  code?: number;
  /** 错误类型 */
  type?: string;
}

/**
 * 备份创建请求类型
 */
export interface BackupCreateRequest {
  /** 备份描述 */
  description: string;
}

/**
 * 备份文件信息类型
 */
export interface BackupFileInfo {
  /** 文件名 */
  filename: string;
  /** 文件路径 */
  path: string;
  /** 备份类型 */
  type: string;
  /** 时间戳 */
  timestamp: string;
  /** 文件大小 */
  size: string;
  /** 完整性验证 */
  integrity: boolean;
  /** 备份描述 */
  description: string;
}

/**
 * 备份列表响应类型
 */
export interface BackupListResponse {
  /** 备份列表 */
  backups: BackupFileInfo[];
  /** 总数 */
  total_count: number;
}

/**
 * 备份恢复状态类型
 */
export interface BackupRecoveryStatus {
  /** 状态 */
  status: 'in_progress' | 'completed' | 'failed' | 'cancelled';
  /** 备份文件 */
  backup_file?: string;
  /** 备份路径 */
  backup_path?: string;
  /** 开始时间 */
  started_at?: string;
  /** 进程ID */
  pid?: number;
  /** 步骤状态 */
  steps?: {
    stopping_services: boolean;
    backing_up_current: boolean;
    restoring_from_backup: boolean;
    validating_integrity: boolean;
    starting_services: boolean;
    cleaning_up: boolean;
  };
  /** 错误信息 */
  error?: string;
  /** 进度百分比 */
  progress?: number;
}