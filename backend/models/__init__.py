from sqlmodel import SQLModel, Field
from datetime import datetime

# 定义基础模型，包含通用字段
class SQLModelBase(SQLModel):
    is_delete: bool = Field(default=False, description="是否被删除")
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}, description="修改时间")

# 导入业务模型和系统初始化模型
from .account.permission import Permission
from .account.role import Role, RolePermissionLink
from .account.user import User
from .base.bin import Bin
from .base.customer import Customer
from .base.equipment import Equipment
from .base.major import Major
from .base.sub_major import SubMajor
from .base.supplier import Supplier
from .base.warehouse import Warehouse
from .material.inbound_order import InboundOrder
from .material.inbound_order_item import InboundOrderItem
from .material.inventory_batch import InventoryBatch
from .material.inventory_detail import InventoryDetail
from .material.inventory_transaction import InventoryTransaction
from .material.material import Material
from .material.outbound_order import OutboundOrder
from .material.outbound_order_item import OutboundOrderItem
from .system.material_code_level import MaterialCodeLevel
from .system.system_init import SystemInit

__all__ = [
    "SQLModelBase",
    "Permission", "Role", "User", "RolePermissionLink",
    "Bin", "Customer", "Equipment", "Major", "SubMajor", "Supplier", "Warehouse",
    "InboundOrder", "InboundOrderItem", "InventoryBatch", "InventoryDetail", "InventoryTransaction", "Material", "OutboundOrder", "OutboundOrderItem",
    "MaterialCodeLevel", "SystemInit"
]