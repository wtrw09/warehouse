"""
系统状态管理路由 - 提供系统健康状态、Redis状态等监控功能
"""
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlmodel import Session
from models.account.user import User
from core.security import get_current_user, get_required_scopes_for_route
from database import get_db
from initialize.initialize_system import is_system_initialized
from core.config import dynamic_settings
from core.session_manager import session_manager
from datetime import datetime

system_status_router = APIRouter(tags=["系统状态管理"])


@system_status_router.get("/system/status")
async def get_system_status(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """获取系统整体状态信息"""
    
    try:
        # 检查系统初始化状态
        system_initialized = is_system_initialized()
        
        # 获取认证策略
        auth_strategy = dynamic_settings.AUTH_STRATEGY
        
        # 检查Redis状态
        redis_status = await session_manager.check_redis_status()
        
        # 构建系统状态响应
        status_info = {
            "system_initialized": system_initialized,
            "auth_strategy": auth_strategy,
            "redis_status": redis_status,
            "timestamp": datetime.now().isoformat(),
            "status": "healthy" if system_initialized else "uninitialized"
        }
        
        # 如果Redis不可用且认证策略是滑动会话模式，添加警告信息
        if auth_strategy == "sliding_session" and not redis_status["available"]:
            status_info["warnings"] = [
                {
                    "type": "redis_unavailable",
                    "message": "Redis服务器异常，当前使用备选存储方案",
                    "severity": "warning",
                    "recommendation": "请尽快检查并启动Redis服务"
                }
            ]
            status_info["status"] = "degraded"
        
        return status_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统状态失败: {str(e)}")


@system_status_router.get("/health")
async def get_health_check():
    """Docker健康检查端点（无需认证）"""
    
    try:
        # 检查数据库连接
        try:
            db_test = next(get_db())
            db_test.close()
            db_status = "healthy"
        except Exception as e:
            db_status = "unhealthy"
        
        # 检查Redis状态
        redis_status = await session_manager.check_redis_status()
        
        # 确定整体状态
        if db_status == "healthy" and redis_status["available"]:
            overall_status = "healthy"
        elif db_status == "healthy" and not redis_status["available"]:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "database": db_status,
            "redis": "healthy" if redis_status["available"] else "unhealthy",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"健康检查失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@system_status_router.get("/system/health")
async def get_system_health(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """系统健康检查端点（需要认证）"""
    
    try:
        # 检查系统初始化状态
        if not is_system_initialized():
            return {
                "status": "unhealthy",
                "message": "系统未初始化",
                "timestamp": datetime.now().isoformat()
            }
        
        # 检查数据库连接
        try:
            # 测试数据库连接
            db_test = next(get_db())
            db_test.close()
            db_status = "healthy"
        except Exception as e:
            db_status = "unhealthy"
        
        # 检查Redis状态
        redis_status = await session_manager.check_redis_status()
        
        # 确定整体状态
        if db_status == "healthy" and redis_status["available"]:
            overall_status = "healthy"
        elif db_status == "healthy" and not redis_status["available"]:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "database": db_status,
            "redis": "healthy" if redis_status["available"] else "unhealthy",
            "redis_message": redis_status["message"],
            "fallback_active": redis_status["fallback_active"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"健康检查失败: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }


@system_status_router.get("/system/redis/alerts")
async def get_redis_alerts(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """获取Redis相关的告警信息"""
    
    try:
        # 检查系统初始化状态
        if not is_system_initialized():
            return {
                "alerts": [],
                "message": "系统未初始化，无法获取Redis状态"
            }
        
        alerts = []
        
        # 获取认证策略
        auth_strategy = dynamic_settings.AUTH_STRATEGY
        
        # 检查Redis状态
        redis_status = await session_manager.check_redis_status()
        
        # 如果认证策略是滑动会话模式且Redis不可用，添加告警
        if auth_strategy == "sliding_session" and not redis_status["available"]:
            alerts.append({
                "id": "redis_unavailable",
                "type": "warning",
                "title": "Redis服务器异常",
                "message": "Redis服务器不可用，当前使用备选存储方案",
                "severity": "warning",
                "timestamp": datetime.now().isoformat(),
                "recommendation": "请尽快检查并启动Redis服务以确保系统最佳性能",
                "details": {
                    "fallback_sessions_count": redis_status.get("fallback_sessions_count", 0),
                    "auth_strategy": auth_strategy
                }
            })
        
        # 如果Redis可用但备选存储中有会话，添加信息告警
        if redis_status["available"] and redis_status.get("fallback_sessions_count", 0) > 0:
            alerts.append({
                "id": "redis_recovered",
                "type": "info",
                "title": "Redis服务已恢复",
                "message": "Redis服务器已恢复正常，但仍有会话数据在备选存储中",
                "severity": "info",
                "timestamp": datetime.now().isoformat(),
                "recommendation": "系统将自动迁移会话数据到Redis存储",
                "details": {
                    "fallback_sessions_count": redis_status.get("fallback_sessions_count", 0)
                }
            })
        
        return {
            "alerts": alerts,
            "total": len(alerts),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Redis告警信息失败: {str(e)}")


@system_status_router.get("/system/redis/monitor")
async def monitor_redis_status(
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/system/redis/monitor"))
):
    """实时监控Redis状态（需要管理员权限）"""
    
    try:
        # 检查系统初始化状态
        if not is_system_initialized():
            raise HTTPException(status_code=400, detail="系统未初始化")
        
        # 获取详细的Redis状态信息
        redis_status = await session_manager.check_redis_status()
        
        # 如果Redis可用，获取更多详细信息
        if redis_status["available"]:
            try:
                redis_client = await session_manager.get_redis_client()
                info = await redis_client.info()
                
                # 提取关键指标
                detailed_info = {
                    "version": info.get("redis_version", "未知"),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "未知"),
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_peak_human": info.get("used_memory_peak_human", "未知"),
                    "used_memory_peak": info.get("used_memory_peak", 0),
                    "used_memory_rss": info.get("used_memory_rss", 0),
                    "used_memory_rss_human": info.get("used_memory_rss_human", "未知"),
                    "used_memory_lua": info.get("used_memory_lua", 0),
                    "used_memory_lua_human": info.get("used_memory_lua_human", "未知"),
                    "used_cpu_sys": info.get("used_cpu_sys", 0),
                    "used_cpu_user": info.get("used_cpu_user", 0),
                    "used_cpu_sys_children": info.get("used_cpu_sys_children", 0),
                    "used_cpu_user_children": info.get("used_cpu_user_children", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "hit_rate": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                }
                
                redis_status["detailed_info"] = detailed_info
                
            except Exception as e:
                redis_status["detailed_info_error"] = f"获取详细Redis信息失败: {str(e)}"
        
        return {
            "monitor_data": redis_status,
            "timestamp": datetime.now().isoformat(),
            "auth_strategy": dynamic_settings.AUTH_STRATEGY
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"监控Redis状态失败: {str(e)}")