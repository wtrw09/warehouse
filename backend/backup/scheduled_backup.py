"""
定时备份管理脚本
每天02:00自动执行:
1. 检查各目录最近一次备份时间
2. 根据策略生成每日备份和每月备份
3. 清理超时的备份文件

备份策略:
- 每日备份: 每天02:00自动创建,保留30天
- 月度备份: 每月1号02:00自动创建,保留12个月
- 用户全量备份: 手动创建,保留5年(60个月)
"""

import os
import sys
import time
import sched
import threading
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
from typing import Dict

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backup.backup_manager import BackupManager, get_backup_manager
from core.logging_config import get_logger

logger = get_logger("backup.scheduled")


class ScheduledBackupManager:
    """定时备份管理器"""
    
    _instance = None  # 单例实例
    _lock = threading.Lock()  # 线程锁
    
    def __new__(cls):
        """实现单例模式，确保不会重复启动"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化定时备份管理器"""
        # 避免重复初始化
        if hasattr(self, '_initialized'):
            return
        
        self.backup_manager = get_backup_manager()  # 使用单例模式
        self.daily_retention_days = 30  # 每日备份保留30天
        self.monthly_retention_count = 12  # 月度备份保留12个月
        self.user_full_retention_count = 60  # 用户全量备份保留60个月(5年)
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.running = False
        self.scheduler_thread = None
        self._initialized = True
    
    def check_last_backup_time(self, backup_type: str) -> Dict:
        """
        检查指定类型的最近一次备份时间
        
        Args:
            backup_type: 备份类型(daily, monthly, user_full)
            
        Returns:
            包含最后备份时间和距今天数的字典
        """
        backups = self.backup_manager.get_backup_list(backup_type)
        
        if not backups:
            logger.info(f"{backup_type}备份: 未找到任何备份文件")
            return {
                "backup_type": backup_type,
                "last_backup": None,
                "days_since_last": None,
                "backup_count": 0
            }
        
        # 获取最新的备份
        latest_backup = backups[0]  # 已按时间倒序排序
        last_time = latest_backup["timestamp"]
        days_since = (datetime.now() - last_time).days
        
        logger.info(
            f"{backup_type}备份: "
            f"最后备份时间={last_time.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"距今{days_since}天, "
            f"共{len(backups)}个备份文件"
        )
        
        return {
            "backup_type": backup_type,
            "last_backup": last_time,
            "days_since_last": days_since,
            "backup_count": len(backups),
            "latest_file": latest_backup["filename"]
        }
    
    def should_create_daily_backup(self) -> bool:
        """
        判断是否需要创建每日备份
        策略: 如果最后一次备份不是今天,则创建
        
        Returns:
            是否需要创建
        """
        info = self.check_last_backup_time("daily")
        
        if info["last_backup"] is None:
            logger.info("需要创建每日备份: 未找到任何备份")
            return True
        
        # 检查最后一次备份是否是今天
        last_date = info["last_backup"].date()
        today = datetime.now().date()
        
        if last_date < today:
            logger.info(f"需要创建每日备份: 最后备份日期={last_date}, 今天={today}")
            return True
        
        logger.info(f"无需创建每日备份: 今天已有备份 ({info['latest_file']})")
        return False
    
    def should_create_monthly_backup(self) -> bool:
        """
        判断是否需要创建月度备份
        策略: 每月1号,如果本月还没有备份,则创建
        
        Returns:
            是否需要创建
        """
        # 只在每月1号执行
        if datetime.now().day != 1:
            logger.info("无需创建月度备份: 今天不是每月1号")
            return False
        
        info = self.check_last_backup_time("monthly")
        
        if info["last_backup"] is None:
            logger.info("需要创建月度备份: 未找到任何备份")
            return True
        
        # 检查最后一次备份是否是本月
        last_month = info["last_backup"].strftime("%Y-%m")
        current_month = datetime.now().strftime("%Y-%m")
        
        if last_month < current_month:
            logger.info(f"需要创建月度备份: 最后备份月份={last_month}, 当前月份={current_month}")
            return True
        
        logger.info(f"无需创建月度备份: 本月已有备份 ({info['latest_file']})")
        return False
    
    def create_backups(self):
        """
        根据策略创建备份
        每日备份: 每天创建
        月度备份: 每月1号创建
        """
        logger.info("=" * 80)
        logger.info("开始执行定时备份任务")
        logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        # 创建每日备份
        if self.should_create_daily_backup():
            try:
                logger.info("开始创建每日备份...")
                result = self.backup_manager.create_backup("daily")
                logger.info(
                    f"每日备份创建成功: {result['filename']}, "
                    f"大小={result['size']}字节, "
                    f"完整性={result['integrity']}"
                )
            except Exception as e:
                logger.error(f"创建每日备份失败: {str(e)}")
        
        # 创建月度备份
        if self.should_create_monthly_backup():
            try:
                logger.info("开始创建月度备份...")
                result = self.backup_manager.create_backup("monthly")
                logger.info(
                    f"月度备份创建成功: {result['filename']}, "
                    f"大小={result['size']}字节, "
                    f"完整性={result['integrity']}"
                )
            except Exception as e:
                logger.error(f"创建月度备份失败: {str(e)}")
    
    def cleanup_expired_backups(self):
        """
        清理过期的备份文件
        - 每日备份: 保留30天
        - 月度备份: 保留12个月
        - 用户全量备份: 保留60个月(5年)
        """
        logger.info("=" * 80)
        logger.info("开始清理过期备份")
        logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)
        
        try:
            # 清理每日备份和月度备份
            result = self.backup_manager.cleanup_old_backups(
                keep_days=self.daily_retention_days,
                keep_monthly=self.monthly_retention_count
            )
            
            logger.info(f"清理完成:")
            logger.info(f"  - 删除每日备份: {result['daily_deleted']}个")
            logger.info(f"  - 删除月度备份: {result['monthly_deleted']}个")
            
            # 单独清理用户全量备份(保留5年)
            deleted_count = self._cleanup_user_full_backups()
            logger.info(f"  - 删除用户全量备份: {deleted_count}个")
            
        except Exception as e:
            logger.error(f"清理备份失败: {str(e)}")
    
    def _cleanup_user_full_backups(self) -> int:
        """
        清理用户全量备份
        保留最近60个月(5年)的备份
        
        Returns:
            删除的备份数量
        """
        deleted_count = 0
        
        try:
            # 获取所有用户全量备份
            backups = self.backup_manager.get_backup_list("user_full")
            backups.sort(key=lambda x: x["timestamp"], reverse=True)
            
            # 保留前60个,删除其余
            if len(backups) > self.user_full_retention_count:
                for backup in backups[self.user_full_retention_count:]:
                    try:
                        backup_path = Path(backup["path"])
                        backup_path.unlink()
                        deleted_count += 1
                        logger.info(f"删除过期用户全量备份: {backup['filename']}")
                    except Exception as e:
                        logger.error(f"删除用户全量备份失败 {backup['path']}: {e}")
        
        except Exception as e:
            logger.error(f"清理用户全量备份异常: {str(e)}")
        
        return deleted_count
    
    def run_scheduled_task(self):
        """
        执行定时任务
        包括创建备份和清理过期备份
        """
        logger.info("\n" + "=" * 80)
        logger.info("定时备份任务开始执行")
        logger.info("=" * 80)
        
        # 1. 检查各目录最近备份时间
        logger.info("\n--- 检查备份状态 ---")
        self.check_last_backup_time("daily")
        self.check_last_backup_time("monthly")
        self.check_last_backup_time("user_full")
        
        # 2. 创建备份
        logger.info("\n--- 创建备份 ---")
        self.create_backups()
        
        # 3. 清理过期备份
        logger.info("\n--- 清理过期备份 ---")
        self.cleanup_expired_backups()
        
        logger.info("\n" + "=" * 80)
        logger.info("定时备份任务执行完成")
        logger.info("=" * 80 + "\n")
    
    def _calculate_next_run_time(self, target_hour: int = 2, target_minute: int = 0) -> float:
        """
        计算下次执行时间（秒数）
        
        Args:
            target_hour: 目标小时（默认2点）
            target_minute: 目标分钟（默认0分）
            
        Returns:
            距离下次执行的秒数
        """
        now = datetime.now()
        # 计算今天的目标时间
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        # 如果今天的目标时间已过，计算明天的
        if now >= target_time:
            target_time += timedelta(days=1)
        
        # 返回距离目标时间的秒数
        seconds_until = (target_time - now).total_seconds()
        logger.info(f"下次执行时间: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return seconds_until
    
    def _schedule_next_run(self):
        """
        调度下一次运行
        """
        if not self.running:
            return
        
        # 计算到下次02:00的秒数
        delay = self._calculate_next_run_time(target_hour=2, target_minute=0)
        
        # 调度下次执行
        self.scheduler.enter(delay, 1, self._run_and_reschedule)
    
    def _run_and_reschedule(self):
        """
        执行任务并重新调度
        """
        try:
            self.run_scheduled_task()
        except Exception as e:
            logger.error(f"定时任务执行异常: {str(e)}")
        finally:
            # 调度下一次执行
            self._schedule_next_run()
    
    def start_scheduler(self, background=False):
        """
        启动定时调度器
        每天02:00执行备份任务
        
        Args:
            background: 是否在后台运行（True时不阻塞主线程）
        """
        # 防止重复启动
        if self.running:
            logger.warning("定时备份调度器已在运行中，跳过重复启动")
            return
        
        logger.info("启动定时备份调度器")
        logger.info(f"任务执行时间: 每天 02:00")
        logger.info(f"每日备份保留: {self.daily_retention_days}天")
        logger.info(f"月度备份保留: {self.monthly_retention_count}个月")
        logger.info(f"用户全量备份保留: {self.user_full_retention_count}个月")
        
        self.running = True
        
        # 调度第一次执行
        self._schedule_next_run()
        
        logger.info("定时调度器已启动,等待执行...")
        
        # 在单独的线程中运行调度器
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # 如果不是后台模式，主线程保持运行
        if not background:
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("收到停止信号,正在关闭调度器...")
                self.stop_scheduler()
    
    def _run_scheduler(self):
        """
        在后台线程中运行调度器
        """
        while self.running:
            self.scheduler.run(blocking=False)
            time.sleep(1)
    
    def stop_scheduler(self):
        """
        停止定时调度器
        """
        if not self.running:
            logger.info("定时备份调度器未在运行")
            return
        
        logger.info("停止定时备份调度器")
        self.running = False
        
        # 等待调度器线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
            logger.info("定时备份调度器已停止")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="定时备份管理脚本")
    parser.add_argument(
        "--now", 
        action="store_true", 
        help="立即执行一次备份任务(用于测试)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="仅检查备份状态,不执行备份和清理"
    )
    
    args = parser.parse_args()
    
    scheduler = ScheduledBackupManager()
    
    if args.check_only:
        # 仅检查状态
        logger.info("检查备份状态...")
        scheduler.check_last_backup_time("daily")
        scheduler.check_last_backup_time("monthly")
        scheduler.check_last_backup_time("user_full")
    elif args.now:
        # 立即执行一次任务
        logger.info("立即执行备份任务...")
        scheduler.run_scheduled_task()
    else:
        # 启动定时调度器
        scheduler.start_scheduler()


if __name__ == "__main__":
    main()
