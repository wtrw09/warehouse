from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List
from datetime import datetime

# 装备模型
class Equipment(SQLModelBase, table=True):
    __tablename__ = "equipments"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True, description="装备ID")
    equipment_code: str = Field(index=True, description="装备编码")
    equipment_name: str = Field(index=True, description="装备名称")
    specification: Optional[str] = Field(default=None, description="规格型号")
    major_id: Optional[int] = Field(default=None, foreign_key="majors.id", description="所属专业ID")
    major_name: Optional[str] = Field(default=None, description="专业名称")
    creator: Optional[str] = Field(default=None, description="创建人")
    is_delete: bool = Field(default=False, description="是否被删除")
    create_time: Optional[datetime] = Field(default=None, description="创建时间")
    update_time: Optional[datetime] = Field(default=None, description="修改时间")
    
    __table_args__ = (
        {"sqlite_autoincrement": True, "extend_existing": True},
    )