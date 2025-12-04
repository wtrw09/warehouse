/**
 * API服务统一导出文件
 * 按照菜单功能模块化组织API服务
 */

// 导出类型定义
export * from './types/index';

// 导出基础API配置
export { default as api } from './base';

// 导出认证相关API
export { authAPI } from './auth';

// 导出账户管理模块API
export { permissionAPI } from './account/permission';
export { roleAPI } from './account/role';
export { userAPI } from './account/user';

// 导出基础数据模块API
export { warehouseAPI } from './base/warehouse';
export { binApi } from './base/bin';
export { customerAPI } from './base/customer';
export { supplierAPI } from './base/supplier';
export { equipmentApi } from './base/equipment';
export { majorAPI } from './base/major';
export { subMajorAPI } from './base/sub_major';
export { materialAPI } from './base/material';



// 导出系统设置模块
export { systemAPI } from './system/system';
export { backupAPI } from './system/backup';
export { dashboardAPI } from './system/dashboard';
export { systemConfigRoutes } from './system/systemConfigRoutes';