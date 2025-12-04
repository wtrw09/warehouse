import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import Login from '../components/Login.vue';
import Home from '../components/Home.vue';
import { systemConfigRoutes } from '../services/system/systemConfigRoutes';

// 定义路由元数据类型
interface RouteMeta {
  requiresAuth?: boolean
  requiresGuest?: boolean
}

// 扩展路由记录类型
type CustomRouteRecordRaw = RouteRecordRaw & {
  meta?: RouteMeta
}

// 路由规则
const routes: CustomRouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      requiresGuest: true
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../components/Register.vue'),
    meta: {
      requiresGuest: true
    }
  },
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/error-file-download',
    name: 'ErrorFileDownload',
    component: () => import('../components/common/import/ErrorFileDownload.vue'),
    meta: {
      requiresAuth: true
    }
  },
  {
      path: "/inventory-details",
      name: "InventoryDetails",
      component: () => import("../components/menu-components/material/InventoryDetails.vue"),
      meta: {
        requiresAuth: true
      }
    },
  {
    path: "/material/inbound-orders",
    name: "InboundOrders",
    component: () => import("../components/menu-components/material/InboundOrders.vue"),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: "/material/inbound-order/edit/:id?",
    name: "InboundOrderEdit",
    component: () => import("../components/menu-components/material/InboundOrderEdit.vue"),
    meta: {
      requiresAuth: true
    }
  },
  {
    path: "/material/outbound-orders",
    name: "OutboundOrders",
    component: () => import("../components/menu-components/material/OutboundOrders.vue"),
    meta: {
      requiresAuth: true
    }
  },
  
  // 系统配置相关路由
  ...systemConfigRoutes,

  // 重定向到首页
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory('/'),
  routes
});

// 路由守卫 - 检查是否需要登录
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token');
  
  // 如果访问需要登录的页面但没有token，则重定向到登录页
  if (to.meta?.requiresAuth && !token) {
    next('/login');
  }
  // 如果已登录但尝试访问登录页，则重定向到首页
  else if (to.meta?.requiresGuest && token) {
    next('/');
  }
  else {
    next();
  }
});

export default router;