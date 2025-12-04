from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class OutboundOrderItemCreate(BaseModel):
    """出库单明细创建模型"""
    batch_id: int = Field(..., description="批次ID")
    quantity: int = Field(..., ge=1, description="数量")


class OutboundOrderCreate(BaseModel):
    """出库单创建模型"""
    order_number: str = Field(..., description="出库单号")
    requisition_reference: Optional[str] = Field(None, description="调拨单号")
    customer_id: int = Field(..., description="客户ID")
    items: List[OutboundOrderItemCreate] = Field(..., description="出库明细列表")


class OutboundOrderItemResponse(BaseModel):
    """出库单明细响应模型"""
    item_id: int = Field(..., description="明细项ID")
    material_id: int = Field(..., description="器材ID")
    material_code: str = Field(..., description="器材编码")
    material_name: str = Field(..., description="器材名称")
    material_specification: str = Field(..., description="品牌型号")
    quantity: int = Field(..., description="数量")
    unit_price: float = Field(..., description="出库单价")
    unit: str = Field(..., description="计量单位")
    batch_number: str = Field(..., description="批次号")
    batch_id: int = Field(..., description="批次ID")
    bin_id: Optional[int] = Field(None, description="货位ID")
    bin_name: Optional[str] = Field(None, description="货位名称")
    equipment_name: Optional[str] = Field(None, description="装备名称")


class OutboundOrderResponse(BaseModel):
    """出库单响应模型"""
    order_id: int = Field(..., description="出库单ID")
    order_number: str = Field(..., description="出库单号")
    requisition_reference: Optional[str] = Field(None, description="调拨单号")
    customer_id: int = Field(..., description="客户ID")
    customer_name: str = Field(..., description="客户名称")
    total_quantity: int = Field(..., description="总数量")
    creator: str = Field(..., description="创建人")
    create_time: datetime = Field(..., description="创建时间")


class OutboundOrderDetailResponse(BaseModel):
    """出库单详情响应模型"""
    order: OutboundOrderResponse = Field(..., description="出库单基本信息")
    items: List[OutboundOrderItemResponse] = Field(..., description="出库明细列表")


class OutboundOrderUpdate(BaseModel):
    """出库单更新模型"""
    requisition_reference: Optional[str] = Field(None, description="调拨单号")
    customer_id: Optional[int] = Field(None, description="客户ID")


class OutboundOrderQueryParams(BaseModel):
    """出库单查询参数模型"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="关键词搜索（出库单号、客户名称、调拨单号）")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    customer_id: Optional[int] = Field(None, description="客户ID")
    sort_by: str = Field("create_time", description="排序字段")
    sort_order: str = Field("desc", description="排序方向（asc/desc）")


class OutboundOrderPaginationResult(BaseModel):
    """出库单分页结果模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    data: List[OutboundOrderResponse] = Field(..., description="出库单列表")


class OutboundOrderListResponse(BaseModel):
    """出库单列表响应模型（不分页）"""
    total: int = Field(..., description="总记录数")
    data: List[OutboundOrderResponse] = Field(..., description="出库单列表")


class OutboundOrderStatistics(BaseModel):
    """出库单统计信息模型"""
    total_orders: int = Field(..., description="总出库单数")
    total_quantity: int = Field(..., description="总出库数量")
    total_amount: float = Field(..., description="总出库金额")
    customer_stats: List[dict] = Field(..., description="按客户统计")
    date_stats: List[dict] = Field(..., description="按日期统计")


class OrderNumberUpdate(BaseModel):
    """出库单号更新模型"""
    order_number: str = Field(..., description="新出库单号")


class TransferNumberUpdate(BaseModel):
    """调拨单号更新模型"""
    requisition_reference: str = Field(..., description="新调拨单号")


class CustomerUpdate(BaseModel):
    """客户更新模型"""
    customer_id: int = Field(..., description="新客户ID")


class CreateTimeUpdate(BaseModel):
    """创建时间更新模型"""
    create_time: datetime = Field(..., description="新创建时间")


class OutboundOrderItemUpdate(BaseModel):
    """出库单明细更新模型"""
    batch_id: Optional[int] = Field(None, description="批次ID")
    quantity: Optional[int] = Field(None, ge=1, description="数量")


class OutboundOrderItemBatchDelete(BaseModel):
    """出库单明细批量删除模型"""
    item_ids: List[int] = Field(..., min_items=1, description="要删除的明细项ID列表")


class BatchDeleteResponse(BaseModel):
    """批量删除响应模型"""
    success: bool = Field(..., description="删除是否成功")
    deleted_count: int = Field(..., description="成功删除的明细项数量")
    message: str = Field(..., description="操作结果消息")