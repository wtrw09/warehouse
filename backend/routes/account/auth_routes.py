from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import Annotated
from jose import JWTError, jwt
from models.account.user import User
from models.account.role import Role
from schemas.account.user import UserResponse
from core.security import get_password_hash, verify_password, create_access_token, get_current_active_user, get_current_user, get_required_scopes_for_route, SECRET_KEY, ALGORITHM
from core.session_manager import session_manager
from core.login_record_manager import get_login_record_manager
from database import get_db
from core.config import dynamic_settings

# 创建用户认证的路由
auth_router = APIRouter(prefix="", tags=["注册与用认证"])

def get_real_client_ip(request: Request) -> str:
    """
    获取真实客户端IP地址（考虑反向代理场景）
    
    当使用Nginx等反向代理时，request.client.host返回的是代理服务器的IP，
    而非真实客户端IP。此函数按优先级从HTTP请求头中提取真实IP。
    
    优先级顺序：
    1. X-Real-IP - Nginx proxy_set_header设置的真实IP（最可靠）
    2. X-Forwarded-For - 代理链中的第一个IP（备用方案）
    3. request.client.host - 直连时的IP（fallback）
    
    Args:
        request: FastAPI的Request对象
    
    Returns:
        str: 客户端真实IP地址
    """
    # 1. 优先从 X-Real-IP 获取（Nginx设置）
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # 2. 从 X-Forwarded-For 获取第一个IP（客户端IP）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For 格式: client_ip, proxy1_ip, proxy2_ip
        # 取第一个IP作为客户端IP
        first_ip = forwarded_for.split(",")[0].strip()
        if first_ip:
            return first_ip
    
    # 3. Fallback到直连IP（无代理场景）
    return request.client.host if request.client else "unknown"

@auth_router.post("/register", response_model=UserResponse)
def register_user(
    db: Annotated[Session, Depends(get_db)],
    username: str = Form(...),
    password: str = Form(...),
    invitation_code: str = Form(None)
):
    # 调试信息
    print(f"[DEBUG] 注册接口收到参数:")
    print(f"  username: {username}")
    print(f"  password: {'*' * len(password) if password else None}")
    print(f"  invitation_code: {invitation_code}")
    print(f"  系统配置的邀请码: {dynamic_settings.ADMIN_INVITATION_CODE}")
    print(f"  邀请码是否匹配: {invitation_code == dynamic_settings.ADMIN_INVITATION_CODE if invitation_code else False}")
    
    # 检查用户名是否已存在
    db_user = db.exec(select(User).where(User.username == username)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邀请码，决定用户角色
    if invitation_code and invitation_code == dynamic_settings.ADMIN_INVITATION_CODE:
        # 管理员邀请码正确，注册为管理员
        role = db.exec(select(Role).where(Role.name == "管理员")).first()
    else:
        # 目前不支持普通用户注册，提示错误信息
        raise HTTPException(status_code=400, detail="目前不支持普通用户注册，请与管理员联系")
    
    # 创建新用户
    hashed_password = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_password, role_id=role.id)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user) 
    # 创建符合UserResponse模型的响应对象，包含权限列表
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        role_id=new_user.role_id,
        roleName=role.name,
        permissions=[perm.id for perm in role.permissions],
        create_time=new_user.create_time,
        update_time=new_user.update_time
    )

