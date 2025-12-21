"""
定时任务管理器 - 管理登录记录清理和数据库备份等定时任务
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlmodel import Session
from .login_record_manager import get_login_record_manager
from backup.backup_manager import get_backup_manager
from database import get_db

logger = logging.getLogger(__name__)

class Scheduler:
    """定时任务管理器"""
    
    def __init__(self):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._running = False
        self._lock = asyncio.Lock()
    
    async def start(self):
        """启动定时任务"""
        async with self._lock:
            if self._running:
                logger.warning("定时任务已经在运行中")
                return
            
            self._running = True
            
            # 启动登录记录清理任务（每天凌晨2点执行）
            self._tasks["login_record_cleanup"] = asyncio.create_task(
                self._login_record_cleanup_task()
            )
            
            # 启动数据库备份清理任务（每天凌晨3点执行）
            self._tasks["backup_cleanup"] = asyncio.create_task(
                self._backup_cleanup_task()
            )
            
            logger.info("定时任务已启动")
    
    async def stop(self):
        """停止定时任务"""
        async with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            # 取消所有任务
            for task_name, task in self._tasks.items():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"任务 {task_name} 已取消")
            
            self._tasks.clear()
            logger.info("定时任务已停止")
    
    async def _login_record_cleanup_task(self):
        """登录记录清理任务"""
        while self._running:
            try:
                # 计算下一次执行时间（明天凌晨2点）
                now = datetime.now()
                next_run = (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
                wait_seconds = (next_run - now).total_seconds()
                
                logger.info(f"登录记录清理任务将在 {wait_seconds:.0f} 秒后执行")
                
                # 等待到执行时间
                await asyncio.sleep(wait_seconds)
                
                if not self._running:
                    break
                
                # 执行清理任务
                await self._cleanup_login_records()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"登录记录清理任务执行失败: {e}")
                # 出错后等待1小时再重试
                await asyncio.sleep(3600)
    
    async def _backup_cleanup_task(self):
        """数据库备份清理任务"""
        while self._running:
            try:
                # 计算下一次执行时间（明天凌晨3点）
                now = datetime.now()
                next_run = (now + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)
                wait_seconds = (next_run - now).total_seconds()
                
                logger.info(f"数据库备份清理任务将在 {wait_seconds:.0f} 秒后执行")
                
                # 等待到执行时间
                await asyncio.sleep(wait_seconds)
                
                if not self._running:
                    break
                
                # 执行清理任务
                await self._cleanup_backups()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"数据库备份清理任务执行失败: {e}")
                # 出错后等待1小时再重试
                await asyncio.sleep(3600)
    
    async def _cleanup_login_records(self):
        """清理登录记录"""
        try:
            logger.info("开始清理登录记录...")
            
            # 获取数据库会话
            db = next(get_db())
            
            # 获取登录记录管理器
            login_record_manager = get_login_record_manager()
            
            # 清理超过3个月的登录记录（归档到历史表）
            cleanup_stats = await login_record_manager.cleanup_old_records(db, keep_days=90)
            
            # 清理超过5年的历史记录
            history_cleanup_count = await login_record_manager.cleanup_old_history(db, keep_years=5)
            
            logger.info(f"登录记录清理完成: 归档 {cleanup_stats['archived']} 条记录, "
                       f"删除历史记录 {history_cleanup_count} 条")
            
        except Exception as e:
            logger.error(f"清理登录记录失败: {e}")
        finally:
            if 'db' in locals():
                db.close()
    
    async def _cleanup_backups(self):
        """清理数据库备份"""
        try:
            logger.info("开始清理数据库备份...")
            
            # 获取备份管理器
            backup_manager = get_backup_manager()
            
            # 清理旧的备份文件
            cleanup_stats = backup_manager.cleanup_old_backups(keep_days=30, keep_monthly=12)
            
            logger.info(f"数据库备份清理完成: 删除每日备份 {cleanup_stats['daily_deleted']} 个, "
                       f"删除月度备份 {cleanup_stats['monthly_deleted']} 个")
            
        except Exception as e:
            logger.error(f"清理数据库备份失败: {e}")
    
    async def run_immediate_cleanup(self):
        """立即执行清理任务（用于手动触发）"""
        try:
            logger.info("开始立即执行清理任务...")
            
            # 执行登录记录清理
            await self._cleanup_login_records()
            
            # 执行数据库备份清理
            await self._cleanup_backups()
            
            logger.info("立即清理任务完成")
            
        except Exception as e:
            logger.error(f"立即清理任务执行失败: {e}")
            raise

# 全局定时任务管理器实例
_scheduler = None

def get_scheduler() -> Scheduler:
    """获取定时任务管理器实例（单例模式）"""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler

async def start_scheduler():
    """启动定时任务（应用启动时调用）"""
    scheduler = get_scheduler()
    await scheduler.start()

async def stop_scheduler():
    """停止定时任务（应用关闭时调用）"""
    scheduler = get_scheduler()
    await scheduler.stop()