<template>
    <el-container class="home-container">
      <!-- 导航栏 - 使用Element Plus的ElHeader和ElContainer -->
      <el-header class="navbar">
        <div class="navbar-left">
          <!-- 菜单折叠按钮 -->
          <el-button 
            class="collapse-btn"
            @click="toggleMenuCollapse"
            :icon="isMenuCollapsed ? Expand : Fold"
            text
            size="large"
          />
          <div class="navbar-brand">
            <SvgIcon :src="logoIcon" width="24px" height="24px" />
            <span style="margin-left: 8px;">仓库管理系统</span>
          </div>
        </div>
        <nav class="navbar-nav">
          <el-dropdown v-if="currentUser" placement="bottom-end">
            <span class="el-dropdown-link">
              <el-avatar :size="32" :src="currentUser.avatar || defaultAvatar" style="margin-right: 8px;">
                {{ currentUser.username.slice(0, 2) }}
              </el-avatar>
              <span>{{ currentUser.username }} ({{ currentUser.roleName }})</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><ArrowRight /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </nav>
      </el-header>
      <el-container class="main-content">
        <el-aside :width="isMenuCollapsed ? '64px' : '180px'" class="aside" :class="{ 'collapsed': isMenuCollapsed }">
          <el-menu height="100%"
            v-model:default-active="activeMenuIndex"
            :default-openeds="['2']"
            ref="menuRef"
            class="el-menu-vertical-demo"
            :collapse="isMenuCollapsed"
            @select="handleMenuClick"
          >
            <template v-for="menu in visibleMenus" :key="menu.index">
              <el-sub-menu v-if="menu && menu.children && Array.isArray(menu.children) && menu.children.length > 0" :index="menu.index">
                <template #title>
                  <el-icon><component :is="menu.icon" /></el-icon>
                  <span>{{ menu.title }}</span>
                </template>
                <!-- 移除重复的权限检查，信任getVisibleMenus的过滤结果 -->
                <el-menu-item
                  v-for="subMenu in menu.children"
                  :key="subMenu?.index || 'default'"
                  :index="subMenu?.index || ''"
                >
                  <el-icon><component :is="subMenu.icon" /></el-icon>
                  <span>{{ subMenu.title }}</span>
                </el-menu-item>
              </el-sub-menu>
              <!-- 叶子菜单项，也移除重复的权限检查 -->
              <el-menu-item v-else-if="menu" :index="menu.index">
                <el-icon><component :is="menu.icon" /></el-icon>
                <span>{{ menu.title }}</span>
              </el-menu-item>
            </template>
          </el-menu>
        </el-aside>
        <el-main class="main-area">
          <component :is="currentComponent" />
        </el-main>
      </el-container>
    </el-container>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, provide, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { ArrowRight, Box, ArrowDown, Expand, Fold, House } from '@element-plus/icons-vue'
import SvgIcon from './SvgIcon.vue';
import { authAPI } from '../services/api';
import { useRouter } from 'vue-router';
import { useMenuStore } from '../stores/menu';
import { useRoute } from 'vue-router';
import { useUserStore } from '../stores/user';
import { menuData, getVisibleMenus } from '../stores/menuPermission';
import { getComponent } from './menu-components/index';
import logoIcon from '../assets/图标.svg';

const router = useRouter();
const currentUser = ref(null);
const defaultAvatar = 'https://cube.elemecdn.com/0/88/03b0d39583f48206768a7534e55bcpng.png';
const leftWidth = ref(200); // 定义左侧列宽
const activeMenuIndex = ref('default'); // 当前激活的菜单索引，默认显示主页
const isMenuCollapsed = ref(false); // 菜单折叠状态

// 服务器状态检测相关
const serverStatusTimer = ref(null);
const serverStatusCheckInterval = 30000; // 30秒检查一次

// 使用菜单store
const menuStore = useMenuStore();
const menuRef = ref();

// 计算属性：获取当前激活的组件
const currentComponent = computed(() => {
  return getComponent(activeMenuIndex.value);
});

// 向子组件提供用户信息
provide('currentUser', currentUser);

// 计算属性：过滤显示的顶级菜单项
const visibleMenus = computed(() => {
  console.log('当前用户权限:', currentUser.value?.permissions);
  console.log('当前用户信息:', currentUser.value);
  
  // 如果用户未登录或没有权限信息，返回空数组
  if (!currentUser.value) {
    console.log('用户未登录');
    return [];
  }
  
  // 检查权限信息是否存在且为数组
  if (!currentUser.value.permissions || !Array.isArray(currentUser.value.permissions)) {
    console.log('用户权限信息不存在或格式不正确');
    console.log('权限信息类型:', typeof currentUser.value.permissions);
    console.log('权限信息值:', currentUser.value.permissions);
    return [];
  }
  
  // 过滤菜单项，只显示用户有权限访问的菜单
  const filteredMenus = getVisibleMenus(currentUser.value.permissions);
  
  console.log('过滤后的菜单:', filteredMenus);
  return filteredMenus;
});

