# 用户管理API使用指南

## 概述

根据用户管理API设计报告，已成功实现完整的用户管理后端API。该API遵循RBAC（基于角色的访问控制）模型，提供用户的增删改查、角色分配、密码管理等核心功能。

## 重要更新说明

### 🔄 路由冲突解决
- **问题**: 调用 `GET /users/statistics` 时出现路由冲突
- **原因**: 参数路由 `/users/{user_id}` 在统计路由之前定义
- **解决**: 已调整路由定义顺序，统计接口现在优先匹配

### 🔒 密码安全增强
- **新增验证**: 修改密码时验证新密码与原密码不相同
- **适用接口**: `PUT /users/me/password` 和 `PUT /users/{user_id}/password/reset`
- **错误提示**: “新密码不能与原密码相同，请选择一个不同的密码”

### 🛠️ 技术修复
- **UserResponse 类型修复**: 解决了 `hashed_password` 字段不存在错误
- **类型安全**: 更新了函数参数类型注解，提升代码健壮性

## 技术架构

- **框架**: FastAPI + SQLModel + Pydantic
- **数据库**: SQLite（支持软删除机制）
- **认证**: OAuth2 Bearer Token (JWT)
- **权限控制**: 基于scope的权限验证机制

## 核心特性

### ✅ 向后兼容性
- 保留所有原有模型和API接口
- 现有认证相关功能继续正常工作
- 新增用户管理功能不影响现有系统

### ✅ 职责分离
- **UserResponse**: 用于认证相关API，包含权限信息
- **UserManagementResponse**: 用于用户管理API，不包含权限信息，包含角色名称冗余

### ✅ 安全设计
- 所有API自动过滤已删除用户（`is_delete=true`）
- 敏感字段（如头像）不暴露给前端
- 完整的权限验证机制

## API接口列表

### 原有接口（保留）
- `GET /users/me` - 获取当前用户信息（包含权限）

### 用户管理接口
| 方法 | 路径 | 描述 | 权限要求 |
|------|------|------|----------|
| GET | `/users` | 获取用户列表（分页） | AUTH-read |
| GET | `/users/{user_id}` | 获取用户详情 | AUTH-read |
| POST | `/users/new` | 创建新用户 | AUTH-edit |
| PUT | `/users/update/{user_id}` | 更新用户信息 | AUTH-edit / AUTH-own |
| PUT | `/users/{user_id}/role` | 用户角色分配 | AUTH-edit |
| DELETE | `/users/delete/{user_id}` | 删除用户（软删除） | AUTH-edit |

### 密码管理接口
| 方法 | 路径 | 描述 | 权限要求 |
|------|------|------|----------|
| PUT | `/users/me/password` | 修改自己的密码 | AUTH-own |
| PUT | `/users/{user_id}/password/reset` | 管理员重置密码 | AUTH-edit |

### 批量操作接口
| 方法 | 路径 | 描述 | 权限要求 |
|------|------|------|----------|
| PUT | `/users/batch/role` | 批量角色分配 | AUTH-edit |

### 统计接口
| 方法 | 路径 | 描述 | 权限要求 |
|------|------|------|----------|
| GET | `/users/statistics` | 获取用户统计信息 | AUTH-read |

## 核心功能特性

### 🔍 高级查询
- **分页**: 支持页码和每页数量设置
- **搜索**: 支持用户名、ID、时间的模糊搜索
- **排序**: 支持按ID、用户名、创建时间、更新时间排序
- **角色筛选**: 支持按角色ID筛选用户

### 🛡️ 权限控制
- **AUTH-read**: 用户/角色/权限读取
- **AUTH-edit**: 用户/角色/权限修改
- **AUTH-own**: 本人信息修改

### 🔒 密码安全验证
- **原密码验证**: 修改密码时验证当前密码正确性
- **新旧密码对比**: 确保新密码与原密码不相同
- **密码复杂度**: 支持最小长度要求（6位）
- **密码加密**: 使用bcrypt算法安全存储

### 💾 软删除机制
- 删除用户时只标记 `is_delete=true`
- 所有查询自动过滤已删除用户
- 前端无法感知到软删除机制

### 📊 数据冗余优化
- 响应中包含 `role_name` 字段
- 减少前端额外API调用
- 提升用户体验

## 数据模型

### 用户管理响应模型
```python
class UserManagementResponse(BaseModel):
    id: int                    # 用户ID
    username: str              # 用户名
    role_id: int              # 角色ID
    role_name: str            # 角色名称（冗余字段）
    create_time: datetime     # 创建时间
    update_time: datetime     # 更新时间
```

### 分页结果模型
```python
class UserPaginationResult(BaseModel):
    total: int                           # 总记录数
    page: int                           # 当前页码
    page_size: int                      # 每页记录数
    total_pages: int                    # 总页数
    data: List[UserManagementResponse]  # 用户数据列表
```

