from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List
from datetime import datetime

# 客户模型
class Customer(SQLModelBase, table=True):
    __tablename__ = "customers"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True, description="客户ID")
    customer_name: str = Field(index=True, description="单位名称")
    customer_city: Optional[str] = Field(default=None, description="所在城市")
    customer_address: Optional[str] = Field(default=None, description="地址")
    customer_contact: Optional[str] = Field(default=None, description="联系方式")
    customer_manager: Optional[str] = Field(default=None, description="负责人")
    customer_level: Optional[int] = Field(default=None, description="客户等级（保留，暂时不用）")
    creator: str = Field(description="创建人")
    is_delete: bool = Field(default=False, description="是否被删除")
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime = Field(default_factory=datetime.now, description="修改时间")
    
    # 外键关系
    outbound_orders: List["OutboundOrder"] = Relationship(back_populates="customer")