from fastapi import APIRouter, Depends, Security, HTTPException, UploadFile, File, Query
from sqlmodel import Session, select, func, and_, or_
from typing import List
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

from models.material.material import Material
from models.base.major import Major
from models.base.equipment import Equipment
from schemas.base.material import (
    MaterialCreate, MaterialUpdate, MaterialResponse,
    BatchMaterialDelete, MaterialListResponse, MaterialQueryParams, MaterialStatistics,
    MaterialPaginationParams, MaterialPaginationResult, MaterialBatchImportResult,
    MajorOptionsResponse, MajorOption, EquipmentOptionsResponse, EquipmentOption
)
from schemas.account.user import UserResponse
from core.security import get_current_active_user, get_required_scopes_for_route
from database import get_db
from utils.material_utils import generate_material_query_code, validate_material_code_unique
from utils.template_utils import download_import_template

material_router = APIRouter(tags=["器材管理"], prefix="/materials")

# 获取器材列表（分页）
@material_router.get("", response_model=MaterialPaginationResult)
def read_materials(
    params: MaterialPaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials"))
):
    """获取器材列表（需要BASE-read权限）"""
    
    # 构建查询条件 - 使用join来支持专业名称和装备名称搜索
    query = select(Material).join(Major, Material.major_id == Major.id, isouter=True).join(Equipment, Material.equipment_id == Equipment.id, isouter=True).where(Material.is_delete != True)
    
    # 器材编码筛选
    if params.material_code:
        query = query.where(Material.material_code.ilike(f"%{params.material_code}%"))
    
    # 器材名称筛选
    if params.material_name:
        query = query.where(Material.material_name.ilike(f"%{params.material_name}%"))
    
    # 器材规格筛选
    if params.material_specification:
        query = query.where(Material.material_specification.ilike(f"%{params.material_specification}%"))
    
    # 专业ID筛选
    if params.major_id:
        query = query.where(Material.major_id == params.major_id)
    
    # 专业名称筛选
    if params.major_name:
        query = query.where(Major.major_name.ilike(f"%{params.major_name}%"))
    
    # 装备ID筛选
    if params.equipment_id:
        query = query.where(Material.equipment_id == params.equipment_id)
    
    # 装备名称筛选
    if params.equipment_name:
        query = query.where(Equipment.equipment_name.ilike(f"%{params.equipment_name}%"))
    
    # 创建人筛选
    if params.creator:
        query = query.where(Material.creator.ilike(f"%{params.creator}%"))
    
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
                
                # 搜索器材编码（模糊匹配）
                keyword_conditions.append(Material.material_code.ilike(f"%{keyword}%"))
                
                # 搜索器材名称（模糊匹配）
                keyword_conditions.append(Material.material_name.ilike(f"%{keyword}%"))
                
                # 搜索器材规格（模糊匹配）
                keyword_conditions.append(Material.material_specification.ilike(f"%{keyword}%"))
                
                # 搜索器材查询码（模糊匹配）
                keyword_conditions.append(Material.material_query_code.ilike(f"%{keyword}%"))
                
                # 搜索创建人（模糊匹配）
                keyword_conditions.append(Material.creator.ilike(f"%{keyword}%"))
                
                # 搜索专业名称（通过join表）
                keyword_conditions.append(Major.major_name.ilike(f"%{keyword}%"))
                
                # 搜索装备名称（通过join表）
                keyword_conditions.append(Equipment.equipment_name.ilike(f"%{keyword}%"))
                
                # 如果该关键词有有效的搜索条件，添加OR组
                if keyword_conditions:
                    all_keyword_conditions.append(or_(*keyword_conditions))
            
            # 如果有有效关键词条件，使用AND连接所有关键词条件组
            if all_keyword_conditions:
                query = query.where(and_(*all_keyword_conditions))
    
    # 排序
    if params.sort_field == "id":
        if params.sort_asc:
            query = query.order_by(getattr(Material, 'id'))
        else:
            query = query.order_by(getattr(Material, 'id').desc())
    elif params.sort_field == "material_name":
        if params.sort_asc:
            query = query.order_by(getattr(Material, 'material_name'))
        else:
            query = query.order_by(getattr(Material, 'material_name').desc())
    elif params.sort_field == "create_time":
        if params.sort_asc:
            query = query.order_by(getattr(Material, 'create_time'))
        else:
            query = query.order_by(getattr(Material, 'create_time').desc())
    elif params.sort_field == "update_time":
        if params.sort_asc:
            query = query.order_by(getattr(Material, 'update_time'))
        else:
            query = query.order_by(getattr(Material, 'update_time').desc())
    else:
        # 如果没有有效的排序字段，默认按id升序排序
        query = query.order_by(getattr(Material, 'id'))
    
    # 获取总数
    total_query = select(func.count()).select_from(query.subquery())
    total = db.exec(total_query).one()
    
    # 分页
    query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
    
    # 执行查询
    materials = db.exec(query).all()
    
    # 获取专业名称和装备名称映射
    major_name_map = {}
    equipment_name_map = {}
    if materials:
        major_ids = [m.major_id for m in materials if m.major_id]
        equipment_ids = [m.equipment_id for m in materials if m.equipment_id]
        
        if major_ids:
            majors = db.exec(select(Major).where(Major.id.in_(major_ids))).all()
            major_name_map = {major.id: major.major_name for major in majors}
        
        if equipment_ids:
            equipments = db.exec(select(Equipment).where(Equipment.id.in_(equipment_ids))).all()
            equipment_name_map = {equipment.id: equipment.equipment_name for equipment in equipments}
    
    # 构建响应数据
    material_responses = []
    for material in materials:
        material_dict = {
            "id": material.id,
            "material_code": material.material_code,
            "material_name": material.material_name,
            "material_specification": material.material_specification,
            "material_desc": material.material_desc,
            "material_wdh": material.material_wdh,
            "safety_stock": material.safety_stock,
            "material_query_code": material.material_query_code,
            "major_id": material.major_id,
            "major_name": major_name_map.get(material.major_id) if material.major_id else None,
            "equipment_id": material.equipment_id,
            "equipment_name": equipment_name_map.get(material.equipment_id) if material.equipment_id else None,
            "creator": material.creator,
            "create_time": material.create_time,
            "update_time": material.update_time
        }
        material_responses.append(MaterialResponse(**material_dict))
    
    # 计算总页数
    total_pages = (total + params.page_size - 1) // params.page_size
    
    return {
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages,
        "data": material_responses
    }

