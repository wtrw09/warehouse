"""
系统配置管理路由 - 管理数据库中的系统配置
"""
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlmodel import Session, select
from sqlalchemy import text
from models.account.user import User
from models.system.system_init import SystemInit
from core.security import get_current_user, get_required_scopes_for_route, Permission
from database import get_db
from database import get_system_config_session
from initialize.initialize_system import is_system_initialized, initialize_system_config, get_system_config as get_system_config_dict, update_system_config
from datetime import datetime
from core.config import dynamic_settings
from core.session_manager import session_manager

# 系统配置数据库依赖函数
def get_system_config_db():
    """获取系统配置数据库会话"""
    with get_system_config_session() as session:
        yield session

system_config_router = APIRouter(tags=["系统配置管理"])


@system_config_router.get("/system/init/status")
async def get_system_init_status(
    db: Session = Depends(get_system_config_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/system/init/status"))
):
    """获取系统初始化状态"""
    
    try:
        # 检查系统初始化表是否存在
        result = db.exec(select(SystemInit))
        init_record = result.first()
        
        return {
            "initialized": init_record is not None and init_record.initialized,
            "init_time": init_record.init_time if init_record else None,
            "init_version": init_record.init_version if init_record else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统初始化状态失败: {str(e)}")


@system_config_router.post("/system/init")
async def initialize_system(
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/system/init"))
):
    """初始化系统配置"""
    
    # 检查是否已初始化
    if is_system_initialized():
        raise HTTPException(status_code=400, detail="系统已初始化，无需重复初始化")
    
    try:
        # 执行系统初始化
        initialize_system_config()
        
        return {
            "message": "系统初始化完成",
            "init_time": datetime.now(),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"系统初始化失败: {str(e)}")


@system_config_router.get("/system/config")
async def get_all_system_configs(
    db: Session = Depends(get_system_config_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/system/config"))
):
    """获取所有系统配置（不包含敏感配置项）"""
    
    try:
        # 检查系统是否已初始化
        if not is_system_initialized():
            raise HTTPException(status_code=400, detail="系统未初始化，请先执行系统初始化")
        
        # 定义不允许返回的敏感配置项
        protected_configs = ["SECRET_KEY", "ALGORITHM", "ADMIN_INVITATION_CODE"]
        protected_placeholders = ",".join([":key" + str(i) for i in range(len(protected_configs))])
        
        # 使用原生SQL查询获取所有配置，排除敏感配置项
        query = text("""
            SELECT id, config_key, config_value, config_type, description, created_time, updated_time, is_active 
            FROM _system_config 
            WHERE is_active = 1 AND config_key NOT IN ({})
        """.format(protected_placeholders))
        
        params = {"key" + str(i): key for i, key in enumerate(protected_configs)}
        result = db.execute(query, params)
        configs = result.fetchall()
        
        config_list = []
        for config in configs:
            config_list.append({
                "id": config.id,
                "config_key": config.config_key,
                "config_value": config.config_value,
                "config_type": config.config_type,
                "description": config.description,
                "created_time": config.created_time,
                "updated_time": config.updated_time,
                "is_active": config.is_active
            })
        
        return {
            "configs": config_list,
            "total": len(config_list)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")


@system_config_router.get("/system/config/{config_key}")
async def get_system_config(
    config_key: str,
    db: Session = Depends(get_system_config_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/system/config/{config_key}"))
):
    """获取特定系统配置"""
    
    try:
        # 检查系统是否已初始化
        if not is_system_initialized():
            raise HTTPException(status_code=400, detail="系统未初始化，请先执行系统初始化")
        
        # 使用原生SQL查询获取配置
        query = text("""
            SELECT id, config_key, config_value, config_type, description, created_time, updated_time, is_active 
            FROM _system_config 
            WHERE config_key = :config_key AND is_active = 1
        """)
        
        result = db.execute(query, {"config_key": config_key})
        config = result.fetchone()
        
        if not config:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_key}")
        
        return {
            "id": config.id,
            "config_key": config.config_key,
            "config_value": config.config_value,
            "config_type": config.config_type,
            "description": config.description,
            "created_time": config.created_time,
            "updated_time": config.updated_time,
            "is_active": config.is_active
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统配置失败: {str(e)}")


@system_config_router.put("/system/config/{config_key}")
async def update_system_config(
    config_key: str,
    config_update: dict,
    db: Session = Depends(get_system_config_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/system/config"))
):
    """更新系统配置"""
    
    try:
        # 检查系统是否已初始化
        if not is_system_initialized():
            raise HTTPException(status_code=400, detail="系统未初始化，请先执行系统初始化")
        
        # 检查是否为不允许修改的敏感配置项
        protected_configs = ["SECRET_KEY", "ALGORITHM", "ADMIN_INVITATION_CODE"]
        if config_key in protected_configs:
            raise HTTPException(
                status_code=403, 
                detail=f"配置项 '{config_key}' 是系统关键配置，不允许通过API修改"
            )
        
        # 使用原生SQL查询获取配置
        query = text("""
            SELECT id, config_key, config_value, config_type, description, created_time, updated_time, is_active 
            FROM _system_config 
            WHERE config_key = :config_key AND is_active = 1
        """)
        
        result = db.execute(query, {"config_key": config_key})
        config = result.fetchone()
        
        if not config:
            raise HTTPException(status_code=404, detail=f"配置不存在: {config_key}")
        
        # 从请求体中获取配置值
        config_value = config_update.get("config_value")
        if config_value is None:
            raise HTTPException(status_code=400, detail="请求体中缺少config_value字段")
        
        # 验证配置值类型
        config_type = config.config_type
        if config_type == "int":
            try:
                int(config_value)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"配置值必须是整数: {config_key}")
        elif config_type == "bool":
            if config_value.lower() not in ("true", "false"):
                raise HTTPException(status_code=400, detail=f"配置值必须是 'true' 或 'false': {config_key}")
        
        # 使用原生SQL更新配置
        update_query = text("""
            UPDATE _system_config 
            SET config_value = :config_value, updated_time = :updated_time 
            WHERE config_key = :config_key AND is_active = 1
        """)
        
        db.execute(update_query, {
            "config_value": config_value,
            "updated_time": datetime.now(),
            "config_key": config_key
        })
        db.commit()
        
        # 设置强制刷新标志位，确保下次获取配置时使用最新值
        dynamic_settings.set_force_refresh_flag()
        
        return {
            "message": "配置更新成功",
            "config_key": config_key,
            "config_value": config_value,
            "updated_time": config.updated_time,
            "config_cache_refreshed": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新系统配置失败: {str(e)}")


@system_config_router.get("/system/redis/status")
async def test_redis_status(
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/system/redis/status"))
):
    """测试Redis服务器状态"""
    
    try:
        # 检查系统是否已初始化
        if not is_system_initialized():
            raise HTTPException(status_code=400, detail="系统未初始化，请先执行系统初始化")
        
        # 获取认证策略配置
        config_dict = get_system_config_dict()
        auth_strategy = config_dict.get("AUTH_STRATEGY", "jwt_fixed")
        
        # 如果当前认证策略是滑动会话模式，检查Redis配置是否存在
        if auth_strategy == "sliding_session":
            redis_url = config_dict.get("REDIS_URL")
            if not redis_url:
                return {
                    "status": "error",
                    "message": "当前认证策略为滑动会话模式，但Redis配置未启用",
                    "redis_available": False
                }
        
        # 使用session_manager检查Redis状态
        redis_status = await session_manager.check_redis_status()
        
        # 构建响应
        response_data = {
            "status": "success" if redis_status["available"] else "error",
            "message": redis_status["message"],
            "redis_available": redis_status["available"],
            "fallback_active": redis_status["fallback_active"],
            "fallback_sessions_count": redis_status.get("fallback_sessions_count", 0),
            "auth_strategy": auth_strategy
        }
        
        # 如果Redis可用，尝试获取更多信息
        if redis_status["available"]:
            try:
                redis_client = await session_manager.get_redis_client()
                info = await redis_client.info()
                response_data.update({
                    "redis_version": info.get("redis_version", "未知"),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "未知")
                })
            except Exception as e:
                print(f"[DEBUG] 获取Redis详细信息失败: {e}")
        
        return response_data
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试Redis状态失败: {str(e)}")