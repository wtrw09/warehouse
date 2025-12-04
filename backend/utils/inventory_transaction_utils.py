from sqlmodel import Session, select
from typing import Optional, List
from datetime import datetime
from models.material.inventory_transaction import InventoryTransaction, ChangeType, ReferenceType
from models.material.material import Material
from models.material.inventory_batch import InventoryBatch
from schemas.material.inventory_transaction import InventoryTransactionCreate
import logging

logger = logging.getLogger(__name__)


def create_inventory_transaction(
    db: Session,
    material_id: int,
    batch_id: int,
    change_type: ChangeType,
    quantity_change: int,
    quantity_before: int,
    quantity_after: int,
    reference_type: ReferenceType,
    reference_id: Optional[int],
    creator: str
) -> InventoryTransaction:
    """
    创建库存变更流水记录
    
    Args:
        db: 数据库会话
        material_id: 器材ID
        batch_id: 批次ID
        change_type: 变更类型（IN/OUT/ADJUST）
        quantity_change: 改变数量（正数增加，负数减少）
        quantity_before: 改变前数量
        quantity_after: 改变后数量
        reference_type: 关联单据类型（inbound/outbound/stocktake）
        reference_id: 关联单据ID
        creator: 操作人
        
    Returns:
        InventoryTransaction: 创建的库存变更流水记录
    """
    # 验证输入参数完整性
    required_params = [
        ("material_id", material_id),
        ("batch_id", batch_id),
        ("change_type", change_type),
        ("quantity_change", quantity_change),
        ("quantity_before", quantity_before),
        ("quantity_after", quantity_after),
        ("reference_type", reference_type),
        ("creator", creator)
    ]
    
    missing_params = []
    for param_name, param_value in required_params:
        # 对于数值参数（quantity_*），允许0值
        if param_name.startswith("quantity_"):
            if param_value is None:
                missing_params.append(param_name)
        # 对于其他参数，使用标准验证
        elif not param_value:
            missing_params.append(param_name)
    
    if missing_params:
        raise ValueError(f"缺少必要的输入参数: {', '.join(missing_params)}")
    
    # 检查器材是否存在
    material = db.exec(select(Material).where(Material.id == material_id)).first()
    if not material:
        raise ValueError(f"器材ID {material_id} 不存在")
    
    # 检查批次是否存在
    batch = db.exec(select(InventoryBatch).where(InventoryBatch.batch_id == batch_id)).first()
    if not batch:
        raise ValueError(f"批次ID {batch_id} 不存在")
    
    # 自动设置操作时间为当前时间
    transaction_time = datetime.now()
    
    # 创建库存变更流水记录
    transaction = InventoryTransaction(
        material_id=material_id,
        batch_id=batch_id,
        change_type=change_type,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        reference_type=reference_type,
        reference_id=reference_id,
        creator=creator,
        transaction_time=transaction_time
    )
    
    db.add(transaction)
    db.flush()
    
    logger.info(f"创建库存变更流水记录成功，流水ID: {transaction.transaction_id}")
    return transaction


def get_inventory_transaction_by_id(
    db: Session,
    transaction_id: int
) -> InventoryTransaction:
    """
    根据ID获取库存变更流水记录
    
    Args:
        db: 数据库会话
        transaction_id: 流水记录ID
        
    Returns:
        InventoryTransaction: 库存变更流水记录
    """
    transaction = db.exec(select(InventoryTransaction).where(InventoryTransaction.transaction_id == transaction_id)).first()
    
    if not transaction:
        raise ValueError(f"库存变更流水记录ID {transaction_id} 不存在")
    
    return transaction


def update_inventory_transaction(
    db: Session,
    transaction_id: int,
    update_data: dict
) -> InventoryTransaction:
    """
    更新库存变更流水记录
    
    Args:
        db: 数据库会话
        transaction_id: 流水记录ID
        update_data: 更新数据字典
        
    Returns:
        InventoryTransaction: 更新后的库存变更流水记录
    """
    # 根据transaction_id查询记录是否存在
    transaction = db.exec(select(InventoryTransaction).where(InventoryTransaction.transaction_id == transaction_id)).first()
    
    if not transaction:
        raise ValueError(f"库存变更流水记录ID {transaction_id} 不存在")
    
    # 验证更新数据的合法性
    allowed_fields = {
        'material_id', 'batch_id', 'change_type', 'quantity_change',
        'quantity_before', 'quantity_after', 'reference_type', 'reference_id', 'creator'
    }
    
    for field in update_data:
        if field not in allowed_fields:
            raise ValueError(f"不允许更新字段: {field}")
    
    # 更新记录字段
    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    db.add(transaction)
    # 注意：这里不调用db.commit()，由外层事务统一提交
    
    logger.info(f"更新库存变更流水记录成功，流水ID: {transaction.transaction_id}")
    return transaction


def delete_inventory_transaction(
    db: Session,
    transaction_id: int
) -> bool:
    """
    删除库存变更流水记录
    
    Args:
        db: 数据库会话
        transaction_id: 流水记录ID
        
    Returns:
        bool: 删除成功状态
    """
    # 根据transaction_id查询记录是否存在
    transaction = db.exec(select(InventoryTransaction).where(InventoryTransaction.transaction_id == transaction_id)).first()
    
    if not transaction:
        raise ValueError(f"库存变更流水记录ID {transaction_id} 不存在")
    
    # 执行删除操作
    db.delete(transaction)
    # 注意：这里不调用db.commit()，由外层事务统一提交
    
    logger.info(f"删除库存变更流水记录成功，流水ID: {transaction_id}")
    return True


