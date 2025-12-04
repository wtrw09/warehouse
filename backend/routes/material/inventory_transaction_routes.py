from fastapi import APIRouter, Depends, Security, HTTPException
from sqlmodel import Session, select, func, and_, or_
from typing import List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

from models.material.inventory_transaction import InventoryTransaction, ChangeType, ReferenceType
from models.material.material import Material
from models.material.inventory_batch import InventoryBatch
from models.material.inbound_order import InboundOrder
from models.material.outbound_order import OutboundOrder
from schemas.material.inventory_transaction import (
    InventoryTransactionCreate, InventoryTransactionUpdate, InventoryTransactionResponse,
    InventoryTransactionQueryParams, InventoryTransactionPaginationResult,
    InventoryTransactionListResponse, InventoryTransactionStatistics,
    InventoryTransactionDetailResponse
)
from schemas.account.user import UserResponse
from core.security import get_current_active_user, get_required_scopes_for_route
from database import get_db

inventory_transactions_router = APIRouter(tags=["库存变更流水管理"], prefix="/inventory-transactions")

# 获取库存变更流水分页列表
@inventory_transactions_router.get("", response_model=InventoryTransactionPaginationResult)
def read_inventory_transactions(
    params: InventoryTransactionQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inventory-transactions"))
):
    """获取库存变更流水分页列表（需要IO_read权限）"""
    
    # 构建查询条件 - 使用join来支持器材名称、批次号、操作人搜索
    query = select(InventoryTransaction).join(Material, InventoryTransaction.material_id == Material.id, isouter=True).join(InventoryBatch, InventoryTransaction.batch_id == InventoryBatch.batch_id, isouter=True)
    
    # 器材ID筛选
    if params.material_id:
        query = query.where(InventoryTransaction.material_id == params.material_id)
    
    # 批次ID筛选
    if params.batch_id:
        query = query.where(InventoryTransaction.batch_id == params.batch_id)
    
    # 变更类型筛选
    if params.change_type:
        query = query.where(InventoryTransaction.change_type == params.change_type)
    
    # 关联单据类型筛选
    if params.reference_type:
        query = query.where(InventoryTransaction.reference_type == params.reference_type)
    
    # 时间范围筛选
    if params.start_date:
        query = query.where(InventoryTransaction.transaction_time >= params.start_date)
    if params.end_date:
        query = query.where(InventoryTransaction.transaction_time <= params.end_date)
    
    # 处理多关键词搜索
    if params.keyword and params.keyword.strip():
        keywords = [keyword.strip().lower() for keyword in params.keyword.split() if keyword.strip()]
        
        if keywords:
            all_keyword_conditions = []
            
            for keyword in keywords:
                keyword_conditions = []
                
                # 搜索器材名称（通过join表）
                keyword_conditions.append(Material.material_name.ilike(f"%{keyword}%"))
                
                # 搜索器材编码（通过join表）
                keyword_conditions.append(Material.material_code.ilike(f"%{keyword}%"))
                
                # 搜索批次号（通过join表）
                keyword_conditions.append(InventoryBatch.batch_number.ilike(f"%{keyword}%"))
                
                # 搜索操作人
                keyword_conditions.append(InventoryTransaction.creator.ilike(f"%{keyword}%"))
                
                if keyword_conditions:
                    all_keyword_conditions.append(or_(*keyword_conditions))
            
            if all_keyword_conditions:
                query = query.where(and_(*all_keyword_conditions))
    
    # 排序
    if params.sort_by == "transaction_time":
        if params.sort_order == "asc":
            query = query.order_by(InventoryTransaction.transaction_time)
        else:
            query = query.order_by(InventoryTransaction.transaction_time.desc())
    elif params.sort_by == "material_name":
        if params.sort_order == "asc":
            query = query.order_by(Material.material_name)
        else:
            query = query.order_by(Material.material_name.desc())
    elif params.sort_by == "reference_number":
        # reference_number 是计算字段，需要特殊处理
        # 由于reference_number不是数据库字段，我们按reference_id排序作为近似处理
        if params.sort_order == "asc":
            query = query.order_by(InventoryTransaction.reference_id)
        else:
            query = query.order_by(InventoryTransaction.reference_id.desc())
    else:
        # 默认按操作时间降序排序
        query = query.order_by(InventoryTransaction.transaction_time.desc())
    
    # 获取总数
    total_query = select(func.count()).select_from(query.subquery())
    total = db.exec(total_query).one()
    
    # 分页
    query = query.offset((params.page - 1) * params.page_size).limit(params.page_size)
    
    # 执行查询
    transactions = db.exec(query).all()
    
    # 获取器材和批次信息映射
    material_map = {}
    batch_map = {}
    if transactions:
        material_ids = [t.material_id for t in transactions]
        batch_ids = [t.batch_id for t in transactions]
        
        if material_ids:
            materials = db.exec(select(Material).where(Material.id.in_(material_ids))).all()
            material_map = {material.id: material for material in materials}
        
        if batch_ids:
            batches = db.exec(select(InventoryBatch).where(InventoryBatch.batch_id.in_(batch_ids))).all()
            batch_map = {batch.batch_id: batch for batch in batches}
    
    # 构建响应数据
    transaction_responses = []
    for transaction in transactions:
        material = material_map.get(transaction.material_id)
        batch = batch_map.get(transaction.batch_id)
        
        # 获取关联单据号
        reference_number = None
        if transaction.reference_type == ReferenceType.INBOUND and transaction.reference_id:
            inbound_order = db.exec(select(InboundOrder).where(InboundOrder.order_id == transaction.reference_id)).first()
            if inbound_order:
                reference_number = inbound_order.order_number
        elif transaction.reference_type == ReferenceType.OUTBOUND and transaction.reference_id:
            outbound_order = db.exec(select(OutboundOrder).where(OutboundOrder.order_id == transaction.reference_id)).first()
            if outbound_order:
                reference_number = outbound_order.order_number
        elif transaction.reference_type == ReferenceType.STOCKTAKE and transaction.reference_id:
            # 盘点单号处理（如果需要）
            reference_number = f"盘点单-{transaction.reference_id}"
        
        transaction_dict = {
            "transaction_id": transaction.transaction_id,
            "material_id": transaction.material_id,
            "material_code": material.material_code if material else None,
            "material_name": material.material_name if material else None,
            "material_specification": material.material_specification if material else None,
            "batch_id": transaction.batch_id,
            "batch_number": batch.batch_number if batch else None,
            "change_type": transaction.change_type,
            "quantity_change": transaction.quantity_change,
            "quantity_before": transaction.quantity_before,
            "quantity_after": transaction.quantity_after,
            "reference_number": reference_number,
            "creator": transaction.creator,
            "transaction_time": transaction.transaction_time
        }
        transaction_responses.append(InventoryTransactionResponse(**transaction_dict))
    
    # 计算总页数
    total_pages = (total + params.page_size - 1) // params.page_size
    
    return {
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages,
        "data": transaction_responses
    }


