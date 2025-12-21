from .. import SQLModelBase
from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.account.role import Role

# 用户模型  
class User(SQLModelBase, table=True):
    __tablename__ = "users"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True)
    username: str = Field(index=True, description="用户名")
    hashed_password: str = Field(description="加密密码")
    avatar: str = Field(default="XX/user.jpg", description="用户头像")
    department: str = Field(default=None, nullable=True, description="所属单位")
    # 外键：一个用户属于一个角色
    role_id: int = Field(foreign_key="roles.id", description="角色ID")
    role: "Role" = Relationship(back_populates="users")