// 检查服务器状态
const checkServerStatus = async () => {
  try {
    // 尝试调用一个简单的API来检查服务器状态
    await authAPI.getCurrentUser();
    // 如果调用成功，说明服务器正常
    return true;
  } catch (error) {
    // 检查是否是网络连接错误或服务器不可用错误
    if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK' || 
        error.message?.includes('Network Error') || error.response?.status >= 500) {
      console.error('服务器连接异常:', error.message);
      
      // 清除token
      localStorage.removeItem('token');
      
      // 显示服务器异常提示
      ElMessage.error('服务器连接异常，请检查服务器状态后重新登录');
      
      // 停止服务器状态检测
      stopServerStatusCheck();
      
      // 跳转到登录页面
      router.push('/login');
      return false;
    }
    
    // 其他错误（如401认证错误）不处理，由响应拦截器处理
    return true;
  }
};

// 启动服务器状态检测
const startServerStatusCheck = () => {
  // 先清除已有的定时器
  if (serverStatusTimer.value) {
    clearInterval(serverStatusTimer.value);
  }
  
  // 设置定时器定期检查服务器状态
  serverStatusTimer.value = setInterval(async () => {
    await checkServerStatus();
  }, serverStatusCheckInterval);
};

// 停止服务器状态检测
const stopServerStatusCheck = () => {
  if (serverStatusTimer.value) {
    clearInterval(serverStatusTimer.value);
    serverStatusTimer.value = null;
  }
};

// 检查是否已登录，如果未登录则自动跳转到登录页面
const checkLoginStatus = async () => {
  try {
    // 尝试获取用户信息，如果成功则说明已登录
    const userData = await authAPI.getCurrentUser();
    currentUser.value = userData;
    
    // 保存用户数据到localStorage，供其他组件使用
    localStorage.setItem('userData', JSON.stringify(userData));
    localStorage.setItem('username', userData.username);
    
    // 设置用户信息到store
    menuStore.setCurrentUser(userData);
    // 设置用户权限数据到userStore
    const userStore = useUserStore();
    userStore.setUser(userData);
    // 初始化菜单状态
    menuStore.initializeMenuState();
    // 菜单展开状态已通过default-openeds属性自动处理
    // console.log('菜单状态初始化完成，默认展开菜单:', menuStore.defaultOpenKeys);
    // console.log('用户权限信息:', userData.permissions);
    
    // 登录成功后启动服务器状态检测
    startServerStatusCheck();
  } catch (err) {
    // console.error('获取用户信息失败:', err);
    // 如果未登录或token无效，重定向到登录页面
    router.push('/login');
  }
};

// 用户登出
const handleLogout = () => {
  try {
    // 停止服务器状态检测
    stopServerStatusCheck();
    
    authAPI.logout();
    currentUser.value = null;
    menuStore.setCurrentUser(null);
    
    // 清除localStorage中的用户数据
    localStorage.removeItem('userData');
    localStorage.removeItem('username');
    
    ElMessage.success('已成功退出登录');
    router.push('/login');
  } catch (error) {
    ElMessage.error('退出登录失败');
  }
};

// 处理菜单折叠/展开
const toggleMenuCollapse = () => {
  isMenuCollapsed.value = !isMenuCollapsed.value;
};

// 处理菜单点击
const handleMenuClick = (index) => {
  console.log('点击菜单项:', index);
  
  // 处理二级菜单（包含'-'的索引）或一级叶子菜单（如'home'）
  if (index.includes('-') || index === 'home') {
    activeMenuIndex.value = index;
  } 
};

// 组件挂载时初始化
onMounted(() => {
  // 调用登录状态检查逻辑
  checkLoginStatus();
  // 强制重置为显示主页，确保刷新后总是显示主页
  activeMenuIndex.value = 'default';
});

// 组件卸载时清理
onUnmounted(() => {
  // 停止服务器状态检测
  stopServerStatusCheck();
});

const route = useRoute();

// 监听路由参数变化
import { watch } from 'vue';
watch(() => route.query.menu, (newMenuIndex) => {
  if (newMenuIndex) {
    activeMenuIndex.value = newMenuIndex;
    // 展开对应的父级菜单
    const parentIndex = newMenuIndex.split('-')[0];
    menuStore.openMenu(parentIndex);
    } else {
    // 如果没有路由参数，确保显示主页
    activeMenuIndex.value = 'default';
    // console.log('无路由参数，显示主页');
  }
}, { immediate: true });
</script>

