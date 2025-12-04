// 菜单组件映射配置
import { defineAsyncComponent } from 'vue';

// 默认主页组件
const DefaultHome = defineAsyncComponent(() => import('./DefaultHome.vue'));

// 基础数据模块组件
const WarehouseConfig = defineAsyncComponent(() => import('./base/WarehouseConfig.vue'));
const BinManagement = defineAsyncComponent(() => import('./base/BinManagement.vue'));
const CustomerManagement = defineAsyncComponent(() => import('./base/CustomerManagement.vue'));
const SupplierManagement = defineAsyncComponent(() => import('./base/SupplierManagement.vue'));
const MajorManagement = defineAsyncComponent(() => import('./base/MajorManagement.vue'));
const EquipmentInfo = defineAsyncComponent(() => import('./base/EquipmentInfo.vue'));
const MaterialInfo = defineAsyncComponent(() => import('./base/MaterialInfo.vue'));

// 器材管理模块组件
const InventoryDetails = defineAsyncComponent(() => import('./material/InventoryDetails.vue'));
const InventoryTransactionQuery = defineAsyncComponent(() => import('./material/InventoryTransactionQuery.vue'));
const InboundManagement = defineAsyncComponent(() => import('./material/InboundManagement.vue'));
const OutboundManagement = defineAsyncComponent(() => import('./material/OutboundManagement.vue'));

// 账户管理模块组件
const PermissionManagement = defineAsyncComponent(() => import('./account/PermissionManagement.vue'));
const RoleManagement = defineAsyncComponent(() => import('./account/RoleManagement.vue'));
const UserManagement = defineAsyncComponent(() => import('./account/UserManagement.vue'));

// 系统设置模块组件
const DatabaseManagement = defineAsyncComponent(() => import('./system/DatabaseManagement.vue'));
const PersonalSettings = defineAsyncComponent(() => import('./system/PersonalSettings.vue'));
const MaterialCodeLevelConfig = defineAsyncComponent(() => import('./system/MaterialCodeLevelConfig.vue'));
const SystemConfigManagement = defineAsyncComponent(() => import('./system/SystemConfigManagement.vue'));

// 组件映射表
export const componentMap = {
  'default': DefaultHome,
  'home': DefaultHome, // 主页菜单
  // 基础数据
  '1-1': WarehouseConfig,
  '1-2': BinManagement,
  '1-3': CustomerManagement,
  '1-4': SupplierManagement,
  '1-5': MajorManagement,
  '1-6': EquipmentInfo,
  '1-7': MaterialInfo,
  // 器材管理
  '2-1': InboundManagement,
  '2-2': OutboundManagement,
  '2-3': InventoryDetails,
  '2-4': InventoryTransactionQuery,
  // 账户管理
  '3-1': PermissionManagement,
  '3-2': RoleManagement,
  '3-3': UserManagement,
  // 系统设置
  '4-1': DatabaseManagement,
  '4-2': PersonalSettings,
  '4-3': MaterialCodeLevelConfig,
  '4-4': SystemConfigManagement,
};

// 获取组件的函数
export const getComponent = (index: string) => {
  return componentMap[index as keyof typeof componentMap] || componentMap.default;
};