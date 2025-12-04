# 器材管理相关路由
from .inventory_transaction_routes import inventory_transactions_router
from .inventory_detail_routes import router as inventory_details_router

__all__ = [
    "inventory_transactions_router",
    "inventory_details_router"
]