from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List
from datetime import datetime, date

# 库存批次模型
class InventoryBatch(SQLModelBase, table=True):
    __tablename__ = "inventory_batches"  # type: ignore[assignment]
    
    batch_id: int = Field(default=None, primary_key=True, index=True, description="批次ID")
    batch_number: str = Field(index=True, unique=True, description="系统生成的唯一批次号")
    material_id: int = Field(foreign_key="materials.id", description="器材ID")
    unit: str = Field(default="个", description="计量单位")
    unit_price: float = Field(description="采购单价，成本依据")
    production_date: Optional[date] = Field(default=None, description="生产日期")
    supplier_id: Optional[int] = Field(default=None, foreign_key="suppliers.id", description="供应商ID")
    inbound_date: Optional[date] = Field(default=None, description="入库日期")
    creator: Optional[str] = Field(default=None, description="操作员")
    is_delete: bool = Field(default=False, description="是否被删除")
    create_time: Optional[datetime] = Field(default=None, description="创建时间")
    update_time: Optional[datetime] = Field(default=None, description="修改时间")
    
    # 外键关系
    material: Optional["Material"] = Relationship(back_populates="inventory_batches")
    supplier: Optional["Supplier"] = Relationship(back_populates="inventory_batches")
    details: List["InventoryDetail"] = Relationship(back_populates="batch")
    inbound_order_items: List["InboundOrderItem"] = Relationship(back_populates="batch")
    outbound_order_items: List["OutboundOrderItem"] = Relationship(back_populates="batch")
    inventory_transactions: List["InventoryTransaction"] = Relationship(back_populates="batch")
    
    __table_args__ = (
        {"sqlite_autoincrement": True, "extend_existing": True},
    )