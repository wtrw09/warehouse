from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from schemas.common import PaginationParams

# 货位基础模型
class BinBase(BaseModel):
    bin_name: str = Field(..., min_length=1, max_length=100, description="货位名称或者位置或说明")
    bin_size: Optional[str] = Field(None, max_length=50, description="货位规格")
    bin_property: Optional[str] = Field(None, max_length=100, description="货位属性")
    warehouse_id: int = Field(..., description="所属仓库ID")
    empty_label: bool = Field(True, description="是否为空")
    bar_code: Optional[str] = Field(None, max_length=100, description="货位码，二维码")

# 创建货位模型
class BinCreate(BinBase):
    pass

# 更新货位模型
class BinUpdate(BaseModel):
    bin_name: Optional[str] = Field(None, min_length=1, max_length=100, description="货位名称或者位置或说明")
    bin_size: Optional[str] = Field(None, max_length=50, description="货位规格")
    bin_property: Optional[str] = Field(None, max_length=100, description="货位属性")
    warehouse_id: Optional[int] = Field(None, description="所属仓库ID")
    empty_label: Optional[bool] = Field(None, description="是否为空")
    bar_code: Optional[str] = Field(None, max_length=100, description="货位码，二维码")

# 货位响应模型
class BinResponse(BinBase):
    id: int = Field(..., description="货位ID")
    warehouse_name: str = Field(..., min_length=1, max_length=100, description="所属仓库名称")
    creator: str = Field(..., min_length=1, max_length=50, description="创建人")
    create_time: datetime = Field(..., description="创建时间")
    update_time: datetime = Field(..., description="修改时间")

    class Config:
        from_attributes = True

# 货位查询参数模型
class BinQueryParams(PaginationParams):
    bin_name: Optional[str] = Field(None, description="按货位名筛选")
    warehouse_id: Optional[int] = Field(None, description="按仓库ID筛选")
    warehouse_name: Optional[str] = Field(None, description="按仓库名筛选")
    bin_property: Optional[str] = Field(None, description="按货位属性筛选")
    empty_label: Optional[bool] = Field(None, description="按是否为空筛选")
    search: Optional[str] = Field(None, description="通用搜索关键词，支持多关键词以空格分隔")

# 货位分页结果模型
class BinPaginationResult(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")
    data: List[BinResponse] = Field(..., description="货位数据列表")

# 批量删除货位模型
class BatchBinDelete(BaseModel):
    bin_ids: List[int] = Field(..., description="货位ID列表")

# 货位统计模型
class BinStatistics(BaseModel):
    total_bins: int = Field(..., description="总货位数（不包含已删除）")
    bins_by_warehouse: List[dict] = Field(..., description="按仓库分组的货位统计")
    bins_by_property: List[dict] = Field(..., description="按货位属性分组的统计")

# 货位属性列表响应模型
class BinPropertiesResponse(BaseModel):
    properties: List[str] = Field(..., description="所有货位属性列表（去重）")