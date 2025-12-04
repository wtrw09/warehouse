"""
系统初始化配置模型
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class SystemInit(SQLModel, table=True):
    """系统初始化状态表"""
    __tablename__ = "_system_init"
    
    id: int = Field(default=None, primary_key=True)
    initialized: bool = Field(default=False, description="系统是否已初始化")
    init_time: Optional[datetime] = Field(default=None, description="初始化时间")
    init_version: Optional[str] = Field(default=None, description="初始化版本")


class SystemConfig(SQLModel, table=True):
    """系统配置表"""
    __tablename__ = "_system_config"
    
    id: int = Field(default=None, primary_key=True)
    config_key: str = Field(unique=True, description="配置键")
    config_value: str = Field(description="配置值")
    config_type: str = Field(default="string", description="配置类型: string/int/bool")
    description: Optional[str] = Field(default=None, description="配置描述")
    created_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_time: datetime = Field(default_factory=datetime.now, description="更新时间")
    is_active: bool = Field(default=True, description="是否启用")