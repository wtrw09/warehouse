from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional


class OutboundOrderItem(SQLModelBase, table=True):
    """出库单明细表"""
    
    __tablename__ = "outbound_order_items"
    
    item_id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="明细项ID，主键，自动递增"
    )
    
    order_id: int = Field(
        foreign_key="outbound_orders.order_id",
        nullable=False,
        description="出库单ID，外键关联outbound_orders表"
    )
    
    material_id: int = Field(
        foreign_key="materials.id",
        nullable=False,
        description="器材ID，外键关联materials表"
    )
    
    material_code: str = Field(
        nullable=False,
        description="器材编码，冗余设置"
    )
    
    material_name: str = Field(
        nullable=False,
        description="器材名称，冗余设置，不随ID变化"
    )
    
    material_specification: str = Field(
        nullable=False,
        description="品牌型号，冗余设置，不随ID变化"
    )
    
    quantity: int = Field(
        default=0,
        nullable=False,
        description="数量"
    )
    
    unit_price: float = Field(
        default=0.0,
        nullable=False,
        description="出库单价，成本依据"
    )
    
    unit: str = Field(
        default="个",
        nullable=False,
        description="计量单位，冗余设置"
    )
    
    batch_id: int = Field(
        foreign_key="inventory_batches.batch_id",
        nullable=False,
        description="从哪个批次出库，外键关联inventory_batches表"
    )
    
    bin_id: Optional[int] = Field(
        default=None,
        foreign_key="bins.id",
        nullable=True,
        description="货位ID，外键关联bins表"
    )
    
    # 外键关系
    order: Optional["OutboundOrder"] = Relationship(back_populates="items")
    material: Optional["Material"] = Relationship(back_populates="outbound_order_items")
    batch: Optional["InventoryBatch"] = Relationship(back_populates="outbound_order_items")
    bin: Optional["Bin"] = Relationship(back_populates="outbound_order_items")
    
    __table_args__ = {
        "comment": "出库单明细表，记录出库单中每个器材的详细信息"
    }