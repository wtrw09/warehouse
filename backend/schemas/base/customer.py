from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from schemas.common.import_schemas import BatchImportResult

# 客户查询参数
class CustomerQueryParams(BaseModel):
    search: Optional[str] = None
    customer_name: Optional[str] = None
    customer_city: Optional[str] = None
    customer_address: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_manager: Optional[str] = None
    sort_field: str = "id"
    sort_asc: bool = True
    page: int = 1
    page_size: int = 10

# 客户创建
class CustomerCreate(BaseModel):
    customer_name: str
    customer_city: Optional[str] = None
    customer_address: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_manager: Optional[str] = None
    customer_level: Optional[int] = None

# 客户更新
class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_city: Optional[str] = None
    customer_address: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_manager: Optional[str] = None
    customer_level: Optional[int] = None

# 客户响应
class CustomerResponse(BaseModel):
    id: int
    customer_name: str
    customer_city: Optional[str]
    customer_address: Optional[str]
    customer_contact: Optional[str]
    customer_manager: Optional[str]
    customer_level: Optional[int]
    create_time: datetime
    update_time: datetime
    is_delete: bool
    creator: str

# 分页结果
class CustomerPaginationResult(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    data: List[CustomerResponse]

# 批量删除
class BatchCustomerDelete(BaseModel):
    customer_ids: List[int]

# 客户统计信息
class CustomerStatistics(BaseModel):
    total_customers: int
    customers_by_city: List[dict]

# 客户批量导入结果
class CustomerBatchImportResult(BatchImportResult):
    pass  # 继承通用导入结果的所有字段