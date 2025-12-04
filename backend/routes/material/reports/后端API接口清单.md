# 仓库管理系统 - 后端API接口清单

## 接口基础信息
- **服务器地址**: `http://localhost:8000`
- **认证方式**: OAuth2 Bearer Token (JWT)
- **内容类型**: `application/json` 或 `application/x-www-form-urlencoded`

---

## 1. 用户认证模块 (注册与认证)

### 1.1 用户注册
- **接口**: `POST /register`
- **描述**: 用户注册接口（目前仅支持管理员注册）
- **请求类型**: `application/x-www-form-urlencoded`
- **请求参数**:
  ```
  username: string (必填) - 用户名
  password: string (必填) - 密码
  invitation_code: string (可选) - 邀请码（管理员注册必需）
  ```
- **响应格式**: `UserResponse`
- **权限要求**: 无（公开接口）

### 1.2 用户登录
- **接口**: `POST /login`
- **描述**: OAuth2 密码模式登录接口
- **请求类型**: `application/x-www-form-urlencoded`
- **请求参数**:
  ```
  username: string (必填) - 用户名
  password: string (必填) - 密码
  ```
- **响应格式**:
  ```json
  {
    "access_token": "string",
    "token_type": "bearer"
  }
  ```
- **权限要求**: 无（公开接口）

---

## 2. 用户管理模块

### 2.1 获取当前用户信息
- **接口**: `GET /users/me`
- **描述**: 获取当前登录用户的完整信息
- **请求参数**: 无
- **响应格式**: `UserResponse`
- **权限要求**: `AUTH-own` (本人信息修改权限)

### 2.2 获取用户列表（分页）
- **接口**: `GET /users`
- **描述**: 获取用户列表，支持分页、搜索、排序
- **请求参数**:
  ```
  page: int = 1 (页码，默认1)
  page_size: int = 10 (每页数量，默认10)
  search: string = null (搜索关键词，可选)
  sort_field: string = "id" (排序字段: id/username/real_name/create_time/update_time/last_login)
  sort_asc: bool = true (排序顺序，true为升序)
  role_id: int = null (按角色ID筛选，可选)
  is_active: bool = null (按激活状态筛选，可选)
  ```
- **响应格式**: `UserPaginationResult`
- **权限要求**: `AUTH-read`

### 2.3 获取用户详情
- **接口**: `GET /users/{user_id}`
- **描述**: 获取指定用户的详细信息
- **请求参数**:
  ```
  user_id: int (路径参数) - 用户ID
  ```
- **响应格式**: `UserDetail`
- **权限要求**: `AUTH-read`

### 2.4 创建用户
- **接口**: `POST /users/new`
- **描述**: 创建新用户
- **请求类型**: `application/json`
- **请求体**: `UserCreate`
  ```json
  {
    "username": "string",
    "password": "string",
    "email": "user@example.com",
    "phone": "13800138000",
    "real_name": "string",
    "avatar": "string",
    "role_id": 1,
    "is_active": true
  }
  ```
- **响应格式**: `UserResponse`
- **权限要求**: `AUTH-edit`

### 2.5 更新用户信息
- **接口**: `PUT /users/update/{user_id}`
- **描述**: 更新用户基本信息
- **请求参数**:
  ```
  user_id: int (路径参数) - 用户ID
  ```
- **请求体**: `UserUpdate`
  ```json
  {
    "username": "string",
    "email": "user@example.com",
    "phone": "13800138000",
    "real_name": "string",
    "avatar": "string",
    "role_id": 1,
    "is_active": true
  }
  ```
- **响应格式**: `UserResponse`
- **权限要求**: `AUTH-edit` 或 `AUTH-own`（仅限更新自己）

### 2.6 用户角色分配
- **接口**: `PUT /users/{user_id}/role`
- **描述**: 为用户分配角色
- **请求参数**:
  ```
  user_id: int (路径参数) - 用户ID
  ```
- **请求体**: `UserRoleAssign`
  ```json
  {
    "role_id": 1
  }
  ```
- **响应格式**: `UserResponse`
- **权限要求**: `AUTH-edit`

### 2.7 用户修改密码（自己）
- **接口**: `PUT /users/me/password`
- **描述**: 用户修改自己的密码
- **请求体**: `UserPasswordUpdate`
  ```json
  {
    "old_password": "string",
    "new_password": "string"
  }
  ```
- **响应格式**: 标准成功响应
- **权限要求**: `AUTH-own`

### 2.8 管理员重置用户密码
- **接口**: `PUT /users/{user_id}/password/reset`
- **描述**: 管理员重置指定用户的密码
- **请求参数**:
  ```
  user_id: int (路径参数) - 用户ID
  ```
- **请求体**: `UserPasswordReset`
  ```json
  {
    "new_password": "string"
  }
  ```
