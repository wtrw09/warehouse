# 用户管理系统 - 前端API接口文档

> 专为前端开发者编写的后端API接口文档，包含完整的接口信息、请求参数、响应格式和调用示例。

## 🔧 基础配置

### 服务器信息
- **基础URL**: `http://localhost:8000`
- **认证方式**: Bearer Token (JWT)
- **请求头设置**:
  ```javascript
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
  ```

### Token获取方式
前端需要先调用登录接口获取Token，然后在后续请求中携带Token。

---

## 🔐 认证接口

### 1. 用户登录
```http
POST /login
Content-Type: application/x-www-form-urlencoded
```

**请求参数 (Form Data)**:
```javascript
{
  username: "string",  // 用户名
  password: "string"   // 密码
}
```

**响应格式**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```



### 2. 用户注册 (仅管理员)
```http
POST /register
Content-Type: application/x-www-form-urlencoded
```

**请求参数 (Form Data)**:
```javascript
{
  username: "string",           // 用户名
  password: "string",           // 密码
  invitation_code: "string"     // 管理员邀请码(必需)
}
```

**响应格式**: 用户信息对象

---

## 👤 用户管理接口

### 3. 获取当前用户信息
```http
GET /users/me
Authorization: Bearer <token>
```

**响应格式**:
```json
{
  "id": 1,
  "username": "admin",
  "role_id": 1,
  "roleName": "管理员",
  "permissions": ["AUTH-read", "AUTH-edit", "AUTH-own"],
  "create_time": "2024-01-01T00:00:00",
  "update_time": "2024-01-01T00:00:00"
}
```



### 4. 获取用户列表 (分页)
```http
GET /users?page=1&page_size=10&search=keyword&role_id=1&sort_field=id&sort_asc=true
Authorization: Bearer <token>
```

**查询参数**:
- `page`: 页码 (默认: 1)
- `page_size`: 每页数量 (默认: 10)
- `search`: 搜索关键词 (可选)
- `role_id`: 角色ID筛选 (可选)
- `sort_field`: 排序字段 (id/username/create_time/update_time)
- `sort_asc`: 排序方向 (true: 升序, false: 降序)

**响应格式**:
```json
{
  "total": 100,
  "page": 1,
  "page_size": 10,
  "total_pages": 10,
  "data": [
    {
      "id": 1,
      "username": "admin",
      "role_id": 1,
      "role_name": "管理员",
      "create_time": "2024-01-01T00:00:00",
      "update_time": "2024-01-01T00:00:00"
    }
  ]
}
```



### 5. 获取用户详情
```http
GET /users/{user_id}
Authorization: Bearer <token>
```

**路径参数**:
- `user_id`: 用户ID

**响应格式**: 同用户列表中的单个用户对象

### 6. 创建新用户
```http
POST /users/new
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "username": "newuser",
  "password": "password123",
  "role_id": 2
}
```

**响应格式**: 用户信息对象



### 7. 更新用户信息
```http
PUT /users/update/{user_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**路径参数**:
- `user_id`: 用户ID

**请求参数** (可选字段):
```json
{
  "username": "updated_username",
  "role_id": 3
}
```

**响应格式**: 更新后的用户信息对象

### 8. 用户角色分配
```http
PUT /users/{user_id}/role
Authorization: Bearer <token>
Content-Type: application/json
```

**路径参数**:
- `user_id`: 用户ID

**请求参数**:
```json
{
  "role_id": 2
}
```

**响应格式**: 更新后的用户信息对象

### 9. 删除用户 (软删除)
```http
DELETE /users/delete/{user_id}
Authorization: Bearer <token>
```

**路径参数**:
- `user_id`: 用户ID

**响应格式**: 被删除的用户信息对象

---

## 🔑 密码管理接口

### 10. 修改自己的密码
```http
PUT /users/me/password
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "old_password": "oldpassword123",
  "new_password": "newpassword456"
}
```

**响应格式**:
```json
{
  "message": "密码修改成功"
}
```



### 11. 管理员重置用户密码
```http
PUT /users/{user_id}/password/reset
Authorization: Bearer <token>
Content-Type: application/json
```

**路径参数**:
- `user_id`: 用户ID

**请求参数**:
```json
{
  "new_password": "newpassword123"
}
```

**响应格式**:
```json
{
  "message": "密码重置成功"
}
```

---

## 📊 批量操作和统计接口

### 12. 批量角色分配
```http
PUT /users/batch/role
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "user_ids": [1, 2, 3, 4],
  "role_id": 2
}
```

**响应格式**:
```json
{
  "success_count": 3,
  "failed_count": 1,
  "failed_users": [4],
  "message": "成功更新3个用户，失败1个用户"
}
```



### 13. 用户统计信息
```http
GET /users/statistics
Authorization: Bearer <token>
```

**响应格式**:
```json
{
  "total_users": 150,
  "users_by_role": [
    {
      "role_id": 1,
      "role_name": "管理员",
      "user_count": 5
    },
    {
      "role_id": 2,
      "role_name": "普通用户",
      "user_count": 145
    }
  ],
  "recent_registrations": 12
}
```

---

## 🎭 角色管理接口

### 14. 获取角色列表
```http
GET /roles?page=1&page_size=10&search=keyword
Authorization: Bearer <token>
```

**查询参数**: 同用户列表

**响应格式**:
```json
{
  "total": 10,
  "page": 1,
  "page_size": 10,
  "total_pages": 1,
  "data": [
    {
      "id": 1,
      "name": "管理员",
      "description": "系统管理员角色",
      "permissions": ["AUTH-read", "AUTH-edit", "AUTH-own"],
      "create_time": "2024-01-01T00:00:00",
      "update_time": "2024-01-01T00:00:00"
    }
  ]
}
```

### 15. 获取角色详情
```http
GET /roles/{role_id}
Authorization: Bearer <token>
```

### 16. 创建角色
```http
POST /roles/new
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "name": "新角色",
  "description": "角色描述",
  "permissions": ["AUTH-read", "BASE-read"]
}
```

### 17. 更新角色信息
```http
PUT /roles/update/{role_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "name": "更新的角色名",
  "description": "更新的描述"
}
```

### 18. 更新角色权限
```http
PUT /roles/{role_id}/permissions
Authorization: Bearer <token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "permission_ids": ["AUTH-read", "AUTH-edit", "BASE-read"]
}
```

### 19. 删除角色
```http
DELETE /roles/delete/{role_id}
Authorization: Bearer <token>
```

---

## 🔐 权限管理接口

### 20. 获取所有权限列表
```http
GET /permissions
Authorization: Bearer <token>
```

**响应格式**:
```json
[
  {
    "id": "AUTH-read",
    "description": "用户/角色/权限读取",
    "create_time": "2024-01-01T00:00:00",
    "update_time": "2024-01-01T00:00:00",
    "is_delete": false
  }
]
```

---

## 🛡️ 权限控制说明

### 权限类型
| 权限ID | 权限名称 | 描述 |
|--------|----------|------|
| `AUTH-read` | 查看权限 | 可以查看用户、角色、权限信息 |
| `AUTH-edit` | 编辑权限 | 可以修改用户、角色、权限信息 |
| `AUTH-own` | 个人权限 | 可以修改自己的信息 |
| `BASE-read` | 基础数据读取 | 可以读取基础数据信息 |
| `BASE-edit` | 基础数据修改 | 可以修改基础数据信息 |
| `IO-read` | 出入库数据读取 | 可以读取出入库数据 |
| `IO-edit` | 出入库数据修改 | 可以修改出入库数据 |
| `STOCK-read` | 库存读取 | 可以读取库存信息 |

### 接口权限要求
| 接口分类 | 需要权限 | 说明 |
|----------|----------|------|
| 获取用户列表/详情 | `AUTH-read` | 查看权限 |
| 创建/更新/删除用户 | `AUTH-edit` | 编辑权限 |
| 修改自己密码/信息 | `AUTH-own` | 个人权限 |
| 角色管理 | `AUTH-read`/`AUTH-edit` | 根据操作类型 |
| 权限管理 | `AUTH-read` | 查看权限 |

---

## ⚠️ 错误处理

### 常见HTTP状态码
- `200`: 请求成功
- `400`: 请求参数错误
- `401`: 未授权 (Token无效或过期)
- `403`: 权限不足
- `404`: 资源不存在
- `500`: 服务器内部错误

### 错误响应格式
```json
{
  "detail": "具体错误信息"
}
```

### 错误处理原则
- `401错误`: Token过期，需要重新登录
- `403错误`: 权限不足，提示用户
- 其他错误: 显示具体错误信息

---

## 📝 重要注意事项

1. **请求路径顺序**: `/users/statistics` 必须在 `/users/{user_id}` 之前匹配
2. **密码安全**: 新密码不能与原密码相同
3. **软删除**: 删除的用户不会物理删除，只是标记为已删除
4. **角色验证**: 分配角色时会验证角色ID的有效性
5. **管理员保护**: 不能删除最后一个管理员用户
6. **分页限制**: 建议每页数量不超过100条
7. **搜索优化**: 支持用户名、ID、时间等多字段模糊搜索
8. **角色名称冗余**: 用户信息中包含`role_name`字段，避免前端二次查询

---

## 🚀 快速开始

1. 获取Token: 调用登录接口获取访问令牌
2. 设置请求头: 在所有请求中携带Bearer Token
3. 权限检查: 根据用户权限显示/隐藏相应功能
4. 处理错误: 统一处理API错误和用户提示

---

## 📞 技术支持

如有接口问题或需要技术支持，请联系后端开发团队。

---

*文档版本: v1.0*  
*最后更新: 2024-01-01*