# 获取所有库存变更流水列表（不分页）
@inventory_transactions_router.get("/all", response_model=InventoryTransactionListResponse)
def get_all_inventory_transactions(
    keyword: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    material_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    change_type: Optional[ChangeType] = None,
    reference_type: Optional[ReferenceType] = None,
    sort_by: str = "transaction_time",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inventory-transactions"))
):
    """获取所有库存变更流水列表（不分页，需要IO_read权限）"""
    
    # 构建查询条件
    query = select(InventoryTransaction).join(Material, InventoryTransaction.material_id == Material.id, isouter=True).join(InventoryBatch, InventoryTransaction.batch_id == InventoryBatch.batch_id, isouter=True)
    
    # 器材ID筛选
    if material_id:
        query = query.where(InventoryTransaction.material_id == material_id)
    
    # 批次ID筛选
    if batch_id:
        query = query.where(InventoryTransaction.batch_id == batch_id)
    
    # 变更类型筛选
    if change_type:
        query = query.where(InventoryTransaction.change_type == change_type)
    
    # 关联单据类型筛选
    if reference_type:
        query = query.where(InventoryTransaction.reference_type == reference_type)
    
    # 时间范围筛选
    if start_date:
        query = query.where(InventoryTransaction.transaction_time >= start_date)
    if end_date:
        query = query.where(InventoryTransaction.transaction_time <= end_date)
    
    # 关键词搜索
    if keyword and keyword.strip():
        keywords = [k.strip().lower() for k in keyword.split() if k.strip()]
        
        if keywords:
            all_keyword_conditions = []
            
            for keyword in keywords:
                keyword_conditions = []
                keyword_conditions.append(Material.material_name.ilike(f"%{keyword}%"))
                keyword_conditions.append(Material.material_code.ilike(f"%{keyword}%"))
                keyword_conditions.append(InventoryBatch.batch_number.ilike(f"%{keyword}%"))
                keyword_conditions.append(InventoryTransaction.creator.ilike(f"%{keyword}%"))
                
                if keyword_conditions:
                    all_keyword_conditions.append(or_(*keyword_conditions))
            
            if all_keyword_conditions:
                query = query.where(and_(*all_keyword_conditions))
    
    # 排序
    if sort_by == "transaction_time":
        if sort_order == "asc":
            query = query.order_by(InventoryTransaction.transaction_time)
        else:
            query = query.order_by(InventoryTransaction.transaction_time.desc())
    elif sort_by == "material_name":
        if sort_order == "asc":
            query = query.order_by(Material.material_name)
        else:
            query = query.order_by(Material.material_name.desc())
    elif sort_by == "reference_number":
        # reference_number 是计算字段，需要特殊处理
        # 由于reference_number不是数据库字段，我们按reference_id排序作为近似处理
        if sort_order == "asc":
            query = query.order_by(InventoryTransaction.reference_id)
        else:
            query = query.order_by(InventoryTransaction.reference_id.desc())
    else:
        query = query.order_by(InventoryTransaction.transaction_time.desc())
    
    # 执行查询
    transactions = db.exec(query).all()
    
    # 获取器材和批次信息映射
    material_map = {}
    batch_map = {}
    if transactions:
        material_ids = [t.material_id for t in transactions]
        batch_ids = [t.batch_id for t in transactions]
        
        if material_ids:
            materials = db.exec(select(Material).where(Material.id.in_(material_ids))).all()
            material_map = {material.id: material for material in materials}
        
        if batch_ids:
            batches = db.exec(select(InventoryBatch).where(InventoryBatch.batch_id.in_(batch_ids))).all()
            batch_map = {batch.batch_id: batch for batch in batches}
    
    # 构建响应数据
    transaction_responses = []
    for transaction in transactions:
        material = material_map.get(transaction.material_id)
        batch = batch_map.get(transaction.batch_id)
        
        # 获取关联单据号
        reference_number = None
        if transaction.reference_type == ReferenceType.INBOUND and transaction.reference_id:
            inbound_order = db.exec(select(InboundOrder).where(InboundOrder.order_id == transaction.reference_id)).first()
            if inbound_order:
                reference_number = inbound_order.order_number
        elif transaction.reference_type == ReferenceType.OUTBOUND and transaction.reference_id:
            outbound_order = db.exec(select(OutboundOrder).where(OutboundOrder.order_id == transaction.reference_id)).first()
            if outbound_order:
                reference_number = outbound_order.order_number
        elif transaction.reference_type == ReferenceType.STOCKTAKE and transaction.reference_id:
            # 盘点单号处理（如果需要）
            reference_number = f"盘点单-{transaction.reference_id}"
        
        transaction_dict = {
            "transaction_id": transaction.transaction_id,
            "material_id": transaction.material_id,
            "material_code": material.material_code if material else None,
            "material_name": material.material_name if material else None,
            "material_specification": material.material_specification if material else None,
            "batch_id": transaction.batch_id,
            "batch_number": batch.batch_number if batch else None,
            "change_type": transaction.change_type,
            "quantity_change": transaction.quantity_change,
            "quantity_before": transaction.quantity_before,
            "quantity_after": transaction.quantity_after,
            "reference_number": reference_number,
            "creator": transaction.creator,
            "transaction_time": transaction.transaction_time
        }
        transaction_responses.append(InventoryTransactionResponse(**transaction_dict))
    
    return {"data": transaction_responses}


