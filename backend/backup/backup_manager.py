"""
备份管理模块
负责管理数据库备份文件
支持主数据库的备份
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# 使用全局日志配置
from core.logging_config import get_logger

logger = get_logger(__name__)

class BackupManager:
    """备份管理器类"""
    
    def __init__(self, db_path: str = "data/warehouse.db", backup_base_dir: str = "backups"):
        """
        初始化备份管理器
        
        Args:
            db_path: 数据库文件路径
            backup_base_dir: 备份文件基础目录
        """
        self.db_path = Path(db_path)
        self.backup_base_dir = Path(backup_base_dir)
        

        
        # 备份目录结构
        self.daily_dir = self.backup_base_dir / "daily"
        self.monthly_dir = self.backup_base_dir / "monthly"
        self.user_full_dir = self.backup_base_dir / "user_full"
        
        # 创建备份目录
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所有备份目录存在"""
        directories = [
            self.daily_dir,
            self.monthly_dir,
            self.user_full_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_backup_list(self, backup_type: str = "all", 
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Dict]:
        """
        获取备份列表
        
        Args:
            backup_type: 备份类型（daily, monthly, user_full, all）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            备份文件信息列表
        """
        backups = []
        
        # 确定要搜索的目录
        if backup_type == "all":
            directories = [self.daily_dir, self.monthly_dir, self.user_full_dir]
        elif backup_type == "daily":
            directories = [self.daily_dir]
        elif backup_type == "monthly":
            directories = [self.monthly_dir]
        elif backup_type == "user_full":
            directories = [self.user_full_dir]
        else:
            raise ValueError(f"不支持的备份类型: {backup_type}")
        
        for directory in directories:
            for backup_file in directory.glob("*.db"):
                # 解析文件名中的时间戳
                file_info = self._parse_backup_filename(backup_file)
                if file_info:
                    # 时间范围筛选
                    if start_date and file_info["timestamp"] < start_date:
                        continue
                    if end_date and file_info["timestamp"] > end_date:
                        continue
                    
                    # 添加文件大小和完整性信息
                    file_info["size"] = f"{backup_file.stat().st_size // 1024}KB"
                    file_info["integrity"] = self.validate_backup_integrity(backup_file)
                    
                    # 添加文件路径信息
                    file_info["path"] = str(backup_file)
                    
                    # 添加默认描述（实际项目中可以从备份元数据中获取）
                    # 这里使用默认描述，实际项目中应该从备份元数据中获取原始描述
                    file_info["description"] = f"{file_info['type']}备份 - {file_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    # 将timestamp转换为ISO格式字符串,确保前端能正确解析时区
                    file_info["timestamp"] = file_info["timestamp"].isoformat()
                    
                    backups.append(file_info)
        
        # 按时间戳排序
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups
    
    def _parse_backup_filename(self, file_path: Path) -> Optional[Dict]:
        """
        解析备份文件名，提取时间戳和类型信息
        
        Args:
            file_path: 备份文件路径
            
        Returns:
            文件信息字典，包含时间戳和类型
        """
        filename = file_path.stem  # 去掉扩展名
        
        # 解析不同类型的备份文件名格式
        if filename.startswith("daily_warehouse_"):
            timestamp_str = filename.replace("daily_warehouse_", "")
            backup_type = "daily"
        elif filename.startswith("monthly_warehouse_"):
            timestamp_str = filename.replace("monthly_warehouse_", "")
            backup_type = "monthly"
        elif filename.startswith("user_full_warehouse_"):
            timestamp_str = filename.replace("user_full_warehouse_", "")
            backup_type = "user_full"
        else:
            return None
        
        try:
            # 解析时间戳格式：YYYYMMDD_HHMMSS
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            return {
                "filename": file_path.name,
                "timestamp": timestamp,
                "type": backup_type
            }
        except ValueError:
            logger.warning(f"无法解析备份文件名的时间戳: {filename}")
            return None
    

    

    
    def create_backup(self, backup_type: str = "daily") -> Dict[str, str]:
        """
        使用sqlite3_backup API创建数据库备份
        同时备份主数据库和系统配置数据库
        
        Args:
            backup_type: 备份类型（daily, monthly, user_full）
            
        Returns:
            备份结果信息
        """
        try:
            # 确定备份目录
            if backup_type == "daily":
                backup_dir = self.daily_dir
            elif backup_type == "monthly":
                backup_dir = self.monthly_dir
            elif backup_type == "user_full":
                backup_dir = self.user_full_dir
            else:
                raise ValueError(f"不支持的备份类型: {backup_type}")
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{backup_type}_warehouse_{timestamp}.db"
            backup_path = backup_dir / backup_filename
            
            # 确保备份目录存在
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 备份主数据库
            source_conn = sqlite3.connect(str(self.db_path))
            backup_conn = sqlite3.connect(str(backup_path))
            
            try:
                # 获取源数据库的备份对象
                source_conn.backup(backup_conn)
                
                # 记录备份元数据
                backup_info = {
                    "filename": backup_filename,
                    "path": str(backup_path),
                    "type": backup_type,
                    "timestamp": datetime.now(),
                    "size": backup_path.stat().st_size,
                    "integrity": self.validate_backup_integrity(backup_path)
                }
                
                logger.info(f"成功创建{backup_type}备份: {backup_filename}")
                return backup_info
                
            except sqlite3.Error as e:
                logger.error(f"备份过程失败: {e}")
                # 如果备份失败，删除不完整的备份文件
                if backup_path.exists():
                    backup_path.unlink()
                raise
            finally:
                source_conn.close()
                backup_conn.close()
                
        except Exception as e:
            logger.error(f"备份创建失败: {e}")
            raise
    
    def validate_backup_integrity(self, backup_file: Path) -> bool:
        """
        验证备份文件完整性
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            是否完整有效
        """
        try:
            # 检查文件是否存在且可读
            if not backup_file.exists() or not backup_file.is_file():
                return False
            
            # 检查文件大小（不能为0）
            if backup_file.stat().st_size == 0:
                return False
            
            # 尝试连接数据库验证完整性
            conn = sqlite3.connect(str(backup_file))
            try:
                # 执行简单的查询验证数据库结构
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                # 检查是否有基本的表结构
                if len(tables) == 0:
                    return False
                
                # 验证数据库是否可正常关闭
                conn.close()
                return True
                
            except sqlite3.Error as e:
                logger.error(f"备份文件完整性验证失败 {backup_file}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"备份文件验证异常 {backup_file}: {e}")
            return False
    

    
    def cleanup_old_backups(self, keep_days: int = 30, 
                           keep_monthly: int = 12) -> Dict[str, int]:
        """
        清理旧的备份文件
        
        Args:
            keep_days: 保留最近多少天的每日备份
            keep_monthly: 保留最近多少个月的月度备份
            
        Returns:
            清理结果统计
        """
        cleanup_stats = {
            "daily_deleted": 0,
            "monthly_deleted": 0,
            "user_full_deleted": 0
        }
        
        current_time = datetime.now()
        
        # 清理每日备份
        daily_backups = self.get_backup_list("daily")
        for backup in daily_backups:
            if (current_time - backup["timestamp"]) > timedelta(days=keep_days):
                try:
                    backup_path = Path(backup["path"])
                    backup_path.unlink()
                    cleanup_stats["daily_deleted"] += 1
                except Exception as e:
                    logger.error(f"删除每日备份失败 {backup['path']}: {e}")
        
        # 清理月度备份（保留指定数量的最新备份）
        monthly_backups = self.get_backup_list("monthly")
        monthly_backups.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if len(monthly_backups) > keep_monthly:
            for backup in monthly_backups[keep_monthly:]:
                try:
                    backup_path = Path(backup["path"])
                    backup_path.unlink()
                    cleanup_stats["monthly_deleted"] += 1
                except Exception as e:
                    logger.error(f"删除月度备份失败 {backup['path']}: {e}")        
        
        return cleanup_stats

    def delete_backup_by_filename(self, filename: str) -> bool:
        """
        根据文件名删除指定的备份文件
        
        Args:
            filename: 备份文件名
            
        Returns:
            是否成功删除
        """
        try:
            # 在所有备份目录中查找文件
            backup_dirs = [self.daily_dir, self.monthly_dir, self.user_full_dir]
            
            for backup_dir in backup_dirs:
                backup_path = backup_dir / filename
                if backup_path.exists():
                    backup_path.unlink()
                    logger.info(f"成功删除备份文件: {filename}")
                    return True
            
            logger.warning(f"未找到备份文件: {filename}")
            return False
            
        except Exception as e:
            logger.error(f"删除备份文件失败 {filename}: {e}")
            return False

# 全局备份管理器实例
_backup_manager = None

def get_backup_manager() -> BackupManager:
    """获取备份管理器实例（单例模式）"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager

if __name__ == "__main__":
    # 测试备份管理器功能
    manager = BackupManager()
    
    # 获取备份列表
    backups = manager.get_backup_list()
    print(f"找到 {len(backups)} 个备份文件")
    
    # 测试备份完整性验证
    if backups:
        integrity = manager.validate_backup_integrity(Path(backups[0]["path"]))
        print(f"第一个备份文件完整性: {integrity}")