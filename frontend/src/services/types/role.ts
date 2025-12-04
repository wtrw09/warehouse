// 角色相关类型
export interface RoleResponse {
  id: number;
  name: string;
  description: string;
}

export interface RoleWithPermissions {
  id: number;
  name: string;
  description: string;
  create_time: string;
  update_time: string;
  is_delete: boolean;
  permissions: string[];
}

export interface RoleCreate {
  name: string;
  description: string;
  permissions: string[];
}

export interface RoleUpdate {
  name: string;
  description: string;
}

export interface UpdateRolePermissions {
  permission_ids: string[];
}

// 注意：Permission 和 UserInfo 类型已在专门的类型文件中定义
// Permission -> @/services/types/permission
// UserInfo -> @/services/types/auth
// 为了避免类型冲突，这里不再重复定义

// 角色表单类型
export interface RoleForm {
  name: string;
  description: string;
  permissions: string[];
}