<style scoped>
.home-container {
  height: 100vh; /* 关键：整个布局占满视口 */
  display: flex;
  flex-direction: column; /* 垂直排列 header 和 content-container */
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
  margin: 0;
  padding: 0;
  border: none;
}

/* 导航栏样式 - 控制导航栏的高度和与下方内容的间距 */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 1rem;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  height: 50px !important;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  margin: 0;
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 菜单折叠按钮样式 */
.collapse-btn {
  color: #4a5568;
  font-size: 18px;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.collapse-btn:hover {
  background-color: #f7fafc;
  color: #667eea;
}

.navbar-brand {
  display: flex;
  align-items: center;
  font-size: 1.5rem;
  font-weight: 700;
  color: #4a5568;
  transition: all 0.3s ease;
}

.navbar-brand:hover {
  color: #667eea;
  transform: translateY(-1px);
}

.navbar-brand .el-icon {
  color: #667eea;
  font-size: 1.6rem;
  transition: all 0.3s ease;
}

.navbar-brand:hover .el-icon {
  transform: rotate(15deg);
}

.navbar-nav {
  display: flex;
  align-items: center;
  height: 100%;
}

/* 下拉菜单链接样式 - 垂直居中 */
.el-dropdown-link {
  display: flex;
  align-items: center;
  height: 100%;
  cursor: pointer;
  padding: 0 1rem;
  border-radius: 8px;
  transition: all 0.3s ease;
  color: #4a5568;
}

.el-dropdown-link:hover {
  background-color: #f7fafc;
  color: #667eea;
}

.el-dropdown-link .el-icon {
  margin-left: 0.5rem;
  transition: transform 0.3s ease;
}

.el-dropdown-link:hover .el-icon {
  transform: rotate(180deg);
}

.el-dropdown-link .el-avatar {
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.el-dropdown-link:hover .el-avatar {
  border-color: #667eea;
  transform: scale(1.1);
}

/* 下拉菜单样式 */
:deep(.el-dropdown-menu) {
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  border: none;
  overflow: hidden;
}

:deep(.el-dropdown-item) {
  padding: 0.75rem 1.5rem;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

:deep(.el-dropdown-item:hover) {
  background-color: #f7fafc;
  color: #667eea;
}

:deep(.el-dropdown-item .el-icon) {
  font-size: 0.9rem;
}

/* 主内容样式 - 控制侧边栏和主内容区之间的间距 */
.main-content {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 0;
  margin: 0;
  padding: 0;
}

/* 侧边栏样式 - 控制侧边栏内边距 */
.aside {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.05);
  height: 100%;
  padding: 0;
  box-sizing: border-box;
  overflow: auto;
  transition: all 0.3s ease;
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  margin: 0;
}

/* 菜单折叠状态 - 控制折叠时的内边距 */
.aside.collapsed {
  padding: 0.1rem 0.1rem;  /* 【间距调整8】折叠状态下的侧边栏内边距 */
}

/* 折叠状态下的菜单样式 */
.aside.collapsed .el-menu {
  border-right: none;
}

/* 折叠状态下隐藏文字 */
.aside.collapsed :deep(.el-menu--collapse .el-sub-menu__title span),
.aside.collapsed :deep(.el-menu--collapse .el-menu-item span) {
  display: none;
}

/* 折叠状态下的图标居中 */
.aside.collapsed :deep(.el-menu--collapse .el-sub-menu__title),
.aside.collapsed :deep(.el-menu--collapse .el-menu-item) {
  justify-content: center;
  padding: 0 20px;
}

.aside::-webkit-scrollbar {
  width: 6px;
}

.aside::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.aside::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.aside::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

/* 主内容区样式 - 控制主内容区内边距 */
.main-area {
  width: 100%;
  background: rgba(255, 255, 255, 0.95);
  height: 100%;
  padding: 0;
  box-sizing: border-box;
  overflow: auto;
  transition: all 0.3s ease;
  margin: 0;
  display: flex;
  flex-direction: column;
}

.main-area::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.main-area::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.main-area::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 4px;
}

.main-area::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navbar {
    padding: 0 0.75rem;
  }
  
  .navbar-brand {
    font-size: 1.3rem;
  }
  
  .aside {
    padding: 0.5rem; /* 减少移动端内边距 */
  }
  
  .aside.collapsed {
    padding: 0.5rem 0.25rem;
  }
  
  .main-area {
    padding: 0.5rem; /* 减少移动端内边距 */
  }
}

@media (max-width: 480px) {
  .navbar {
    padding: 0 0.5rem;
  }
  
  .navbar-brand {
    font-size: 1.2rem;
  }
  
  .el-dropdown-link {
    padding: 0 0.25rem; /* 减小移动端内边距 */
  }
  
  .el-dropdown-link span:not(:first-child) {
    display: none;
  }
  
  .main-area {
    padding: 0.5rem; /* 减小移动端内边距 */
  }
}
</style>
