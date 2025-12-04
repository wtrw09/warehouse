from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# 二级专业基础模型
class SubMajorBase(BaseModel):
    sub_major_name: str = Field(..., min_length=1, max_length=100, description="二级专业名称")
    sub_major_code: str = Field(..., max_length=50, description="二级专业代码")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    major_id: Optional[int] = Field(None, description="所属一级专业ID")
    major_name: Optional[str] = Field(None, max_length=100, description="一级专业名称")
    reserved: Optional[str] = Field(None, max_length=100, description="保留字段")

# 二级专业查询参数模型
class SubMajorQueryParams(BaseModel):
    search: Optional[str] = Field(None, description="搜索关键词，支持多关键词空格分隔")
    major_id: Optional[int] = Field(None, description="按一级专业ID筛选")

# 创建二级专业模型
class SubMajorCreate(BaseModel):
    sub_major_name: str = Field(..., min_length=1, max_length=100, description="二级专业名称")
    sub_major_code: Optional[str] = Field(None, max_length=50, description="二级专业代码")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    major_id: Optional[int] = Field(None, description="所属一级专业ID")

# 更新二级专业模型
class SubMajorUpdate(BaseModel):
    sub_major_name: Optional[str] = Field(None, min_length=1, max_length=100, description="二级专业名称")
    sub_major_code: Optional[str] = Field(None, max_length=50, description="二级专业代码")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    major_id: Optional[int] = Field(None, description="所属一级专业ID")

# 二级专业响应模型（不包含is_delete字段）
class SubMajorResponse(SubMajorBase):
    id: int = Field(..., description="二级专业ID")
    creator: Optional[str] = Field(None, min_length=1, max_length=50, description="创建人")
    create_time: Optional[datetime] = Field(None, description="创建时间")
    update_time: Optional[datetime] = Field(None, description="修改时间")

    class Config:
        from_attributes = True

# 批量删除二级专业模型
class BatchSubMajorDelete(BaseModel):
    sub_major_ids: List[int] = Field(..., description="二级专业ID列表")

# 二级专业列表响应模型（不分页）
class SubMajorListResponse(BaseModel):
    data: List[SubMajorResponse] = Field(..., description="二级专业数据列表")
    total: int = Field(..., description="总记录数")

# 二级专业统计信息模型
class SubMajorStatistics(BaseModel):
    total_count: int = Field(..., description="总数量")
    major_distribution: dict = Field(..., description="按一级专业分布统计")

# 添加二级专业描述模型
class SubMajorAddDescription(BaseModel):
    """添加二级专业描述字段模式"""
    sub_major_id: int = Field(..., description="二级专业ID")
    description: str = Field(..., description="要添加的描述内容")

class SubMajorAddDescriptionResult(BaseModel):
    """添加二级专业描述字段结果模式"""
    message: str = Field(..., description="操作结果消息")
    sub_major_id: int = Field(..., description="二级专业ID")
    new_description_list: List[str] = Field(..., description="更新后的描述列表")