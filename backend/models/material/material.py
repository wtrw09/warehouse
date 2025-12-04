from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List
from datetime import datetime

# 器材模型
class Material(SQLModelBase, table=True):
    __tablename__ = "materials"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True, description="器材ID")
    material_code: str = Field(index=True, description="器材编码")
    material_name: str = Field(index=True, description="器材名称")
    material_specification: Optional[str] = Field(default=None, description="器材规格")
    material_desc: Optional[str] = Field(default=None, description="器材描述")
    material_wdh: Optional[str] = Field(default=None, description="器材尺寸（宽深高）")
    safety_stock: Optional[int] = Field(default=None, description="安全库存")
    material_query_code: Optional[str] = Field(default=None, description="器材查询编码")
    major_id: Optional[int] = Field(default=None, foreign_key="majors.id", description="所属专业ID")
    major_name: Optional[str] = Field(default=None, description="专业名称")
    equipment_id: Optional[int] = Field(default=None, foreign_key="equipments.id", description="所属装备ID")
    equipment_name: Optional[str] = Field(default=None, description="装备名称")
    creator: Optional[str] = Field(default=None, description="创建人")
    is_delete: bool = Field(default=False, description="是否被删除")
    create_time: Optional[datetime] = Field(default=None, description="创建时间")
    update_time: Optional[datetime] = Field(default=None, description="修改时间")
    
    # 外键关系
    inventory_batches: List["InventoryBatch"] = Relationship(back_populates="material")
    inventory_details: List["InventoryDetail"] = Relationship(back_populates="material")
    inbound_order_items: List["InboundOrderItem"] = Relationship(back_populates="material", sa_relationship_kwargs={"lazy": "selectin"})
    outbound_order_items: List["OutboundOrderItem"] = Relationship(back_populates="material", sa_relationship_kwargs={"lazy": "selectin"})
    inventory_transactions: List["InventoryTransaction"] = Relationship(back_populates="material")
    
    __table_args__ = (
        {"sqlite_autoincrement": True, "extend_existing": True},
    )