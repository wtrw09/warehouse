from pydantic_settings import BaseSettings
from typing import Literal, Dict, Any
from sqlmodel import Session, select
import threading
from datetime import datetime, timedelta

# 延迟导入数据库引擎以避免循环导入
def get_engine():
    from database import get_engine as get_db_engine
    return get_db_engine()

def get_system_config_engine():
    from database import get_system_config_engine as get_system_config_engine_func
    return get_system_config_engine_func()

class DynamicSettings:
    """动态配置管理器 - 支持从数据库动态加载配置"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._last_update = None
        self._cache_ttl = 3600  # 缓存3600秒（60分钟），减少频繁数据库访问
        self._lock = threading.Lock()
        self._force_refresh_flag = False  # 强制刷新标志位
        
        # 默认配置
        self._defaults = {
            "DATABASE_URL": "sqlite:///./data/warehouse.db",
            "SECRET_KEY": "K8#mPq$9@L",
            "ALGORITHM": "HS256",
            "ACCESS_TOKEN_EXPIRE_MINUTES": 1440,
            "ADMIN_INVITATION_CODE": "ADMIN-7X9F-K2B8-R4P6-QTZ3",
            "AUTH_STRATEGY": "sliding_session",
            "SLIDING_SESSION_TIMEOUT_MINUTES": 1440,
            "ACCESS_TOKEN_SHORT_EXPIRE_MINUTES": 60,
            "REDIS_URL": "redis://:redis123@redis:6379"
        }
    
    def _is_cache_expired(self) -> bool:
        """检查缓存是否过期"""
        if not self._last_update:
            return True
        return datetime.now() - self._last_update > timedelta(seconds=self._cache_ttl)
    
    def _load_config_from_db(self) -> Dict[str, Any]:
        """从数据库加载配置"""
        config_dict = {}
        try:
            # 使用系统配置数据库引擎
            engine = get_system_config_engine()
            with Session(engine) as db:
                # 使用原生SQL查询避免导入SystemConfig模型
                from sqlalchemy import text
                query = text("SELECT config_key, config_value, config_type FROM _system_config WHERE is_active = 1")
                result = db.exec(query)
                configs = result.fetchall()
                
                for config in configs:
                    config_key, config_value, config_type = config
                    # 根据配置类型转换值
                    if config_type == "int":
                        config_dict[config_key] = int(config_value)
                    elif config_type == "bool":
                        config_dict[config_key] = config_value.lower() == "true"
                    else:
                        config_dict[config_key] = config_value
                
                print(f"[DEBUG] 从系统配置数据库加载了 {len(configs)} 个配置项")
                
        except Exception as e:
            print(f"[WARNING] 从系统配置数据库加载配置失败: {e}")
            # 使用默认配置
            config_dict = self._defaults.copy()
        
        return config_dict
    
    def get(self, key: str, default=None):
        """获取配置值"""
        with self._lock:
            # 检查缓存是否过期或强制刷新标志位被设置
            if self._is_cache_expired() or self._force_refresh_flag:
                # 重新加载配置
                self._cache = self._load_config_from_db()
                self._last_update = datetime.now()
                # 重置强制刷新标志位
                self._force_refresh_flag = False
            
            # 返回配置值，如果不存在则返回默认值
            return self._cache.get(key, self._defaults.get(key, default))
    
    def refresh(self):
        """强制刷新配置缓存"""
        with self._lock:
            self._cache = {}
            self._last_update = None
            print("[DEBUG] 配置缓存已强制刷新")
    
    def set_force_refresh_flag(self):
        """设置强制刷新标志位，下次获取配置时会强制刷新"""
        with self._lock:
            self._force_refresh_flag = True
            print("[DEBUG] 强制刷新标志位已设置")
    
    def get_force_refresh_flag(self):
        """获取当前强制刷新标志位状态"""
        with self._lock:
            return self._force_refresh_flag
    
    def __getattr__(self, name: str):
        """支持属性访问方式获取配置"""
        value = self.get(name)
        if value is None:
            raise AttributeError(f"配置项 '{name}' 不存在")
        return value

# 创建全局动态配置实例
dynamic_settings = DynamicSettings()

# 保持原有Settings类兼容性（用于向后兼容）
class Settings(BaseSettings):
    """静态配置类 - 用于向后兼容"""
    
    @property
    def DATABASE_URL(self) -> str:
        return dynamic_settings.DATABASE_URL
    
    @property
    def SECRET_KEY(self) -> str:
        return dynamic_settings.SECRET_KEY
    
    @property
    def ALGORITHM(self) -> str:
        return dynamic_settings.ALGORITHM
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return dynamic_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    @property
    def ADMIN_INVITATION_CODE(self) -> str:
        return dynamic_settings.ADMIN_INVITATION_CODE
    
    @property
    def AUTH_STRATEGY(self) -> str:
        return dynamic_settings.AUTH_STRATEGY
    
    @property
    def SLIDING_SESSION_TIMEOUT_MINUTES(self) -> int:
        return dynamic_settings.SLIDING_SESSION_TIMEOUT_MINUTES
    
    @property
    def ACCESS_TOKEN_SHORT_EXPIRE_MINUTES(self) -> int:
        return dynamic_settings.ACCESS_TOKEN_SHORT_EXPIRE_MINUTES
    
    @property
    def REDIS_URL(self) -> str:
        return dynamic_settings.REDIS_URL

settings = Settings()

