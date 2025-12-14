from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class InventoryDetailResponse(BaseModel):
    """库存器材明细响应模型"""
    detail_id: int = Field(..., description="明细ID")
    material_id: int = Field(..., description="器材ID")
    material_code: str = Field(..., description="器材编码")
    material_name: str = Field(..., description="器材名称")
    material_specification: Optional[str] = Field(None, description="器材规格型号")
    batch_id: Optional[int] = Field(None, description="批次ID")
    batch_number: str = Field(..., description="批次编号")
    quantity: int = Field(..., description="库存数量")
    unit: str = Field(..., description="计量单位")
    unit_price: float = Field(..., description="单价")
    supplier_name: Optional[str] = Field(None, description="供应商名称")
    production_date: Optional[date] = Field(None, description="生产日期")
    inbound_date: Optional[date] = Field(None, description="入库日期")
    major_id: Optional[int] = Field(None, description="专业ID")
    major_name: Optional[str] = Field(None, description="专业名称")
    equipment_id: Optional[int] = Field(None, description="装备ID")
    equipment_name: Optional[str] = Field(None, description="装备名称")
    equipment_specification: Optional[str] = Field(None, description="装备型号")
    bin_name: Optional[str] = Field(None, description="货位名称")
    warehouse_name: Optional[str] = Field(None, description="仓库名称")
    update_time: datetime = Field(..., description="更新时间")
    last_updated: date = Field(..., description="上次更新日期")


class PaginatedInventoryDetailsResponse(BaseModel):
    """库存器材明细分页结果模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    data: List[InventoryDetailResponse] = Field(..., description="库存器材明细列表")


class InventoryDetailsListResponse(BaseModel):
    """库存器材明细列表响应模型（不分页）"""
    total: int = Field(..., description="总记录数")
    data: List[InventoryDetailResponse] = Field(..., description="库存器材明细列表")





class MajorOptionsResponse(BaseModel):
    """专业选项响应模型"""
    data: List[Dict[str, Any]] = Field(..., description="专业选项列表，包含id和major_name")
    total_count: int = Field(..., description="去重后的专业数量")


class EquipmentIdsResponse(BaseModel):
    """装备ID集合响应模型"""
    equipment_ids: List[int] = Field(..., description="装备ID集合")
    total_count: int = Field(..., description="去重后的装备数量")


class EquipmentOption(BaseModel):
    """装备选项响应模型"""
    id: int = Field(..., description="装备ID")
    display_name: str = Field(..., description="显示名称")


class EquipmentOptionsResponse(BaseModel):
    """装备选项集合响应模型"""
    data: List[EquipmentOption] = Field(..., description="装备选项列表")
    total: int = Field(..., description="总记录数")


class InventoryDetailsBaseQueryParams(BaseModel):
    """库存器材明细基础查询参数模型"""
    keyword: Optional[str] = Field(None, description="关键词搜索（器材编码、器材名称、规格型号、批次编号、专业名称、装备名称、装备型号）")
    major_id: Optional[List[int]] = Field(None, description="专业ID数组，支持多选")
    equipment_id: Optional[List[int]] = Field(None, description="装备ID数组，支持多选")
    warehouse_id: Optional[int] = Field(None, description="仓库ID")
    bin_id: Optional[int] = Field(None, description="货位ID")
    quantity_filter: Optional[str] = Field(None, description="库存数量筛选：'has_stock'（有库存），'no_stock'（无库存），None（全部）")
    sort_by: str = Field("material_code", description="排序字段")
    sort_order: str = Field("asc", description="排序方向（asc/desc）")


class InventoryDetailsQueryParams(InventoryDetailsBaseQueryParams):
    """库存器材明细查询参数模型（分页）"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")


class InventoryDetailsAllQueryParams(InventoryDetailsBaseQueryParams):
    """库存器材明细查询参数模型（不分页）"""
    pass