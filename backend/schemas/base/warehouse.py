from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from schemas.common import PaginationParams
from schemas.common.import_schemas import ImportError

# 仓库基础模型
class WarehouseBase(BaseModel):
    warehouse_name: str = Field(..., min_length=1, max_length=100, description="仓库名")
    warehouse_city: Optional[str] = Field(None, max_length=50, description="所在城市")
    warehouse_address: Optional[str] = Field(None, max_length=200, description="地址")
    warehouse_contact: Optional[str] = Field(None, max_length=50, description="联系方式")
    warehouse_manager: Optional[str] = Field(None, max_length=50, description="负责人")

# 创建仓库模型
class WarehouseCreate(WarehouseBase):
    pass

# 更新仓库模型
class WarehouseUpdate(BaseModel):
    warehouse_name: Optional[str] = Field(None, min_length=1, max_length=100, description="仓库名")
    warehouse_city: Optional[str] = Field(None, max_length=50, description="所在城市")
    warehouse_address: Optional[str] = Field(None, max_length=200, description="地址")
    warehouse_contact: Optional[str] = Field(None, max_length=50, description="联系方式")
    warehouse_manager: Optional[str] = Field(None, max_length=50, description="负责人")

# 仓库响应模型
class WarehouseResponse(WarehouseBase):
    id: int = Field(..., description="仓库ID")
    creator: str = Field(..., min_length=1, max_length=50, description="创建人")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="修改时间")

    class Config:
        from_attributes = True

# 仓库查询参数模型
class WarehouseQueryParams(PaginationParams):
    warehouse_name: Optional[str] = Field(None, description="按仓库名筛选")
    warehouse_city: Optional[str] = Field(None, description="按城市筛选")
    warehouse_manager: Optional[str] = Field(None, description="按负责人筛选")
    search: Optional[str] = Field(None, description="通用搜索关键词，支持多关键词以空格分隔")

# 仓库分页结果模型
class WarehousePaginationResult(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")
    data: List[WarehouseResponse] = Field(..., description="仓库数据列表")

# 批量删除仓库模型
class BatchWarehouseDelete(BaseModel):
    warehouse_ids: List[int] = Field(..., description="仓库ID列表")

# 仓库统计模型
class WarehouseStatistics(BaseModel):
    total_warehouses: int = Field(..., description="总仓库数（不包含已删除）")
    warehouses_by_city: List[dict] = Field(..., description="按城市分组的仓库统计")

# 仓库批量导入结果
class WarehouseBatchImportResult(BaseModel):
    total_count: int = Field(..., description="总记录数")
    success_count: int = Field(..., description="成功导入数")
    error_count: int = Field(..., description="导入失败数")
    errors: List[ImportError] = Field(..., description="错误详情")
    import_time: datetime = Field(..., description="导入时间")
    has_error_file: bool = Field(default=False, description="是否有错误文件")
    error_file_name: Optional[str] = Field(default=None, description="错误文件名")

    class Config:
        from_attributes = True