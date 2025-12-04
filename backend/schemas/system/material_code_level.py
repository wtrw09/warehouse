from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MaterialCodeLevelBase(BaseModel):
    """基础模式"""
    level_code: str = Field(..., max_length=50, description="层级路径码，如'1', '1-1', '1-2-3'")
    level_name: str = Field(..., max_length=100, description="层级名称")
    code: str = Field(..., max_length=10, description="编码中显示的代码")
    description: Optional[str] = Field(None, description="说明")

class MaterialCodeLevelCreate(MaterialCodeLevelBase):
    """创建模式"""
    pass

class MaterialCodeLevelUpdate(BaseModel):
    """更新模式"""
    level_code: Optional[str] = Field(None, max_length=50, description="层级路径码")
    level_name: Optional[str] = Field(None, max_length=100, description="层级名称")
    code: Optional[str] = Field(None, max_length=10, description="编码中显示的代码")
    description: Optional[str] = Field(None, description="说明")

class MaterialCodeLevelResponse(MaterialCodeLevelBase):
    """响应模式"""
    id: int
    
    class Config:
        from_attributes = True

class MaterialCodeLevelQueryParams(BaseModel):
    """查询参数模式"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词")
    level_code: Optional[str] = Field(None, description="层级路径码筛选")
    level_name: Optional[str] = Field(None, description="层级名称筛选")
    sort_by: str = Field("id", description="排序字段")
    sort_order: str = Field("desc", description="排序方向: asc/desc")

class MaterialCodeLevelPaginationResult(BaseModel):
    """分页结果模式"""
    total: int
    page: int
    page_size: int
    items: List[MaterialCodeLevelResponse]

class MaterialCodeLevelStatistics(BaseModel):
    """统计信息模式"""
    total_count: int
    level_count_by_depth: dict

class BatchMaterialCodeLevelDelete(BaseModel):
    """批量删除模式"""
    ids: List[int]

class MaterialCodeLevelBatchImportResult(BaseModel):
    """批量导入结果模式"""
    success_count: int
    error_count: int
    errors: List[str]

class MaterialCodeLevelAddDescription(BaseModel):
    """添加描述字段模式"""
    level_code: str = Field(..., description="层级路径码")
    description: str = Field(..., description="要添加的描述内容")

class MaterialCodeLevelAddDescriptionResult(BaseModel):
    """添加描述字段结果模式"""
    message: str
    level_code: str
    new_description_list: List[str]