"""
用户登录记录模型
"""
from models import SQLModelBase
from sqlmodel import Field
from typing import Optional
from datetime import datetime

class UserLoginRecord(SQLModelBase, table=True):
    """用户登录记录表 - 存储近3个月的活跃登录记录"""
    __tablename__ = "user_login_records"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(index=True, description="用户ID")
    username: str = Field(index=True, description="用户名")
    ip_address: str = Field(description="登录IP地址")
    user_agent: str = Field(description="用户代理信息")
    login_time: datetime = Field(default_factory=datetime.now, description="登录时间")
    logout_time: Optional[datetime] = Field(default=None, description="登出时间")
    is_active: bool = Field(default=True, description="是否活跃会话")

class UserLoginHistory(SQLModelBase, table=True):
    """用户登录历史表 - 存储超过3个月的历史登录记录"""
    __tablename__ = "user_login_history"  # type: ignore[assignment]
    
    id: int = Field(default=None, primary_key=True, index=True)
    user_id: int = Field(index=True, description="用户ID")
    username: str = Field(index=True, description="用户名")
    ip_address: str = Field(description="登录IP地址")
    user_agent: str = Field(description="用户代理信息")
    login_time: datetime = Field(description="登录时间")
    logout_time: Optional[datetime] = Field(default=None, description="登出时间")

    archived_time: datetime = Field(default_factory=datetime.now, description="归档时间")