# 获取单个库存变更流水记录详情
@inventory_transactions_router.get("/get/{transaction_id}", response_model=InventoryTransactionDetailResponse)
def get_inventory_transaction_by_id(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inventory-transactions/get"))
):
    """获取单个库存变更流水记录详情（需要IO_read权限）"""
    
    # 查询记录
    transaction = db.exec(select(InventoryTransaction).where(InventoryTransaction.transaction_id == transaction_id)).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="库存变更流水记录不存在")
    
    # 获取器材信息
    material = db.exec(select(Material).where(Material.id == transaction.material_id)).first()
    
    # 获取批次信息
    batch = db.exec(select(InventoryBatch).where(InventoryBatch.batch_id == transaction.batch_id)).first()
    
    # 获取关联单据号
    reference_number = None
    if transaction.reference_type == ReferenceType.INBOUND and transaction.reference_id:
        inbound_order = db.exec(select(InboundOrder).where(InboundOrder.order_id == transaction.reference_id)).first()
        if inbound_order:
            reference_number = inbound_order.order_number
    elif transaction.reference_type == ReferenceType.OUTBOUND and transaction.reference_id:
        outbound_order = db.exec(select(OutboundOrder).where(OutboundOrder.order_id == transaction.reference_id)).first()
        if outbound_order:
            reference_number = outbound_order.order_number
    elif transaction.reference_type == ReferenceType.STOCKTAKE and transaction.reference_id:
        # 盘点单号处理（如果需要）
        reference_number = f"盘点单-{transaction.reference_id}"
    
    transaction_dict = {
        "transaction_id": transaction.transaction_id,
        "material_id": transaction.material_id,
        "material_code": material.material_code if material else None,
        "material_name": material.material_name if material else None,
        "material_specification": material.material_specification if material else None,
        "batch_id": transaction.batch_id,
        "batch_number": batch.batch_number if batch else None,
        "change_type": transaction.change_type,
        "quantity_change": transaction.quantity_change,
        "quantity_before": transaction.quantity_before,
        "quantity_after": transaction.quantity_after,
        "reference_number": reference_number,
        "creator": transaction.creator,
        "transaction_time": transaction.transaction_time
    }
    
    return {"transaction": InventoryTransactionResponse(**transaction_dict)}


