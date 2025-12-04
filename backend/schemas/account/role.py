from typing import Optional
from pydantic import BaseModel
from typing import Optional, List
from core.security import Permission as SecurityPermission
from datetime import datetime

class RoleBase(BaseModel):
    """角色基础模型，定义角色的基本属性"""
    name: str  # 角色名称
    description: Optional[str] = None  # 角色描述，可选字段

class RoleCreate(RoleBase):
    """用于创建角色的模型，继承自 RoleBase"""
    permissions: List[str] = [SecurityPermission.STOCK_READ.value]  # 角色权限列表，默认包含STOCK-read权限


class RoleResponse(RoleBase):
    """用于返回角色信息的模型，继承自 RoleBase"""
    id: int
    create_time: datetime  # 创建时间
    update_time: datetime  # 修改时间
    
class RoleUpdate(RoleBase):
    """用于更新角色的模型，继承自 RoleBase"""
    pass
    
class RoleWithPermissions(RoleResponse):
    """包含权限信息的角色模型"""
    permissions: List[str] = []
    
class UpdateRolePermissions(BaseModel):
    """用于更新角色权限的模型"""
    permission_ids: List[str]

class PaginationResult(BaseModel):
    """通用分页结果模型"""
    total: int  # 总记录数
    page: int  # 当前页码
    page_size: int  # 每页记录数
    total_pages: int  # 总页数
    data: List[RoleWithPermissions]  # 分页数据列表