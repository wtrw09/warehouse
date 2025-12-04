"""
固定手动恢复脚本
支持通过命令行参数传递备份文件路径和状态文件路径
"""

import os
import sys
import time
import json
import shutil
import sqlite3
import psutil
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 使用全局日志配置
from core.logging_config import get_logger

# 使用专门的恢复处理器日志记录器，确保日志写入restore_processor.log
logger = get_logger("backup.restore_processor")

class FixedManualRecovery:
    """固定手动恢复类"""
    
    def __init__(self, backup_file_path: str, status_file_path: str):
        """
        初始化恢复处理器
        
        Args:
            backup_file_path: 备份文件路径
            status_file_path: 状态文件路径
        """
        self.backup_file_path = Path(backup_file_path)
        self.status_file_path = Path(status_file_path)
        self.temp_dir = Path("temp_recovery")
        self.main_db_path = Path("data/warehouse.db")
        self.backup_db_path = self.temp_dir / "warehouse_backup.db"
    
    def update_status(self, status: str, error_message: Optional[str] = None):
        """更新恢复状态"""
        try:
            # 确保状态文件存在且有基本结构
            if not self.status_file_path.exists():
                # 创建初始状态文件
                status_data = {
                    "status": status,
                    "backup_file": str(self.backup_file_path.name),
                    "backup_path": str(self.backup_file_path),
                    "started_at": datetime.now().isoformat(),
                    "pid": os.getpid(),
                    "steps": {
                        "stopping_services": False,
                        "backing_up_current": False,
                        "restoring_from_backup": False,
                        "validating_integrity": False,
                        "starting_services": False,
                        "cleaning_up": False
                    }
                }
                # 写入初始状态文件
                with open(self.status_file_path, 'w', encoding='utf-8') as f:
                    json.dump(status_data, f, ensure_ascii=False, indent=2)
            else:
                # 读取现有状态文件
                with open(self.status_file_path, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
            
            # 更新状态
            status_data["status"] = status
            if error_message is not None:
                status_data["error_message"] = error_message
            if status in ["completed", "failed"]:
                status_data["completed_at"] = datetime.now().isoformat()
            
            # 更新步骤状态
            if "steps" in status_data:
                if status == "stopping_services":
                    status_data["steps"]["stopping_services"] = True
                elif status == "backing_up_current":
                    status_data["steps"]["backing_up_current"] = True
                elif status == "restoring_from_backup":
                    status_data["steps"]["restoring_from_backup"] = True
                elif status == "validating_integrity":
                    status_data["steps"]["validating_integrity"] = True
                elif status == "starting_services":
                    status_data["steps"]["starting_services"] = True
                elif status == "cleaning_up":
                    status_data["steps"]["cleaning_up"] = True
            
            # 写入状态文件
            with open(self.status_file_path, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"更新状态文件失败: {str(e)}")
    
    def stop_fastapi_services(self):
        """停止FastAPI服务进程"""
        logger.info("正在停止FastAPI服务...")
        
        # 查找并停止Uvicorn进程
        uvicorn_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and any('uvicorn' in str(arg).lower() for arg in cmdline):
                    uvicorn_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 停止进程
        for proc in uvicorn_processes:
            try:
                logger.info(f"停止进程 PID: {proc.pid}")
                proc.terminate()
                proc.wait(timeout=10)
            except psutil.TimeoutExpired:
                logger.warning(f"进程 {proc.pid} 未正常停止，强制终止")
                proc.kill()
            except Exception as e:
                logger.error(f"停止进程 {proc.pid} 失败: {str(e)}")
        
        # 等待进程完全停止
        time.sleep(3)
        
        # 验证进程是否已停止
        for proc in uvicorn_processes:
            if psutil.pid_exists(proc.pid):
                logger.error(f"进程 {proc.pid} 仍在运行")
                return False
        
        logger.info("FastAPI服务已停止")
        return True
    
    def backup_current_database(self):
        """备份当前数据库"""
        logger.info("正在备份当前数据库...")
        
        if not self.main_db_path.exists():
            logger.warning("主数据库文件不存在，无需备份")
            return True
        
        try:
            # 创建备份目录
            self.temp_dir.mkdir(exist_ok=True)
            
            # 使用SQLite的backup API进行备份，避免数据库损坏
            source_conn = sqlite3.connect(str(self.main_db_path))
            backup_conn = sqlite3.connect(str(self.backup_db_path))
            
            try:
                # 使用backup API将当前数据库备份
                source_conn.backup(backup_conn)
                logger.info(f"当前数据库已备份到: {self.backup_db_path}")
                return True
            except sqlite3.Error as e:
                logger.error(f"数据库备份过程失败: {str(e)}")
                # 如果备份失败，删除不完整的备份文件
                if self.backup_db_path.exists():
                    self.backup_db_path.unlink()
                return False
            finally:
                source_conn.close()
                backup_conn.close()
                
        except Exception as e:
            logger.error(f"数据库备份失败: {str(e)}")
            return False
    
    def restore_from_backup(self):
        """从备份文件恢复数据库"""
        logger.info("正在从备份文件恢复数据库...")
        
        if not self.backup_file_path.exists():
            logger.error(f"备份文件不存在: {self.backup_file_path}")
            return False
        
        try:
            # 确保目标目录存在
            self.main_db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用SQLite的backup API进行恢复，避免数据库损坏
            backup_conn = sqlite3.connect(str(self.backup_file_path))
            target_conn = sqlite3.connect(str(self.main_db_path))
            
            try:
                # 使用backup API将备份恢复到目标数据库
                backup_conn.backup(target_conn)
                logger.info(f"数据库已从备份恢复: {self.main_db_path}")
                return True
            except sqlite3.Error as e:
                logger.error(f"数据库恢复过程失败: {str(e)}")
                return False
            finally:
                backup_conn.close()
                target_conn.close()
                
        except Exception as e:
            logger.error(f"数据库恢复失败: {str(e)}")
            return False
    
    def validate_database_integrity(self):
        """验证数据库完整性"""
        logger.info("正在验证数据库完整性...")
        
        if not self.main_db_path.exists():
            logger.error("数据库文件不存在")
            return False
        
        try:
            # 连接数据库并执行简单查询
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            # 检查数据库是否能正常打开
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            # 检查是否有基本表
            if not tables:
                logger.warning("数据库中没有表")
            
            conn.close()
            logger.info("数据库完整性验证通过")
            return True
            
        except Exception as e:
            logger.error(f"数据库完整性验证失败: {str(e)}")
            return False
    
    def start_fastapi_services(self):
        """启动FastAPI服务"""
        logger.info("正在启动FastAPI服务...")
        
        try:
            import subprocess
            import sys
            
            # 直接使用main.py启动服务，避免模块导入问题
            # 确保使用当前工作目录的绝对路径
            current_dir = Path.cwd()
            main_script = current_dir / "main.py"
            
            if not main_script.exists():
                logger.error(f"主程序文件不存在: {main_script}")
                return False
            
            # 使用与原始启动相同的参数
            subprocess_args = [
                sys.executable, str(main_script),
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload"
            ]
            
            # 启动Uvicorn服务器
            process = subprocess.Popen(subprocess_args, cwd=current_dir)
            
            # 等待服务启动
            time.sleep(8)  # 增加等待时间确保服务完全启动
            
            # 检查进程是否在运行
            if process.poll() is None:
                logger.info(f"FastAPI服务已启动，PID: {process.pid}")
                logger.info(f"使用配置: {subprocess_args}")
                return True
            else:
                logger.error("FastAPI服务启动失败")
                return False
                
        except Exception as e:
            logger.error(f"启动FastAPI服务失败: {str(e)}")
            return False
    
    def cleanup(self):
        """清理临时文件"""
        logger.info("正在清理临时文件...")
        
        try:
            # 删除临时备份文件
            if self.backup_db_path.exists():
                self.backup_db_path.unlink()
                logger.info("临时备份文件已删除")
            
            # 清理state_backup目录中的状态备份文件
            state_backup_dir = Path("backups/state_backup")
            if state_backup_dir.exists():
                # 删除所有JSON状态备份文件
                json_files = list(state_backup_dir.glob("*.json"))
                for json_file in json_files:
                    try:
                        json_file.unlink()
                        logger.info(f"已删除状态备份文件: {json_file.name}")
                    except Exception as e:
                        logger.warning(f"删除状态备份文件失败 {json_file}: {str(e)}")
                
                if json_files:
                    logger.info(f"已清理 {len(json_files)} 个状态备份文件")
                else:
                    logger.info("状态备份目录为空，无需清理")
            else:
                logger.info("状态备份目录不存在，无需清理")
            
            # 保留状态文件用于监控
            logger.info("清理完成")
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {str(e)}")
    
    def execute_restore(self):
        """执行完整的恢复流程"""
        logger.info("开始执行数据库恢复流程")
        
        try:
            # 步骤1: 停止FastAPI服务
            self.update_status("stopping_services")
            if not self.stop_fastapi_services():
                self.update_status("failed", "停止服务失败")
                return False
            
            # 步骤2: 备份当前数据库
            self.update_status("backing_up_current")
            if not self.backup_current_database():
                self.update_status("failed", "备份当前数据库失败")
                return False
            
            # 步骤3: 从备份文件恢复
            self.update_status("restoring_from_backup")
            if not self.restore_from_backup():
                self.update_status("failed", "从备份文件恢复失败")
                return False
            
            # 步骤4: 验证数据库完整性
            self.update_status("validating_integrity")
            if not self.validate_database_integrity():
                self.update_status("failed", "数据库完整性验证失败")
                return False
            
            # 步骤5: 启动FastAPI服务
            self.update_status("starting_services")
            if not self.start_fastapi_services():
                self.update_status("failed", "启动服务失败")
                return False
            
            # 步骤6: 清理临时文件
            self.update_status("cleaning_up")
            self.cleanup()
            
            # 步骤7: 标记完成
            self.update_status("completed")
            logger.info("数据库恢复流程完成")
            return True
            
        except Exception as e:
            error_msg = f"恢复流程异常: {str(e)}"
            logger.error(error_msg)
            self.update_status("failed", error_msg)
            return False

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python backup/manual_recovery_fixed.py <backup_file_path> <status_file_path>")
        print("示例: python backup/manual_recovery_fixed.py backup/warehouse_20251108_195654.db temp_recovery/restore_status.json")
        sys.exit(1)
    
    backup_file_path = sys.argv[1]
    status_file_path = sys.argv[2]
    
    processor = FixedManualRecovery(backup_file_path, status_file_path)
    success = processor.execute_restore()
    
    if success:
        print("恢复操作成功完成")
        sys.exit(0)
    else:
        print("恢复操作失败")
        sys.exit(1)

if __name__ == "__main__":
    main()