- **响应格式**: 标准成功响应
- **权限要求**: `AUTH-edit`

### 2.9 激活/禁用用户
- **接口**: `PUT /users/{user_id}/status`
- **描述**: 激活或禁用用户账户
- **请求参数**:
  ```
  user_id: int (路径参数) - 用户ID
  ```
- **请求体**: `UserStatusUpdate`
  ```json
  {
    "is_active": true
  }
  ```
- **响应格式**: `UserResponse`
- **权限要求**: `AUTH-edit`

### 2.10 删除用户
- **接口**: `DELETE /users/delete/{user_id}`
- **描述**: 软删除用户（标记为已删除）
- **请求参数**:
  ```
  user_id: int (路径参数) - 用户ID
  ```
- **响应格式**: `UserResponse`
- **权限要求**: `AUTH-edit`

### 2.11 批量用户角色分配
- **接口**: `PUT /users/batch/role`
- **描述**: 批量为多个用户分配角色
- **请求体**: `BatchUserRoleAssign`
  ```json
  {
    "user_ids": [1, 2, 3],
    "role_id": 1
  }
  ```
- **响应格式**: `BatchOperationResult`
- **权限要求**: `AUTH-edit`

### 2.12 批量用户状态更新
- **接口**: `PUT /users/batch/status`
- **描述**: 批量更新用户激活状态
- **请求体**: `BatchUserStatusUpdate`
  ```json
  {
    "user_ids": [1, 2, 3],
    "is_active": true
  }
  ```
- **响应格式**: `BatchOperationResult`
- **权限要求**: `AUTH-edit`

### 2.13 用户统计信息
- **接口**: `GET /users/statistics`
- **描述**: 获取用户统计信息
- **请求参数**: 无
- **响应格式**: `UserStatistics`
- **权限要求**: `AUTH-read`

---

## 3. 角色管理模块

### 3.1 获取角色列表（分页）
- **接口**: `GET /roles`
- **描述**: 获取角色信息（支持分页、搜索、排序）
- **请求参数**:
  ```
  page: int = 1 (页码，默认1)
  page_size: int = 10 (每页数量，默认10)
  search: string = null (搜索关键词，可选)
  sort_field: string = "id" (排序字段: id/name/create_time/update_time)
  sort_asc: bool = true (排序顺序，true为升序)
  ```
- **响应格式**: `PaginationResult`
- **权限要求**: `AUTH-read`

### 3.2 获取单个角色详情
- **接口**: `GET /roles/{role_id}`
- **描述**: 获取指定角色的详细信息，包含权限列表
- **请求参数**:
  ```
  role_id: int (路径参数) - 角色ID
  ```
- **响应格式**: `RoleWithPermissions`
- **权限要求**: `AUTH-read`

### 3.3 创建新角色
- **接口**: `POST /roles/new`
- **描述**: 创建新角色并分配权限
- **请求类型**: `application/json`
- **请求体**: `RoleCreate`
  ```json
  {
    "name": "string",
    "description": "string",
    "permissions": ["AUTH-read", "AUTH-edit"]
  }
  ```
- **响应格式**: `RoleResponse`
- **权限要求**: `AUTH-edit`

### 3.4 更新角色信息
- **接口**: `PUT /roles/update/{role_id}`
- **描述**: 更新角色的基本信息（名称、描述）
- **请求参数**:
  ```
  role_id: int (路径参数) - 角色ID
  ```
- **请求体**: `RoleUpdate`
  ```json
  {
    "name": "string",
    "description": "string"
  }
  ```
- **响应格式**: `RoleResponse`
- **权限要求**: `AUTH-edit`

### 3.5 更新角色权限
- **接口**: `PUT /roles/{role_id}/permissions`
- **描述**: 更新指定角色的权限列表
- **请求参数**:
  ```
  role_id: int (路径参数) - 角色ID
  ```
- **请求体**: `UpdateRolePermissions`
  ```json
  {
    "permission_ids": ["AUTH-read", "AUTH-edit", "BASE-read"]
  }
  ```
- **响应格式**: `RoleWithPermissions`
- **权限要求**: `AUTH-edit`

### 3.6 删除角色
- **接口**: `DELETE /roles/delete/{role_id}`
- **描述**: 软删除指定角色（如果角色下有用户则无法删除）
- **请求参数**:
  ```
  role_id: int (路径参数) - 角色ID
  ```
- **响应格式**: `RoleResponse`
- **权限要求**: `AUTH-edit`

---

## 4. 权限管理模块

### 4.1 获取所有权限列表
- **接口**: `GET /permissions`
- **描述**: 获取系统中所有可用的权限信息
- **请求参数**: 无
- **响应格式**: `List[Permission]`
- **权限要求**: `AUTH-read`

---

## 5. 数据模型说明

