from fastapi import APIRouter, Depends, Security, HTTPException
from sqlmodel import Session, select, func, and_, or_
from typing import List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from models.base.equipment import Equipment
from models.base.major import Major
from schemas.base.equipment import (
    EquipmentCreate, EquipmentUpdate, EquipmentResponse,
    BatchEquipmentDelete, EquipmentListResponse, EquipmentQueryParams, EquipmentStatistics,
    EquipmentPaginationParams, EquipmentPaginationResult
)
from schemas.account.user import UserResponse
from core.security import get_current_active_user, get_required_scopes_for_route
from database import get_db

equipment_router = APIRouter(tags=["装备管理"], prefix="/equipments")

# 获取装备列表（分页）
@equipment_router.get("", response_model=EquipmentPaginationResult)
def read_equipments(
    params: EquipmentPaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/equipments"))
):
    """获取装备列表（需要BASE-read权限）"""
    
    # 构建查询条件 - 使用join来支持专业名称搜索
    query = select(Equipment).join(Major, Equipment.major_id == Major.id, isouter=True).where(Equipment.is_delete != True)
    
    # 装备名称筛选
    if params.equipment_name:
        query = query.where(Equipment.equipment_name.ilike(f"%{params.equipment_name}%"))
    
    # 规格型号筛选
    if params.specification:
        query = query.where(Equipment.specification.ilike(f"%{params.specification}%"))
    
    # 专业ID筛选
    if params.major_id:
        query = query.where(Equipment.major_id == params.major_id)
    
    # 专业名称筛选
    if params.major_name:
        query = query.where(Major.major_name.ilike(f"%{params.major_name}%"))
    
    # 创建人筛选
    if params.creator:
        query = query.where(Equipment.creator.ilike(f"%{params.creator}%"))
    
    # 处理多关键词搜索
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
                
                # 搜索装备名称（模糊匹配）
                keyword_conditions.append(Equipment.equipment_name.ilike(f"%{keyword}%"))
                
                # 搜索规格型号（模糊匹配）
                keyword_conditions.append(Equipment.specification.ilike(f"%{keyword}%"))
                
                # 搜索创建人（模糊匹配）
                keyword_conditions.append(Equipment.creator.ilike(f"%{keyword}%"))
                
                # 搜索专业名称（通过join表）
                keyword_conditions.append(Major.major_name.ilike(f"%{keyword}%"))
                
                # 如果该关键词有有效的搜索条件，添加OR组
                if keyword_conditions:
                    all_keyword_conditions.append(or_(*keyword_conditions))
            
            # 如果有有效关键词条件，使用AND连接所有关键词条件组
            if all_keyword_conditions:
                query = query.where(and_(*all_keyword_conditions))
    
    # 排序
    if params.sort_field == "id":
        if params.sort_asc:
            query = query.order_by(getattr(Equipment, 'id'))
        else:
            query = query.order_by(getattr(Equipment, 'id').desc())
    elif params.sort_field == "equipment_name":
        if params.sort_asc:
            query = query.order_by(getattr(Equipment, 'equipment_name'))
        else:
            query = query.order_by(getattr(Equipment, 'equipment_name').desc())
    elif params.sort_field == "create_time":
        if params.sort_asc:
            query = query.order_by(getattr(Equipment, 'create_time'))
        else:
            query = query.order_by(getattr(Equipment, 'create_time').desc())
    elif params.sort_field == "update_time":
        if params.sort_asc:
            query = query.order_by(getattr(Equipment, 'update_time'))
        else:
            query = query.order_by(getattr(Equipment, 'update_time').desc())
    else:
        # 如果没有有效的排序字段，默认按id升序排序
        query = query.order_by(getattr(Equipment, 'id'))
    
    # 获取总数
    total_query = select(func.count()).select_from(query.subquery())
    total = db.exec(total_query).one()
    
    # 分页
    query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
    
    # 执行查询
    equipments = db.exec(query).all()
    
    # 获取专业名称映射
    major_name_map = {}
    if equipments:
        major_ids = [eq.major_id for eq in equipments if eq.major_id]
        if major_ids:
            majors = db.exec(select(Major).where(Major.id.in_(major_ids))).all()
            major_name_map = {major.id: major.major_name for major in majors}
    
    # 直接使用装备数据构建响应
    equipment_responses = []
    for equipment in equipments:
        equipment_dict = {
            "id": equipment.id,
            "equipment_name": equipment.equipment_name,
            "specification": equipment.specification,
            "major_id": equipment.major_id,
            "major_name": major_name_map.get(equipment.major_id) if equipment.major_id else None,
            "creator": equipment.creator,
            "create_time": equipment.create_time,
            "update_time": equipment.update_time
        }
        equipment_responses.append(EquipmentResponse(**equipment_dict))
    
    # 计算总页数
    total_pages = (total + params.page_size - 1) // params.page_size
    
    return {
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages,
        "data": equipment_responses
    }

