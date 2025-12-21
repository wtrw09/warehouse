"""
用户登录记录相关的Pydantic模型
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class LoginRecordResponse(BaseModel):
    """登录记录响应模型"""
    id: int
    user_id: int
    username: str
    ip_address: str
    user_agent: str
    login_time: datetime
    logout_time: Optional[datetime]
    is_active: bool


class PaginatedLoginRecords(BaseModel):
    """分页登录记录响应"""
    total: int
    page: int
    page_size: int
    total_pages: int
    records: List[LoginRecordResponse]