# 获取所有器材列表（不分页）
@material_router.get("/all", response_model=MaterialListResponse)
async def get_all_materials(
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials"))
):
    """获取所有器材数据，不分页不排序"""
    try:
        materials = db.exec(
            select(Material).where(Material.is_delete != True)
        ).all()
        
        # 构建响应数据
        material_responses = []
        for material in materials:
            material_dict = {
            "id": material.id,
            "material_code": material.material_code,
            "material_name": material.material_name,
            "material_specification": material.material_specification,
            "material_desc": material.material_desc,
            "material_wdh": material.material_wdh,
            "safety_stock": material.safety_stock,
            "material_query_code": material.material_query_code,
            "major_id": material.major_id,
            "major_name": None,  # 不分页查询不获取关联名称
            "equipment_id": material.equipment_id,
            "equipment_name": None,  # 不分页查询不获取关联名称
            "creator": material.creator,
            "create_time": material.create_time,
            "update_time": material.update_time
        }
            material_responses.append(MaterialResponse(**material_dict))
        
        return MaterialListResponse(
            data=material_responses,
            total=len(material_responses)
        )
    except Exception as e:
        logger.error(f"获取器材列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取器材列表失败: {str(e)}")

# 获取单个器材详情
@material_router.get("/get/{id}", response_model=MaterialResponse)
async def get_material(
    id: int,
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials/get"))
):
    """获取单个器材详情"""
    try:
        material = db.exec(
            select(Material).where(Material.id == id, Material.is_delete != True)
        ).first()
        
        if not material:
            raise HTTPException(status_code=404, detail="器材不存在")
        
        # 获取专业名称和装备名称
        major_name = None
        equipment_name = None
        
        if material.major_id:
            major = db.exec(select(Major).where(Major.id == material.major_id)).first()
            major_name = major.major_name if major else None
        
        if material.equipment_id:
            equipment = db.exec(select(Equipment).where(Equipment.id == material.equipment_id)).first()
            equipment_name = equipment.equipment_name if equipment else None
        
        material_dict = {
            "id": material.id,
            "material_code": material.material_code,
            "material_name": material.material_name,
            "material_specification": material.material_specification,
            "material_desc": material.material_desc,
            "material_wdh": material.material_wdh,
            "safety_stock": material.safety_stock,
            "material_query_code": material.material_query_code,
            "major_id": material.major_id,
            "major_name": major_name,
            "equipment_id": material.equipment_id,
            "equipment_name": equipment_name,
            "creator": material.creator,
            "create_time": material.create_time,
            "update_time": material.update_time
        }
        
        return MaterialResponse(**material_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取器材详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取器材详情失败: {str(e)}")

# 创建器材
@material_router.post("", response_model=MaterialResponse)
async def create_material(
    material: MaterialCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials/new"))
):
    """创建新器材"""
    print("创建器材请求:", material);
    
    # 处理equipment_id为空字符串或无效值的情况
    if hasattr(material, 'equipment_id') and (material.equipment_id == "" or material.equipment_id is None):
        material.equipment_id = None
    
    try:
        # 验证器材编码的唯一性
        if not validate_material_code_unique(db, material.material_code):
            raise HTTPException(status_code=400, detail="器材编码已存在")
        
        # 智能生成器材查询码：如果用户提供了查询码则使用用户提供的，否则自动生成
        if material.material_query_code:
            material_query_code = material.material_query_code
        else:
            material_query_code = generate_material_query_code(material.material_name, material.material_specification)
        
        # 自动获取major_id：通过equipment_id查询装备表获取对应的major_id
        major_id = None
        major_name = None
        equipment_name = None
        
        if material.equipment_id:
            equipment = db.exec(select(Equipment).where(Equipment.id == material.equipment_id)).first()
            if equipment:
                major_id = equipment.major_id
                equipment_name = equipment.equipment_name
                
                # 获取专业名称
                if major_id:
                    major = db.exec(select(Major).where(Major.id == major_id)).first()
                    major_name = major.major_name if major else None
        
        # 创建器材记录
        db_material = Material(
            material_code=material.material_code,
            material_name=material.material_name,
            material_specification=material.material_specification if material.material_specification else None,
            material_desc=material.material_desc,
            material_wdh=material.material_wdh,
            safety_stock=material.safety_stock,
            material_query_code=material_query_code,
            major_id=major_id,
            major_name=major_name,
            equipment_id=material.equipment_id,
            equipment_name=equipment_name,
            creator=current_user.username,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        
        db.add(db_material)
        db.commit()
        db.refresh(db_material)
        
        # 构建响应数据
        material_dict = {
            "id": db_material.id,
            "material_code": db_material.material_code,
            "material_name": db_material.material_name,
            "material_specification": db_material.material_specification,
            "material_desc": db_material.material_desc,
            "material_wdh": db_material.material_wdh,
            "safety_stock": db_material.safety_stock,
            "material_query_code": db_material.material_query_code,
            "major_id": db_material.major_id,
            "major_name": major_name,
            "equipment_id": db_material.equipment_id,
            "equipment_name": equipment_name,
            "creator": db_material.creator,
            "create_time": db_material.create_time,
            "update_time": db_material.update_time
        }
        
        return MaterialResponse(**material_dict)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"创建器材失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建器材失败: {str(e)}")

# 更新器材
@material_router.put("/update/{id}", response_model=MaterialResponse)
async def update_material(
    id: int,
    material_update: MaterialUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials/update"))
):
    """更新器材信息"""
    try:
        # 获取现有器材
        db_material = db.exec(
            select(Material).where(Material.id == id, Material.is_delete != True)
        ).first()
        
        if not db_material:
            raise HTTPException(status_code=404, detail="器材不存在")
        
        # 如果更新了器材编码，需要验证唯一性
        if material_update.material_code:
            if not validate_material_code_unique(db, material_update.material_code, exclude_id=id):
                raise HTTPException(status_code=400, detail="器材编码已存在")
        
        # 更新字段 - 使用exclude_none=True而不是exclude_unset=True，以便正确处理空值
        update_data = material_update.model_dump(exclude_none=True)
        
        # 智能更新器材查询码逻辑：
        # 1. 如果用户明确提供了material_query_code，则使用用户提供的值
        # 2. 如果用户没有提供material_query_code，但更新了器材名称或规格，则重新生成查询码
        # 3. 如果用户没有提供material_query_code且没有更新器材名称或规格，则保持原有查询码不变
        
        if "material_query_code" in update_data:
            # 用户明确提供了查询码，使用用户提供的值
            pass  # 不需要额外处理，直接使用用户提供的值
        elif material_update.material_name is not None or material_update.material_specification is not None:
            # 用户没有提供查询码，但更新了器材名称或规格，重新生成查询码
            new_name = material_update.material_name if material_update.material_name is not None else db_material.material_name
            new_spec = material_update.material_specification if material_update.material_specification is not None else db_material.material_specification
            update_data["material_query_code"] = generate_material_query_code(new_name, new_spec)
        
        # 装备和专业字段智能处理逻辑：
        # 1. 装备有值，专业为空：通过装备获取专业信息
        # 2. 装备为空：同时清空专业和装备信息
        # 处理装备和专业字段更新
        if material_update.equipment_id:
            # 装备有值，通过装备表获取对应的专业信息
            equipment = db.exec(select(Equipment).where(Equipment.id == material_update.equipment_id)).first()
            if equipment:
                update_data["major_id"] = equipment.major_id
                update_data["equipment_name"] = equipment.equipment_name
                
                # 获取专业名称
                if equipment.major_id:
                    major = db.exec(select(Major).where(Major.id == equipment.major_id)).first()
                    update_data["major_name"] = major.major_name if major else None
        else:
            # 装备为空（None、空值或undefined），同时清空专业和装备信息
            update_data["major_id"] = None
            update_data["equipment_id"] = None  # 关键：必须同时清空equipment_id
            update_data["equipment_name"] = None
            update_data["major_name"] = None
        
        # 设置更新时间
        update_data["update_time"] = datetime.now()
        
        # 更新器材记录
        for field, value in update_data.items():
            setattr(db_material, field, value)
        
        db.add(db_material)
        db.commit()
        db.refresh(db_material)
        
        # 构建响应数据
        material_dict = {
            "id": db_material.id,
            "material_code": db_material.material_code,
            "material_name": db_material.material_name,
            "material_specification": db_material.material_specification,
            "material_desc": db_material.material_desc,
            "material_wdh": db_material.material_wdh,
            "safety_stock": db_material.safety_stock,
            "material_query_code": db_material.material_query_code,
            "major_id": db_material.major_id,
            "major_name": db_material.major_name,
            "equipment_id": db_material.equipment_id,
            "equipment_name": db_material.equipment_name,
            "creator": db_material.creator,
            "create_time": db_material.create_time,
            "update_time": db_material.update_time
        }
        
        return MaterialResponse(**material_dict)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新器材失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新器材失败: {str(e)}")

# 删除器材（软删除）
@material_router.delete("/delete/{id}")
async def delete_material(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials/delete"))
):
    """删除器材（软删除）"""
    try:
        # 获取器材
        db_material = db.exec(
            select(Material).where(Material.id == id, Material.is_delete != True)
        ).first()
        
        if not db_material:
            raise HTTPException(status_code=404, detail="器材不存在")
        
        # 软删除
        db_material.is_delete = True
        db_material.update_time = datetime.now()
        
        db.add(db_material)
        db.commit()
        
        return {"message": "器材删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除器材失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除器材失败: {str(e)}")

# 批量删除器材
@material_router.post("/batch-delete")
async def batch_delete_materials(
    batch_delete: BatchMaterialDelete,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials/delete"))
):
    """批量删除器材"""
    try:
        success_count = 0
        error_count = 0
        errors = []
        
        for material_id in batch_delete.ids:
            try:
                # 获取器材
                db_material = db.exec(
                    select(Material).where(Material.id == material_id, Material.is_delete != True)
                ).first()
                
                if not db_material:
                    error_count += 1
                    errors.append(f"器材ID {material_id} 不存在")
                    continue
                
                # 软删除
                db_material.is_delete = True
                db_material.update_time = datetime.now()
                
                db.add(db_material)
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"器材ID {material_id} 删除失败: {str(e)}")
        
        db.commit()
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
    except Exception as e:
        db.rollback()
        logger.error(f"批量删除器材失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量删除器材失败: {str(e)}")

