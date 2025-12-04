from sqlmodel import SQLModel, Field
from typing import Optional, List
from sqlalchemy import JSON
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

class MaterialCodeLevel(SQLModel, table=True):
    """器材编码分类层级表"""
    __tablename__ = "material_code_levels"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    level_code: str = Field(max_length=50, nullable=False, unique=True, description="层级路径码，如'1', '1-1', '1-2-3'")
    level_name: str = Field(max_length=100, nullable=False, description="层级名称")
    code: str = Field(max_length=10, nullable=False, description="编码中显示的代码")
    description: Optional[str] = Field(default=None, sa_column=Field(JSON), description="说明列表（JSON格式），用户可以自行添加多个说明项")
    
    def __repr__(self):
        return f"<MaterialCodeLevel(id={self.id}, level_code='{self.level_code}', level_name='{self.level_name}', code='{self.code}')>"
    
    def get_description_list(self) -> List[str]:
        """获取说明列表"""
        import json
        if self.description:
            try:
                return json.loads(self.description)
            except json.JSONDecodeError:
                return [self.description]
        return []
    
    def set_description_list(self, description_list: List[str]):
        """设置说明列表"""
        import json
        if description_list:
            self.description = json.dumps(description_list, ensure_ascii=False)
        else:
            self.description = None