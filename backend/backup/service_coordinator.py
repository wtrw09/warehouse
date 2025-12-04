"""
服务启动协调机制
在应用启动时检查恢复状态，确保系统一致性
"""

import json
import psutil
from pathlib import Path
from datetime import datetime

# 使用全局日志配置
from core.logging_config import get_logger

logger = get_logger(__name__)

class ServiceCoordinator:
    """服务协调器类"""
    
    def __init__(self):
        """初始化服务协调器"""
        self.status_file = Path("temp_recovery/restore_status.json")
        self.temp_dir = Path("temp_recovery")
        self.main_db_path = Path("data/warehouse.db")
        
    def check_restore_status(self):
        """检查恢复状态"""
        if not self.status_file.exists():
            logger.info("未发现恢复状态文件，系统正常启动")
            return True
        
        try:
            with open(self.status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
            
            status = status_data.get("status", "unknown")
            backup_file = status_data.get("backup_file", "unknown")
            pid = status_data.get("pid")
            
            logger.info(f"发现恢复状态: {status}, 备份文件: {backup_file}, PID: {pid}")
            
            # 根据状态处理
            if status == "in_progress":
                return self.handle_in_progress_status(status_data)
            elif status == "completed":
                return self.handle_completed_status(status_data)
            elif status == "failed":
                return self.handle_failed_status(status_data)
            else:
                logger.warning(f"未知的恢复状态: {status}")
                return self.handle_unknown_status(status_data)
                
        except Exception as e:
            logger.error(f"检查恢复状态失败: {str(e)}")
            return False
    
    def handle_in_progress_status(self, status_data):
        """处理进行中的恢复状态"""
        logger.warning("发现进行中的恢复操作，检查进程状态...")
        
        pid = status_data.get("pid")
        if pid and psutil.pid_exists(pid):
            logger.info(f"恢复进程 {pid} 仍在运行，等待完成")
            return False
        else:
            logger.error("恢复进程已终止但状态仍为进行中，标记为失败")
            
            # 更新状态为失败
            status_data["status"] = "failed"
            status_data["error_message"] = "恢复进程意外终止"
            status_data["completed_at"] = datetime.now().isoformat()
            
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
            
            return self.handle_failed_status(status_data)
    
    def handle_completed_status(self, status_data):
        """处理已完成的恢复状态"""
        logger.info("恢复操作已完成，清理状态文件")
        
        # 归档状态文件
        self.archive_status_file(status_data)
        
        # 清理临时文件
        self.cleanup_temp_files()
        
        logger.info("恢复状态清理完成，系统正常启动")
        return True
    
    def handle_failed_status(self, status_data):
        """处理失败的恢复状态"""
        error_message = status_data.get("error_message", "未知错误")
        logger.error(f"恢复操作失败: {error_message}")
        
        # 尝试回滚到原始数据库
        if self.rollback_to_original():
            logger.info("成功回滚到原始数据库")
        else:
            logger.error("回滚失败，系统可能处于不一致状态")
        
        # 归档状态文件
        self.archive_status_file(status_data)
        
        # 清理临时文件
        self.cleanup_temp_files()
        
        logger.info("恢复失败处理完成，系统正常启动")
        return True
    
    def handle_unknown_status(self, status_data):
        """处理未知状态"""
        logger.warning("处理未知恢复状态，尝试回滚")
        
        # 尝试回滚
        if self.rollback_to_original():
            logger.info("成功回滚到原始数据库")
        
        # 归档状态文件
        self.archive_status_file(status_data)
        
        # 清理临时文件
        self.cleanup_temp_files()
        
        logger.info("未知状态处理完成，系统正常启动")
        return True
    
    def rollback_to_original(self):
        """回滚到原始数据库"""
        backup_db_path = self.temp_dir / "warehouse_backup.db"
        
        if backup_db_path.exists():
            try:
                logger.info("正在回滚到原始数据库...")
                
                # 确保主数据库目录存在
                self.main_db_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 恢复原始数据库
                import shutil
                shutil.copy2(backup_db_path, self.main_db_path)
                
                # 验证恢复
                if self.main_db_path.exists():
                    logger.info("数据库回滚成功")
                    return True
                else:
                    logger.error("数据库回滚失败")
                    return False
                    
            except Exception as e:
                logger.error(f"数据库回滚失败: {str(e)}")
                return False
        else:
            logger.warning("未找到原始数据库备份，无法回滚")
            return False
    
    def archive_status_file(self, status_data):
        """归档状态文件"""
        try:
            archive_dir = Path("temp_recovery/archive")
            archive_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = archive_dir / f"restore_status_{timestamp}.json"
            
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
            
            # 删除原始状态文件
            if self.status_file.exists():
                self.status_file.unlink()
            
            logger.info(f"状态文件已归档: {archive_file}")
            
        except Exception as e:
            logger.error(f"归档状态文件失败: {str(e)}")
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            backup_db_path = self.temp_dir / "warehouse_backup.db"
            
            if backup_db_path.exists():
                backup_db_path.unlink()
                logger.info("临时备份文件已清理")
            
            # 保留归档目录
            logger.info("临时文件清理完成")
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
    
    def verify_system_consistency(self):
        """验证系统一致性"""
        logger.info("正在验证系统一致性...")
        
        # 检查数据库文件是否存在
        if not self.main_db_path.exists():
            logger.error("主数据库文件不存在")
            return False
        
        # 检查数据库完整性
        try:
            import sqlite3
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            # 检查基本表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            if not tables:
                logger.error("数据库中没有表")
                return False
            
            # 检查关键表
            required_tables = ['users', 'roles', 'permissions']
            existing_tables = [table[0] for table in tables]
            
            missing_tables = []
            for table in required_tables:
                if table not in existing_tables:
                    missing_tables.append(table)
            
            if missing_tables:
                logger.warning(f"缺少关键表: {missing_tables}")
            
            conn.close()
            logger.info("系统一致性验证通过")
            return True
            
        except Exception as e:
            logger.error(f"系统一致性验证失败: {str(e)}")
            return False

def initialize_system():
    """系统初始化函数"""
    coordinator = ServiceCoordinator()
    
    # 检查恢复状态
    if not coordinator.check_restore_status():
        logger.error("恢复状态检查失败，系统无法启动")
        return False
    
    # 验证系统一致性
    if not coordinator.verify_system_consistency():
        logger.error("系统一致性验证失败")
        return False
    
    logger.info("系统初始化完成")
    return True

if __name__ == "__main__":
    # 测试服务协调器
    success = initialize_system()
    if success:
        print("系统初始化成功")
    else:
        print("系统初始化失败")