# 获取器材统计信息
@material_router.get("/statistics", response_model=MaterialStatistics)
async def get_material_statistics(
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials/statistics"))
):
    """获取器材统计信息"""
    try:
        # 获取总数量
        total_count = db.exec(
            select(func.count()).where(Material.is_delete != True)
        ).one()
        
        # 按专业统计
        major_stats = db.exec(
            select(Material.major_id, func.count(Material.id))
            .where(Material.is_delete != True, Material.major_id.isnot(None))
            .group_by(Material.major_id)
        ).all()
        
        major_count = {}
        for major_id, count in major_stats:
            major = db.exec(select(Major).where(Major.id == major_id)).first()
            if major:
                major_count[major.major_name] = count
        
        # 按装备统计
        equipment_stats = db.exec(
            select(Material.equipment_id, func.count(Material.id))
            .where(Material.is_delete != True, Material.equipment_id.isnot(None))
            .group_by(Material.equipment_id)
        ).all()
        
        equipment_count = {}
        for equipment_id, count in equipment_stats:
            equipment = db.exec(select(Equipment).where(Equipment.id == equipment_id)).first()
            if equipment:
                equipment_count[equipment.equipment_name] = count
        
        return MaterialStatistics(
            total_count=total_count,
            major_count=major_count,
            equipment_count=equipment_count
        )
    except Exception as e:
        logger.error(f"获取器材统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取器材统计信息失败: {str(e)}")

