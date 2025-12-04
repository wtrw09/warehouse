from models import SQLModelBase
from sqlmodel import Field, Relationship
from typing import Optional, List
from datetime import datetime
from sqlalchemy import JSON

# 二级专业模型
class SubMajor(SQLModelBase, table=True):
    __tablename__ = "sub_majors"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True, description="二级专业ID")
    sub_major_name: str = Field(index=True, description="二级专业名称")
    sub_major_code: str = Field(index=True, description="二级专业代码")
    description: Optional[str] = Field(default=None, sa_column=Field(JSON), description="描述列表（JSON格式），用户可以自行添加多个描述项，修改时自动删除重复项")
    major_id: Optional[int] = Field(default=None, foreign_key="majors.id", description="所属一级专业ID")
    major_name: Optional[str] = Field(default=None, description="一级专业名称")
    reserved: Optional[str] = Field(default=None, description="保留字段")
    creator: Optional[str] = Field(default=None, description="创建人")
    is_delete: bool = Field(default=False, description="是否被删除")
    create_time: Optional[datetime] = Field(default=None, description="创建时间")
    update_time: Optional[datetime] = Field(default=None, description="修改时间")
    
    # 与一级专业的关联关系
    major: Optional["Major"] = Relationship(back_populates="sub_majors")
    
    def get_description_list(self) -> List[str]:
        """获取描述列表，返回去重后的字符串列表"""
        import json
        if self.description:
            try:
                description_list = json.loads(self.description)
                if isinstance(description_list, list):
                    # 去重并过滤空值
                    unique_descriptions = []
                    for desc in description_list:
                        if isinstance(desc, str) and desc.strip() and desc not in unique_descriptions:
                            unique_descriptions.append(desc.strip())
                    return unique_descriptions
                elif isinstance(description_list, str):
                    return [description_list.strip()] if description_list.strip() else []
            except json.JSONDecodeError:
                return [self.description.strip()] if self.description.strip() else []
        return []
    
    def set_description_list(self, description_list: List[str]):
        """设置描述列表，自动去重并转换为JSON字符串"""
        import json
        if description_list:
            # 去重并过滤空值
            unique_descriptions = []
            for desc in description_list:
                if isinstance(desc, str) and desc.strip() and desc.strip() not in unique_descriptions:
                    unique_descriptions.append(desc.strip())
            
            if unique_descriptions:
                self.description = json.dumps(unique_descriptions, ensure_ascii=False)
            else:
                self.description = None
        else:
            self.description = None
    
    def add_description(self, description: str):
        """添加单个描述项，自动去重"""
        if not description or not isinstance(description, str) or not description.strip():
            return
            
        current_list = self.get_description_list()
        description = description.strip()
        
        # 检查是否已存在
        if description not in current_list:
            current_list.append(description)
            self.set_description_list(current_list)
    
    def remove_description(self, description: str):
        """删除指定的描述项"""
        if not description or not isinstance(description, str):
            return
            
        current_list = self.get_description_list()
        description = description.strip()
        
        if description in current_list:
            current_list.remove(description)
            self.set_description_list(current_list)
    
    def clear_descriptions(self):
        """清空所有描述项"""
        self.description = None