# 创建库存变更流水记录
@inventory_transactions_router.post("", response_model=InventoryTransactionResponse)
def create_inventory_transaction(
    transaction_data: InventoryTransactionCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inventory-transactions/new"))
):
    """创建库存变更流水记录（需要IO_edit权限）"""
    
    # 验证器材是否存在
    material = db.exec(select(Material).where(Material.id == transaction_data.material_id)).first()
    if not material:
        raise HTTPException(status_code=400, detail="器材不存在")
    
    # 验证批次是否存在
    batch = db.exec(select(InventoryBatch).where(InventoryBatch.batch_id == transaction_data.batch_id)).first()
    if not batch:
        raise HTTPException(status_code=400, detail="批次不存在")
    
    # 创建库存变更流水记录
    transaction = InventoryTransaction(
        material_id=transaction_data.material_id,
        batch_id=transaction_data.batch_id,
        change_type=transaction_data.change_type,
        quantity_change=transaction_data.quantity_change,
        quantity_before=transaction_data.quantity_before,
        quantity_after=transaction_data.quantity_after,
        reference_type=transaction_data.reference_type,
        reference_id=transaction_data.reference_id,
        creator=transaction_data.creator,
        transaction_time=datetime.now()
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # 获取关联单据号
    reference_number = None
    if transaction.reference_type == ReferenceType.INBOUND and transaction.reference_id:
        inbound_order = db.exec(select(InboundOrder).where(InboundOrder.order_id == transaction.reference_id)).first()
        if inbound_order:
            reference_number = inbound_order.order_number
    elif transaction.reference_type == ReferenceType.OUTBOUND and transaction.reference_id:
        outbound_order = db.exec(select(OutboundOrder).where(OutboundOrder.order_id == transaction.reference_id)).first()
        if outbound_order:
            reference_number = outbound_order.order_number
    elif transaction.reference_type == ReferenceType.STOCKTAKE and transaction.reference_id:
        # 盘点单号处理（如果需要）
        reference_number = f"盘点单-{transaction.reference_id}"
    
    # 构建响应数据
    transaction_dict = {
        "transaction_id": transaction.transaction_id,
        "material_id": transaction.material_id,
        "material_code": material.material_code,
        "material_name": material.material_name,
        "material_specification": material.material_specification,
        "batch_id": transaction.batch_id,
        "batch_number": batch.batch_number,
        "change_type": transaction.change_type,
        "quantity_change": transaction.quantity_change,
        "quantity_before": transaction.quantity_before,
        "quantity_after": transaction.quantity_after,
        "reference_number": reference_number,
        "creator": transaction.creator,
        "transaction_time": transaction.transaction_time
    }
    
    return InventoryTransactionResponse(**transaction_dict)


# 获取库存变更统计信息
@inventory_transactions_router.get("/statistics", response_model=InventoryTransactionStatistics)
def get_inventory_transaction_statistics(
    material_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inventory-transactions"))
):
    """获取库存变更统计信息（需要IO_read权限）"""
    
    # 构建查询条件
    query = select(InventoryTransaction)
    
    if material_id:
        query = query.where(InventoryTransaction.material_id == material_id)
    
    if batch_id:
        query = query.where(InventoryTransaction.batch_id == batch_id)
    
    if start_date:
        query = query.where(InventoryTransaction.transaction_time >= start_date)
    
    if end_date:
        query = query.where(InventoryTransaction.transaction_time <= end_date)
    
    # 执行查询
    transactions = db.exec(query).all()
    
    # 统计信息
    total_in = 0
    total_out = 0
    total_adjust = 0
    
    for transaction in transactions:
        if transaction.change_type == ChangeType.IN:
            total_in += transaction.quantity_change
        elif transaction.change_type == ChangeType.OUT:
            total_out += abs(transaction.quantity_change)  # 出库数量取绝对值
        elif transaction.change_type == ChangeType.ADJUST:
            total_adjust += transaction.quantity_change
    
    net_change = total_in - total_out + total_adjust
    
    return InventoryTransactionStatistics(
        total_in=total_in,
        total_out=total_out,
        total_adjust=total_adjust,
        net_change=net_change,
        transaction_count=len(transactions)
    )