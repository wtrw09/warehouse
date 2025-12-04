# 用户管理API设计报告

## 1. 设计概述

基于现有角色管理API的架构模式，设计一套完整的用户管理API接口，遵循RBAC（基于角色的访问控制）模型，提供用户的增删改查、角色分配、密码管理等核心功能。

### 1.1 设计原则

- **一致性原则**: 与现有角色管理API保持相同的架构模式和响应格式
- **安全性原则**: 所有接口都需要适当的权限验证，敏感信息需要脱敏处理
- **扩展性原则**: 支持分页、搜索、排序等高级查询功能
- **维护性原则**: 采用软删除机制，保留数据历史记录

### 1.2 技术架构

- **框架**: FastAPI + SQLModel + Pydantic
- **数据库**: 基于现有数据库结构（SQLite）
- **认证**: OAuth2 Bearer Token (JWT)
- **权限控制**: 基于scope的权限验证机制
- **软删除机制**: 所有API自动过滤`is_delete=true`的数据，不暴露给前端

## 2. 数据模型设计

### 2.1 基于现有User模型设计

严格按照现有User模型字段进行API设计，不添加额外字段：

```python
# models/user.py (当前模型)
from models import SQLModelBase
from sqlmodel import Field, Relationship

class User(SQLModelBase, table=True):
    __tablename__ = "users"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True)
    username: str = Field(index=True, unique=True, description="用户名")
    hashed_password: str = Field(description="加密密码")
    # 外键：一个用户属于一个角色
    role_id: int = Field(foreign_key="roles.id", description="角色ID")
    role: "Role" = Relationship(back_populates="users")
    
    # 继承自SQLModelBase的字段：
    # is_delete: bool = Field(default=False, description="是否被删除")
    # create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    # update_time: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}, description="修改时间")
```

### 2.2 用户相关Schema设计

严格按照User模型字段设计Schema：

```python
# schemas/user.py (基于现有模型)
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from schemas.common import PaginationParams

# ===== 原有模型（保留，用于现有API） =====

# 基础用户模型
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

# 注册管理员模型
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    invitation_code: Optional[str] = None

# 登录用户模型
class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

# 返回用户信息（原有模型，包含权限信息）
class UserResponse(UserBase):
    id: int
    role_id: int
    roleName: str  # 角色名称
    permissions: list = []  # 对应权限列表
    create_time: datetime
    update_time: datetime 

# 用户角色信息
class UserPermission(UserBase):
    roleName: str


# ===== 新增用户管理模型（按照API设计报告） =====

# 基础用户管理模型（继承UserBase，严格按照User数据库模型字段）
class UserManagementBase(UserBase):
    role_id: int = Field(..., description="角色ID")

# 创建用户模型
class UserManagementCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    role_id: int = Field(..., description="角色ID")

# 更新用户模型
class UserManagementUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    role_id: Optional[int] = Field(None, description="角色ID")

# 密码相关模型
class UserPasswordUpdate(BaseModel):
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")

class UserPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")

# 用户角色分配模型
class UserRoleAssign(BaseModel):
    role_id: int = Field(..., description="角色ID")

# 用户管理响应模型（严格按照User模型字段，不包含权限信息，包含角色名称冗余）
class UserManagementResponse(BaseModel):
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role_id: int = Field(..., description="角色ID")
    role_name: str = Field(..., description="角色名称")  # 冗余字段，便于前端显示
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="修改时间")

    class Config:
        from_attributes = True

# 用户查询参数模型
class UserQueryParams(PaginationParams):
    role_id: Optional[int] = Field(None, description="按角色ID筛选")
    # 继承自PaginationParams: page, page_size, search, sort_field, sort_asc

# 用户分页结果模型
class UserPaginationResult(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")
    data: List[UserManagementResponse] = Field(..., description="用户数据列表")

# 批量用户角色分配模型
class BatchUserRoleAssign(BaseModel):
    user_ids: List[int] = Field(..., description="用户ID列表")
    role_id: int = Field(..., description="角色ID")

# 批量操作结果模型
class BatchOperationResult(BaseModel):
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_users: List[int] = Field(default=[], description="失败的用户ID列表")
    message: str = Field(..., description="操作结果描述")

# 用户统计模型
class UserStatistics(BaseModel):
    total_users: int = Field(..., description="总用户数（不包含已删除）")
    users_by_role: List[dict] = Field(..., description="按角色分组的用户统计")
    recent_registrations: int = Field(..., description="最近7天注册用户数")

# 标准错误响应模型
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="错误详情")
    error_code: Optional[str] = Field(None, description="错误代码")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
```

