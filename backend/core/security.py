import bcrypt
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from core.config import dynamic_settings
from core.session_manager import session_manager
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer,SecurityScopes  
from typing import Annotated, Dict, List, Optional
from sqlmodel import Session, select
from database import get_db
from models.account.user import User
from models.account.role import Role
from schemas.account.user import UserResponse
from enum import Enum
import json

# JWT相关配置（使用动态配置）
SECRET_KEY = dynamic_settings.SECRET_KEY
ALGORITHM = dynamic_settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = dynamic_settings.ACCESS_TOKEN_EXPIRE_MINUTES

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与加密密码是否匹配"""
    # 检查密码长度，bcrypt限制为72字节
    if len(plain_password.encode('utf-8')) > 72:
        return False
    try:
        # 直接使用bcrypt库进行密码验证
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # 任何错误都返回False
        return False

def get_password_hash(password: str) -> str:
    """生成密码的哈希值"""
    # 检查密码长度，bcrypt限制为72字节
    if len(password.encode('utf-8')) > 72:
        raise ValueError("密码长度不能超过72字节")
    try:
        # 直接使用bcrypt库生成密码哈希
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hashed.decode('utf-8')
    except Exception as e:
        raise ValueError(f"密码加密失败: {e}")


def create_access_token(data: dict, ip_address: str, user_permissions: list | None = None) -> str:
    """生成JWT访问令牌，包含用户权限作为scopes"""
    to_encode = data.copy()
    
    # 根据认证策略设置不同的过期时间（使用动态配置）
    if dynamic_settings.AUTH_STRATEGY == "sliding_session":
        # 滑动会话模式：使用短时效token
        expire_minutes = dynamic_settings.ACCESS_TOKEN_SHORT_EXPIRE_MINUTES
    else:
        # 固定过期模式：使用配置的过期时间
        expire_minutes = dynamic_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire, "ip": ip_address})
    
    # 添加认证策略标识
    to_encode.update({"auth_strategy": dynamic_settings.AUTH_STRATEGY})
    
    # 添加用户权限作为scopes
    if user_permissions:
        to_encode.update({"scopes": user_permissions})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



# 权限枚举（定义所有可用权限）
class Permission(str, Enum):
    AUTH_READ = "AUTH-read"  # 用户/角色/权限读取
    AUTH_EDIT = "AUTH-edit"  # 用户/角色/权限修改
    AUTH_OWN = "AUTH-own"  # 本人信息修改
    BASE_READ = "BASE-read"  # 仓库信息读取
    BASE_EDIT = "BASE-edit"  # 仓库信息修改
    IO_READ = "IO-read"  # 出入库数据读取
    IO_EDIT = "IO-edit"  # 出入库数据修改
    STOCK_READ = "STOCK-read"  # 库存读取
    SYSTEM_READ = "SYSTEM-read"  # 系统设置读取
    SYSTEM_EDIT = "SYSTEM-edit"  # 系统设置修改

# 权限描述映射
PERMISSION_DESCRIPTIONS = {
    Permission.AUTH_READ: "用户/角色/权限读取",
    Permission.AUTH_EDIT: "用户/角色/权限修改",
    Permission.AUTH_OWN: "本人信息修改",
    Permission.BASE_READ: "仓库信息读取",
    Permission.BASE_EDIT: "仓库信息修改",
    Permission.IO_READ: "出入库数据读取",
    Permission.IO_EDIT: "出入库数据修改",
    Permission.STOCK_READ: "库存读取",
    Permission.SYSTEM_READ: "系统设置读取",
    Permission.SYSTEM_EDIT: "系统设置修改"
}

# 路由-权限映射表
ROUTE_PERMISSIONS: Dict[str, List[Permission]] = {
    # 配置管理
    "/config/auth-strategy": [Permission.SYSTEM_EDIT],
    "/config/status": [Permission.SYSTEM_READ],

    
    # 系统配置管理
    "/system/init/status": [Permission.SYSTEM_READ],
    "/system/init": [Permission.SYSTEM_EDIT],
    "/system/config": [Permission.SYSTEM_EDIT],
    
    # 角色管理
    "/roles": [Permission.AUTH_READ],
    "/roles/new": [Permission.AUTH_EDIT],
    "/roles/delete": [Permission.AUTH_EDIT],
    "/roles/update": [Permission.AUTH_EDIT],
    "/roles/permissions": [Permission.AUTH_EDIT],
    
    # 权限管理
    "/permissions": [Permission.AUTH_READ],
    
    # 用户管理
    "/users": [Permission.AUTH_READ],
    "/users/me": [Permission.AUTH_OWN],
    "/users/new": [Permission.AUTH_EDIT],
    "/users/update": [Permission.AUTH_EDIT],
    "/users/delete": [Permission.AUTH_EDIT],
    "/users/statistics": [Permission.AUTH_READ],

    # 仓库管理
    "/warehouses": [Permission.STOCK_READ],
    "/warehouses/new": [Permission.BASE_EDIT],
    "/warehouses/get": [Permission.BASE_READ],
    "/warehouses/update": [Permission.BASE_EDIT],
    "/warehouses/delete": [Permission.BASE_EDIT],
    "/warehouses/statistics": [Permission.BASE_READ],

    # 客户管理
    "/customers": [Permission.BASE_READ],
    "/customers/new": [Permission.BASE_EDIT],
    "/customers/get": [Permission.BASE_READ],
    "/customers/update": [Permission.BASE_EDIT],
    "/customers/delete": [Permission.BASE_EDIT],
    "/customers/statistics": [Permission.BASE_READ],

    # 供应商管理
    "/suppliers": [Permission.BASE_READ],
    "/suppliers/new": [Permission.BASE_EDIT],
    "/suppliers/get": [Permission.BASE_READ],
    "/suppliers/update": [Permission.BASE_EDIT],
    "/suppliers/delete": [Permission.BASE_EDIT],
    "/suppliers/statistics": [Permission.BASE_READ],
    "/suppliers/batch-import": [Permission.BASE_EDIT],
    "/suppliers/import-template": [Permission.BASE_EDIT],
    "/suppliers/download-error-file": [Permission.BASE_EDIT],

    # 货位管理
    "/bins": [Permission.BASE_READ],
    "/bins/statistics": [Permission.BASE_READ],
    "/bins/get": [Permission.BASE_READ],
    "/bins/new": [Permission.BASE_EDIT],
    "/bins/update": [Permission.BASE_EDIT],
    "/bins/delete": [Permission.BASE_EDIT],

    # 专业管理
    "/majors": [Permission.BASE_READ],
    "/majors/new": [Permission.BASE_EDIT],
    "/majors/get": [Permission.BASE_READ],
    "/majors/update": [Permission.BASE_EDIT],
    "/majors/delete": [Permission.BASE_EDIT],
    "/majors/statistics": [Permission.BASE_READ],

    # 装备管理
    "/equipments": [Permission.BASE_READ],
    "/equipments/new": [Permission.BASE_EDIT],
    "/equipments/get": [Permission.BASE_READ],
    "/equipments/update": [Permission.BASE_EDIT],
    "/equipments/delete": [Permission.BASE_EDIT],
    "/equipments/statistics": [Permission.BASE_READ],

    # 器材管理
    "/materials": [Permission.BASE_READ],
    "/materials/new": [Permission.BASE_EDIT],
    "/materials/get": [Permission.BASE_READ],
    "/materials/update": [Permission.BASE_EDIT],
    "/materials/delete": [Permission.BASE_EDIT],
    "/materials/statistics": [Permission.BASE_READ],
    "/materials/major-options": [Permission.BASE_READ],
    "/materials/equipment-options": [Permission.BASE_READ],
    "/materials/download-error-file": [Permission.BASE_EDIT],

    # 器材编码分类层级管理
    "/material-code-levels": [Permission.BASE_EDIT],
    "/material-code-levels/new": [Permission.BASE_EDIT],
    "/material-code-levels/get": [Permission.BASE_EDIT],
    "/material-code-levels/update": [Permission.BASE_EDIT],
    "/material-code-levels/delete": [Permission.BASE_EDIT],
    "/material-code-levels/statistics": [Permission.BASE_EDIT],
    "/material-code-levels/delete-all": [Permission.BASE_EDIT],
    "/material-code-levels/generate-from-sub-majors": [Permission.BASE_EDIT],

    # 二级专业管理
    "/sub-majors": [Permission.BASE_READ],
    "/sub-majors/new": [Permission.BASE_EDIT],
    "/sub-majors/get": [Permission.BASE_READ],
    "/sub-majors/update": [Permission.BASE_EDIT],
    "/sub-majors/delete": [Permission.BASE_EDIT],
    "/sub-majors/statistics": [Permission.BASE_READ],
    
    # 库存变更流水管理
    "/inventory-transactions": [Permission.IO_READ],
    "/inventory-transactions/all": [Permission.IO_READ],
    "/inventory-transactions/get": [Permission.IO_READ],
    "/inventory-transactions/new": [Permission.IO_EDIT],
    "/inventory-transactions/statistics": [Permission.IO_READ],
    
    # 入库单管理
    "/inbound-orders": [Permission.IO_READ],
    "/inbound-orders/all": [Permission.IO_READ],
    "/inbound-orders/get": [Permission.IO_READ],
    "/inbound-orders/statistics": [Permission.IO_READ],
    "/inbound-orders/new": [Permission.IO_EDIT],
    "/inbound-orders/delete": [Permission.IO_EDIT],
    "/inbound-orders/update-order-number": [Permission.IO_EDIT],
    "/inbound-orders/update-transfer-number": [Permission.IO_EDIT],
    "/inbound-orders/update-supplier": [Permission.IO_EDIT],
    "/inbound-orders/update-contract-number": [Permission.IO_EDIT],
    "/inbound-orders/update-create-time": [Permission.IO_EDIT],
    "/inbound-orders/items/new": [Permission.IO_EDIT],
    "/inbound-orders/items/update": [Permission.IO_EDIT],
    "/inbound-orders/items/delete": [Permission.IO_EDIT],
    "/inbound-orders/generate-order-number": [Permission.IO_EDIT],
    "/inbound-orders/generate-batch-code": [Permission.IO_EDIT],
    "/inbound-orders/suppliers": [Permission.IO_READ],
    "/inbound-orders/pdf": [Permission.IO_EDIT],
    "/inbound-orders/excel": [Permission.IO_EDIT],
    
    # 出库单管理
    "/outbound-orders": [Permission.IO_READ],
    "/outbound-orders/all": [Permission.IO_READ],
    "/outbound-orders/get": [Permission.IO_READ],
    "/outbound-orders/statistics": [Permission.IO_READ],
    "/outbound-orders/new": [Permission.IO_EDIT],
    "/outbound-orders/delete": [Permission.IO_EDIT],
    "/outbound-orders/update-order-number": [Permission.IO_EDIT],
    "/outbound-orders/update-transfer-number": [Permission.IO_EDIT],
    "/outbound-orders/update-customer": [Permission.IO_EDIT],
    "/outbound-orders/items/new": [Permission.IO_EDIT],
    "/outbound-orders/items/update": [Permission.IO_EDIT],
    "/outbound-orders/items/delete": [Permission.IO_EDIT],
    "/outbound-orders/generate-order-number": [Permission.IO_EDIT],
    "/outbound-orders/customers": [Permission.IO_READ],
    "/outbound-orders/pdf": [Permission.IO_EDIT],
    "/outbound-orders/excel": [Permission.IO_EDIT],
    
    # 库存器材明细查询
    "/inventory-details": [Permission.STOCK_READ],
    "/inventory-details/all": [Permission.STOCK_READ],
    "/inventory-details/major-ids": [Permission.STOCK_READ],
    "/inventory-details/equipment-ids": [Permission.STOCK_READ],
    "/inventory-details/export-excel": [Permission.STOCK_READ],

    # 器材分类账页
    "/material-ledger/pdf": [Permission.IO_EDIT],
    
    # 数据库恢复管理
    "/api/backup/create": [Permission.SYSTEM_EDIT],
    "/api/backup/recover": [Permission.SYSTEM_EDIT],
    "/api/backup/status": [Permission.SYSTEM_READ],
    "/api/backup/backups": [Permission.SYSTEM_READ],
    "/api/backup/history": [Permission.SYSTEM_READ],
    "/api/backup/cleanup": [Permission.SYSTEM_EDIT],
    
    # 登录记录查询
    "/login-records": [Permission.AUTH_READ],
    "/login-records/{record_id}": [Permission.AUTH_READ],
    "/login-records/stats/summary": [Permission.AUTH_READ],
    "/login-records/my": [Permission.AUTH_OWN],
}

def get_required_scopes_for_route(route_path: str) -> list:
    """根据路由路径从配置映射表中获取所需的权限scopes"""
    required_permissions = ROUTE_PERMISSIONS.get(route_path, [])
    # 将Permission枚举转换为字符串格式的scopes
    return [perm.value for perm in required_permissions]
    
# OAuth2 with scopes for permission checking
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login",
    scopes={perm.value: PERMISSION_DESCRIPTIONS[perm] for perm in Permission}
)

async def get_current_user(
    request: Request,
    security_scopes: SecurityScopes,  # 自动解析所需的scopes
    token: str = Depends(oauth2_scheme)
)-> Dict:
    """从JWT令牌中获取当前用户，支持两种认证策略"""
    print(f"[DEBUG] get_current_user() - 开始用户认证")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解码JWT令牌
        print(f"获取信息1 - SECRET_KEY: {SECRET_KEY}, ALGORITHM: {ALGORITHM}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"获取信息2 - 解码成功: {payload}")
        username: str | None = payload.get("username")
        user_scopes: List[str] = payload.get("scopes", [])  # JWT中存储的权限
        auth_strategy: str = payload.get("auth_strategy", "jwt_fixed")
        
        if username is None:
            raise credentials_exception
            
        # 检查权限是否足够（如果路由定义了required_scopes）
        if security_scopes.scopes:
            for scope in security_scopes.scopes:
                if scope not in user_scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少权限: {scope}",
                    )
        print(f"当前模式：{auth_strategy}")
        # 根据认证策略进行额外验证
        if auth_strategy == "sliding_session":
            # 滑动会话模式：检查会话状态
            is_valid = await session_manager.is_session_valid(username)
            print(f"[DEBUG] get_current_user() - 滑动会话验证结果: {is_valid}")
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="会话已过期，请重新登录",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # 更新最后活动时间
            await session_manager.update_last_activity(username)
        else:
            # JWT固定模式：检查令牌是否过期
            expire_timestamp = payload.get("exp")
            if expire_timestamp:
                expire_time = datetime.fromtimestamp(expire_timestamp, tz=timezone.utc)
                current_time = datetime.now(timezone.utc)
                if current_time > expire_time:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="令牌已过期，请重新登录",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            
    except jwt.ExpiredSignatureError:
        # JWT令牌过期
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception    
    
    # 构建用户信息
    user_info = {
         "username": username,
         "scopes": user_scopes,
         "auth_strategy": auth_strategy,
    }
    
    # 如果Redis不可用，添加提醒标记
    if auth_strategy == "sliding_session" and not session_manager.is_redis_available():
        user_info["redis_unavailable"] = True
        user_info["redis_status_message"] = "Redis服务器异常，当前使用备选存储方案，请尽快处理Redis服务"
    
    return user_info


async def get_current_active_user(
    current_user: Annotated[Dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
) -> UserResponse:
    """获取当前活跃用户的完整信息并返回UserResponse"""
    
    username = current_user.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取Redis状态信息
    redis_unavailable = current_user.get("redis_unavailable")
    redis_status_message = current_user.get("redis_status_message")
    
    # 优先从会话中获取用户信息（避免数据库查询）
    auth_strategy = current_user.get("auth_strategy")
    
    if auth_strategy == "sliding_session":
        # 滑动会话模式：从会话获取用户信息
        session_data = await session_manager.get_session(username)
        
        if session_data and session_data.get("active"):
            # 从会话中构建用户响应（无需查数据库）
            permissions_str = session_data.get("permissions", "[]")
            permissions = json.loads(permissions_str) if isinstance(permissions_str, str) else permissions_str
            
            # 从数据库仅获取user_id和department（轻量查询）
            user_data = db.exec(
                select(User)
                .where(User.username == username, User.is_delete != True)
            ).first()
            
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return UserResponse(
                id=user_data.id,
                username=username,
                role_id=user_data.role_id,
                roleName=session_data.get("role_name", ""),
                permissions=permissions,
                department=user_data.department,
                create_time=user_data.create_time if user_data.create_time else datetime.now(timezone.utc),
                update_time=user_data.update_time if user_data.update_time else datetime.now(timezone.utc),
                redis_unavailable=redis_unavailable,
                redis_status_message=redis_status_message
            )
    
    # JWT固定模式：优先从Token中解析用户信息（避免数据库查询）
    user_scopes = current_user.get("scopes", [])
    
    # 从数据库仅获取必要的补充信息（id, department, timestamps）
    user_data = db.exec(
        select(User)
        .where(User.username == username, User.is_delete != True)
    ).first()
    
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从数据库加载角色名称（轻量查询）
    role = db.exec(select(Role).where(Role.id == user_data.role_id)).first()
    
    # 构建UserResponse对象（权限直接从JWT获取）
    return UserResponse(
        id=user_data.id,
        username=user_data.username,
        role_id=user_data.role_id,
        roleName=role.name if role else "",
        permissions=user_scopes,  # 直接使用JWT中的权限
        department=user_data.department,
        create_time=user_data.create_time if user_data.create_time else datetime.now(timezone.utc),
        update_time=user_data.update_time if user_data.update_time else datetime.now(timezone.utc),
        redis_unavailable=redis_unavailable,
        redis_status_message=redis_status_message
    )



