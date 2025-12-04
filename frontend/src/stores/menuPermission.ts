import { ref, markRaw } from 'vue';
import {
  HomeFilled, Shop, UserFilled, ShoppingBag,
  Briefcase, Monitor, Setting, Document,
  Plus, Minus, List, Key, User, Avatar,
  Coin, Coordinate, ScaleToOriginal, Notebook, House
} from '@element-plus/icons-vue';

// 定义菜单项接口
export interface MenuItem {
  index: string;
  title: string;
  icon: any;
  permission: string;
  children?: MenuItem[];
}

// 定义菜单数据
export const menuData = ref<MenuItem[]>([
  {
    index: 'home',
    title: '主页',
    icon: markRaw(House),
    permission: 'AUTH-own', // 所有登录用户都可以访问
    children: []
  },
  {
    index: '1',
    title: '基础数据',
    icon: markRaw(HomeFilled),
    permission: 'BASE-read',
    children: [
      { index: '1-1', title: '仓库配置', icon: markRaw(Shop), permission: 'BASE-read' },
      { index: '1-2', title: '货位配置', icon: markRaw(ScaleToOriginal), permission: 'BASE-read' },
      { index: '1-3', title: '客户管理', icon: markRaw(UserFilled), permission: 'BASE-read' },
      { index: '1-4', title: '供应商管理', icon: markRaw(ShoppingBag), permission: 'BASE-read' },
      { index: '1-5', title: '专业信息', icon: markRaw(Document), permission: 'BASE-read' },
      { index: '1-6', title: '装备信息', icon: markRaw(Briefcase), permission: 'BASE-read' },
      { index: '1-7', title: '器材信息', icon: markRaw(Monitor), permission: 'BASE-read' }
    ]
  },
  {
      index: '2',
      title: '出入库管理',
      icon: markRaw(ScaleToOriginal),
      permission: 'STOCK-read',
      children: [
        { index: '2-1', title: '入库管理', icon: markRaw(Plus), permission: 'IO-edit' }, // 修正：入库需要编辑权限
        { index: '2-2', title: '出库管理', icon: markRaw(Minus), permission: 'IO-edit' }, // 修正：出库需要编辑权限
        { index: '2-3', title: '库存明细', icon: markRaw(List), permission: 'STOCK-read' },
        { index: '2-4', title: '库存变更流水', icon: markRaw(Notebook), permission: 'IO-read' }
      ]
    },
  {
    index: '3',
    title: '账户管理',
    icon: markRaw(User),
    permission: 'AUTH-read',
    children: [
      { index: '3-1', title: '权限管理', icon: markRaw(Key), permission: 'AUTH-read' },
      { index: '3-2', title: '角色管理', icon: markRaw(Avatar), permission: 'AUTH-read' },
      { index: '3-3', title: '用户管理', icon: markRaw(UserFilled), permission: 'AUTH-edit' }
    ]
  },
  {
    index: '4',
    title: '系统设置',
    icon: markRaw(Setting),
    permission: 'AUTH-own',
    children: [
      { index: '4-1', title: '数据库管理', icon: markRaw(Coin), permission: 'AUTH-edit' },
      { index: '4-2', title: '个人设置', icon: markRaw(Coordinate), permission: 'AUTH-own' },
      { index: '4-3', title: '器材编码设置', icon: markRaw(ScaleToOriginal), permission: 'BASE-edit' },
      { index: '4-4', title: '系统配置管理', icon: markRaw(Setting), permission: 'AUTH-edit' }
    ]
  }
]);

// 权限检查函数
export const hasPermission = (userPermissions: string[] | undefined, requiredPermission: string | undefined): boolean => {
  // 如果没有用户权限列表或没有指定所需权限，默认返回false
  if (!userPermissions || !Array.isArray(userPermissions) || !requiredPermission || typeof requiredPermission !== 'string') {
    console.debug('权限检查失败:', { userPermissions, requiredPermission });
    return false;
  }
  
  // 检查用户是否拥有指定权限
  const hasPerms = userPermissions.includes(requiredPermission);
  // console.debug(`权限检查: ${requiredPermission} -> ${hasPerms}`);
  return hasPerms;
};

