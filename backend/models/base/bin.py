from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List
from models.base.warehouse import Warehouse

# 货位模型
class Bin(SQLModelBase, table=True):
    __tablename__ = "bins"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True, description="货位ID")
    bin_name: str = Field(index=True, description="货位名称或者位置或说明")
    bin_size: Optional[str] = Field(default=None, description="货位规格")
    bin_property: Optional[str] = Field(default=None, description="货位属性")
    warehouse_id: int = Field(foreign_key="warehouses.id", description="所属仓库ID")
    warehouse_name: str = Field(description="所属仓库名称")
    empty_label: bool = Field(default=True, description="是否为空")
    bar_code: Optional[str] = Field(default=None, description="货位码，二维码")
    creator: str = Field(description="创建人")
    
    # 与仓库的关系
    warehouse: Optional[Warehouse] = Relationship(back_populates="bins")
    
    # 与入库单明细的关系
    inbound_order_items: List["InboundOrderItem"] = Relationship(back_populates="bin")
    # 与出库单明细的关系
    outbound_order_items: List["OutboundOrderItem"] = Relationship(back_populates="bin")
    # 与库存明细的关系
    inventory_details: List["InventoryDetail"] = Relationship(back_populates="bin")

# 在Warehouse模型中添加反向关系
# 需要更新warehouse.py文件，添加：
# bins: List["Bin"] = Relationship(back_populates="warehouse")