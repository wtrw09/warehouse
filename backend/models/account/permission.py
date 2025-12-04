from models import SQLModelBase
from sqlmodel import Field

class Permission(SQLModelBase, table=True):
    __tablename__ = "permissions"  # type: ignore[assignment]
    
    id: str = Field(default=None, primary_key=True, index=True, description="权限编号")
    name: str = Field(index=True, unique=True, description="权限名称")
    description: str = Field(description="权限描述")