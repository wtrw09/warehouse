from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# 导入通用导入schemas
from schemas.common.import_schemas import BatchImportResult

# 供应商查询参数
class SupplierQueryParams(BaseModel):
    search: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_city: Optional[str] = None
    supplier_address: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_manager: Optional[str] = None
    sort_field: str = "id"
    sort_asc: bool = True
    page: int = 1
    page_size: int = 10

# 供应商创建
class SupplierCreate(BaseModel):
    supplier_name: str
    supplier_city: Optional[str] = None
    supplier_address: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_manager: Optional[str] = None
    supplier_level: Optional[int] = None

# 供应商更新
class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    supplier_city: Optional[str] = None
    supplier_address: Optional[str] = None
    supplier_contact: Optional[str] = None
    supplier_manager: Optional[str] = None
    supplier_level: Optional[int] = None

# 供应商响应
class SupplierResponse(BaseModel):
    id: int
    supplier_name: str
    supplier_city: Optional[str]
    supplier_address: Optional[str]
    supplier_contact: Optional[str]
    supplier_manager: Optional[str]
    supplier_level: Optional[int]
    create_time: datetime
    update_time: datetime
    is_delete: bool
    creator: str

# 分页结果
class SupplierPaginationResult(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[SupplierResponse]

# 批量删除
class BatchSupplierDelete(BaseModel):
    supplier_ids: List[int]

# 供应商统计信息
class SupplierStatistics(BaseModel):
    total_suppliers: int

# 供应商批量删除结果
class SupplierBatchDeleteResult(BaseModel):
    success_count: int
    failed_count: int
    failed_suppliers: List[int]
    message: str

# 供应商批量导入结果
class SupplierBatchImportResult(BatchImportResult):
    pass  # 继承通用导入结果的所有字段