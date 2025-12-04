from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional
from datetime import datetime
from enum import Enum


class ChangeType(str, Enum):
    """库存变更类型枚举"""
    IN = "IN"      # 入库
    OUT = "OUT"    # 出库
    ADJUST = "ADJUST"  # 调整


class ReferenceType(str, Enum):
    """关联单据类型枚举"""
    INBOUND = "inbound"      # 入库单
    OUTBOUND = "outbound"    # 出库单
    STOCKTAKE = "stocktake"  # 盘点单


class InventoryTransaction(SQLModelBase, table=True):
    """库存变更流水表"""
    
    __tablename__ = "inventory_transactions"
    
    transaction_id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="流水ID，主键，自动递增"
    )
    
    material_id: int = Field(
        foreign_key="materials.id",
        nullable=False,
        description="器材ID，外键关联materials表"
    )
    
    batch_id: int = Field(
        foreign_key="inventory_batches.batch_id",
        nullable=False,
        description="批次ID，外键关联inventory_batches表"
    )
    
    change_type: ChangeType = Field(
        nullable=False,
        description="处理类型：IN(入库)、OUT(出库)、ADJUST(调整)"
    )
    
    quantity_change: int = Field(
        nullable=False,
        description="改变数量，正数表示增加，负数表示减少"
    )
    
    quantity_before: int = Field(
        nullable=False,
        description="改变前数量"
    )
    
    quantity_after: int = Field(
        nullable=False,
        description="改变后数量"
    )
    
    reference_type: ReferenceType = Field(
        nullable=False,
        description="关联单据类型：inbound(入库单)、outbound(出库单)、stocktake(盘点单)"
    )
    
    reference_id: Optional[int] = Field(
        default=None,
        nullable=True,
        description="关联单据ID（如入库单ID、出库单ID、盘点单ID）"
    )
    
    creator: str = Field(
        nullable=False,
        description="操作人"
    )
    
    transaction_time: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="操作时间"
    )
    
    # 外键关系
    material: Optional["Material"] = Relationship(back_populates="inventory_transactions")
    batch: Optional["InventoryBatch"] = Relationship(back_populates="inventory_transactions")
    
    __table_args__ = {
        "comment": "库存变更流水表，记录所有库存变动明细，用于审计和追溯"
    }