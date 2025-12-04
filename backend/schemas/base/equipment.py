from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from schemas.common import PaginationParams

# 装备基础模型
class EquipmentBase(BaseModel):
    equipment_name: str = Field(..., min_length=1, max_length=100, description="装备名称")
    specification: Optional[str] = Field(None, max_length=100, description="规格型号")

# 装备查询参数模型
class EquipmentQueryParams(BaseModel):
    equipment_name: Optional[str] = Field(None, description="装备名称")
    specification: Optional[str] = Field(None, description="规格型号")
    major_id: Optional[int] = Field(None, description="所属专业ID")
    creator: Optional[str] = Field(None, description="创建人")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    sort_field: Optional[str] = Field(None, description="排序字段")
    sort_asc: bool = Field(True, description="是否升序")

# 装备分页查询参数模型
class EquipmentPaginationParams(PaginationParams):
    equipment_name: Optional[str] = Field(None, description="装备名称")
    specification: Optional[str] = Field(None, description="规格型号")
    major_id: Optional[int] = Field(None, description="所属专业ID")
    major_name: Optional[str] = Field(None, description="专业名称")
    creator: Optional[str] = Field(None, description="创建人")
    sort_field: Optional[str] = Field(None, description="排序字段")
    sort_asc: bool = Field(True, description="是否升序")
    search: Optional[str] = Field(None, description="通用搜索关键词，支持多关键词以空格分隔")

# 创建装备模型
class EquipmentCreate(EquipmentBase):
    major_id: Optional[int] = Field(None, description="所属专业ID")

# 更新装备模型
class EquipmentUpdate(BaseModel):
    equipment_name: Optional[str] = Field(None, min_length=1, max_length=100, description="装备名称")
    specification: Optional[str] = Field(None, max_length=100, description="规格型号")
    major_id: Optional[int] = Field(None, description="所属专业ID")

# 装备响应模型（不包含is_delete字段）
class EquipmentResponse(EquipmentBase):
    id: int = Field(..., description="装备ID")
    major_id: Optional[int] = Field(None, description="所属专业ID")
    major_name: Optional[str] = Field(None, description="专业名称")
    creator: Optional[str] = Field(None, min_length=1, max_length=50, description="创建人")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="修改时间")

    class Config:
        from_attributes = True

# 批量删除装备模型
class BatchEquipmentDelete(BaseModel):
    equipment_ids: List[int] = Field(..., description="装备ID列表")

# 装备列表响应模型（不分页）
class EquipmentListResponse(BaseModel):
    data: List[EquipmentResponse] = Field(..., description="装备数据列表")
    total: int = Field(..., description="总记录数")

# 装备分页结果模型
class EquipmentPaginationResult(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")
    data: List[EquipmentResponse] = Field(..., description="装备数据列表")

# 装备统计模型
class EquipmentStatistics(BaseModel):
    total_count: int = Field(..., description="总装备数量")
    major_count: dict = Field(..., description="按专业分类统计")