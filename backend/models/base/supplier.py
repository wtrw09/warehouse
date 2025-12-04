from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List
from datetime import datetime

# 供应商模型
class Supplier(SQLModelBase, table=True):
    __tablename__ = "suppliers"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True, description="供应商ID")
    supplier_name: str = Field(index=True, description="供应商名称")
    supplier_city: Optional[str] = Field(default=None, description="所在城市")
    supplier_address: Optional[str] = Field(default=None, description="地址")
    supplier_manager: Optional[str] = Field(default=None, description="负责人")
    supplier_contact: Optional[str] = Field(default=None, description="联系方式")
    supplier_level: Optional[int] = Field(default=None, description="供应商等级（保留，暂时不用）")
    creator: str = Field(description="创建人")
    is_delete: bool = Field(default=False, description="是否被删除")
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime = Field(default_factory=datetime.now, description="修改时间")
    
    # 外键关系
    inventory_batches: List["InventoryBatch"] = Relationship(back_populates="supplier")
    inbound_orders: List["InboundOrder"] = Relationship(back_populates="supplier")