from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List
from datetime import datetime

# 专业模型
class Major(SQLModelBase, table=True):
    __tablename__ = "majors"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True, description="专业ID")
    major_name: str = Field(index=True, description="专业名称")
    major_code: str = Field(index=True, description="专业代码")
    creator: Optional[str] = Field(default=None, description="创建人")
    is_delete: bool = Field(default=False, description="是否被删除")
    create_time: Optional[datetime] = Field(default=None, description="创建时间")
    update_time: Optional[datetime] = Field(default=None, description="修改时间")
    
    # 与二级专业的反向关系
    sub_majors: List["SubMajor"] = Relationship(back_populates="major")