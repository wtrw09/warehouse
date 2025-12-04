from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List

# 仓库模型
class Warehouse(SQLModelBase, table=True):
    __tablename__ = "warehouses"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True, description="仓库ID")
    warehouse_name: str = Field(index=True, description="仓库名")
    warehouse_city: Optional[str] = Field(default=None, description="所在城市")
    warehouse_address: Optional[str] = Field(default=None, description="地址")
    warehouse_contact: Optional[str] = Field(default=None, description="联系方式")
    warehouse_manager: Optional[str] = Field(default=None, description="负责人")
    creator: str = Field(description="创建人")
    
    # 与货位的关系
    bins: List["Bin"] = Relationship(back_populates="warehouse")