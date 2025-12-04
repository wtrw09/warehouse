from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List
from datetime import datetime


class InboundOrder(SQLModelBase, table=True):
    """入库单表"""
    
    __tablename__ = "inbound_orders"
    
    order_id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="入库单ID，主键，自动递增"
    )
    
    order_number: str = Field(
        index=True,
        unique=True,
        nullable=False,
        description="入库单号，如 RK20251003-001"
    )
    
    requisition_reference: Optional[str] = Field(
        default=None,
        nullable=True,
        description="调拨单号（可选）"
    )
    
    contract_reference: Optional[str] = Field(
        default=None,
        nullable=True,
        description="合同参考号（可选）"
    )
    
    total_quantity: int = Field(
        default=0,
        description="总数量"
    )
    
    supplier_id: int = Field(
        foreign_key="suppliers.id",
        nullable=False,
        description="供应商ID，外键关联suppliers表"
    )
    
    supplier_name: str = Field(
        nullable=False,
        description="供应商名称，冗余设置，防止ID失效"
    )
    
    creator: str = Field(
        nullable=False,
        description="创建人"
    )
    
    create_time: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="创建时间"
    )
    
    # 外键关系
    supplier: Optional["Supplier"] = Relationship(back_populates="inbound_orders")
    items: List["InboundOrderItem"] = Relationship(back_populates="order")
    
    __table_args__ = {
        "comment": "入库单表，记录器材入库信息"
    }