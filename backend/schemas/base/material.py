from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from schemas.common.base import PaginationResult

# 器材创建模式
class MaterialCreate(BaseModel):
    material_code: str
    material_name: str
    material_specification: Optional[str] = None
    material_desc: Optional[str] = None
    material_wdh: Optional[str] = None
    safety_stock: Optional[int] = None
    material_query_code: Optional[str] = None  # 用户可选的查询码字段
    equipment_id: Optional[int] = None

# 器材更新模式
class MaterialUpdate(BaseModel):
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    material_specification: Optional[str] = None
    material_desc: Optional[str] = None
    material_wdh: Optional[str] = None
    safety_stock: Optional[int] = None
    material_query_code: Optional[str] = None  # 用户可选的查询码字段
    major_id: Optional[int] = None
    equipment_id: Optional[int] = None

# 器材响应模式
class MaterialResponse(BaseModel):
    id: int
    material_code: str
    material_name: str
    material_specification: Optional[str]
    material_desc: Optional[str]
    material_wdh: Optional[str]
    safety_stock: Optional[int]
    material_query_code: Optional[str]
    major_id: Optional[int]
    major_name: Optional[str]
    equipment_id: Optional[int]
    equipment_name: Optional[str]
    creator: Optional[str]
    create_time: Optional[datetime]
    update_time: Optional[datetime]

    class Config:
        from_attributes = True

# 器材查询参数
class MaterialQueryParams(BaseModel):
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    material_specification: Optional[str] = None
    material_desc: Optional[str] = None
    material_wdh: Optional[str] = None
    safety_stock: Optional[int] = None
    major_id: Optional[int] = None
    major_name: Optional[str] = None
    equipment_id: Optional[int] = None
    equipment_name: Optional[str] = None
    creator: Optional[str] = None
    search: Optional[str] = None
    sort_field: Optional[str] = "id"
    sort_asc: Optional[bool] = True

# 器材分页参数
class MaterialPaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(10, ge=1, le=1000, description="每页记录数，最大100")
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    material_specification: Optional[str] = None
    material_desc: Optional[str] = None
    material_wdh: Optional[str] = None
    safety_stock: Optional[int] = None
    major_id: Optional[int] = None
    major_name: Optional[str] = None
    equipment_id: Optional[int] = None
    equipment_name: Optional[str] = None
    creator: Optional[str] = None
    search: Optional[str] = None
    sort_field: Optional[str] = "id"
    sort_asc: Optional[bool] = True

# 器材分页结果
class MaterialPaginationResult(PaginationResult):
    data: List[MaterialResponse]

# 器材列表响应
class MaterialListResponse(BaseModel):
    data: List[MaterialResponse]
    total: int

# 器材统计信息
class MaterialStatistics(BaseModel):
    total_count: int
    major_count: dict
    equipment_count: dict

# 批量删除器材
class BatchMaterialDelete(BaseModel):
    ids: List[int]

# 批量导入结果
class MaterialBatchImportResult(BaseModel):
    success_count: int
    error_count: int
    errors: List[str]

# 准专业选项响应模型
class MajorOption(BaseModel):
    id: int
    major_name: str

class MajorOptionsResponse(BaseModel):
    data: List[MajorOption]

# 装备选项响应模型
class EquipmentOption(BaseModel):
    id: int
    display_name: str

class EquipmentOptionsResponse(BaseModel):
    data: List[EquipmentOption]
    total: int

# 器材定位查询参数
class MaterialLocateParams(BaseModel):
    material_code: str = Field(..., description="器材编码(仅支持精确匹配)")
    page_size: int = Field(10, ge=1, le=100, description="每页大小,用于计算页码")

# 器材定位结果
class MaterialLocateResult(BaseModel):
    found: bool = Field(..., description="是否找到匹配器材")
    material: Optional[MaterialResponse] = Field(None, description="匹配的器材详情")
    position: Optional[int] = Field(None, description="器材在ID升序列表中的位置(从1开始)")
    target_page: Optional[int] = Field(None, description="器材所在页码")
    page_size: int = Field(10, description="用于计算页码的每页大小")
    total_before: Optional[int] = Field(None, description="该器材之前的器材数量(ID更小的器材数)")
    suggestions: List[MaterialResponse] = Field(default_factory=list, description="保留字段(始终为空列表)")