# 获取所有装备列表（不分页）
@equipment_router.get("/all", response_model=EquipmentListResponse)
async def get_all_equipments(
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/equipments"))
):
    """获取所有装备数据，不分页不排序"""
    try:
        equipments = db.exec(
            select(Equipment).where(Equipment.is_delete != True)
        ).all()
        
        # 直接使用装备数据构建响应
        equipment_responses = []
        for equipment in equipments:
            equipment_dict = {
                "id": equipment.id,
                "equipment_name": equipment.equipment_name,
                "specification": equipment.specification,
                "major_id": equipment.major_id,
                "major_name": None,  # 查询函数直接返回None，不通过major_id获取
                "creator": equipment.creator,
                "create_time": equipment.create_time,
                "update_time": equipment.update_time
            }
            equipment_responses.append(EquipmentResponse(**equipment_dict))
        
        return EquipmentListResponse(
            data=equipment_responses,
            total=len(equipment_responses)
        )
    except Exception as e:
        logger.error(f"获取装备列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取装备列表失败")

# 获取单个装备详情
@equipment_router.get("/get/{id}", response_model=EquipmentResponse)
async def get_equipment(
    id: int,
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/equipments/get"))
):
    """获取单个装备详情"""
    try:
        equipment = db.exec(
            select(Equipment).where(Equipment.id == id, Equipment.is_delete != True)
        ).first()
        
        if not equipment:
            raise HTTPException(status_code=404, detail="装备不存在")
        
        # 直接使用装备数据构建响应
        equipment_dict = {
            "id": equipment.id,
            "equipment_name": equipment.equipment_name,
            "specification": equipment.specification,
            "major_id": equipment.major_id,
            "major_name": None,  # 查询函数直接返回None，不通过major_id获取
            "creator": equipment.creator,
            "create_time": equipment.create_time,
            "update_time": equipment.update_time
        }
        return EquipmentResponse(**equipment_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取装备详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取装备详情失败")

# 创建新装备
@equipment_router.post("", response_model=EquipmentResponse)
async def create_equipment(
    equipment: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/equipments/new"))
):
    """创建新装备"""
    try:
        # 检查装备名称和规格型号组合是否已存在（未删除的）
        existing_equipment = db.exec(
            select(Equipment).where(
                Equipment.equipment_name == equipment.equipment_name,
                Equipment.specification == equipment.specification,
                Equipment.is_delete != True
            )
        ).first()
        
        if existing_equipment:
            raise HTTPException(status_code=400, detail="装备名称和规格型号组合已存在")
        
        # 验证专业ID是否存在
        major_name = None
        if equipment.major_id:
            major = db.exec(select(Major).where(Major.id == equipment.major_id, Major.is_delete != True)).first()
            if not major:
                raise HTTPException(status_code=400, detail="专业ID不存在")
            major_name = major.major_name
        
        # 创建新装备
        db_equipment = Equipment(
            equipment_name=equipment.equipment_name,
            specification=equipment.specification,
            major_id=equipment.major_id,
            major_name=major_name,
            creator=current_user.username,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        
        db.add(db_equipment)
        db.commit()
        db.refresh(db_equipment)
       
        # 直接从装备表读取major_name
        equipment_dict = {
            "id": db_equipment.id,
            "equipment_name": db_equipment.equipment_name,
            "specification": db_equipment.specification,
            "major_id": db_equipment.major_id,
            "major_name": db_equipment.major_name,
            "creator": db_equipment.creator,
            "create_time": db_equipment.create_time,
            "update_time": db_equipment.update_time
        }
        return EquipmentResponse(**equipment_dict)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建装备失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建装备失败")

# 更新装备信息
@equipment_router.put("/update/{id}", response_model=EquipmentResponse)
async def update_equipment(
    id: int,
    equipment_update: EquipmentUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/equipments/update"))
):
    """更新装备信息"""
    try:
        # 查找装备
        db_equipment = db.exec(
            select(Equipment).where(Equipment.id == id, Equipment.is_delete != True)
        ).first()
        
        if not db_equipment:
            raise HTTPException(status_code=404, detail="装备不存在")
        
        # 检查装备名称和规格型号组合是否与其他装备重复（排除自身）
        if equipment_update.equipment_name or equipment_update.specification:
            existing_equipment = db.exec(
                select(Equipment).where(
                    Equipment.equipment_name == equipment_update.equipment_name,
                    Equipment.specification == equipment_update.specification,
                    Equipment.id != id,
                    Equipment.is_delete != True
                )
            ).first()
            
            if existing_equipment:
                raise HTTPException(status_code=400, detail="装备名称和规格型号组合已存在")
        
        # 更新字段
        update_data = equipment_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(db_equipment, field, value)
        
        # 如果更新了major_id，则验证专业ID是否存在并获取对应的major_name
        if equipment_update.major_id is not None:
            major = db.exec(select(Major).where(Major.id == equipment_update.major_id, Major.is_delete != True)).first()
            if not major:
                raise HTTPException(status_code=400, detail="专业ID不存在")
            db_equipment.major_name = major.major_name
        
        db_equipment.update_time = datetime.now()
        
        db.add(db_equipment)
        db.commit()
        db.refresh(db_equipment)
        
        # 通过major_id获取专业名称
        major_name = None
        if db_equipment.major_id:
            major = db.exec(select(Major).where(Major.id == db_equipment.major_id, Major.is_delete != True)).first()
            if major:
                major_name = major.major_name
        
        # 构建包含major_name的响应
        equipment_dict = {
            "id": db_equipment.id,
            "equipment_name": db_equipment.equipment_name,
            "specification": db_equipment.specification,
            "major_id": db_equipment.major_id,
            "major_name": major_name,
            "creator": db_equipment.creator,
            "create_time": db_equipment.create_time,
            "update_time": db_equipment.update_time
        }
        return EquipmentResponse(**equipment_dict)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新装备失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新装备失败")

# 删除单个装备
@equipment_router.delete("/delete/{id}")
async def delete_equipment(
    id: int,
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/equipments/delete"))
):
    """软删除单个装备"""
    try:
        # 查找装备
        db_equipment = db.exec(
            select(Equipment).where(Equipment.id == id, Equipment.is_delete != True)
        ).first()
        
        if not db_equipment:
            raise HTTPException(status_code=404, detail="装备不存在")
        
        # 软删除
        db_equipment.is_delete = True
        db_equipment.update_time = datetime.now()
        
        db.add(db_equipment)
        db.commit()
        
        return {"message": "装备删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除装备失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除装备失败")

# 批量删除装备
@equipment_router.post("/batch-delete")
async def batch_delete_equipments(
    batch_delete: BatchEquipmentDelete,
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/equipments/delete"))
):
    """批量软删除装备"""
    try:
        success_count = 0
        
        for equipment_id in batch_delete.equipment_ids:
            # 查找装备
            db_equipment = db.exec(
                select(Equipment).where(Equipment.id == equipment_id, Equipment.is_delete != True)
            ).first()
            
            if db_equipment:
                # 软删除
                db_equipment.is_delete = True
                db_equipment.update_time = datetime.now()
                db.add(db_equipment)
                success_count += 1
        
        db.commit()
        
        return {
            "message": f"成功删除 {success_count} 个装备",
            "success_count": success_count,
            "total_count": len(batch_delete.equipment_ids)
        }
    except Exception as e:
        db.rollback()
        logger.error(f"批量删除装备失败: {str(e)}")
        raise HTTPException(status_code=500, detail="批量删除装备失败")

# 获取装备统计信息
@equipment_router.get("/statistics", response_model=EquipmentStatistics)
async def get_equipment_statistics(
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/equipments/statistics"))
):
    """获取装备统计信息"""
    try:
        # 总装备数量
        total_count = db.exec(
            select(func.count(Equipment.id)).where(Equipment.is_delete != True)
        ).first()
        
        # 按专业分类统计
        major_count = {}
        equipments = db.exec(
            select(Equipment).where(Equipment.is_delete != True)
        ).all()
        
        for equipment in equipments:
            major_name = equipment.major_name or "未分类"
            if major_name in major_count:
                major_count[major_name] += 1
            else:
                major_count[major_name] = 1
        
        return EquipmentStatistics(
            total_count=total_count or 0,
            major_count=major_count
        )
    except Exception as e:
        logger.error(f"获取装备统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取装备统计信息失败")