# 批量导入器材（占位实现）
@material_router.post("/batch-import", response_model=MaterialBatchImportResult)
async def batch_import_materials(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials"))
):
    """批量导入器材"""
    # 这里实现Excel导入逻辑，暂时返回占位响应
    return MaterialBatchImportResult(
        success_count=0,
        error_count=0,
        errors=["批量导入功能暂未实现"]
    )

# 下载器材导入模板
@material_router.get("/import-template")
async def download_material_import_template(
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials/import-template"))
):
    """下载器材导入模板文件（需要BASE-edit权限）"""
    return await download_import_template('material')

# 下载错误文件
@material_router.get("/download-error-file")
async def download_material_error_file(
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials/download-error-file"))
):
    """下载器材导入错误文件"""
    # 这里实现错误文件下载逻辑，暂时返回占位响应
    raise HTTPException(status_code=501, detail="错误文件下载功能暂未实现")

# 获取器材表中所有准专业的合集（不重复）
@material_router.get("/major-options", response_model=MajorOptionsResponse)
async def get_major_options(
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials/major-options"))
):
    """获取器材表中所有准专业的合集（不重复）"""
    try:
        # 查询器材表中所有不重复的准专业ID
        major_ids = db.exec(
            select(Material.major_id)
            .where(Material.is_delete != True, Material.major_id.isnot(None))
            .distinct()
        ).all()
        
        # 获取准专业详细信息
        major_options = []
        for major_id in major_ids:
            major = db.exec(select(Major).where(Major.id == major_id)).first()
            if major:
                major_options.append(MajorOption(id=major.id, major_name=major.major_name))
        
        return MajorOptionsResponse(data=major_options)
    except Exception as e:
        logger.error(f"获取准专业选项失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取准专业选项失败: {str(e)}")