// 获取所有菜单的权限列表
export const getAllPermissions = (): string[] => {
  const permissions = new Set<string>();
  
  const collectPermissions = (items: MenuItem[]) => {
    items.forEach(item => {
      permissions.add(item.permission);
      if (item.children && item.children.length > 0) {
        collectPermissions(item.children);
      }
    });
  };
  
  collectPermissions(menuData.value);
  return Array.from(permissions);
};

// 根据用户权限过滤菜单
export const getVisibleMenus = (userPermissions: string[] | undefined): MenuItem[] => {
  if (!userPermissions || !Array.isArray(userPermissions)) {
    console.warn('用户权限为空或格式不正确:', userPermissions);
    return [];
  }
  
  // 确保menuData.value存在且是数组
  if (!menuData.value || !Array.isArray(menuData.value)) {
    console.warn('菜单数据不存在或格式不正确:', menuData.value);
    return [];
  }
  
  const filterMenuItems = (items: MenuItem[]): MenuItem[] => {
    return items
      .filter(item => {
        // 确保item和item.permission存在
        if (!item || !item.permission) {
          console.warn('无效的菜单项:', item);
          return false;
        }
        return hasPermission(userPermissions, item.permission);
      })
      .map(item => {
        const filteredItem = { ...item };
        
        // 处理子菜单
        if (item.children && Array.isArray(item.children) && item.children.length > 0) {
          filteredItem.children = filterMenuItems(item.children);
        } else {
          filteredItem.children = [];
        }
        
        return filteredItem;
      })
      // 修正过滤逻辑：只有父菜单本身无权限且无可见子菜单时才过滤掉
      .filter(item => {
        // 如果有子菜单，则检查是否有可见的子菜单
        if (item.children && item.children.length > 0) {
          return true; // 有可见子菜单就保留
        }
        // 没有子菜单的项目（叶子节点），只要用户有权限就保留
        return hasPermission(userPermissions, item.permission);
      });
  };
  
  const result = filterMenuItems(menuData.value);
  return result;
};

// 获取指定索引的菜单项
export const getMenuItemByIndex = (index: string): MenuItem | undefined => {
  if (!index || typeof index !== 'string') {
    console.warn('无效的菜单索引:', index);
    return undefined;
  }
  
  if (!menuData.value || !Array.isArray(menuData.value)) {
    console.warn('菜单数据不存在:', menuData.value);
    return undefined;
  }
  
  let foundItem: MenuItem | undefined;
  
  const searchMenuItem = (items: MenuItem[]): boolean => {
    for (const item of items) {
      if (!item) continue;
      
      if (item.index === index) {
        foundItem = item;
        return true;
      }
      
      if (item.children && Array.isArray(item.children) && item.children.length > 0) {
        if (searchMenuItem(item.children)) {
          return true;
        }
      }
    }
    return false;
  };
  
  searchMenuItem(menuData.value);
  
  if (!foundItem) {
    console.warn(`未找到索引为 '${index}' 的菜单项`);
  }
  
  return foundItem;
};

// 验证用户权限和菜单数据一致性
export const validateUserPermissions = (userPermissions: string[]): {
  validPermissions: string[];
  invalidPermissions: string[];
  missingPermissions: string[];
} => {
  const allMenuPermissions = getAllPermissions();
  const validPermissions: string[] = [];
  const invalidPermissions: string[] = [];
  
  // 检查用户权限的有效性
  userPermissions.forEach(perm => {
    if (allMenuPermissions.includes(perm)) {
      validPermissions.push(perm);
    } else {
      invalidPermissions.push(perm);
    }
  });
  
  // 找出缺失的权限（菜单中定义但用户没有的）
  const missingPermissions = allMenuPermissions.filter(perm => !userPermissions.includes(perm));
  
  return {
    validPermissions,
    invalidPermissions,
    missingPermissions
  };
};
