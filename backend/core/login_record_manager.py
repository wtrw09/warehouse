"""
登录记录管理器 - 管理用户登录记录和单IP登录限制
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlmodel import Session, select, text
from models.account.user_login_record import UserLoginRecord, UserLoginHistory

class LoginRecordManager:
    """登录记录管理器"""
    
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def record_login(self, db: Session, user_id: int, username: str, 
                          ip_address: str, user_agent: str) -> int:
        """
        记录用户登录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            username: 用户名
            ip_address: IP地址
            user_agent: 用户代理
            
        Returns:
            登录记录ID
        """
        async with self._lock:
            # 创建登录记录
            login_record = UserLoginRecord(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                is_active=True
            )
            
            db.add(login_record)
            db.commit()
            db.refresh(login_record)
            
            return login_record.id
    
    async def record_logout(self, db: Session, user_id: int, ip_address: Optional[str] = None, username: Optional[str] = None) -> bool:
        """
        记录用户登出
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            ip_address: 当前登出IP地址（可选）
            username: 当前登出用户名（可选）
            
        Returns:
            是否成功记录
        """
        async with self._lock:
            # 查找活跃的登录记录
            query = select(UserLoginRecord).where(
                UserLoginRecord.user_id == user_id,
                UserLoginRecord.is_active == True
            )
           
            # 获取所有活跃的登录记录，而不仅仅是最近的一条
            login_records = db.exec(query).all()
            
            if login_records:
                print(f"[DEBUG] record_logout - 找到 {len(login_records)} 条活跃记录")
                logout_time = datetime.now()
                
                for record in login_records:
                    # 检查是否是当前IP和用户名的记录
                    if ip_address and username and record.ip_address == ip_address and record.username == username:
                        # 是当前用户的记录，更新登出时间和状态
                        print(f"[DEBUG] record_logout - 更新当前IP记录: {record.ip_address} - {record.username}")
                        record.logout_time = logout_time
                        record.is_active = False
                    else:
                        # 是其他IP的记录，只更新状态，保持原有登出时间
                        print(f"[DEBUG] record_logout - 更新其他IP记录: {record.ip_address} - {record.username}")
                        record.is_active = False
                        # 登出时间保持不变
                
                db.commit()
                return True
            
            return False
    
    async def check_single_ip_login(self, db: Session, user_id: int, ip_address: str) -> bool:
        """
        检查是否允许单IP登录
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            ip_address: 当前登录IP
            
        Returns:
            True: 允许登录（当前IP或没有其他活跃会话）
            False: 不允许登录（有其他IP的活跃会话）
        """
        async with self._lock:
            # 查找用户当前活跃的登录记录
            active_records = db.exec(
                select(UserLoginRecord).where(
                    UserLoginRecord.user_id == user_id,
                    UserLoginRecord.is_active == True
                )
            ).all()
            
            # 如果没有活跃记录，允许登录
            if not active_records:
                return True
            
            # 检查是否有其他IP的活跃会话
            for record in active_records:
                if record.ip_address != ip_address:
                    # 有其他IP的活跃会话，不允许登录
                    return False
            
            # 只有当前IP的活跃会话，允许登录
            return True
    
    async def force_logout_other_sessions(self, db: Session, user_id: int, current_ip: str) -> int:
        """
        强制登出其他IP的会话
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            current_ip: 当前登录IP
            
        Returns:
            强制登出的会话数量
        """
        async with self._lock:
            # 查找其他IP的活跃会话
            other_sessions = db.exec(
                select(UserLoginRecord).where(
                    UserLoginRecord.user_id == user_id,
                    UserLoginRecord.is_active == True,
                    UserLoginRecord.ip_address != current_ip
                )
            ).all()
            
            logout_count = 0
            for session in other_sessions:
                # 只更新状态，保持原有登出时间不变
                session.is_active = False
                logout_count += 1
            
            if logout_count > 0:
                db.commit()
            
            return logout_count
    
    async def get_user_active_sessions(self, db: Session, user_id: int) -> List[UserLoginRecord]:
        """
        获取用户当前活跃的会话
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            活跃会话列表
        """
        return db.exec(
            select(UserLoginRecord).where(
                UserLoginRecord.user_id == user_id,
                UserLoginRecord.is_active == True
            ).order_by(UserLoginRecord.login_time.desc())
        ).all()
    
    async def cleanup_old_records(self, db: Session, keep_days: int = 90) -> Dict[str, int]:
        """
        清理旧的登录记录
        
        Args:
            db: 数据库会话
            keep_days: 保留天数
            
        Returns:
            清理统计
        """
        async with self._lock:
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            
            # 查找需要归档的记录
            old_records = db.exec(
                select(UserLoginRecord).where(
                    UserLoginRecord.login_time < cutoff_time
                )
            ).all()
            
            archived_count = 0
            deleted_count = 0
            
            for record in old_records:
                # 归档到历史表
                history_record = UserLoginHistory(
                    user_id=record.user_id,
                    username=record.username,
                    ip_address=record.ip_address,
                    user_agent=record.user_agent,
                    login_time=record.login_time,
                    logout_time=record.logout_time
                )
                
                db.add(history_record)
                db.delete(record)
                archived_count += 1
            
            if archived_count > 0:
                db.commit()
            
            return {
                "archived": archived_count,
                "deleted": deleted_count
            }
    
    async def cleanup_old_history(self, db: Session, keep_years: int = 5) -> int:
        """
        清理旧的历史记录
        
        Args:
            db: 数据库会话
            keep_years: 保留年数
            
        Returns:
            删除的记录数量
        """
        async with self._lock:
            cutoff_time = datetime.now() - timedelta(days=keep_years * 365)
            
            # 删除超过保留年限的历史记录
            result = db.exec(
                text("DELETE FROM user_login_history WHERE login_time < :cutoff_time"),
                {"cutoff_time": cutoff_time}
            )
            
            deleted_count = result.rowcount
            db.commit()
            
            return deleted_count

# 全局登录记录管理器实例
_login_record_manager = None

def get_login_record_manager() -> LoginRecordManager:
    """获取登录记录管理器实例（单例模式）"""
    global _login_record_manager
    if _login_record_manager is None:
        _login_record_manager = LoginRecordManager()
    return _login_record_manager