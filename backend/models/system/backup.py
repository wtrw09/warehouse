"""
备份相关模型定义
包含手动备份功能的请求/响应模型
"""
from pydantic import BaseModel
class BackupListResponse(BaseModel):
    """备份列表响应"""
    backups: list
    total_count: int