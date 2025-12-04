from typing import List, Optional, TYPE_CHECKING
from models import SQLModelBase
from sqlmodel import Field, Relationship

if TYPE_CHECKING:
    from models.account.user import User
    from models.account.permission import Permission

# 角色和权限的多对多关系表
class RolePermissionLink(SQLModelBase, table=True):
    __tablename__ = "role_permissions"  # type: ignore[assignment]
    
    role_id: Optional[int] = Field(default=None, foreign_key="roles.id", primary_key=True)
    permission_id: Optional[str] = Field(default=None, foreign_key="permissions.id", primary_key=True)

class Role(SQLModelBase, table=True):
    __tablename__ = "roles"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True)
    name: str = Field(index=True, description="角色名称")
    description: str = Field(description="角色描述")
    
    # 多对多关系：一个角色可以有多个权限
    permissions: List["Permission"] = Relationship(link_model=RolePermissionLink)
    
    # 一对多关系：一个角色可以有多个用户
    users: List["User"] = Relationship(back_populates="role")