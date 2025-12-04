from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# 通用导入错误信息
class ImportError(BaseModel):
    row_index: int = Field(..., description="行号")
    field: str = Field(..., description="字段名")
    error_message: str = Field(..., description="错误信息")
    raw_data: Dict[str, Any] = Field(..., description="原始数据")

# 通用批量导入结果
class BatchImportResult(BaseModel):
    total_count: int = Field(..., description="总记录数")
    success_count: int = Field(..., description="成功导入数")
    error_count: int = Field(..., description="导入失败数")
    errors: List[ImportError] = Field(..., description="错误详情")
    import_time: datetime = Field(..., description="导入时间")
    has_error_file: bool = Field(default=False, description="是否有错误文件")
    error_file_name: Optional[str] = Field(default=None, description="错误文件名")

# 模板字段配置
class TemplateField(BaseModel):
    key: str = Field(..., description="字段键")
    label: str = Field(..., description="显示标签")
    required: bool = Field(..., description="是否必填")
    type: str = Field(default="string", description="字段类型")
    max_length: Optional[int] = Field(default=None, description="最大长度")
    placeholder: Optional[str] = Field(default=None, description="占位符")
    example: Optional[str] = Field(default=None, description="示例值")

# 验证规则配置
class ValidationRule(BaseModel):
    field: str = Field(..., description="字段名")
    type: str = Field(..., description="验证类型")
    value: Optional[Any] = Field(default=None, description="验证值")
    message: str = Field(..., description="错误消息")

# 预览列配置
class PreviewColumn(BaseModel):
    key: str = Field(..., description="字段键")
    label: str = Field(..., description="显示标签")
    width: Optional[int] = Field(default=120, description="列宽度")

# 导入配置基类
class ImportConfig(BaseModel):
    entity_name: str = Field(..., description="实体名称")
    entity_key: str = Field(..., description="实体键")
    template_fields: List[TemplateField] = Field(..., description="模板字段配置")
    validation_rules: List[ValidationRule] = Field(..., description="验证规则")
    unique_fields: List[str] = Field(default_factory=list, description="唯一性检查字段")
    preview_columns: List[PreviewColumn] = Field(..., description="预览列配置")