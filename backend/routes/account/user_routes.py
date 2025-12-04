from fastapi import APIRouter, Depends, Security, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select, func, and_, or_, text, delete
from sqlalchemy.orm import selectinload
from sqlalchemy import String
from typing import Annotated, List, Dict
from datetime import datetime, timedelta
from models.account.user import User
from models.account.role import Role
from schemas.account.user import (
    UserResponse, UserManagementResponse, UserManagementCreate, 
    UserManagementUpdate, UserPasswordUpdate, UserPasswordReset,
    UserRoleAssign, UserQueryParams, UserPaginationResult,
    BatchUserRoleAssign, BatchOperationResult, UserStatistics
)
from core.security import (
    get_current_active_user, get_current_user, get_required_scopes_for_route,
    get_password_hash, verify_password
)
from database import get_db



user_router = APIRouter(tags=["用户管理"])


# 获取当前用户
@user_router.get("/users/me", response_model=UserResponse)
def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/users/me"))
):
    """获取当前登录用户信息（受保护的路由）"""
    # 创建并返回UserResponse实例，确保包含权限列表
    return current_user

# 获取用户表，不获取密码
@user_router.get("/users", response_model=UserPaginationResult)
def read_users_paginated(
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/users")),
    params: UserQueryParams = Depends(UserQueryParams)
):
    """获取用户列表，支持分页、搜索、排序（需要AUTH_READ权限）"""
    # 计算偏移量
    offset = (params.page - 1) * params.page_size
    
    # 基础查询（过滤已删除用户）
    query = select(User).where(User.is_delete != True)
    
    # 按角色ID筛选
    if params.role_id:
        query = query.where(User.role_id == params.role_id)
    
    # 搜索功能（多关键词搜索）
    if params.search and params.search.strip():
        keywords = [keyword.strip().lower() for keyword in params.search.split() if keyword.strip()]
        
        # 如果没有有效关键词，则不进行筛选
        if not keywords:
            # 没有有效关键词，不添加搜索条件
            pass
        else:
            # 为每个关键词构建搜索条件组，关键词之间是AND关系
            all_keyword_conditions = []
            
            for keyword in keywords:
                # 为单个关键词构建条件组（内部是OR关系）
                keyword_conditions = []
                
                # 搜索角色名称，通过roles表找到匹配的用户ID
                role_match_query = select(User.id).join(Role).where(
                    or_(
                        text(f"roles.name LIKE '%{keyword}%'"),  # 匹配角色名称
                        text(f"roles.description LIKE '%{keyword}%'")  # 匹配角色描述
                    )
                )
                role_matched_user_ids = db.exec(role_match_query).all()
                # 如果找到角色匹配的用户ID，添加到搜索条件
                if role_matched_user_ids:
                    keyword_conditions.append(text(f"users.id IN ({','.join(map(str, role_matched_user_ids))})"))
                
                # 搜索用户ID（如果关键词是数字）
                if keyword.isdigit():
                    keyword_conditions.append(text(f"users.id = {int(keyword)}"))
                
                # 搜索用户名（模糊匹配）
                keyword_conditions.append(text(f"users.username LIKE '%{keyword}%'"))
                
                # 搜索创建时间（数据库层面模糊匹配）
                keyword_conditions.append(text(f"CAST(users.create_time AS TEXT) LIKE '%{keyword}%'"))
                
                # 搜索修改时间（数据库层面模糊匹配）
                keyword_conditions.append(text(f"CAST(users.update_time AS TEXT) LIKE '%{keyword}%'"))
                
                # 如果该关键词有有效的搜索条件，添加OR组
                if keyword_conditions:
                    all_keyword_conditions.append(or_(*keyword_conditions))
            
            # 如果有有效关键词条件，使用AND连接所有关键词条件组
            if all_keyword_conditions:
                query = query.where(and_(*all_keyword_conditions))
    
    # 排序功能
    if params.sort_field == "id":
        query = query.order_by(text("id ASC" if params.sort_asc else "id DESC"))
    elif params.sort_field == "username":
        query = query.order_by(text("username ASC" if params.sort_asc else "username DESC"))
    elif params.sort_field == "create_time":
        query = query.order_by(text("create_time ASC" if params.sort_asc else "create_time DESC"))
    elif params.sort_field == "update_time":
        query = query.order_by(text("update_time ASC" if params.sort_asc else "update_time DESC"))
    else:
        query = query.order_by(text("id ASC"))  # 默认排序
    
    # 预加载角色信息
    query = query.options(selectinload(User.role))  # type: ignore
    
    # 获取总记录数
    total_count = db.exec(select(func.count()).select_from(query.subquery())).one()
    
    # 计算总页数
    total_pages = (total_count + params.page_size - 1) // params.page_size
    
    # 获取分页数据
    users = db.exec(query.offset(offset).limit(params.page_size)).all()
    
    # 转换为UserManagementResponse格式
    data = [
        UserManagementResponse(
            id=user.id,
            username=user.username,
            role_id=user.role_id,
            role_name=user.role.name if user.role else "未知角色",
            department=user.department,
            create_time=user.create_time,
            update_time=user.update_time
        )
        for user in users
    ]
    
    return UserPaginationResult(
        total=total_count,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
        data=data
    )