def get_inventory_transactions_by_criteria(
    db: Session,
    material_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    change_type: Optional[ChangeType] = None,
    reference_type: Optional[ReferenceType] = None,
    reference_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 10
) -> List[InventoryTransaction]:
    """
    根据条件查询库存变更流水记录
    
    Args:
        db: 数据库会话
        material_id: 器材ID
        batch_id: 批次ID
        change_type: 变更类型
        reference_type: 关联单据类型
        reference_id: 关联单据ID
        start_date: 开始时间
        end_date: 结束时间
        page: 页码
        page_size: 每页数量
        
    Returns:
        List[InventoryTransaction]: 库存变更流水记录列表
    """
    # 构建查询条件
    query = select(InventoryTransaction)
    
    if material_id:
        query = query.where(InventoryTransaction.material_id == material_id)
    
    if batch_id:
        query = query.where(InventoryTransaction.batch_id == batch_id)
    
    if change_type:
        query = query.where(InventoryTransaction.change_type == change_type)
    
    if reference_type:
        query = query.where(InventoryTransaction.reference_type == reference_type)
    
    if reference_id:
        query = query.where(InventoryTransaction.reference_id == reference_id)
    
    if start_date:
        query = query.where(InventoryTransaction.transaction_time >= start_date)
    
    if end_date:
        query = query.where(InventoryTransaction.transaction_time <= end_date)
    
    # 执行分页查询
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # 按操作时间降序排序
    query = query.order_by(InventoryTransaction.transaction_time.desc())
    
    transactions = db.exec(query).all()
    
    return transactions


def get_transaction_statistics(
    db: Session,
    material_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> dict:
    """
    获取库存变更统计信息
    
    Args:
        db: 数据库会话
        material_id: 器材ID
        batch_id: 批次ID
        start_date: 开始时间
        end_date: 结束时间
        
    Returns:
        dict: 统计信息字典
    """
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
    
    # 根据条件查询入库、出库、调整数量
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
    
    # 计算总变更数量
    net_change = total_in - total_out + total_adjust
    
    # 返回统计结果
    return {
        'total_in': total_in,
        'total_out': total_out,
        'total_adjust': total_adjust,
        'net_change': net_change,
        'transaction_count': len(transactions)
    }


def create_inbound_transaction(
    db: Session,
    material_id: int,
    batch_id: int,
    quantity_change: int,
    quantity_before: int,
    quantity_after: int,
    reference_id: Optional[int],
    creator: str
) -> InventoryTransaction:
    """
    创建入库流水记录（专用函数）
    
    Args:
        db: 数据库会话
        material_id: 器材ID
        batch_id: 批次ID
        quantity_change: 入库数量
        quantity_before: 入库前数量
        quantity_after: 入库后数量
        reference_id: 入库单ID
        creator: 操作人
        
    Returns:
        InventoryTransaction: 创建的入库流水记录
    """
    return create_inventory_transaction(
        db=db,
        material_id=material_id,
        batch_id=batch_id,
        change_type=ChangeType.IN,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        reference_type=ReferenceType.INBOUND,
        reference_id=reference_id,
        creator=creator
    )


def create_outbound_transaction(
    db: Session,
    material_id: int,
    batch_id: int,
    quantity_change: int,
    quantity_before: int,
    quantity_after: int,
    reference_id: Optional[int],
    creator: str
) -> InventoryTransaction:
    """
    创建出库流水记录（专用函数）
    
    Args:
        db: 数据库会话
        material_id: 器材ID
        batch_id: 批次ID
        quantity_change: 出库数量（负数）
        quantity_before: 出库前数量
        quantity_after: 出库后数量
        reference_id: 出库单ID
        creator: 操作人
        
    Returns:
        InventoryTransaction: 创建的出库流水记录
    """
    return create_inventory_transaction(
        db=db,
        material_id=material_id,
        batch_id=batch_id,
        change_type=ChangeType.OUT,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        reference_type=ReferenceType.OUTBOUND,
        reference_id=reference_id,
        creator=creator
    )


def create_stock_adjust_transaction(
    db: Session,
    material_id: int,
    batch_id: int,
    quantity_change: int,
    quantity_before: int,
    quantity_after: int,
    reference_id: Optional[int],
    creator: str
) -> InventoryTransaction:
    """
    创建库存调整流水记录（专用函数）
    
    Args:
        db: 数据库会话
        material_id: 器材ID
        batch_id: 批次ID
        quantity_change: 调整数量（正数增加，负数减少）
        quantity_before: 调整前数量
        quantity_after: 调整后数量
        reference_id: 盘点单ID
        creator: 操作人
        
    Returns:
        InventoryTransaction: 创建的库存调整流水记录
    """
    return create_inventory_transaction(
        db=db,
        material_id=material_id,
        batch_id=batch_id,
        change_type=ChangeType.ADJUST,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        reference_type=ReferenceType.STOCKTAKE,
        reference_id=reference_id,
        creator=creator
    )