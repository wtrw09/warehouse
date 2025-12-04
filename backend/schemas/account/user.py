from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from schemas.common import PaginationParams

class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)

class UserCreate(UserBase):  # 注册管理员模型
    password: str = Field(..., min_length=6)
    invitation_code: Optional[str] = None

class UserLogin(BaseModel):  # 登录用户
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserResponse(UserBase):  # 返回验证的个人用户信息（包含权限信息）
    id: int
    role_id: int
    # 角色名称
    roleName: str
    # 对应权限列表
    permissions: list = []
    department: Optional[str] = Field(None, description="所属单位")
    create_time: datetime
    update_time: datetime
    # Redis状态提示（可选）
    redis_unavailable: Optional[bool] = Field(None, description="Redis是否不可用")
    redis_status_message: Optional[str] = Field(None, description="Redis状态提示信息") 

# 用户角色信息
class UserPermission(UserBase):
    roleName: str



# 基础用户模型（严格按照User数据库模型字段）
class UserManagementBase(UserBase):
    role_id: int = Field(..., description="角色ID")

# 创建常规用户模型
class UserManagementCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    role_id: int = Field(..., description="角色ID")
    department: Optional[str] = Field(None, description="所属单位")

# 更新用户模型
class UserManagementUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=50, description="用户名")
    role_id: Optional[int] = Field(None, description="角色ID")
    department: Optional[str] = Field(None, description="所属单位")

# 密码相关模型
class UserPasswordUpdate(BaseModel):
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")

class UserPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")

# 用户角色分配模型
class UserRoleAssign(BaseModel):
    role_id: int = Field(..., description="角色ID")

# 用户响应模型（严格按照User模型字段，不包含权限信息）
class UserManagementResponse(BaseModel):
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role_id: int = Field(..., description="角色ID")
    role_name: str = Field(..., description="角色名称")
    department: Optional[str] = Field(None, description="所属单位")
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