### UserResponse
```json
{
  "id": 1,
  "username": "string",
  "email": "user@example.com",
  "phone": "13800138000",
  "real_name": "string",
  "avatar": "string",
  "role_id": 1,
  "roleName": "string",
  "permissions": ["AUTH-read", "AUTH-edit"],
  "is_active": true,
  "last_login": "2024-01-01T00:00:00",
  "create_time": "2024-01-01T00:00:00",
  "update_time": "2024-01-01T00:00:00"
}
```

### UserDetail
```json
{
  "id": 1,
  "username": "string",
  "email": "user@example.com",
  "phone": "13800138000",
  "real_name": "string",
  "avatar": "string",
  "role_id": 1,
  "roleName": "string",
  "permissions": ["AUTH-read", "AUTH-edit"],
  "is_active": true,
  "last_login": "2024-01-01T00:00:00",
  "create_time": "2024-01-01T00:00:00",
  "update_time": "2024-01-01T00:00:00",
  "email_masked": "u***@example.com",
  "phone_masked": "138****5678"
}
```

### UserPaginationResult
```json
{
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10,
  "data": []
}
```

### UserStatistics
```json
{
  "total_users": 100,
  "active_users": 85,
  "inactive_users": 15,
  "users_by_role": [
    {
      "role_name": "管理员",
      "count": 5
    },
    {
      "role_name": "普通用户",
      "count": 95
    }
  ],
  "recent_registrations": 10,
  "recent_logins": 45
}
```

### BatchOperationResult
```json
{
  "success_count": 8,
  "failed_count": 2,
  "failed_users": [3, 7],
  "message": "批量操作完成，8个成功，2个失败"
}
```

### RoleResponse
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "create_time": "2024-01-01T00:00:00",
  "update_time": "2024-01-01T00:00:00"
}
```

### RoleWithPermissions
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "create_time": "2024-01-01T00:00:00",
  "update_time": "2024-01-01T00:00:00",
  "is_delete": false,
  "permissions": ["AUTH-read", "AUTH-edit"]
}
```

### PaginationResult
```json
{
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10,
  "data": []
}
```

### Permission
```json
{
  "id": "AUTH-read",
  "description": "用户/角色/权限读取",
  "create_time": "2024-01-01T00:00:00",
  "update_time": "2024-01-01T00:00:00",
  "is_delete": false
}
```

---

## 6. 权限说明

系统中定义的权限类型：

| 权限ID | 权限名称 | 描述 |
|--------|----------|------|
| `AUTH-read` | 用户/角色/权限读取 | 可以查看用户、角色、权限信息 |
| `AUTH-edit` | 用户/角色/权限修改 | 可以修改用户、角色、权限信息 |
| `AUTH-own` | 本人信息修改 | 可以修改自己的信息 |
| `BASE-read` | 仓库信息读取 | 可以读取基础数据信息 |
| `BASE-edit` | 仓库信息修改 | 可以修改基础数据信息 |
| `IO-read` | 出入库数据读取 | 可以读取出入库数据 |
| `IO-edit` | 出入库数据修改 | 可以修改出入库数据 |
| `STOCK-read` | 库存读取 | 可以读取库存信息 |

---

## 7. 错误响应格式

所有接口在出错时返回标准的HTTP错误响应：

```json
{
  "detail": "错误描述信息"
}
```

常见错误码：
- `400` - 请求参数错误
- `401` - 未授权（登录失效或未登录）
- `403` - 权限不足
- `404` - 资源不存在
- `500` - 服务器内部错误

---

## 8. 前端调用示例

### 8.1 登录获取Token
```javascript
const loginResponse = await fetch('http://localhost:8000/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  },
  body: new URLSearchParams({
    username: 'admin',
    password: 'password'
  })
});
const loginData = await loginResponse.json();
const token = loginData.access_token;
```

### 8.2 使用Token调用受保护接口
```javascript
const response = await fetch('http://localhost:8000/users/me', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
const userData = await response.json();
```

### 8.3 创建角色示例
```javascript
const createRoleResponse = await fetch('http://localhost:8000/roles/new', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: '测试角色',
    description: '测试角色描述',
    permissions: ['AUTH-read', 'BASE-read']
  })
});
```

---

## 9. 注意事项

1. **认证机制**: 除登录和注册接口外，所有接口都需要在请求头中携带有效的Bearer Token
2. **权限检查**: 每个接口都有相应的权限要求，请确保当前用户具有所需权限
3. **分页查询**: 角色列表接口支持分页，建议在数据量大时使用分页功能
4. **搜索功能**: 角色列表支持多关键词搜索，可以搜索角色名称、权限等信息
5. **软删除**: 角色删除采用软删除机制，实际数据不会被物理删除
6. **时区**: 所有时间字段均为UTC时间格式

---

*最后更新时间: 2024年*