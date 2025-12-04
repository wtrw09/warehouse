from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import date


class InventoryDetail(SQLModel, table=True):
    """库存明细表"""
    
    __tablename__ = "inventory_details"
    
    detail_id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="明细ID，主键"
    )
    
    batch_id: int = Field(
        foreign_key="inventory_batches.batch_id",
        description="批次ID，外键关联inventory_batches表"
    )
    
    material_id: int = Field(
        foreign_key="materials.id",
        description="器材ID，外键关联materials表"
    )
    
    bin_id: Optional[int] = Field(
        default=None,
        foreign_key="bins.id",
        nullable=True,
        description="货位ID，外键关联bins表"
    )
    
    quantity: int = Field(
        default=0,
        description="该批次在当前货位的数量"
    )
    
    last_updated: date = Field(
        description="上次更新日期"
    )
    
    # 外键关系
    batch: Optional["InventoryBatch"] = Relationship(back_populates="details")
    material: Optional["Material"] = Relationship(back_populates="inventory_details")
    bin: Optional["Bin"] = Relationship(back_populates="inventory_details")
    
    __table_args__ = {
        "comment": "库存明细表，记录每个批次在不同货位的库存分布情况"
    }