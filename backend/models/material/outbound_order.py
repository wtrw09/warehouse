from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List
from datetime import datetime


class OutboundOrder(SQLModelBase, table=True):
    """出库单表"""
    
    __tablename__ = "outbound_orders"
    
    order_id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="出库单ID，主键，自动递增"
    )
    
    order_number: str = Field(
        index=True,
        unique=True,
        nullable=False,
        description="出库单号，如 CK20251003-001"
    )
    
    requisition_reference: Optional[str] = Field(
        default=None,
        nullable=True,
        description="调拨单号（可选）"
    )
    
    total_quantity: int = Field(
        default=0,
        nullable=False,
        description="总数量"
    )
    
    customer_id: int = Field(
        foreign_key="customers.id",
        nullable=False,
        description="客户ID，外键关联customers表"
    )
    
    customer_name: str = Field(
        nullable=False,
        description="客户名称，冗余设置，防止ID失效"
    )
    
    creator: str = Field(
        nullable=False,
        description="操作人"
    )
    
    create_time: datetime = Field(
        default_factory=datetime.now,
        nullable=False,
        description="创建时间"
    )
    
    # 外键关系
    customer: Optional["Customer"] = Relationship(back_populates="outbound_orders")
    items: List["OutboundOrderItem"] = Relationship(back_populates="order", sa_relationship_kwargs={"lazy": "selectin"})
    
    __table_args__ = {
        "comment": "出库单表，记录器材出库信息"
    }