@auth_router.post("/login")
async def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 密码模式登录接口，支持两种认证策略，实现单IP登录限制"""
    # 查找用户并加载角色信息
    user = db.exec(select(User).join(Role).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 获取客户端IP地址和User-Agent（考虑反向代理场景）
    client_host = get_real_client_ip(request)
    user_agent = request.headers.get("user-agent", "unknown")
    
    # 获取登录记录管理器
    login_record_manager = get_login_record_manager()
    
    # 检查单IP登录限制
    allow_login = await login_record_manager.check_single_ip_login(db, user.id, client_host)
    
    if not allow_login:
        # 有其他IP的活跃会话，强制登出其他会话
        logout_count = await login_record_manager.force_logout_other_sessions(db, user.id, client_host)
        
        # 如果使用滑动会话模式，还需要清理Redis会话
        if dynamic_settings.AUTH_STRATEGY == "sliding_session" and logout_count > 0:
            # 强制删除Redis中的其他会话
            await session_manager.delete_session(user.username)
        
        # 返回警告信息
        response_data = {
            "access_token": None,
            "token_type": "bearer",
            "warning": f"检测到您在其他位置登录，已强制登出 {logout_count} 个会话，请重新登录"
        }
        
        # 记录新的登录
        await login_record_manager.record_login(db, user.id, user.username, client_host, user_agent)
        
        return response_data
    
    # 获取用户权限列表
    user_permissions = [perm.id for perm in user.role.permissions]
    
    # 生成JWT令牌，添加用户名、角色名和权限scopes
    access_token = create_access_token(
        data={"username": user.username, "role_name": user.role.name},
        ip_address=client_host,
        user_permissions=user_permissions
    )
    
    # 记录登录
    await login_record_manager.record_login(db, user.id, user.username, client_host, user_agent)
    
    # 根据认证策略处理会话管理
    response_data = {"access_token": access_token, "token_type": "bearer"}
    
    if dynamic_settings.AUTH_STRATEGY == "sliding_session":
        # 滑动会话模式：创建会话
        
        # 检查Redis是否可用
        redis_available = session_manager.is_redis_available()
        
        # 创建会话
        await session_manager.create_session(
            user_id=user.username,
            user_data={
                "username": user.username,
                "role_name": user.role.name,
                "permissions": user_permissions
            },  # 传递必要的用户信息
            ip_address=client_host,
            user_agent=user_agent
        )
        
        # 调试：打印会话创建信息
        print(f"[DEBUG] 登录接口 - 会话创建: user_id={user.username}, redis_available={redis_available}")
        # 尝试获取会话以验证
        session_data = await session_manager.get_session(user.username)
        print(f"[DEBUG] 登录接口 - 获取会话数据: {session_data}")
        
        # 如果Redis不可用，在响应中添加提醒信息
        if not redis_available:
            response_data["redis_unavailable"] = True
            response_data["redis_status_message"] = "Redis服务器异常，当前使用备选存储方案，请尽快处理Redis服务"
            print(f"[DEBUG] 登录接口检测到Redis不可用，已添加提醒信息")
    
    return response_data


@auth_router.post("/refresh-token")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """JWT令牌续期接口 - 前端在令牌过期前调用此接口获取新令牌"""
    
    # 从Authorization头获取令牌
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="缺少有效的认证令牌",
            headers={"X-Error-Code": "INVALID_TOKEN"}
        )
    
    token = authorization.replace("Bearer ", "")
    
    # 尝试解析令牌，即使过期也要获取用户名
    username = None
    auth_strategy = None
    
    try:
        # 解码JWT令牌（即使过期也要尝试获取用户名）
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        username = payload.get("username")
        auth_strategy = payload.get("auth_strategy", "jwt_fixed")
    except JWTError:
        raise HTTPException(
            status_code=401, 
            detail="令牌格式无效",
            headers={"X-Error-Code": "INVALID_TOKEN_FORMAT"}
        )
    
    if not username:
        raise HTTPException(
            status_code=401, 
            detail="无法验证用户身份：用户信息缺失",
            headers={"X-Error-Code": "INVALID_USER_IDENTITY"}
        )
    
    # 检查Redis会话状态（仅滑动会话模式需要）
    if auth_strategy == "sliding_session":
        # 调试：打印验证前的信息
        print(f"[DEBUG] refresh_token - 开始验证会话: username={username}, auth_strategy={auth_strategy}")
        # 检查会话是否有效
        is_valid = await session_manager.is_session_valid(username)
        print(f"[DEBUG] refresh_token - is_session_valid结果: {is_valid}")
        if not is_valid:
            # 检查会话是否存在
            session_data = await session_manager.get_session(username)
            print(f"[DEBUG] refresh_token - 获取会话数据: {session_data}")
            if session_data is None:
                error_detail = "会话不存在，可能已超时或用户已登出"
                error_code = "SESSION_NOT_FOUND"
            elif not session_data.get("active", False):
                error_detail = "会话已失效，用户可能已在其他设备登录"
                error_code = "SESSION_INACTIVE"
            else:
                error_detail = "会话已过期，请重新登录"
                error_code = "SESSION_EXPIRED"
            
            raise HTTPException(
                status_code=401, 
                detail=error_detail,
                headers={"X-Error-Code": error_code}
            )
        
        # 更新最后活动时间
        await session_manager.update_last_activity(username)
        print(f"[DEBUG] refresh_token - 已更新最后活动时间")
    
    # 获取用户信息
    user = db.exec(select(User).join(Role).where(User.username == username)).first()
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="用户不存在或已被删除",
            headers={"X-Error-Code": "USER_NOT_FOUND"}
        )
    
    # 检查用户状态
    if user.is_delete:
        raise HTTPException(
            status_code=401, 
            detail="用户账户已被禁用，请联系管理员",
            headers={"X-Error-Code": "USER_DISABLED"}
        )
    
    # 获取客户端IP地址（考虑反向代理场景）
    client_host = get_real_client_ip(request)
    
    # 获取用户权限列表
    user_permissions = [perm.id for perm in user.role.permissions]
    
    # 生成新的JWT令牌
    new_access_token = create_access_token(
        data={"username": user.username, "role_name": user.role.name},
        ip_address=client_host,
        user_permissions=user_permissions
    )
    
    response_data = {
        "access_token": new_access_token, 
        "token_type": "bearer",
        "message": "令牌续期成功",
        "expires_in": dynamic_settings.ACCESS_TOKEN_SHORT_EXPIRE_MINUTES * 60 if auth_strategy == "sliding_session" else dynamic_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
    
    # 如果Redis不可用，添加提醒信息
    if auth_strategy == "sliding_session" and not session_manager.is_redis_available():
        response_data["redis_unavailable"] = True
        response_data["redis_status_message"] = "Redis服务器异常，当前使用备选存储方案，请尽快处理Redis服务"
    
    return response_data


@auth_router.post("/logout")
async def logout_user(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    """用户登出接口"""
    print(f"[DEBUG] logout_user - 开始处理登出请求")
    username = current_user.get("username")
    print(f"[DEBUG] logout_user - 当前用户: {username}")
    
    if username:
        # 根据认证策略处理会话清理
        print(f"[DEBUG] logout_user - 认证策略: {dynamic_settings.AUTH_STRATEGY}")
        if dynamic_settings.AUTH_STRATEGY == "sliding_session":
            print(f"[DEBUG] logout_user - 调用delete_session方法")
            # 删除Redis会话
            result = await session_manager.delete_session(username)
            print(f"[DEBUG] logout_user - delete_session返回结果: {result}")
        
        # 记录登出时间
        login_record_manager = get_login_record_manager()
        
        # 查找用户ID
        user = db.exec(select(User).where(User.username == username)).first()
        if user:
            print(f"[DEBUG] logout_user - 找到用户ID: {user.id}")
            # 获取当前请求的IP地址（考虑反向代理场景）
            current_ip = get_real_client_ip(request)
            await login_record_manager.record_logout(db, user.id, current_ip, username)
        else:
            print(f"[DEBUG] logout_user - 未找到用户")
    else:
        print(f"[DEBUG] logout_user - 用户名为空")
    
    print(f"[DEBUG] logout_user - 登出处理完成")
    return {"message": "登出成功"}