## 3. API接口设计

### 数据过滤原则

**重要**: 所有用户查询接口都必须在SQL查询中添加 `WHERE is_delete != True` 条件，确保：
1. 已删除的用户不会返回给前端
2. `is_delete`字段不出现在任何响应模型中
3. 前端无法感知到软删除机制的存在

### 3.1 用户列表查询（分页）

**接口信息**:
- **路径**: `GET /users`
- **描述**: 获取用户列表，支持分页、搜索、排序（自动过滤已删除用户）
- **权限要求**: `AUTH-read`

**请求参数**:
```python
class UserQueryParams(PaginationParams):
    role_id: Optional[int] = Field(None, description="按角色ID筛选")
    # 继承自PaginationParams: page, page_size, search, sort_field, sort_asc
```

**支持排序字段**: `id`, `username`, `create_time`, `update_time`

**搜索功能**: 支持按用户名进行模糊搜索

**响应格式**: `UserPaginationResult`

注：在API响应中，使用`UserManagementResponse`作为数据列表的元素类型，包含`role_name`冗余字段便于前端显示。

### 3.2 获取用户详情

**接口信息**:
- **路径**: `GET /users/{user_id}`
- **描述**: 获取指定用户的详细信息（不返回已删除用户）
- **权限要求**: `AUTH-read`

**路径参数**:
- `user_id`: int - 用户ID

**响应格式**: `UserManagementResponse`

### 3.3 创建用户

**接口信息**:
- **路径**: `POST /users/new`
- **描述**: 创建新用户
- **权限要求**: `AUTH-edit`

**请求体**: `UserManagementCreate`

**响应格式**: `UserManagementResponse`

**业务逻辑**:
1. 验证用户名唯一性
2. 验证角色ID有效性
3. 密码加密存储

### 3.4 更新用户信息

**接口信息**:
- **路径**: `PUT /users/update/{user_id}`
- **描述**: 更新用户基本信息
- **权限要求**: `AUTH-edit` 或 `AUTH-own`（仅限更新自己）

**路径参数**:
- `user_id`: int - 用户ID

**请求体**: `UserManagementUpdate`

**响应格式**: `UserManagementResponse`

**业务逻辑**:
1. 权限验证：管理员可更新任何用户，普通用户只能更新自己
2. 验证用户名唯一性（如果有修改）
3. 验证角色ID有效性（如果有修改）

### 3.5 用户角色分配

**接口信息**:
- **路径**: `PUT /users/{user_id}/role`
- **描述**: 为用户分配角色
- **权限要求**: `AUTH-edit`

**路径参数**:
- `user_id`: int - 用户ID

**请求体**: `UserRoleAssign`

**响应格式**: `UserManagementResponse`

### 3.6 用户密码管理

#### 3.6.1 用户修改密码（自己）

**接口信息**:
- **路径**: `PUT /users/me/password`
- **描述**: 用户修改自己的密码
- **权限要求**: `AUTH-own`

**请求体**: `UserPasswordUpdate`

**响应格式**: 标准成功响应

#### 3.6.2 管理员重置用户密码

**接口信息**:
- **路径**: `PUT /users/{user_id}/password/reset`
- **描述**: 管理员重置指定用户的密码
- **权限要求**: `AUTH-edit`

**路径参数**:
- `user_id`: int - 用户ID

**请求体**: `UserPasswordReset`

**响应格式**: 标准成功响应

### 3.7 删除用户

**接口信息**:
- **路径**: `DELETE /users/delete/{user_id}`
- **描述**: 软删除用户（标记为已删除）
- **权限要求**: `AUTH-edit`

**路径参数**:
- `user_id`: int - 用户ID

**响应格式**: `UserManagementResponse`

**业务逻辑**:
1. 检查是否为最后一个管理员用户
2. 软删除：设置 `is_delete = True`，不物理删除数据
3. 更新 `update_time` 字段
4. 后续所有API查询都会自动过滤此用户

### 3.8 批量操作接口

#### 3.8.1 批量用户角色分配

**接口信息**:
- **路径**: `PUT /users/batch/role`
- **描述**: 批量为多个用户分配角色
- **权限要求**: `AUTH-edit`

**请求体**:
```python
class BatchUserRoleAssign(BaseModel):
    user_ids: List[int] = Field(..., description="用户ID列表")
    role_id: int = Field(..., description="角色ID")
```