## 使用示例

### 1. 获取用户列表（分页）
```http
GET /users?page=1&page_size=10&search=admin&sort_field=create_time&sort_asc=false
Authorization: Bearer <token>
```

### 2. 创建用户
```http
POST /users/new
Authorization: Bearer <token>
Content-Type: application/json

{
    "username": "newuser",
    "password": "password123",
    "role_id": 2
}
```

### 3. 更新用户信息
```http
PUT /users/update/1
Authorization: Bearer <token>
Content-Type: application/json

{
    "username": "updated_username",
    "role_id": 3
}
```

### 4. 批量角色分配
```http
PUT /users/batch/role
Authorization: Bearer <token>
Content-Type: application/json

{
    "user_ids": [1, 2, 3],
    "role_id": 2
}
```

### 5. 修改密码（带验证）
```http
PUT /users/me/password
Authorization: Bearer <token>
Content-Type: application/json

{
    "old_password": "oldpassword123",
    "new_password": "newpassword456"
}
```

**注意**: 新密码不能与原密码相同，否则会返回400错误。

### 6. 统计信息查询
```http
GET /users/statistics
Authorization: Bearer <token>
```

**注意**: 该接口在参数路由之前匹配，解决了之前的路由冲突问题。
```http
PUT /users/batch/role
Authorization: Bearer <token>
Content-Type: application/json

{
    "user_ids": [1, 2, 3],
    "role_id": 2
}
```

## 错误处理

### 标准错误响应
```json
{
    "detail": "错误详情",
    "error_code": "USER_NOT_FOUND",
    "timestamp": "2025-01-01T00:00:00"
}
```

### 常见错误代码
| HTTP状态码 | 错误代码 | 描述 | 示例场景 |
|------------|----------|------|----------|
| 400 | USER_EXISTS | 用户已存在 | 创建用户时用户名重复 |
| 400 | INVALID_ROLE | 无效角色 | 分配不存在的角色 |
| 400 | WEAK_PASSWORD | 密码强度不足 | 密码不符合复杂度要求 |
| 400 | SAME_PASSWORD | 新旧密码相同 | 新密码与原密码相同 |
| 401 | INVALID_CREDENTIALS | 凭据无效 | 修改密码时原密码错误 |
| 403 | INSUFFICIENT_PERMISSION | 权限不足 | 普通用户尝试删除其他用户 |
| 404 | USER_NOT_FOUND | 用户不存在 | 操作不存在的用户 |
| 409 | LAST_ADMIN | 最后管理员 | 尝试删除最后一个管理员 |

## 部署说明

### 1. 启动服务
```bash
cd /path/to/project
python main.py
```

### 2. 访问API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 权限配置
确保在 `core/security.py` 中正确配置了路由权限映射：
```python
ROUTE_PERMISSIONS = {
    "/users": [Permission.AUTH_READ],
    "/users/new": [Permission.AUTH_EDIT],
    "/users/update": [Permission.AUTH_EDIT],
    "/users/delete": [Permission.AUTH_EDIT],
    # ... 其他路由配置
}
```

## 测试

### 自动化测试
运行测试脚本：
```bash
python test_user_management_api.py
```

### 手动测试
1. 使用管理员账户登录获取token
2. 使用token访问各个API接口
3. 验证权限控制是否正确
4. 测试分页、搜索、排序功能

## 注意事项

### ℹ️ 重要提醒
1. **向后兼容性**: 原有API继续使用 `UserResponse` 模型
2. **权限验证**: 确保用户具有相应权限才能访问接口
3. **软删除**: 已删除用户不会在列表中显示，但数据仍保留在数据库中
4. **密码安全**: 所有密码都经过bcrypt加密存储，且新密码不能与原密码相同
5. **头像字段**: 虽然数据库中存在avatar字段，但不暴露给前端
6. **路由顺序**: 统计接口 `/users/statistics` 已优化为在参数路由之前匹配

### 🔧 配置建议
1. 定期备份数据库文件
2. 设置适当的JWT过期时间
3. 监控API使用情况和性能
4. 定期清理软删除的数据（可选）

### 📦 更新日志

### v1.1 - 2025年1月
- ✅ 修复路由冲突问题（统计接口优先匹配）
- ✅ 增强密码安全验证（新旧密码不能相同）
- ✅ 修复UserResponse类型错误
- ✅ 优化错误处理和提示信息
- ✅ 更新API文档和使用指南

### v1.0 - 2025年1月
- ✅ 实现完整的用户管理API
- ✅ 支持分页、搜索、排序
- ✅ 实现软删除机制
- ✅ 添加批量操作支持
- ✅ 实现用户统计功能
- ✅ 确保向后兼容性
- ✅ 完善权限控制机制

---

如有问题或建议，请联系开发团队。