"""
会话管理器 - 支持滑动会话超时功能
"""
import asyncio
import json
import redis.asyncio as redis
import time
from typing import Optional, Dict, Any
from core.config import dynamic_settings

class SessionManager:
    """会话管理器类"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.session_prefix = "session:"
        self._redis_available = True  # Redis可用状态
        self._fallback_sessions: Dict[str, Dict[str, Any]] = {}  # 备选存储方案：内存存储
        self._last_check_time = 0  # 上次检查Redis的时间
        self._check_interval = 10  # Redis状态检查间隔（秒），避免频繁检查
        self._lock = asyncio.Lock()  # 保护_fallback_sessions的并发访问
        
    async def get_redis_client(self) -> Optional[redis.Redis]:
        """获取Redis客户端连接，如果Redis不可用则返回None"""
        redis_url = dynamic_settings.REDIS_URL
        current_time = time.time()
        
        # 如果Redis之前标记为不可用，且距离上次检查时间不足检查间隔，直接返回None（快速失败）
        if not self._redis_available and (current_time - self._last_check_time) < self._check_interval:
            return None
        
        # 如果已有可用的Redis连接，快速验证
        if self.redis_client and self._redis_available:
            try:
                await self.redis_client.ping()
                return self.redis_client
            except Exception:
                # 连接已断开，标记为不可用
                self._redis_available = False
                self._last_check_time = current_time
                self.redis_client = None
                return None
        
        # 尝试建立新连接或重新连接
        self._last_check_time = current_time
        
        try:
            if self.redis_client:
                await self.redis_client.close()
                self.redis_client = None
            
            self.redis_client = redis.from_url(
                redis_url, 
                encoding="utf-8", 
                decode_responses=True,
                socket_connect_timeout=5,  # 连接超时5秒（Docker环境需要更长时间）
                socket_timeout=5,  # 操作超时5秒
                retry_on_timeout=False,  # 不重试，快速失败
                retry_on_error=[]
            )
            
            # 测试连接
            await self.redis_client.ping()
            self._redis_available = True
            return self.redis_client
            
        except Exception as e:
            self._redis_available = False
            self.redis_client = None
            return None
    
    def is_redis_available(self) -> bool:
        """检查Redis是否可用"""
        return self._redis_available
    
    async def check_redis_status(self) -> Dict[str, Any]:
        """检查Redis状态并返回详细信息"""
        try:
            redis_client = await self.get_redis_client()
            if redis_client:
                # 测试连接
                await redis_client.ping()
                return {
                    "available": True,
                    "message": "Redis服务器运行正常",
                    "fallback_active": False
                }
            else:
                return {
                    "available": False,
                    "message": "Redis服务器不可用，已启用备选存储方案",
                    "fallback_active": True,
                    "fallback_sessions_count": len(self._fallback_sessions)
                }
        except Exception as e:
            return {
                "available": False,
                "message": f"Redis服务器异常: {str(e)}",
                "fallback_active": True,
                "fallback_sessions_count": len(self._fallback_sessions)
            }
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    def _get_session_key(self, user_id: str) -> str:
        """生成会话键"""
        return f"{self.session_prefix}{user_id}"
    
    async def create_session(self, user_id: str, user_data: Dict[str, Any], 
                           ip_address: str, user_agent: str) -> bool:
        """创建新会话"""
        try:
            redis_client = await self.get_redis_client()
            
            # 存储必要的会话信息，包括用户基本信息
            session_data = {
                "user_id": user_id,
                "last_activity": int(time.time()),
                "created_at": int(time.time()),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "active": True
            }
            
            # 添加用户基本信息到会话数据
            if user_data:
                session_data["username"] = user_data.get("username", "")
                session_data["role_name"] = user_data.get("role_name", "")
                session_data["permissions"] = user_data.get("permissions", [])
            
            # 设置会话数据，过期时间为滑动会话超时时间
            timeout_seconds = dynamic_settings.SLIDING_SESSION_TIMEOUT_MINUTES * 60
            
            if redis_client:
                # Redis可用，使用Redis存储
                # 将所有值转换为字符串以兼容Redis
                redis_data = {
                    "user_id": str(session_data["user_id"]),
                    "last_activity": str(session_data["last_activity"]),
                    "created_at": str(session_data["created_at"]),
                    "ip_address": str(session_data["ip_address"]),
                    "user_agent": str(session_data["user_agent"]),
                    "active": "True",
                    "username": str(session_data.get("username", "")),
                    "role_name": str(session_data.get("role_name", "")),
                    "permissions": json.dumps(session_data.get("permissions", []))
                }
                
                await redis_client.hset(
                    self._get_session_key(user_id),
                    mapping=redis_data
                )
                await redis_client.expire(
                    self._get_session_key(user_id), 
                    timeout_seconds
                )
                print(f"[DEBUG] 会话已创建在Redis中: {user_id}")
            else:
                # Redis不可用，使用备选存储方案
                session_data["expires_at"] = int(time.time()) + timeout_seconds
                async with self._lock:
                    self._fallback_sessions[user_id] = session_data
                print(f"[DEBUG] 会话已创建在备选存储中: {user_id}")
            
            return True
        except Exception as e:
            print(f"创建会话失败: {e}")
            return False
    
    async def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        try:
            redis_client = await self.get_redis_client()
            
            if redis_client:
                # Redis可用，从Redis获取
                session_data = await redis_client.hgetall(self._get_session_key(user_id))
                
                if not session_data:
                    return None
                
                # 转换数据类型
                session_data["last_activity"] = int(session_data.get("last_activity", 0))
                session_data["created_at"] = int(session_data.get("created_at", 0))
                session_data["active"] = session_data.get("active", "False").lower() == "true"
                
                return session_data
            else:
                # Redis不可用，从备选存储获取
                async with self._lock:
                    session_data = self._fallback_sessions.get(user_id)
                    if session_data:
                        # 检查是否过期
                        current_time = int(time.time())
                        expires_at = session_data.get("expires_at", 0)
                        print(f"[DEBUG] get_session备选存储 - user_id={user_id}, expires_at={expires_at}, current_time={current_time}, session_data keys={list(session_data.keys())}")
                        print(f"[DEBUG] get_session备选存储 - 时间差: {expires_at - current_time}秒")
                        if current_time > expires_at:
                            # 会话已过期，删除
                            print(f"[DEBUG] get_session备选存储 - 会话已过期，删除: user_id={user_id}")
                            del self._fallback_sessions[user_id]
                            return None
                        print(f"[DEBUG] get_session备选存储 - 会话有效，返回数据")
                        return session_data
                    else:
                        print(f"[DEBUG] get_session备选存储 - 未找到会话: user_id={user_id}, fallback_sessions keys={list(self._fallback_sessions.keys())}")
                        return None
        except Exception as e:
            print(f"获取会话失败: {e}")
            return None
    
    async def update_last_activity(self, user_id: str) -> bool:
        """更新最后活动时间"""
        try:
            redis_client = await self.get_redis_client()
            
            # 检查会话是否存在且活跃
            session_data = await self.get_session(user_id)
            if not session_data or not session_data.get("active"):
                return False
            
            if redis_client:
                # Redis可用，更新Redis中的会话
                await redis_client.hset(
                    self._get_session_key(user_id),
                    "last_activity",
                    str(int(time.time()))
                )
                # 刷新Redis键的TTL，延长会话有效期
                timeout_seconds = dynamic_settings.SLIDING_SESSION_TIMEOUT_MINUTES * 60
                await redis_client.expire(
                    self._get_session_key(user_id), 
                    timeout_seconds
                )
            else:
                # Redis不可用，更新备选存储中的会话
                async with self._lock:
                    if user_id in self._fallback_sessions:
                        current_time = int(time.time())
                        self._fallback_sessions[user_id]["last_activity"] = current_time
                        # 在备用模式下也需要更新过期时间，实现真正的滑动过期
                        timeout_seconds = dynamic_settings.SLIDING_SESSION_TIMEOUT_MINUTES * 60
                        self._fallback_sessions[user_id]["expires_at"] = current_time + timeout_seconds
            
            return True
        except Exception as e:
            print(f"更新活动时间失败: {e}")
            return False
    
    async def is_session_valid(self, user_id: str) -> bool:
        """检查会话是否有效（未超时）"""
        try:
            session_data = await self.get_session(user_id)
            if not session_data:
                print(f"[DEBUG] is_session_valid - 未找到会话数据: user_id={user_id}")
                return False
                
            # 检查会话是否活跃
            active = session_data.get("active", False)
            print(f"[DEBUG] is_session_valid - 获取active字段: {active}, 类型: {type(active)}")
            if not active:
                print(f"[DEBUG] is_session_valid - 会话不活跃: user_id={user_id}, active={active}")
                return False
            
            last_activity = session_data.get("last_activity", 0)
            current_time = int(time.time())
            timeout_seconds = dynamic_settings.SLIDING_SESSION_TIMEOUT_MINUTES * 60
            time_diff = current_time - last_activity

            print(f"[DEBUG] is_session_valid - user_id={user_id}, active={active}, last_activity={last_activity}, current_time={current_time}, timeout_seconds={timeout_seconds}, time_diff={time_diff}, expires_at={session_data.get('expires_at', 'N/A')}")
            # 检查是否超时
            if time_diff > timeout_seconds:
                # 会话超时，标记为不活跃
                print(f"[DEBUG] is_session_valid - 会话超时，标记为不活跃: user_id={user_id}, time_diff={time_diff} > timeout_seconds={timeout_seconds}")
                await self.invalidate_session(user_id)
                return False
            
            print(f"[DEBUG] is_session_valid - 会话有效: user_id={user_id}")
            return True
        except Exception as e:
            print(f"检查会话有效性失败: {e}")
            return False
    
    async def invalidate_session(self, user_id: str) -> bool:
        """使会话失效"""
        try:
            redis_client = await self.get_redis_client()
            
            if redis_client:
                # Redis可用，在Redis中使会话失效
                await redis_client.hset(self._get_session_key(user_id), "active", "False")
            else:
                # Redis不可用，在备选存储中使会话失效
                async with self._lock:
                    if user_id in self._fallback_sessions:
                        self._fallback_sessions[user_id]["active"] = False
            
            return True
        except Exception as e:
            print(f"使会话失效失败: {e}")
            return False
    
    async def delete_session(self, user_id: str) -> bool:
        """删除会话"""
        try:
            print(f"[DEBUG] delete_session - 方法开始执行: user_id={user_id}")
            redis_client = await self.get_redis_client()
            print(f"[DEBUG] delete_session - Redis客户端状态: {redis_client is not None}")
            
            print(f"[DEBUG] delete_session - 开始删除会话: user_id={user_id}")
            if redis_client:
                print(f"[DEBUG] delete_session - 使用Redis删除会话")
                # Redis可用，从Redis删除会话
                await redis_client.delete(self._get_session_key(user_id))
                print(f"[DEBUG] delete_session - Redis会话删除完成")
            else:
                print(f"[DEBUG] delete_session - 使用备选存储方案")
                # Redis不可用，从备选存储删除会话
                async with self._lock:
                    print(f"[DEBUG] delete_session - 获取锁成功")
                    if user_id in self._fallback_sessions:
                        print(f"[DEBUG] delete_session - 找到备选存储中的会话")
                        # 在删除会话前，记录登出信息
                        session_data = self._fallback_sessions[user_id]
                        username = session_data.get("username", "")
                        print(f"[DEBUG] delete_session - 会话中的用户名: {username}")
                        
                        # 记录登出时间到数据库
                        if username:
                            try:
                                from database import get_db
                                from core.login_record_manager import get_login_record_manager
                                from sqlmodel import Session, select
                                from models.account.user import User
                                
                                db = next(get_db())
                                login_record_manager = get_login_record_manager()
                                
                                # 查找用户ID
                                user = db.exec(select(User).where(User.username == username)).first()
                                if user:
                                    print(f"[DEBUG] delete_session - 找到用户ID: {user.id}")
                                    # 获取当前会话的IP地址（从会话数据中）
                                    session_ip = session_data.get("ip_address", None)
                                    await login_record_manager.record_logout(db, user.id, session_ip, username)
                                    print(f"[DEBUG] 备选存储方案 - 已记录用户登出: {username}")
                                else:
                                    print(f"[DEBUG] delete_session - 未找到用户")
                                
                                db.close()
                            except Exception as db_error:
                                print(f"[WARNING] 备选存储方案 - 记录登出信息失败: {db_error}")
                        else:
                            print(f"[DEBUG] delete_session - 会话中没有用户名")
                        
                        # 删除会话
                        del self._fallback_sessions[user_id]
                        print(f"[DEBUG] delete_session - 备选存储会话删除完成")
                    else:
                        print(f"[DEBUG] delete_session - 备选存储中未找到会话")
            
            print(f"[DEBUG] delete_session - 方法执行完成，返回True")
            return True
        except Exception as e:
            print(f"删除会话失败: {e}")
            return False


# 全局会话管理器实例
session_manager = SessionManager()