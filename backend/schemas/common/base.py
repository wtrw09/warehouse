# 基础schemas模块 
from pydantic import BaseModel, Field
from typing import Optional

class PaginationParams(BaseModel):
    """分页查询参数基类"""
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(10, ge=1, le=1000, description="每页记录数，最大100")
    search: Optional[str] = Field(None, description="搜索关键词")
    sort_field: Optional[str] = Field(None, description="排序字段")
    sort_asc: bool = Field(True, description="是否升序排序")

class PaginationResult(BaseModel):
    """分页查询结果基类"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")