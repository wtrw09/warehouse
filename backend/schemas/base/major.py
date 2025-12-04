from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# 专业基础模型
class MajorBase(BaseModel):
    major_name: str = Field(..., min_length=1, max_length=100, description="专业名称")

# 专业查询参数模型
class MajorQueryParams(BaseModel):
    search: Optional[str] = Field(None, description="搜索关键词，支持多关键词空格分隔")

# 创建专业模型
class MajorCreate(MajorBase):
    major_code: Optional[str] = Field(None, min_length=0, max_length=2, description="专业代码")

# 更新专业模型
class MajorUpdate(BaseModel):
    major_name: Optional[str] = Field(None, min_length=1, max_length=100, description="专业名称")
    major_code: Optional[str] = Field(None, min_length=0, max_length=2, description="专业代码")

# 专业响应模型（不包含is_delete字段）
class MajorResponse(MajorBase):
    id: int = Field(..., description="专业ID")
    major_code: str = Field(..., min_length=2, max_length=2, description="专业代码")
    creator: Optional[str] = Field(None, min_length=1, max_length=50, description="创建人")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="修改时间")

    class Config:
        from_attributes = True

# 批量删除专业模型
class BatchMajorDelete(BaseModel):
    major_ids: List[int] = Field(..., description="专业ID列表")

# 专业列表响应模型（不分页）
class MajorListResponse(BaseModel):
    data: List[MajorResponse] = Field(..., description="专业数据列表")
    total: int = Field(..., description="总记录数")