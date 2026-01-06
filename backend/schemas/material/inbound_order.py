from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


class InboundOrderItemCreate(BaseModel):
    """入库单明细创建模型"""
    material_id: int = Field(..., description="器材ID")
    batch_number: str = Field(..., description="批次号")
    quantity: int = Field(..., ge=1, description="数量")
    unit_price: float = Field(..., ge=0, description="采购单价")
    unit: str = Field(..., description="计量单位")
    bin_id: Optional[int] = Field(None, description="货位ID")
    production_date: Optional[date] = Field(None, description="生产日期")


class InboundOrderCreate(BaseModel):
    """入库单创建模型"""
    order_number: str = Field(..., description="入库单号")
    requisition_reference: Optional[str] = Field(None, description="调拨单号")
    contract_reference: Optional[str] = Field(None, description="合同参考号")
    supplier_id: int = Field(..., description="供应商ID")
    inbound_date: date = Field(..., description="入库日期")
    items: List[InboundOrderItemCreate] = Field(..., description="入库明细列表")


class InboundOrderItemResponse(BaseModel):
    """入库单明细响应模型"""
    item_id: int = Field(..., description="明细项ID")
    material_id: int = Field(..., description="器材ID")
    material_code: str = Field(..., description="器材编码")
    material_name: str = Field(..., description="器材名称")
    material_specification: str = Field(..., description="品牌型号")
    quantity: int = Field(..., description="数量")
    unit_price: float = Field(..., description="采购单价")
    unit: str = Field(..., description="计量单位")
    batch_number: str = Field(..., description="批次号")
    bin_id: Optional[int] = Field(None, description="货位ID")
    bin_name: Optional[str] = Field(None, description="货位名称")
    equipment_name: Optional[str] = Field(None, description="装备名称")
    production_date: Optional[date] = Field(None, description="生产日期")


class InboundOrderResponse(BaseModel):
    """入库单响应模型"""
    order_id: int = Field(..., description="入库单ID")
    order_number: str = Field(..., description="入库单号")
    requisition_reference: Optional[str] = Field(None, description="调拨单号")
    contract_reference: Optional[str] = Field(None, description="合同参考号")
    supplier_id: int = Field(..., description="供应商ID")
    supplier_name: str = Field(..., description="供应商名称")
    total_quantity: int = Field(..., description="总数量")
    creator: str = Field(..., description="创建人")
    create_time: datetime = Field(..., description="创建时间")
    inbound_date: date = Field(..., description="入库日期")


class InboundOrderDetailResponse(BaseModel):
    """入库单详情响应模型"""
    order: InboundOrderResponse = Field(..., description="入库单基本信息")
    items: List[InboundOrderItemResponse] = Field(..., description="入库明细列表")


class InboundOrderUpdate(BaseModel):
    """入库单更新模型"""
    requisition_reference: Optional[str] = Field(None, description="调拨单号")
    contract_reference: Optional[str] = Field(None, description="合同参考号")
    supplier_id: Optional[int] = Field(None, description="供应商ID")
    inbound_date: Optional[date] = Field(None, description="入库日期")


class InboundOrderQueryParams(BaseModel):
    """入库单查询参数模型"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    keyword: Optional[str] = Field(None, description="关键词搜索（入库单号、供应商名称、调拨单号、合同号）")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    supplier_id: Optional[int] = Field(None, description="供应商ID")
    sort_by: str = Field("create_time", description="排序字段")
    sort_order: str = Field("desc", description="排序方向（asc/desc）")


class InboundOrderPaginationResult(BaseModel):
    """入库单分页结果模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    data: List[InboundOrderResponse] = Field(..., description="入库单列表")


class InboundOrderListResponse(BaseModel):
    """入库单列表响应模型（不分页）"""
    total: int = Field(..., description="总记录数")
    data: List[InboundOrderResponse] = Field(..., description="入库单列表")


class InboundOrderStatistics(BaseModel):
    """入库单统计信息模型"""
    total_orders: int = Field(..., description="总入库单数")
    total_quantity: int = Field(..., description="总入库数量")
    total_amount: float = Field(..., description="总入库金额")
    supplier_stats: List[dict] = Field(..., description="按供应商统计")
    date_stats: List[dict] = Field(..., description="按日期统计")


class OrderNumberUpdate(BaseModel):
    """入库单号更新模型"""
    order_number: str = Field(..., description="新入库单号")


class TransferNumberUpdate(BaseModel):
    """调拨单号更新模型"""
    requisition_reference: str = Field(..., description="新调拨单号")


class SupplierUpdate(BaseModel):
    """供应商更新模型"""
    supplier_id: int = Field(..., description="新供应商ID")


class ContractNumberUpdate(BaseModel):
    """合同号更新模型"""
    contract_reference: str = Field(..., description="新合同参考号")


class InboundCreateTimeUpdate(BaseModel):
    """入库单创建时间更新模型"""
    create_time: datetime = Field(..., description="创建时间")


class InboundOrderItemUpdate(BaseModel):
    """入库单明细更新模型"""
    material_id: Optional[int] = Field(None, description="器材ID")
    batch_number: Optional[str] = Field(None, description="批次号")
    quantity: Optional[int] = Field(None, ge=1, description="数量")
    unit_price: Optional[float] = Field(None, ge=0, description="采购单价")
    unit: Optional[str] = Field(None, description="计量单位")
    bin_id: Optional[int] = Field(None, description="货位ID")
    production_date: Optional[date] = Field(None, description="生产日期")