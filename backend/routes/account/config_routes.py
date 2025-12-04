"""
配置管理路由 - 允许管理员动态切换认证策略和Redis配置（基于数据库）
"""
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlmodel import Session, select, text
from models.account.user import User
from core.security import get_current_user, get_required_scopes_for_route, Permission
from core.config import dynamic_settings
from database import get_system_config_session
from initialize.initialize_system import get_system_config
import redis.asyncio as redis

config_router = APIRouter(tags=["配置管理"])


@config_router.get("/config/auth-strategy")
async def get_auth_strategy_config(
    db: Session = Depends(get_system_config_session),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/config/auth-strategy"))
):
    """获取当前认证策略配置（从数据库）"""
    
    # 从数据库获取配置
    config_dict = get_system_config()
    
    return {
        "auth_strategy": config_dict.get("AUTH_STRATEGY", "jwt_fixed"),
        "access_token_expire_minutes": int(config_dict.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30)),
        "sliding_session_timeout_minutes": int(config_dict.get("SLIDING_SESSION_TIMEOUT_MINUTES", 480)),
        "access_token_short_expire_minutes": int(config_dict.get("ACCESS_TOKEN_SHORT_EXPIRE_MINUTES", 5)),
        "redis_url": config_dict.get("REDIS_URL", "redis://:redis123@redis:6379")
    }


@config_router.put("/config/auth-strategy")
async def update_auth_strategy_config(
    auth_strategy: str = None,
    access_token_expire_minutes: int = None,
    sliding_session_timeout_minutes: int = None,
    access_token_short_expire_minutes: int = None,
    redis_url: str = None,
    db: Session = Depends(get_system_config_session),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/config/auth-strategy"))
):
    """更新认证策略配置（到数据库）"""
    
    # 验证认证策略参数
    if auth_strategy and auth_strategy not in ["jwt_fixed", "sliding_session"]:
        raise HTTPException(status_code=400, detail="认证策略必须是 'jwt_fixed' 或 'sliding_session'")
    
    # 获取当前配置用于返回值
    current_config = get_system_config()
    
    # 更新配置到数据库
    try:
        if auth_strategy:
            update_query = text("UPDATE _system_config SET config_value = :config_value WHERE config_key = 'AUTH_STRATEGY'")
            db.execute(update_query, {"config_value": auth_strategy})
            
            if access_token_expire_minutes:
                update_query = text("UPDATE _system_config SET config_value = :config_value WHERE config_key = 'ACCESS_TOKEN_EXPIRE_MINUTES'")
                db.execute(update_query, {"config_value": str(access_token_expire_minutes)})
            
            if sliding_session_timeout_minutes:
                update_query = text("UPDATE _system_config SET config_value = :config_value WHERE config_key = 'SLIDING_SESSION_TIMEOUT_MINUTES'")
                db.execute(update_query, {"config_value": str(sliding_session_timeout_minutes)})
            
            if access_token_short_expire_minutes:
                update_query = text("UPDATE _system_config SET config_value = :config_value WHERE config_key = 'ACCESS_TOKEN_SHORT_EXPIRE_MINUTES'")
                db.execute(update_query, {"config_value": str(access_token_short_expire_minutes)})
            
            if redis_url:
                update_query = text("UPDATE _system_config SET config_value = :config_value WHERE config_key = 'REDIS_URL'")
                db.execute(update_query, {"config_value": redis_url})
            
            db.commit()
        
        # 立即刷新配置缓存，使配置立即生效
        dynamic_settings.refresh()
        print("[DEBUG] 配置缓存已刷新，配置立即生效")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")
    
    return {
        "message": "配置更新成功，已立即生效",
        "auth_strategy": auth_strategy or current_config.get("AUTH_STRATEGY", "jwt_fixed"),
        "access_token_expire_minutes": access_token_expire_minutes or int(current_config.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30)),
        "sliding_session_timeout_minutes": sliding_session_timeout_minutes or int(current_config.get("SLIDING_SESSION_TIMEOUT_MINUTES", 480)),
        "access_token_short_expire_minutes": access_token_short_expire_minutes or int(current_config.get("ACCESS_TOKEN_SHORT_EXPIRE_MINUTES", 5)),
        "redis_url": redis_url or current_config.get("REDIS_URL", "redis://:redis123@redis:6379")
    }


@config_router.get("/config/status")
async def get_auth_status(
    db: Session = Depends(get_system_config_session),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/config/status"))
):
    """获取认证系统状态信息（从数据库）"""
    
    # 从数据库获取配置
    config_dict = get_system_config()
    auth_strategy = config_dict.get("AUTH_STRATEGY", "jwt_fixed")
    
    # 检查Redis连接状态（如果使用滑动会话模式）
    redis_status = "未使用"
    if auth_strategy == "sliding_session":
        try:
            from core.session_manager import session_manager
            redis_client = await session_manager.get_redis_client()
            await redis_client.ping()
            redis_status = "正常"
        except Exception as e:
            redis_status = f"异常: {str(e)}"
    
    return {
        "current_strategy": auth_strategy,
        "strategy_description": "JWT固定过期时间" if auth_strategy == "jwt_fixed" else "滑动会话超时",
        "token_expire_minutes": int(config_dict.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30)) if auth_strategy == "jwt_fixed" else int(config_dict.get("ACCESS_TOKEN_SHORT_EXPIRE_MINUTES", 5)),
        "session_timeout_minutes": int(config_dict.get("SLIDING_SESSION_TIMEOUT_MINUTES", 480)) if auth_strategy == "sliding_session" else None,
        "redis_status": redis_status,
        "config_source": "数据库"
    }