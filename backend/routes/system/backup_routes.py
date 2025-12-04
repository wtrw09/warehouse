"""
备份路由模块

该模块提供备份相关的API接口
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Security
import logging

from backup.backup_manager import get_backup_manager

from core.security import get_current_user, get_required_scopes_for_route
from models.account.user import User
from models.system.backup import BackupListResponse

# 配置日志
logger = logging.getLogger(__name__)

# 创建备份路由
backup_router = APIRouter(prefix="/api/backup", tags=["backup"])



@backup_router.post("/create")
async def create_backup(
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/api/backup/create"))
):
    """
    创建手动备份（固定使用user_full类型）
    
    Returns:
        备份创建结果
    """
    try:
        # 直接执行备份操作
        backup_manager = get_backup_manager()
        result = backup_manager.create_backup("user_full")
        
        return {"message": "备份创建成功", "result": result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")



@backup_router.get("/list", response_model=BackupListResponse)
async def get_backup_list(
    keyword: str = None,
    backup_type: str = "all",
    sort_by: str = "timestamp",
    sort_order: str = "desc",
    days_back: int = None,
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/api/backup/list"))
):
    """
    获取备份列表（支持搜索、筛选和排序）
    
    Args:
        keyword: 文件名关键词搜索
        backup_type: 备份类型筛选（daily, monthly, user_full, all）
        sort_by: 排序字段（timestamp, filename, type, size）
        sort_order: 排序顺序（asc, desc）
        days_back: 回溯天数
        
    Returns:
        备份列表信息
    """
    try:
        backup_manager = get_backup_manager()
        
        # 计算时间范围
        start_date = None
        end_date = None
        if days_back is not None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
        
        # 获取备份列表
        backups = backup_manager.get_backup_list(
            backup_type=backup_type,
            start_date=start_date,
            end_date=end_date
        )
        
        # 文件名多关键词搜索（AND关系）
        if keyword:
            keywords = [k.strip().lower() for k in keyword.split() if k.strip()]
            if keywords:
                backups = [backup for backup in backups 
                          if all(k in backup["filename"].lower() for k in keywords)]
        
        # 排序处理
        if sort_by in ["timestamp", "filename", "type", "size"]:
            reverse = sort_order.lower() == "desc"
            backups.sort(key=lambda x: x[sort_by], reverse=reverse)
        
        return BackupListResponse(
            backups=backups,
            total_count=len(backups)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取备份列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")

@backup_router.post("/recover/{filename}")
async def recover_backup(
    filename: str,
    admin_password: str = None,
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/api/backup/recover"))
):
    """
    通过指定文件名恢复备份
    
    Args:
        filename: 备份文件名
        admin_password: 管理员密码（可选，用于验证）
        
    Returns:
        恢复操作启动结果
    """
    try:
        # 获取备份管理器
        backup_manager = get_backup_manager()
        
        # 验证备份文件是否存在
        backup_list = backup_manager.get_backup_list()
        backup_file = None
        for backup in backup_list:
            if backup["filename"] == filename:
                backup_file = backup
                break
        
        if not backup_file:
            raise HTTPException(status_code=404, detail=f"未找到备份文件: {filename}")
        
        # 检查是否已有恢复操作在进行
        status_file = Path("temp_recovery/restore_status.json")
        if status_file.exists():
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
                
                if status_data.get("status") == "in_progress":
                    raise HTTPException(status_code=409, detail="已有恢复操作正在进行中")
            except Exception:
                pass
        
        # 创建恢复状态文件
        status_data = {
            "status": "in_progress",
            "backup_file": filename,
            "backup_path": backup_file["path"],
            "started_at": datetime.now().isoformat(),
            "pid": None,
            "steps": {
                "stopping_services": False,
                "backing_up_current": False,
                "restoring_from_backup": False,
                "validating_integrity": False,
                "starting_services": False,
                "cleaning_up": False
            }
        }
        
        # 确保目录存在
        status_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        
        try:
            # 启动独立恢复进程 - 支持两种方式
            import subprocess
            import sys
            
            # 使用绝对路径确保子进程能找到文件
            backup_abs_path = str(Path(backup_file["path"]).absolute())
            status_abs_path = str(status_file.absolute())
            
            # 方式1: 优先使用固定恢复脚本
            fixed_recovery_script = Path("backup/manual_recovery_fixed.py")
            if fixed_recovery_script.exists():
                process = subprocess.Popen([
                    sys.executable, str(fixed_recovery_script),
                    backup_abs_path, status_abs_path
                ], cwd=Path.cwd())  # 设置正确的工作目录
                logger.info(f"使用固定恢复脚本启动恢复进程 PID: {process.pid}")
            else:
                # 方式2: 回退到原来的恢复处理器
                process = subprocess.Popen([
                    sys.executable, "-m", "backup.restore_processor",
                    backup_abs_path, status_abs_path
                ], cwd=Path.cwd())  # 设置正确的工作目录
                logger.info(f"使用恢复处理器启动恢复进程 PID: {process.pid}")
            
            # 更新状态文件中的进程ID
            status_data["pid"] = process.pid
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"启动恢复进程 PID: {process.pid}, 备份文件: {filename}")
            
            return {
                "message": "恢复操作已启动",
                "status": "in_progress",
                "pid": process.pid,
                "backup_file": filename,
                "status_file": str(status_file),
                "recovery_method": "fixed_script" if fixed_recovery_script.exists() else "restore_processor"
            }
            
        except Exception as e:
            # 清理状态文件
            if status_file.exists():
                status_file.unlink()
            
            logger.error(f"启动恢复进程失败: {str(e)}")
            raise HTTPException(status_code=500, detail="启动恢复进程失败")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"恢复操作启动失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"恢复操作启动失败: {str(e)}")

@backup_router.delete("/{filename}")
async def delete_backup(
    filename: str,
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/api/backup/{filename}"))
):
    """
    删除指定文件名的备份文件
    
    Args:
        filename: 备份文件名
        
    Returns:
        删除结果
    """
    try:
        backup_manager = get_backup_manager()
        success = backup_manager.delete_backup_by_filename(filename)
        
        if success:
            return {
                "message": f"成功删除备份文件: {filename}"
            }
        else:
            raise HTTPException(status_code=404, detail=f"未找到备份文件: {filename}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除备份失败: {str(e)}")



# 路由导出
__all__ = ["backup_router"]