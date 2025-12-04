import { RouteRecordRaw } from 'vue-router';

// 定义路由元数据类型
interface RouteMeta {
  requiresAuth?: boolean
  requiresGuest?: boolean
}

// 扩展路由记录类型
type CustomRouteRecordRaw = RouteRecordRaw & {
  meta?: RouteMeta
}

// 系统配置相关路由规则
export const systemConfigRoutes: CustomRouteRecordRaw[] = [
  {
    path: "/system/config",
    name: "SystemConfigManagement",
    component: () => import("../../components/menu-components/system/SystemConfigManagement.vue"),
    meta: {
      requiresAuth: true
    }
  }
  // 备份相关路由已移除，相关组件文件已被删除
];