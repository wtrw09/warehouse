from math import log
from fastapi import APIRouter, Depends, HTTPException, Security
from datetime import datetime
from sqlmodel import Session, select,delete
from sqlalchemy import or_, String, func, and_, text
from sqlalchemy.orm import selectinload
from models.account.role import Role, RolePermissionLink
from models.account.user import User
from models.account.permission import Permission
from schemas.account.role import RoleCreate, RoleResponse, RoleWithPermissions, RoleUpdate, UpdateRolePermissions, PaginationResult
from core.security import get_current_user, get_required_scopes_for_route, Permission as SecurityPermission
from database import get_db
from fastapi import APIRouter, Depends, Security, HTTPException, status
from schemas.common import PaginationParams


# 创建角色管理的路由
role_router = APIRouter(tags=["角色管理"])

@role_router.get("/roles", response_model=PaginationResult)
def read_roles(
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/roles")),
    params: PaginationParams = Depends(PaginationParams)
):
    """获取所有角色信息（需要AUTH_READ权限）"""
    # 计算偏移量
    offset = (params.page - 1) * params.page_size
    # 基础查询
    query = select(Role).where(Role.is_delete != True)
    
    # 应用排序
    if params.sort_field == "id":
        if params.sort_asc:
            query = query.order_by(text("id ASC"))
        else:
            query = query.order_by(text("id DESC"))
    elif params.sort_field == "name":
        if params.sort_asc:
            query = query.order_by(text("name ASC"))
        else:
            query = query.order_by(text("name DESC"))
    elif params.sort_field == "create_time":
        if params.sort_asc:
            query = query.order_by(text("create_time ASC"))
        else:
            query = query.order_by(text("create_time DESC"))
    elif params.sort_field == "update_time":
        if params.sort_asc:
            query = query.order_by(text("update_time ASC"))
        else:
            query = query.order_by(text("update_time DESC"))
    else:
        # 如果没有有效的排序字段，默认按id升序排序
        query = query.order_by(text("id ASC"))
    
    # 如果提供了搜索关键词，则添加搜索条件
    if params.search:
        # 将关键词字符串按空格分割为多个关键词，并过滤掉空字符串
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
                
                # 搜索权限名称或描述，通过role_permissions表找到匹配的角色ID
                permission_match_query = select(RolePermissionLink.role_id).join(Permission).where(
                    or_(
                        text(f"permissions.id LIKE '%{keyword}%'"),  # 匹配权限ID（如AUTH-edit）
                        text(f"permissions.name LIKE '%{keyword}%'"),  # 匹配权限名称
                        text(f"permissions.description LIKE '%{keyword}%'")  # 匹配权限描述
                    )
                )
                permission_matched_role_ids = db.exec(permission_match_query).all()
                # 如果找到权限匹配的角色ID，添加到搜索条件
                logger.debug('根据权限搜索到的角色ID: %s', permission_matched_role_ids)
                if permission_matched_role_ids:
                    keyword_conditions.append(text(f"roles.id IN ({','.join(map(str, permission_matched_role_ids))})"))
                
                # 搜索角色ID（如果关键词是数字）
                if keyword.isdigit():
                    keyword_conditions.append(text(f"roles.id = {int(keyword)}"))
                
                # 搜索角色名称（模糊匹配）
                keyword_conditions.append(text(f"roles.name LIKE '%{keyword}%'"))
                
                # 搜索创建时间（数据库层面模糊匹配）
                keyword_conditions.append(text(f"CAST(roles.create_time AS TEXT) LIKE '%{keyword}%'"))
                
                # 搜索修改时间（数据库层面模糊匹配）
                keyword_conditions.append(text(f"CAST(roles.update_time AS TEXT) LIKE '%{keyword}%'"))
                
                # 如果该关键词有有效的搜索条件，添加OR组
                if keyword_conditions:
                    all_keyword_conditions.append(or_(*keyword_conditions))
            
            # 如果有有效关键词条件，使用AND连接所有关键词条件组
            if all_keyword_conditions:
                query = query.where(and_(*all_keyword_conditions))
    
    # 预加载权限关系，以便在内存中进行权限字段的搜索
    query = query.options(selectinload(Role.permissions))  # type: ignore
    # logger.debug('执行角色查询，当前查询条件: %s', query)
    # 获取总记录数
    total_count = db.exec(select(func.count()).select_from(query.subquery())).one()
    
    # 计算总页数
    total_pages = (total_count + params.page_size - 1) // params.page_size
    
    # 获取分页数据
    roles = db.exec(
        query.offset(offset).limit(params.page_size)
    ).all()
    
    # 转换为RoleWithPermissions格式
    data = []
    for role in roles:
        role_dict = role.model_dump()
        role_dict["permissions"] = [p.id for p in role.permissions]
        data.append(RoleWithPermissions(**role_dict))
    
    # 返回包含分页信息的结果
    return PaginationResult(
        total=total_count,
        page=params.page,
        page_size=params.page_size,
        total_pages=total_pages,
        data=data
    )