**响应格式**:
```python
class BatchOperationResult(BaseModel):
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_users: List[int] = Field(default=[], description="失败的用户ID列表")
    message: str = Field(..., description="操作结果描述")
```

### 3.9 用户统计接口

**接口信息**:
- **路径**: `GET /users/statistics`
- **描述**: 获取用户统计信息
- **权限要求**: `AUTH-read`

**响应格式**:
```python
class UserStatistics(BaseModel):
    total_users: int = Field(..., description="总用户数（不包含已删除）")
    users_by_role: List[dict] = Field(..., description="按角色分组的用户统计")
    recent_registrations: int = Field(..., description="最近7天注册用户数")
```

## 5. 实现建议

### 5.1 数据库优化

1. **索引设计**:
   - 为 `username` 字段添加唯一索引（已存在）
   - 为 `role_id` 字段添加普通索引
   - 为 `create_time`, `update_time` 添加索引以支持排序

2. **数据完整性**:
   - 添加外键约束确保角色ID有效性

### 5.2 安全性考虑

1. **密码安全**:
   - 使用强加密算法（如bcrypt）
   - 实施密码复杂度策略
   - 记录密码修改历史

3. **防护措施**:
   - 用户名查重
   - 限制密码重试次数
   - 会话超时管理

### 5.3 性能优化

1. **查询优化**:
   - 使用预加载（selectinload）减少N+1查询
   - 分页查询优化，避免深度分页
   - 缓存热点数据（如角色权限信息）

2. **批量操作优化**:
   - 使用批量插入/更新减少数据库往返
   - 事务管理确保数据一致性

## 6. 错误处理

### 6.1 标准错误响应

```python
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="错误详情")
    error_code: Optional[str] = Field(None, description="错误代码")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误时间")
```

### 6.2 错误代码定义

| HTTP状态码 | 错误代码 | 错误描述 | 示例场景 |
|------------|----------|----------|----------|
| 400 | USER_EXISTS | 用户已存在 | 创建用户时用户名重复 |
| 400 | INVALID_ROLE | 无效角色 | 分配不存在的角色 |
| 400 | WEAK_PASSWORD | 密码强度不足 | 密码不符合复杂度要求 |
| 401 | INVALID_CREDENTIALS | 凭据无效 | 修改密码时原密码错误 |
| 403 | INSUFFICIENT_PERMISSION | 权限不足 | 普通用户尝试删除其他用户 |
| 404 | USER_NOT_FOUND | 用户不存在 | 操作不存在的用户 |
| 409 | LAST_ADMIN | 最后管理员 | 尝试删除最后一个管理员 |

## 7. 测试策略

### 7.1 单元测试

- 每个API接口的业务逻辑测试
- 权限验证逻辑测试
- 数据校验逻辑测试
- 错误处理测试

### 7.2 集成测试

- 完整的用户生命周期测试
- 角色权限集成测试
- 批量操作测试
- 数据一致性测试

### 7.3 性能测试

- 分页查询性能测试
- 批量操作性能测试
- 并发操作测试

## 8. 部署注意事项

### 8.1 环境配置

- 数据库连接池配置
- JWT密钥管理

### 8.2 监控告警

- API响应时间监控
- 错误率监控
- 用户活跃度统计
- 安全异常告警

## 9. 总结

本用户管理API设计严格遵循User模型的字段设计，提供了完整的用户生命周期管理功能，包括：

- ✅ 基于User模型的CRUD操作
- ✅ 灵活的权限控制机制
- ✅ 简单的查询和统计功能
- ✅ 批量操作支持
- ✅ 安全性和性能考虑
- ✅ 标准化的错误处理
- ✅ 可扩展的设计架构

### 9.1 模型设计亮点

1. **向后兼容性**: 保留所有原有模型，确保现有API继续正常工作
2. **职责分离**: 
   - `UserResponse`: 用于认证相关API，包含权限信息
   - `UserManagementResponse`: 用于用户管理API，不包含权限信息，包含角色名称冗余
3. **代码复用**: `UserManagementBase`继承`UserBase`，避免重复代码
4. **数据冗余优化**: 在响应模型中包含`role_name`字段，减少前端额外请求
5. **类型安全**: 严格的字段验证和类型注解

该设计严格按照User模型字段，不添加额外信息，可以满足仓库管理系统的用户管理需求。

---

*设计文档版本: v1.1*  
*最后更新时间: 2025年*
*更新内容: 更新最终模型设计，增加职责分离和向后兼容性设计*