# ===== 新增用户管理API（按照设计报告） =====

# 统计接口需要放在 {user_id} 路由之前，避免路由冲突
@user_router.get("/users/statistics", response_model=UserStatistics)
def get_user_statistics(
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/users"))
):
    """获取用户统计信息（需要AUTH_READ权限）"""
    # 总用户数（不包含已删除）
    total_users = db.exec(
        select(func.count()).select_from(User).where(User.is_delete != True)
    ).one()
    
    # 按角色分组的用户统计（简化实现）
    roles = db.exec(select(Role).where(Role.is_delete != True)).all()
    users_by_role = []
    
    for role in roles:
        user_count = db.exec(
            select(func.count())
            .select_from(User)
            .where(User.role_id == role.id, User.is_delete != True)
        ).one()
        
        users_by_role.append({
            "role_id": role.id,
            "role_name": role.name,
            "user_count": user_count
        })
    
    # 最近7天注册用户数
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_registrations = db.exec(
        select(func.count())
        .select_from(User)
        .where(
            User.is_delete != True,
            User.create_time >= seven_days_ago
        )
    ).one()
    
    return UserStatistics(
        total_users=total_users,
        users_by_role=users_by_role,
        recent_registrations=recent_registrations
    )



@user_router.get("/users/{user_id}", response_model=UserManagementResponse)
def get_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/users"))
):
    """获取指定用户的详细信息（不返回已删除用户）"""
    user = db.exec(
        select(User)
        .options(selectinload(User.role))  # type: ignore
        .where(User.id == user_id, User.is_delete != True)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserManagementResponse(
        id=user.id,
        username=user.username,
        role_id=user.role_id,
        role_name=user.role.name if user.role else "未知角色",
        department=user.department,
        create_time=user.create_time,
        update_time=user.update_time
    )

@user_router.post("/users/new", response_model=UserManagementResponse)
def create_user(
    user_data: UserManagementCreate,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/users/new"))
):
    """创建新用户（需要AUTH_EDIT权限）"""
    # 验证用户名唯一性
    existing_user = db.exec(
        select(User).where(User.username == user_data.username, User.is_delete != True)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 验证角色ID有效性
    role = db.exec(select(Role).where(Role.id == user_data.role_id, Role.is_delete != True)).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色ID不存在"
        )
    
    # 创建新用户
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        role_id=user_data.role_id,
        department=user_data.department,
        avatar="XX/user.jpg"  # 默认头像，但不暴露给前端
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # 加载角色信息
    db.refresh(new_user)
    user_with_role = db.exec(
        select(User).options(selectinload(User.role)).where(User.id == new_user.id)  # type: ignore
    ).first()
    
    if not user_with_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户创建失败"
        )
    
    return UserManagementResponse(
        id=user_with_role.id,
        username=user_with_role.username,
        role_id=user_with_role.role_id,
        role_name=user_with_role.role.name if user_with_role.role else "未知角色",
        department=user_with_role.department,
        create_time=user_with_role.create_time,
        update_time=user_with_role.update_time
    )

# ===== 批量操作接口 =====

@user_router.put("/users/batch/role", response_model=BatchOperationResult)
def batch_assign_user_role(
    batch_data: BatchUserRoleAssign,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/users/update"))
):
    """批量为多个用户分配角色（需要AUTH_EDIT权限）"""
    # 验证角色ID有效性
    role = db.exec(select(Role).where(Role.id == batch_data.role_id, Role.is_delete != True)).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色ID不存在"
        )
    
    success_count = 0
    failed_count = 0
    failed_users = []
    
    # 获取所有目标用户
    users = db.exec(
        select(User).where(
            User.id.in_(batch_data.user_ids),  # type: ignore
            User.is_delete != True
        )
    ).all()
    
    # 检查哪些用户ID不存在
    existing_user_ids = {user.id for user in users}
    for user_id in batch_data.user_ids:
        if user_id not in existing_user_ids:
            failed_users.append(user_id)
            failed_count += 1
    
    # 批量更新角色
    try:
        for user in users:
            user.role_id = batch_data.role_id
            user.update_time = datetime.now()
            success_count += 1
        
        db.commit()
        
        return BatchOperationResult(
            success_count=success_count,
            failed_count=failed_count,
            failed_users=failed_users,
            message=f"成功更新{success_count}个用户，失败{failed_count}个用户"
        )
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量操作失败: {str(e)}"
        )

