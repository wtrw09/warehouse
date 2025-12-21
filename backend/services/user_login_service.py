"""
用户登录记录服务
"""
from sqlmodel import Session, select, text
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from models.account.user_login_record import UserLoginRecord, UserLoginHistory
from models.account.user import User
import logging

logger = logging.getLogger(__name__)

class UserLoginService:
    """用户登录记录服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_login_record(
        self, 
        user_id: int, 
        username: str, 
        ip_address: str, 
        user_agent: str,
        auth_strategy: str = "jwt_fixed"
    ) -> UserLoginRecord:
        """创建登录记录"""
        try:
            login_record = UserLoginRecord(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                auth_strategy=auth_strategy,
                is_active=True
            )
            
            self.db.add(login_record)
            self.db.commit()
            self.db.refresh(login_record)
            
            logger.info(f"创建登录记录成功: 用户={username}, IP={ip_address}")
            return login_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建登录记录失败: {e}")
            raise
    
    def update_logout_time(self, record_id: int) -> bool:
        """更新登出时间"""
        try:
            record = self.db.get(UserLoginRecord, record_id)
            if record:
                record.logout_time = datetime.now()
                record.is_active = False
                self.db.commit()
                logger.info(f"更新登出时间成功: 记录ID={record_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新登出时间失败: {e}")
            return False
    
    def get_active_sessions_by_user(self, user_id: int) -> List[UserLoginRecord]:
        """获取用户的活跃会话"""
        try:
            query = select(UserLoginRecord).where(
                UserLoginRecord.user_id == user_id,
                UserLoginRecord.is_active == True
            ).order_by(UserLoginRecord.login_time.desc())
            
            return self.db.exec(query).all()
        except Exception as e:
            logger.error(f"获取活跃会话失败: {e}")
            return []
    
    def get_login_records_by_ip(self, ip_address: str, days: int = 90) -> List[UserLoginRecord]:
        """根据IP地址获取登录记录"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            query = select(UserLoginRecord).where(
                UserLoginRecord.ip_address == ip_address,
                UserLoginRecord.login_time >= cutoff_time
            ).order_by(UserLoginRecord.login_time.desc())
            
            return self.db.exec(query).all()
        except Exception as e:
            logger.error(f"根据IP获取登录记录失败: {e}")
            return []
    
    def archive_old_records(self, days_threshold: int = 90) -> Dict[str, int]:
        """归档超过指定天数的登录记录到历史表"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_threshold)
            
            # 查询需要归档的记录
            query = select(UserLoginRecord).where(
                UserLoginRecord.login_time < cutoff_time
            )
            
            records_to_archive = self.db.exec(query).all()
            archived_count = 0
            
            for record in records_to_archive:
                # 创建历史记录
                history_record = UserLoginHistory(
                    user_id=record.user_id,
                    username=record.username,
                    ip_address=record.ip_address,
                    user_agent=record.user_agent,
                    login_time=record.login_time,
                    logout_time=record.logout_time,
                    auth_strategy=record.auth_strategy
                )
                
                self.db.add(history_record)
                self.db.delete(record)
                archived_count += 1
            
            self.db.commit()
            logger.info(f"成功归档 {archived_count} 条登录记录")
            
            return {
                "archived_count": archived_count,
                "days_threshold": days_threshold
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"归档登录记录失败: {e}")
            return {"archived_count": 0, "error": str(e)}
    
    def cleanup_old_history(self, years_threshold: int = 5) -> Dict[str, int]:
        """清理超过指定年限的历史记录"""
        try:
            cutoff_time = datetime.now() - timedelta(days=years_threshold * 365)
            
            # 删除超过年限的历史记录
            delete_query = text(
                "DELETE FROM user_login_history WHERE login_time < :cutoff_time"
            )
            
            result = self.db.exec(delete_query, {"cutoff_time": cutoff_time})
            deleted_count = result.rowcount
            
            self.db.commit()
            logger.info(f"成功清理 {deleted_count} 条历史登录记录")
            
            return {
                "deleted_count": deleted_count,
                "years_threshold": years_threshold
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"清理历史记录失败: {e}")
            return {"deleted_count": 0, "error": str(e)}
    
    def get_user_login_statistics(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """获取用户登录统计信息"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            
            # 总登录次数
            total_logins_query = select(UserLoginRecord).where(
                UserLoginRecord.user_id == user_id,
                UserLoginRecord.login_time >= cutoff_time
            )
            total_logins = len(self.db.exec(total_logins_query).all())
            
            # 不同IP数量
            distinct_ips_query = text("""
                SELECT COUNT(DISTINCT ip_address) 
                FROM user_login_records 
                WHERE user_id = :user_id AND login_time >= :cutoff_time
            """)
            
            distinct_ips_result = self.db.exec(distinct_ips_query, {
                "user_id": user_id,
                "cutoff_time": cutoff_time
            })
            distinct_ips = distinct_ips_result.scalar() or 0
            
            # 最近登录时间
            recent_login_query = select(UserLoginRecord.login_time).where(
                UserLoginRecord.user_id == user_id,
                UserLoginRecord.login_time >= cutoff_time
            ).order_by(UserLoginRecord.login_time.desc()).limit(1)
            
            recent_login_result = self.db.exec(recent_login_query).first()
            recent_login = recent_login_result[0] if recent_login_result else None
            
            # 平均登录间隔（天）
            avg_interval_days = 0
            if total_logins > 1:
                interval_query = text("""
                    SELECT AVG(DATEDIFF(day, prev.login_time, curr.login_time))
                    FROM (
                        SELECT login_time, 
                               LAG(login_time) OVER (ORDER BY login_time) as prev_login_time
                        FROM user_login_records 
                        WHERE user_id = :user_id AND login_time >= :cutoff_time
                    ) as intervals
                    WHERE prev_login_time IS NOT NULL
                """)
                
                interval_result = self.db.exec(interval_query, {
                    "user_id": user_id,
                    "cutoff_time": cutoff_time
                })
                avg_interval_days = interval_result.scalar() or 0
            
            return {
                "total_logins": total_logins,
                "distinct_ips": distinct_ips,
                "recent_login": recent_login.isoformat() if recent_login else None,
                "avg_interval_days": round(avg_interval_days, 2),
                "analysis_period_days": days
            }
            
        except Exception as e:
            logger.error(f"获取用户登录统计信息失败: {e}")
            return {
                "total_logins": 0,
                "distinct_ips": 0,
                "recent_login": None,
                "avg_interval_days": 0,
                "analysis_period_days": days,
                "error": str(e)
            }