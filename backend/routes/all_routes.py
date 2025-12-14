from fastapi import APIRouter, Depends, HTTPException, Security
from database import get_db
# 导入角色管理路由
from routes.account.role_routes import role_router
# 导入用户认证路由
from routes.account.auth_routes import auth_router
# 导入用户管理路由
from routes.account.user_routes import user_router
# 导入权限管理路由
from routes.account.permission_routes import permission_router
# 导入配置管理路由
from routes.account.config_routes import config_router
# 导入仓库管理路由
from routes.base.warehouse_routes import warehouse_router
# 导入客户管理路由
from routes.base.customer_routes import customer_router
# 导入供应商管理路由
from routes.base.supplier_routes import supplier_router
# 导入货位管理路由
from routes.base.bin_routes import router as bin_router
# 导入专业管理路由
from routes.base.major_routes import major_router
# 导入装备管理路由
from routes.base.equipment_routes import equipment_router
# 导入器材管理路由
from routes.base.material_routes import material_router
# 导入器材编码分类层级管理路由
from routes.system.material_code_level_routes import material_code_level_router
# 导入系统配置管理路由
from routes.system.system_config_routes import system_config_router
# 导入二级专业管理路由
from routes.base.sub_major_routes import sub_major_router
# 导入库存变更流水管理路由
from routes.material.inventory_transaction_routes import inventory_transactions_router
# 导入入库单管理路由
from routes.material.inbound_order_routes import inbound_orders_router
# 导入出库单管理路由
from routes.material.outbound_order_routes import outbound_orders_router
# 导入库存器材明细查询路由
from routes.material.inventory_detail_routes import inventory_details_router
# 导入器材分类账页生成路由
from routes.material.material_ledger_routes import material_ledger_router
# 导入系统状态管理路由
from routes.system.system_status_routes import system_status_router

# 导入手动备份路由
from routes.system.backup_routes import backup_router
# 导入主页仪表板路由
from routes.system.dashboard_routes import dashboard_router

router = APIRouter()

# 包含角色管理路由
router.include_router(role_router)
# 包含用户认证路由
router.include_router(auth_router)
# 包含用户管理路由
router.include_router(user_router)
# 包含权限管理路由
router.include_router(permission_router)
# 包含配置管理路由
router.include_router(config_router)
# 包含仓库管理路由
router.include_router(warehouse_router)
# 包含客户管理路由
router.include_router(customer_router)
# 包含供应商管理路由
router.include_router(supplier_router)
# 包含货位管理路由
router.include_router(bin_router)
# 包含专业管理路由
router.include_router(major_router)
# 包含装备管理路由
router.include_router(equipment_router)
# 包含器材管理路由
router.include_router(material_router)
# 包含器材编码分类层级管理路由
router.include_router(material_code_level_router)
# 包含系统配置管理路由
router.include_router(system_config_router)
# 包含二级专业管理路由
router.include_router(sub_major_router)
# 包含库存变更流水管理路由
router.include_router(inventory_transactions_router)
# 包含入库单管理路由
router.include_router(inbound_orders_router)
# 包含出库单管理路由
router.include_router(outbound_orders_router)
# 包含库存器材明细查询路由
router.include_router(inventory_details_router)
# 包含器材分类账页生成路由
router.include_router(material_ledger_router)
# 包含系统状态管理路由
router.include_router(system_status_router)

# 包含手动备份路由
router.include_router(backup_router)
# 包含主页仪表板路由
router.include_router(dashboard_router)