# 根据专业ID列表获取这些专业下的装备合集
@material_router.get("/equipment-options", response_model=EquipmentOptionsResponse)
async def get_equipment_options_by_majors(
    major_ids: List[int] = Query(None, description="专业ID列表，为空则返回所有装备"),
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/materials/get"))
):
    """根据专业ID列表获取这些专业下的装备合集，如果专业ID列表为空则返回所有装备"""
    try:
        # 构建查询条件
        query_conditions = [
            Material.is_delete != True,
            Material.equipment_id.isnot(None)
        ]
        
        # 如果传入了专业ID列表，则添加专业ID过滤条件
        if major_ids:
            # 验证专业是否存在
            for major_id in major_ids:
                major = db.exec(select(Major).where(Major.id == major_id)).first()
                if not major:
                    raise HTTPException(status_code=404, detail=f"专业ID {major_id} 不存在")
            
            query_conditions.append(Material.major_id.in_(major_ids))
        
        # 查询器材表中所有不重复的装备ID
        equipment_ids = db.exec(
            select(Material.equipment_id)
            .where(*query_conditions)
            .distinct()
        ).all()
        
        # 获取装备详细信息
        equipment_options = []
        for equipment_id in equipment_ids:
            equipment = db.exec(select(Equipment).where(Equipment.id == equipment_id)).first()
            if equipment:
                # 构建显示名称
                display_name = f"{equipment.equipment_name}"
                if equipment.specification:
                    display_name += f" {equipment.specification}"
                
                equipment_options.append(EquipmentOption(
                    id=equipment.id,
                    display_name=display_name
                ))
        
        return EquipmentOptionsResponse(data=equipment_options, total=len(equipment_options))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取装备选项失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取装备选项失败: {str(e)}")