@role_router.get("/roles/{role_id}", response_model=RoleWithPermissions)
def read_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/roles"))
):
    """获取单个角色详情（包含权限信息，需要AUTH_READ权限）"""
    role = db.exec(select(Role).where(Role.id == role_id, Role.is_delete != True)).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    # 转换为RoleWithPermissions格式
    role_dict = role.model_dump()
    role_dict["permissions"] = [p.id for p in role.permissions]
    return RoleWithPermissions(**role_dict)

@role_router.post("/roles/new", response_model=RoleResponse)
def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/roles/new"))
):
    """创建新角色（需要AUTH_EDIT权限）"""
    # 检查角色名称是否已存在
    existing_role = db.exec(select(Role).where(Role.name == role_data.name, Role.is_delete != True)).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="角色名称已存在")
    
    # 创建Role实例并设置属性
    new_role = Role(
        name=role_data.name,
        description=role_data.description or ""
    )
    
    # 添加新角色到数据库
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    # 验证用户提供的权限是否存在
    existing_permissions = db.exec(select(Permission).where(Permission.id.in_(role_data.permissions))).all()  # type: ignore
    if len(existing_permissions) != len(role_data.permissions):
        # 找出不存在的权限ID
        existing_permission_ids = {p.id for p in existing_permissions}
        invalid_permissions = [perm for perm in role_data.permissions if perm not in existing_permission_ids]
        raise HTTPException(status_code=400, detail=f"以下权限ID不存在: {', '.join(invalid_permissions)}")
    
    # 为新角色分配用户提供的权限
    for permission in existing_permissions:
        role_permission_link = RolePermissionLink(role_id=new_role.id, permission_id=permission.id)
        db.add(role_permission_link)
    
    db.commit()
    db.refresh(new_role)
    
    # 确保 create_time 和 update_time 存在
    if not hasattr(new_role, 'create_time') or new_role.create_time is None:
        new_role.create_time = datetime.now()
    if not hasattr(new_role, 'update_time') or new_role.update_time is None:
        new_role.update_time = datetime.now()
    
    # 返回符合RoleResponse模型的数据
    return RoleResponse(
        id=new_role.id, 
        name=new_role.name, 
        description=new_role.description or "",
        create_time=new_role.create_time,
        update_time=new_role.update_time
    )

@role_router.put("/roles/update/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/roles/update"))
):
    """更新角色信息（需要AUTH_EDIT权限）"""
    role = db.exec(select(Role).where(Role.id == role_id, Role.is_delete != True)).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 检查新的角色名称是否已被其他角色使用
    if role_data.name != role.name:
        existing_role = db.exec(select(Role).where(Role.name == role_data.name, Role.is_delete != True)).first()
        if existing_role:
            raise HTTPException(status_code=400, detail="角色名称已存在")
    
    # 更新角色信息
    role.name = role_data.name
    role.description = role_data.description or ""
    role.update_time = datetime.now()
    
    db.commit()
    db.refresh(role)
    
    return RoleResponse(
        id=role.id, 
        name=role.name, 
        description=role.description,
        create_time=role.create_time,
        update_time=role.update_time
    )

@role_router.put("/roles/{role_id}/permissions", response_model=RoleWithPermissions)
def update_role_permissions(
    role_id: int,
    permissions_data: UpdateRolePermissions,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/roles/permissions"))
):
    """更新角色权限（需要AUTH_EDIT权限）"""
    role = db.exec(
        select(Role)
        .where(Role.id == role_id, Role.is_delete != True)
        .options(selectinload(Role.permissions))  # type: ignore  #预加载权限关系
        ).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 验证权限ID是否存在
    existing_permissions = db.exec(select(Permission).where(Permission.id.in_(permissions_data.permission_ids))).all()  # type: ignore
    if len(existing_permissions) != len(permissions_data.permission_ids):
        raise HTTPException(status_code=400, detail="部分权限ID不存在")
    
    # 清除现有的角色权限关联
    db.exec(  # type: ignore
        delete(RolePermissionLink)
        .where(RolePermissionLink.role_id == role_id)  # type: ignore
    )
    
    # 添加新的角色权限关联
    for permission_id in permissions_data.permission_ids:
        role_permission_link = RolePermissionLink(role_id=role.id, permission_id=permission_id)
        db.add(role_permission_link)
    
    db.commit()
    db.refresh(role)
    
    # 转换为RoleWithPermissions格式返回
    role_dict = role.model_dump()
    role_dict["permissions"] = [p.id for p in role.permissions]
    return RoleWithPermissions(**role_dict)

@role_router.delete("/roles/delete/{role_id}", response_model=RoleResponse)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/roles/delete"))
):
    """删除指定角色（需要AUTH_EDIT权限）"""
    role = db.exec(select(Role).where(Role.id == role_id, Role.is_delete != True)).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 检查是否有用户正在使用该角色
    if role.users:
        raise HTTPException(status_code=400, detail="该角色下有用户，无法删除")
    
    role.is_delete = True
    role.update_time = datetime.now()
    db.commit()
    
    return RoleResponse(
        id=role.id, 
        name=role.name, 
        description=role.description,
        create_time=role.create_time,
        update_time=role.update_time
    )