@user_router.put("/users/{user_id}/role", response_model=UserManagementResponse)
def assign_user_role(
    user_id: int,
    role_data: UserRoleAssign,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/users/update"))
):
    """为用户分配角色（需要AUTH_EDIT权限）"""
    # 获取目标用户
    user = db.exec(select(User).where(User.id == user_id, User.is_delete != True)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证角色ID有效性
    role = db.exec(select(Role).where(Role.id == role_data.role_id, Role.is_delete != True)).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色ID不存在"
        )
    
    # 更新用户角色
    user.role_id = role_data.role_id
    user.update_time = datetime.now()
    
    db.commit()
    db.refresh(user)
    
    # 加载角色信息
    user_with_role = db.exec(
        select(User).options(selectinload(User.role)).where(User.id == user.id)  # type: ignore
    ).first()
    
    if not user_with_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="角色分配失败"
        )
    
    return UserManagementResponse(
        id=user_with_role.id,
        username=user_with_role.username,
        role_id=user_with_role.role_id,
        role_name=user_with_role.role.name if user_with_role.role else "未知角色",
        department=user_with_role.department,
        create_time=user_with_role.create_time,
        update_time=user_with_role.update_time
    )

@user_router.put("/users/me/password")
def change_own_password(
    password_data: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """用户修改自己的密码（需要AUTH_OWN权限）"""
    # 从数据库获取完整的用户信息（包含密码哈希）
    db_user = db.exec(
        select(User).where(User.id == current_user.id, User.is_delete != True)
    ).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证原密码
    if not verify_password(password_data.old_password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    # 验证新密码与原密码是否相同
    if verify_password(password_data.new_password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与原密码相同，请选择一个不同的密码"
        )
    
    # 更新密码
    db_user.hashed_password = get_password_hash(password_data.new_password)
    db_user.update_time = datetime.now()
    
    db.commit()
    
    return {"message": "密码修改成功"}

@user_router.put("/users/{user_id}/password/reset")
def reset_user_password(
    user_id: int,
    password_data: UserPasswordReset,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/users/update"))
):
    """管理员重置指定用户的密码（需要AUTH_EDIT权限）"""
    # 获取目标用户
    user = db.exec(select(User).where(User.id == user_id, User.is_delete != True)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 验证新密码与当前密码是否相同
    if verify_password(password_data.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与当前密码相同，请选择一个不同的密码"
        )
    
    # 更新密码
    user.hashed_password = get_password_hash(password_data.new_password)
    user.update_time = datetime.now()
    
    db.commit()
    
    return {"message": "密码重置成功"}

@user_router.delete("/users/delete/{user_id}", response_model=UserManagementResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/users/delete"))
):
    """软删除用户（标记为已删除，需要AUTH_EDIT权限）"""
    # 获取目标用户
    user = db.exec(
        select(User)
        .options(selectinload(User.role))  # type: ignore
        .where(User.id == user_id, User.is_delete != True)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查是否为最后一个管理员用户（简化检查）
    if user.role and "AUTH-edit" in [perm.id for perm in user.role.permissions]:
        admin_count = db.exec(
            select(func.count())
            .select_from(User)
            .join(Role)
            .where(
                User.is_delete != True,
                Role.is_delete != True,
                Role.id == user.role_id
            )
        ).one()
        
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="不能删除最后一个管理员用户"
            )
    
    # 软删除：设置 is_delete = True
    user.is_delete = True
    user.update_time = datetime.now()
    
    db.commit()
    
    return UserManagementResponse(
        id=user.id,
        username=user.username,
        role_id=user.role_id,
        role_name=user.role.name if user.role else "未知角色",
        department=user.department,
        create_time=user.create_time,
        update_time=user.update_time
    )

@user_router.put("/users/update/{user_id}", response_model=UserManagementResponse)
def update_user(
    user_id: int,
    user_data: UserManagementUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新用户基本信息（需要AUTH_EDIT或AUTH_OWN权限）"""
    # 获取目标用户
    target_user = db.exec(
        select(User).where(User.id == user_id, User.is_delete != True)
    ).first()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限验证：管理员可更新任何用户，普通用户只能更新自己
    current_user_permissions = current_user.permissions
    
    if "AUTH-edit" not in current_user_permissions:
        if current_user.id != user_id or "AUTH-own" not in current_user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
    
    # 验证用户名唯一性（如果有修改）
    if user_data.username and user_data.username != target_user.username:
        existing_user = db.exec(
            select(User).where(User.username == user_data.username, User.is_delete != True)
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
    
    # 验证角色ID有效性（如果有修改）
    if user_data.role_id and user_data.role_id != target_user.role_id:
        role = db.exec(select(Role).where(Role.id == user_data.role_id, Role.is_delete != True)).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色ID不存在"
            )
    
    # 更新用户信息
    if user_data.username:
        target_user.username = user_data.username
    if user_data.role_id:
        target_user.role_id = user_data.role_id
    if user_data.department is not None:
        target_user.department = user_data.department
    
    target_user.update_time = datetime.now()
    
    db.commit()
    db.refresh(target_user)
    
    # 加载角色信息
    user_with_role = db.exec(
        select(User).options(selectinload(User.role)).where(User.id == target_user.id)  # type: ignore
    ).first()
    
    if not user_with_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户更新失败"
        )
    
    return UserManagementResponse(
        id=user_with_role.id,
        username=user_with_role.username,
        role_id=user_with_role.role_id,
        role_name=user_with_role.role.name if user_with_role.role else "未知角色",
        create_time=user_with_role.create_time,
        update_time=user_with_role.update_time
    )