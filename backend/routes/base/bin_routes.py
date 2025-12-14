from fastapi import APIRouter, Depends, HTTPException, Security
from sqlmodel import Session, select, func, and_, or_, distinct
from typing import Optional
import logging

from models.base.bin import Bin
from models.base.warehouse import Warehouse
from schemas.base.bin import (
    BinCreate, BinUpdate, BinResponse, BinQueryParams, 
    BinPaginationResult, BatchBinDelete, BinStatistics, BinPropertiesResponse
)
from schemas.account.user import UserResponse
from database import get_db
from core.security import get_current_active_user, get_required_scopes_for_route

# 获取日志记录器
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bins", tags=["货位管理"])

@router.get("", response_model=BinPaginationResult)
def get_bins(
    params: BinQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/bins"))
):
    """获取货位列表（需要BASE-read权限）"""
    try:
        # 构建查询条件
        conditions = []
        
        # 基本筛选条件
        if params.bin_name:
            conditions.append(Bin.bin_name.ilike(f"%{params.bin_name}%"))
        if params.warehouse_id:
            conditions.append(Bin.warehouse_id == params.warehouse_id)
        if params.warehouse_name:
            conditions.append(Bin.warehouse_name.ilike(f"%{params.warehouse_name}%"))
        if params.bin_property:
            conditions.append(Bin.bin_property.ilike(f"%{params.bin_property}%"))
        if params.empty_label is not None:
            conditions.append(Bin.empty_label == params.empty_label)
        
        # 通用搜索条件
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
                    
                    # 搜索货位名称（模糊匹配）
                    keyword_conditions.append(Bin.bin_name.ilike(f"%{keyword}%"))
                    
                    # 搜索仓库名称（模糊匹配）
                    keyword_conditions.append(Bin.warehouse_name.ilike(f"%{keyword}%"))
                    
                    # 搜索货位属性（模糊匹配）
                    keyword_conditions.append(Bin.bin_property.ilike(f"%{keyword}%"))
                    
                    # 搜索货位规格（模糊匹配）
                    keyword_conditions.append(Bin.bin_size.ilike(f"%{keyword}%"))
                    
                    # 搜索是否为空（精确匹配关键词"是"、"否"、"空"、"满"等）
                    if keyword in ["是", "空", "empty", "true", "1"]:
                        keyword_conditions.append(Bin.empty_label == True)
                    elif keyword in ["否", "满", "not empty", "false", "0"]:
                        keyword_conditions.append(Bin.empty_label == False)
                    
                    # 如果该关键词有有效的搜索条件，添加OR组
                    if keyword_conditions:
                        all_keyword_conditions.append(or_(*keyword_conditions))
                
                # 如果有有效关键词条件，使用AND连接所有关键词条件组
                if all_keyword_conditions:
                    conditions.append(and_(*all_keyword_conditions))
        
        # 排除已删除的记录
        conditions.append(Bin.is_delete == False)
        
        # 构建查询
        query = select(Bin).where(and_(*conditions))
        
        # 排序
        if params.sort_field:
            sort_field = getattr(Bin, params.sort_field, Bin.id)
            query = query.order_by(sort_field.desc() if not params.sort_asc else sort_field.asc())
        else:
            query = query.order_by(Bin.id.desc())
        
        # 分页
        total = db.scalar(select(func.count()).select_from(query.subquery()))
        query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
        
        bins = db.exec(query).all()
        
        return BinPaginationResult(
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=(total + params.page_size - 1) // params.page_size,
            data=bins
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取货位列表失败: {str(e)}")

@router.get("/statistics", response_model=BinStatistics)
def get_bin_statistics(
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/bins/statistics"))
):
    """获取货位统计信息（需要BASE-read权限）"""
    try:
        # 总货位数
        total_bins = db.scalar(
            select(func.count(Bin.id)).where(Bin.is_delete == False)
        ) or 0
        
        # 按仓库分组统计
        bins_by_warehouse = db.exec(
            select(
                Bin.warehouse_id, 
                Bin.warehouse_name, 
                func.count(Bin.id).label("count")
            )
            .where(Bin.is_delete == False)
            .group_by(Bin.warehouse_id, Bin.warehouse_name)
            .order_by(func.count(Bin.id).desc())
        ).all()
        
        # 按货位属性分组统计
        bins_by_property = db.exec(
            select(
                Bin.bin_property, 
                func.count(Bin.id).label("count")
            )
            .where(Bin.is_delete == False, Bin.bin_property.isnot(None))
            .group_by(Bin.bin_property)
            .order_by(func.count(Bin.id).desc())
        ).all()
        
        return BinStatistics(
            total_bins=total_bins,
            bins_by_warehouse=[{"warehouse_id": w[0], "warehouse_name": w[1], "count": w[2]} for w in bins_by_warehouse],
            bins_by_property=[{"property": p[0], "count": p[1]} for p in bins_by_property]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取货位统计信息失败: {str(e)}")

@router.get("/get/{bin_id}", response_model=BinResponse)
def get_bin(
    bin_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/bins/get"))
):
    """获取单个货位信息（需要BASE-read权限）"""
    try:
        bin = db.get(Bin, bin_id)
        if not bin or bin.is_delete:
            raise HTTPException(status_code=404, detail="货位不存在")
        return bin
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取货位信息失败: {str(e)}")

@router.post("", response_model=BinResponse)
def create_bin(
    bin_data: BinCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/bins/new"))
):
    """创建货位（需要BASE-edit权限）"""
    try:
        # 检查仓库是否存在
        warehouse = db.get(Warehouse, bin_data.warehouse_id)
        if not warehouse or warehouse.is_delete:
            raise HTTPException(status_code=404, detail="仓库不存在")
        
        # 检查货位名称在同一个仓库中是否唯一（排除已删除的）
        existing_bin = db.exec(
            select(Bin).where(
                Bin.bin_name == bin_data.bin_name,
                Bin.warehouse_id == bin_data.warehouse_id,
                Bin.is_delete == False
            )
        ).first()
        
        if existing_bin:
            raise HTTPException(status_code=400, detail="该仓库中已存在相同名称的货位")
        
        # 创建货位，自动设置创建人和仓库名称
        bin_dict = bin_data.model_dump()
        bin_dict["creator"] = current_user.username
        bin_dict["warehouse_name"] = warehouse.warehouse_name
        
        new_bin = Bin(**bin_dict)
        db.add(new_bin)
        db.commit()
        db.refresh(new_bin)
        
        return new_bin
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建货位失败: {str(e)}")

@router.put("/update/{bin_id}", response_model=BinResponse)
def update_bin(
    bin_id: int,
    bin_data: BinUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/bins/update"))
):
    """更新货位信息（需要BASE-edit权限）"""
    try:
        bin = db.get(Bin, bin_id)
        if not bin or bin.is_delete:
            raise HTTPException(status_code=404, detail="货位不存在")
        
        # 如果更新了仓库ID，检查新仓库是否存在并获取仓库名称
        if bin_data.warehouse_id is not None and bin_data.warehouse_id != bin.warehouse_id:
            warehouse = db.get(Warehouse, bin_data.warehouse_id)
            if not warehouse or warehouse.is_delete:
                raise HTTPException(status_code=404, detail="仓库不存在")
            # 更新仓库名称
            bin.warehouse_name = warehouse.warehouse_name
        else:
            # 即使仓库ID没有变化，也主动获取当前仓库的最新名称并更新
            # 这样可以确保货位中的仓库名称与仓库表中的最新名称保持一致
            warehouse = db.get(Warehouse, bin.warehouse_id)
            if warehouse and not warehouse.is_delete:
                bin.warehouse_name = warehouse.warehouse_name
        
        # 调试输出：打印接收到的更新数据
        update_data = bin_data.model_dump(exclude_none=True)
        print(f"DEBUG: 更新货位 {bin_id} 接收到的数据: {update_data}")
        
        # 如果更新了货位名称或仓库ID，检查唯一性约束
        if (bin_data.bin_name is not None and bin_data.bin_name != bin.bin_name) or \
           (bin_data.warehouse_id is not None and bin_data.warehouse_id != bin.warehouse_id):
            
            check_name = bin_data.bin_name if bin_data.bin_name is not None else bin.bin_name
            check_warehouse_id = bin_data.warehouse_id if bin_data.warehouse_id is not None else bin.warehouse_id
            
            existing_bin = db.exec(
                select(Bin).where(
                    Bin.bin_name == check_name,
                    Bin.warehouse_id == check_warehouse_id,
                    Bin.is_delete == False,
                    Bin.id != bin_id
                )
            ).first()
            
            if existing_bin:
                raise HTTPException(status_code=400, detail="该仓库中已存在相同名称的货位")
        
        # 更新字段 - 使用exclude_none=True而不是exclude_unset=True，以便正确处理空值
        update_data = bin_data.model_dump(exclude_none=True)
        
        # 调试日志：打印接收到的数据
        logger.debug(f"更新货位 {bin_id} 接收到的数据: {update_data}")
        
        for field, value in update_data.items():
            setattr(bin, field, value)
        
        db.commit()
        db.refresh(bin)
        
        return bin
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新货位失败: {str(e)}")

@router.delete("/delete/{bin_id}")
def delete_bin(
    bin_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/bins/delete"))
):
    """删除货位（软删除，需要BASE-edit权限）"""
    try:
        bin = db.get(Bin, bin_id)
        if not bin or bin.is_delete:
            raise HTTPException(status_code=404, detail="货位不存在")
        
        bin.is_delete = True
        db.commit()
        
        return {"message": "货位删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除货位失败: {str(e)}")

@router.post("/batch-delete")
def batch_delete_bins(
    delete_data: BatchBinDelete,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/bins/delete"))
):
    """批量删除货位（需要BASE-edit权限）"""
    try:
        if not delete_data.bin_ids:
            raise HTTPException(status_code=400, detail="请选择要删除的货位")
        
        bins_to_delete = db.exec(
            select(Bin).where(Bin.id.in_(delete_data.bin_ids), Bin.is_delete == False)
        ).all()
        
        if not bins_to_delete:
            raise HTTPException(status_code=404, detail="未找到要删除的货位")
        
        for bin in bins_to_delete:
            bin.is_delete = True
        
        db.commit()
        
        return {"message": f"成功删除 {len(bins_to_delete)} 个货位"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除货位失败: {str(e)}")

@router.get("/properties/all", response_model=BinPropertiesResponse)
def get_all_bin_properties(
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/bins"))
):
    """获取所有货位属性列表（去重）（需要BASE-read权限）"""
    try:
        # 查询所有非空且不重复的货位属性
        properties = db.exec(
            select(distinct(Bin.bin_property))
            .where(Bin.is_delete == False, Bin.bin_property.isnot(None))
            .order_by(Bin.bin_property)
        ).all()
        
        # 过滤掉空字符串并转换为列表
        properties_list = [prop for prop in properties if prop and prop.strip()]
        
        return BinPropertiesResponse(properties=properties_list)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取货位属性列表失败: {str(e)}")