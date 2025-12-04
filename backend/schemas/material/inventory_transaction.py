from pydantic import BaseModel
from typing import Optional, List
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


class InventoryTransactionCreate(BaseModel):
    """创建库存变更流水记录"""
    material_id: int
    batch_id: int
    change_type: ChangeType
    quantity_change: int
    quantity_before: int
    quantity_after: int
    reference_type: ReferenceType
    reference_id: Optional[int] = None
    creator: str


class InventoryTransactionUpdate(BaseModel):
    """更新库存变更流水记录"""
    material_id: Optional[int] = None
    batch_id: Optional[int] = None
    change_type: Optional[ChangeType] = None
    quantity_change: Optional[int] = None
    quantity_before: Optional[int] = None
    quantity_after: Optional[int] = None
    reference_type: Optional[ReferenceType] = None
    reference_id: Optional[int] = None
    creator: Optional[str] = None


class InventoryTransactionResponse(BaseModel):
    """库存变更流水记录响应"""
    transaction_id: int
    material_id: int
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    material_specification: Optional[str] = None
    batch_id: int
    batch_number: Optional[str] = None
    change_type: ChangeType
    quantity_change: int
    quantity_before: int
    quantity_after: int
    reference_number: Optional[str] = None
    creator: str
    transaction_time: datetime

    class Config:
        from_attributes = True


class InventoryTransactionQueryParams(BaseModel):
    """库存变更流水查询参数"""
    page: int = 1
    page_size: int = 10
    keyword: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    material_id: Optional[int] = None
    batch_id: Optional[int] = None
    change_type: Optional[ChangeType] = None
    reference_type: Optional[ReferenceType] = None
    sort_by: str = "transaction_time"
    sort_order: str = "desc"


class InventoryTransactionPaginationResult(BaseModel):
    """库存变更流水分页结果"""
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[InventoryTransactionResponse]


class InventoryTransactionListResponse(BaseModel):
    """库存变更流水列表响应（不分页）"""
    data: List[InventoryTransactionResponse]


class InventoryTransactionStatistics(BaseModel):
    """库存变更统计信息"""
    total_in: int = 0
    total_out: int = 0
    total_adjust: int = 0
    net_change: int = 0
    transaction_count: int = 0


class InventoryTransactionDetailResponse(BaseModel):
    """库存变更流水详情响应"""
    transaction: InventoryTransactionResponse