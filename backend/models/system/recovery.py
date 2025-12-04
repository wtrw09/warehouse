"""
恢复相关模型定义
包含时间点恢复功能的请求/响应模型，支持主数据库和系统配置数据库的恢复
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel


class RecoveryRequest(BaseModel):
    """恢复请求"""
    target_datetime: datetime
    operation_id: Optional[str] = None


class RecoveryResponse(BaseModel):
    """恢复响应"""
    operation_id: str
    status: str
    recovery_db_path: str
    recovery_system_config_db_path: str
    backup_used: Dict[str, Any]
    system_config_backup_used: Optional[Dict[str, Any]] = None
    wal_files_applied: int
    verification_result: Dict[str, Any]
    system_config_verification_result: Dict[str, Any]
    target_datetime: datetime
    completed_at: datetime


class RecoveryTimelineResponse(BaseModel):
    """时间线响应"""
    timeline: List[Dict[str, Any]]


class RecoveryHistoryResponse(BaseModel):
    """恢复历史响应"""
    history: List[Dict[str, Any]]


class RecoveryTimelineRequest(BaseModel):
    """获取时间线请求"""
    days_back: int = 30


class RecoveryExecuteRequest(BaseModel):
    """执行恢复请求"""
    target_datetime: datetime
    operation_id: Optional[str] = None
    confirm: bool = False  # 确认执行恢复
    cancel: bool = False   # 取消恢复操作


class RecoveryStatusResponse(BaseModel):
    """恢复状态响应"""
    operation_id: str
    status: str
    progress: int
    current_step: str
    target_datetime: datetime
    started_at: datetime
    updated_at: datetime
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class BackupListResponse(BaseModel):
    """备份列表响应"""
    backups: list
    total_count: int