from fastapi import APIRouter, Depends, HTTPException, Query, Security, Response
from sqlmodel import Session, select, func, and_, or_, delete
from typing import Optional
from datetime import date, datetime
import os

from database import get_db
from core.security import get_current_active_user, get_required_scopes_for_route
from schemas.account.user import UserResponse
from schemas.material import (
    InboundOrderCreate, InboundOrderResponse, InboundOrderDetailResponse, InboundOrderPaginationResult, InboundOrderListResponse,
    InboundOrderStatistics, OrderNumberUpdate, TransferNumberUpdate,
    SupplierUpdate, ContractNumberUpdate, InboundOrderItemUpdate,
    InboundOrderItemCreate, InboundOrderItemResponse, InboundOrderUpdate,
    BatchCodeGenerateRequest, BatchCodeGenerateResponse
)
from models.material.inbound_order import InboundOrder
from models.material.inbound_order_item import InboundOrderItem
from models.material.outbound_order import OutboundOrder
from models.material.outbound_order_item import OutboundOrderItem
from models.base.supplier import Supplier
from models.material.material import Material
from models.base.bin import Bin
from models.material.inventory_batch import InventoryBatch
from models.material.inventory_detail import InventoryDetail
from models.material.inventory_transaction import InventoryTransaction, ChangeType, ReferenceType
from utils.inventory_transaction_utils import create_inbound_transaction, create_inventory_transaction
from utils.pdf_generator import generate_inbound_order_pdf

# 创建入库单管理路由
inbound_orders_router = APIRouter(tags=["入库单管理"], prefix="/inbound-orders")


@inbound_orders_router.get("", response_model=InboundOrderPaginationResult)
async def read_inbound_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（入库单号、供应商名称、调拨单号、合同号）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    sort_by: str = Query("create_time", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向（asc/desc）"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/"))
):
    """获取入库单分页列表"""
    
    # 构建查询条件
    query = select(InboundOrder)
    
    # 关键词搜索
    if keyword:
        # 分割关键词，支持多关键词搜索（空格分隔，AND关系）
        keywords = keyword.strip().split()
        if keywords:
            # 为每个关键词创建OR条件（在单个字段内搜索）
            keyword_filters = []
            for kw in keywords:
                kw_filter = or_(
                    InboundOrder.order_number.contains(kw),
                    InboundOrder.supplier_name.contains(kw),
                    InboundOrder.requisition_reference.contains(kw),
                    InboundOrder.contract_reference.contains(kw)
                )
                keyword_filters.append(kw_filter)
            
            # 将所有关键词的OR条件用AND连接
            query = query.where(and_(*keyword_filters))
    
    # 日期筛选
    if start_date:
        query = query.where(InboundOrder.create_time >= start_date)
    if end_date:
        query = query.where(InboundOrder.create_time <= end_date)
    
    # 供应商筛选
    if supplier_id:
        query = query.where(InboundOrder.supplier_id == supplier_id)
    
    # 排序
    sort_field = getattr(InboundOrder, sort_by, InboundOrder.create_time)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    # 分页
    total = db.exec(select(func.count()).select_from(query.subquery())).one()
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # 执行查询
    orders = db.exec(query).all()
    
    # 构建响应数据
    order_responses = []
    for order in orders:
        order_responses.append(InboundOrderResponse(
            order_id=order.order_id,
            order_number=order.order_number,
            requisition_reference=order.requisition_reference,
            contract_reference=order.contract_reference,
            supplier_id=order.supplier_id,
            supplier_name=order.supplier_name,
            total_quantity=order.total_quantity,
            creator=order.creator,
            create_time=order.create_time,
            inbound_date=order.create_time.date()
        ))
    
    return InboundOrderPaginationResult(
        total=total,
        page=page,
        page_size=page_size,
        data=order_responses
    )


@inbound_orders_router.get("/all", response_model=InboundOrderListResponse)
async def get_all_inbound_orders(
    keyword: Optional[str] = Query(None, description="关键词搜索（入库单号、供应商名称、调拨单号、合同号）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    supplier_id: Optional[int] = Query(None, description="供应商ID"),
    sort_by: str = Query("create_time", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向（asc/desc）"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/all"))
):
    """获取所有入库单列表（不分页）"""
    
    # 构建查询条件
    query = select(InboundOrder)
    
    # 关键词搜索
    if keyword:
        # 分割关键词，支持多关键词搜索（空格分隔，AND关系）
        keywords = keyword.strip().split()
        if keywords:
            # 为每个关键词创建OR条件（在单个字段内搜索）
            keyword_filters = []
            for kw in keywords:
                kw_filter = or_(
                    InboundOrder.order_number.contains(kw),
                    InboundOrder.supplier_name.contains(kw),
                    InboundOrder.requisition_reference.contains(kw),
                    InboundOrder.contract_reference.contains(kw)
                )
                keyword_filters.append(kw_filter)
            
            # 将所有关键词的OR条件用AND连接
            query = query.where(and_(*keyword_filters))
    
    # 日期筛选
    if start_date:
        query = query.where(InboundOrder.create_time >= start_date)
    if end_date:
        query = query.where(InboundOrder.create_time <= end_date)
    
    # 供应商筛选
    if supplier_id:
        query = query.where(InboundOrder.supplier_id == supplier_id)
    
    # 排序
    sort_field = getattr(InboundOrder, sort_by, InboundOrder.create_time)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    # 执行查询
    orders = db.exec(query).all()
    
    # 构建响应数据
    order_responses = []
    for order in orders:
        order_responses.append(InboundOrderResponse(
            order_id=order.order_id,
            order_number=order.order_number,
            requisition_reference=order.requisition_reference,
            contract_reference=order.contract_reference,
            supplier_id=order.supplier_id,
            supplier_name=order.supplier_name,
            total_quantity=order.total_quantity,
            creator=order.creator,
            create_time=order.create_time,
            inbound_date=order.create_time.date()
        ))
    
    return InboundOrderListResponse(
        total=len(orders),
        data=order_responses
    )


@inbound_orders_router.get("/get/{order_id}", response_model=InboundOrderDetailResponse)
async def get_inbound_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/get"))
):
    """获取单个入库单的详细信息"""
    
    # 获取入库单基本信息
    order = db.get(InboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    
    # 获取入库单明细
    items_query = select(InboundOrderItem).where(InboundOrderItem.order_id == order_id)
    items = db.exec(items_query).all()
    
    # 构建明细响应数据
    item_responses = []
    for item in items:
        # 获取货位信息
        bin_info = db.get(Bin, item.bin_id)
        bin_name = bin_info.bin_name if bin_info else ""
        
        # 获取装备信息（通过器材关联）
        material = db.get(Material, item.material_id)
        equipment_name = material.equipment_name if material else ""
        
        # 获取批次信息
        batch = db.get(InventoryBatch, item.batch_id)
        batch_number = batch.batch_number if batch else ""
        
        item_responses.append(InboundOrderItemResponse(
            item_id=item.item_id,
            material_id=item.material_id,
            material_code=item.material_code,
            material_name=item.material_name,
            material_specification=item.material_specification,
            quantity=item.quantity,
            unit_price=item.unit_price,
            unit=item.unit,
            batch_number=batch_number,
            bin_id=item.bin_id,
            bin_name=bin_name,
            equipment_name=equipment_name,
            production_date=item.production_date
        ))
    
    # 构建入库单基本信息
    order_response = InboundOrderResponse(
        order_id=order.order_id,
        order_number=order.order_number,
        requisition_reference=order.requisition_reference,
        contract_reference=order.contract_reference,
        supplier_id=order.supplier_id,
        supplier_name=order.supplier_name,
        total_quantity=order.total_quantity,
        creator=order.creator,
        create_time=order.create_time,
        inbound_date=order.create_time.date()
    )
    
    return InboundOrderDetailResponse(
        order=order_response,
        items=item_responses
    )


@inbound_orders_router.post("", response_model=InboundOrderResponse)
async def create_inbound_order(
    order_data: InboundOrderCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/"))
):
    """创建新入库单"""
    
    # 验证入库单号唯一性
    existing_order = db.exec(
        select(InboundOrder).where(InboundOrder.order_number == order_data.order_number)
    ).first()
    if existing_order:
        raise HTTPException(status_code=400, detail="入库单号已存在")
    
    # 验证供应商存在
    supplier = db.get(Supplier, order_data.supplier_id)
    if not supplier:
        raise HTTPException(status_code=400, detail="供应商不存在")
    
    # 验证明细数据
    for item in order_data.items:
        # 验证器材存在
        material = db.get(Material, item.material_id)
        if not material:
            raise HTTPException(status_code=400, detail=f"器材ID {item.material_id} 不存在")
        
        # 验证货位存在（如果提供了货位ID）
        if item.bin_id is not None:
            bin_info = db.get(Bin, item.bin_id)
            if not bin_info:
                raise HTTPException(status_code=400, detail=f"货位ID {item.bin_id} 不存在")
        
        # 验证批次号唯一性
        existing_batch = db.exec(
            select(InventoryBatch).where(InventoryBatch.batch_number == item.batch_number)
        ).first()
        if existing_batch:
            raise HTTPException(status_code=400, detail=f"批次号 {item.batch_number} 已存在")
    
    # 开始事务
    try:
        # 创建入库单
        new_order = InboundOrder(
            order_number=order_data.order_number,
            requisition_reference=order_data.requisition_reference,
            contract_reference=order_data.contract_reference,
            supplier_id=order_data.supplier_id,
            supplier_name=supplier.supplier_name,
            total_quantity=sum(item.quantity for item in order_data.items),
            creator=current_user.username
        )
        db.add(new_order)
        
        # 创建明细项和批次
        for item in order_data.items:
            material = db.get(Material, item.material_id)
            
            # 创建库存批次
            new_batch = InventoryBatch(
                batch_number=item.batch_number,
                material_id=item.material_id,
                supplier_id=order_data.supplier_id,
                production_date=item.production_date,
                unit_price=item.unit_price,
                unit=item.unit,
                inbound_date=datetime.now().date(),
                creator=current_user.username,
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            db.add(new_batch)
        
        # 使用db.flush()获取自增ID，但不提交事务
        db.flush()
        
        # 创建入库明细和库存明细
        for item in order_data.items:
            # 查询对应的批次对象以获取batch_id
            batch = db.exec(
                select(InventoryBatch).where(InventoryBatch.batch_number == item.batch_number)
            ).first()
            
            # 查询器材信息以获取器材编码、名称和规格
            material = db.get(Material, item.material_id)
            if not material:
                raise HTTPException(status_code=400, detail=f"器材ID {item.material_id} 不存在")
            
            # 创建入库明细
            new_item = InboundOrderItem(
                order_id=new_order.order_id,
                material_id=item.material_id,
                material_code=material.material_code,
                material_name=material.material_name,
                material_specification=material.material_specification if material.material_specification else "",
                quantity=item.quantity,
                unit_price=item.unit_price,
                unit=item.unit,
                batch_id=batch.batch_id,
                bin_id=item.bin_id,
                production_date=item.production_date
            )
            db.add(new_item)
            
            # 创建库存明细
            new_detail = InventoryDetail(
                batch_id=batch.batch_id,
                material_id=item.material_id,
                bin_id=item.bin_id,
                quantity=item.quantity,
                last_updated=new_order.create_time.date()  # 确保是date类型
            )
            db.add(new_detail)
        
        # 创建库存变更流水记录
        for item in order_data.items:
            # 查询对应的批次对象以获取batch_id
            batch = db.exec(
                select(InventoryBatch).where(InventoryBatch.batch_number == item.batch_number)
            ).first()
            
            # 手动创建库存变更流水记录
            transaction = InventoryTransaction(
                material_id=item.material_id,
                batch_id=batch.batch_id,
                change_type="IN",
                quantity_change=item.quantity,
                quantity_before=0,
                quantity_after=item.quantity,
                reference_type="inbound",
                reference_id=new_order.order_id,
                creator=current_user.username,
                transaction_time=datetime.now()
            )
            db.add(transaction)
        
        # 一次性提交所有数据库操作，确保事务原子性
        db.commit()
        db.refresh(new_order)
        
        # 构建响应数据
        return InboundOrderResponse(
            order_id=new_order.order_id,
            order_number=new_order.order_number,
            requisition_reference=new_order.requisition_reference,
            contract_reference=new_order.contract_reference,
            supplier_id=new_order.supplier_id,
            supplier_name=new_order.supplier_name,
            total_quantity=new_order.total_quantity,
            creator=new_order.creator,
            create_time=new_order.create_time,
            inbound_date=new_order.create_time.date()
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建入库单失败: {str(e)}")


@inbound_orders_router.delete("/delete/{order_id}")
async def delete_inbound_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/delete"))
):
    """删除入库单"""
    
    # 获取入库单
    order = db.get(InboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    
    # 获取入库明细中的所有批次号
    items = db.exec(
        select(InboundOrderItem).where(InboundOrderItem.order_id == order_id)
    ).all()
    
    batch_ids = [item.batch_id for item in items]
    
    # 检查是否有出库单引用了这些批次
    problematic_items = []
    for batch_id in batch_ids:
        outbound_items = db.exec(
            select(OutboundOrderItem).where(OutboundOrderItem.batch_id == batch_id)
        ).all()
        
        if outbound_items:
            # 获取相关的出库单编码和统计出库单数量
            outbound_order_numbers = []
            outbound_order_ids = set()  # 用于统计唯一的出库单数量
            
            for outbound_item in outbound_items:
                outbound_order = db.get(OutboundOrder, outbound_item.order_id)
                if outbound_order and outbound_order.order_number:
                    outbound_order_numbers.append(outbound_order.order_number)
                    outbound_order_ids.add(outbound_order.order_id)
            
            # 获取批次信息
            batch = db.get(InventoryBatch, batch_id)
            if batch:
                material = db.get(Material, batch.material_id)
                if material:
                    problematic_items.append({
                        "material_name": material.material_name,
                        "batch_number": batch.batch_number,
                        "outbound_order_numbers": outbound_order_numbers,
                        "outbound_count": len(outbound_order_ids)  # 计算唯一的出库单数量
                    })
    
    # 如果有出库引用，不允许删除
    if problematic_items:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "以下器材已有出库记录，无法删除入库单",
                "problematic_items": problematic_items
            }
        )
    
    # 开始事务删除
    try:
        # 删除库存变更流水记录
        from models.material.inventory_transaction import InventoryTransaction
        db.exec(delete(InventoryTransaction).where(
            InventoryTransaction.reference_id == order_id,
            InventoryTransaction.reference_type == "inbound"
        ))
        
        # 删除库存明细记录
        for batch_id in batch_ids:
            db.exec(delete(InventoryDetail).where(InventoryDetail.batch_id == batch_id))
        
        # 删除入库明细记录
        db.exec(delete(InboundOrderItem).where(InboundOrderItem.order_id == order_id))
        
        # 删除库存批次记录
        for batch_id in batch_ids:
            db.exec(delete(InventoryBatch).where(InventoryBatch.batch_id == batch_id))
        
        # 删除入库单
        db.delete(order)
        
        db.commit()
        
        return {"message": "入库单删除成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除入库单失败: {str(e)}")


@inbound_orders_router.get("/statistics", response_model=InboundOrderStatistics)
async def get_inbound_order_statistics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/statistics"))
):
    """获取入库单统计信息"""
    
    # 构建基础查询
    query = select(InboundOrder)
    
    # 日期筛选
    if start_date:
        query = query.where(InboundOrder.create_time >= start_date)
    if end_date:
        query = query.where(InboundOrder.create_time <= end_date)
    
    # 获取所有入库单
    orders = db.exec(query).all()
    
    # 计算统计信息
    total_orders = len(orders)
    total_quantity = sum(order.total_quantity for order in orders)
    
    # 计算总金额（需要查询明细）
    total_amount = 0
    for order in orders:
        items = db.exec(
            select(InboundOrderItem).where(InboundOrderItem.order_id == order.order_id)
        ).all()
        total_amount += sum(item.quantity * item.unit_price for item in items)
    
    # 按供应商统计
    supplier_stats = {}
    for order in orders:
        supplier_name = order.supplier_name
        if supplier_name not in supplier_stats:
            supplier_stats[supplier_name] = {"count": 0, "quantity": 0, "amount": 0}
        
        supplier_stats[supplier_name]["count"] += 1
        supplier_stats[supplier_name]["quantity"] += order.total_quantity
        
        # 计算该供应商的金额
        items = db.exec(
            select(InboundOrderItem).where(InboundOrderItem.order_id == order.order_id)
        ).all()
        amount = sum(item.quantity * item.unit_price for item in items)
        supplier_stats[supplier_name]["amount"] += amount
    
    # 按日期统计
    date_stats = {}
    for order in orders:
        date_key = order.create_time.date().isoformat()
        if date_key not in date_stats:
            date_stats[date_key] = {"count": 0, "quantity": 0, "amount": 0}
        
        date_stats[date_key]["count"] += 1
        date_stats[date_key]["quantity"] += order.total_quantity
        
        # 计算该日期的金额
        items = db.exec(
            select(InboundOrderItem).where(InboundOrderItem.order_id == order.order_id)
        ).all()
        amount = sum(item.quantity * item.unit_price for item in items)
        date_stats[date_key]["amount"] += amount
    
    return InboundOrderStatistics(
        total_orders=total_orders,
        total_quantity=total_quantity,
        total_amount=total_amount,
        supplier_stats=[{"supplier": k, **v} for k, v in supplier_stats.items()],
        date_stats=[{"date": k, **v} for k, v in date_stats.items()]
    )


# 入库单字段修改路由
@inbound_orders_router.put("/{order_id}/update-order-number")
async def update_order_number(
    order_id: int,
    update_data: OrderNumberUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/update-order-number"))
):
    """修改入库单号"""
    
    # 验证新入库单号的唯一性
    existing_order = db.exec(
        select(InboundOrder).where(InboundOrder.order_number == update_data.order_number)
    ).first()
    if existing_order and existing_order.order_id != order_id:
        raise HTTPException(status_code=400, detail="入库单号已存在")
    
    # 获取入库单
    order = db.get(InboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    
    # 开始事务
    try:
        old_order_number = order.order_number
        order.order_number = update_data.order_number
        
        # 更新库存变更流水表中相关记录
        from models.material.inventory_transaction import InventoryTransaction
        transactions = db.exec(
            select(InventoryTransaction)
            .where(InventoryTransaction.reference_id == order_id)
            .where(InventoryTransaction.reference_type == "inbound")
        ).all()
        
        # 这里需要根据实际需求更新reference_id或其他字段
        # 由于reference_id是入库单ID，不是单号，所以不需要更新
        
        db.commit()
        
        return {"message": "入库单号修改成功", "new_order_number": update_data.order_number}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修改入库单号失败: {str(e)}")


@inbound_orders_router.put("/{order_id}/update-transfer-number")
async def update_transfer_number(
    order_id: int,
    update_data: TransferNumberUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/update-transfer-number"))
):
    """修改调拨单号"""
    
    order = db.get(InboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    
    order.requisition_reference = update_data.requisition_reference
    db.commit()
    
    return {"message": "调拨单号修改成功", "new_transfer_number": update_data.requisition_reference}


@inbound_orders_router.put("/{order_id}/update-supplier")
async def update_supplier(
    order_id: int,
    update_data: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/update-supplier"))
):
    """修改入库单供应商"""
    
    # 验证供应商存在
    supplier = db.get(Supplier, update_data.supplier_id)
    if not supplier:
        raise HTTPException(status_code=400, detail="供应商不存在")
    
    order = db.get(InboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    
    order.supplier_id = update_data.supplier_id
    order.supplier_name = supplier.supplier_name
    db.commit()
    
    return {"message": "供应商修改成功", "new_supplier_id": update_data.supplier_id, "new_supplier_name": supplier.supplier_name}


@inbound_orders_router.put("/{order_id}/update-contract-number")
async def update_contract_number(
    order_id: int,
    update_data: ContractNumberUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/update-contract-number"))
):
    """修改入库单合同号"""
    
    order = db.get(InboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    
    order.contract_reference = update_data.contract_reference
    db.commit()
    
    return {"message": "合同号修改成功", "new_contract_number": update_data.contract_reference}


@inbound_orders_router.put("/{order_id}/update-inbound-date")
async def update_inbound_date(
    order_id: int,
    update_data: InboundOrderUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/update-inbound-date"))
):
    """修改入库单入库日期"""
    
    # 获取入库单
    order = db.get(InboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    
    # 更新入库日期
    if update_data.inbound_date is not None:
        order.inbound_date = update_data.inbound_date
    
    # 更新其他字段（如果需要）
    if update_data.requisition_reference is not None:
        order.requisition_reference = update_data.requisition_reference
    if update_data.contract_reference is not None:
        order.contract_reference = update_data.contract_reference
    if update_data.supplier_id is not None:
        # 验证供应商存在
        supplier = db.get(Supplier, update_data.supplier_id)
        if not supplier:
            raise HTTPException(status_code=400, detail="供应商不存在")
        order.supplier_id = update_data.supplier_id
        order.supplier_name = supplier.supplier_name
    
    db.commit()
    
    return {"message": "入库单信息修改成功", "updated_fields": {
        "inbound_date": update_data.inbound_date
    }}


# 入库单明细管理路由
@inbound_orders_router.post("/{order_id}/items")
async def add_inbound_order_item(
    order_id: int,
    item_data: InboundOrderItemCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/items/new"))
):
    """新增入库单明细中一条器材信息"""
    
    # 验证入库单存在
    order = db.get(InboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    
    # 验证器材存在
    material = db.get(Material, item_data.material_id)
    if not material:
        raise HTTPException(status_code=400, detail="器材不存在")
    
    # 验证货位存在（如果提供了货位ID）
    if item_data.bin_id is not None:
        bin_info = db.get(Bin, item_data.bin_id)
        if not bin_info:
            raise HTTPException(status_code=400, detail="货位不存在")
    
    # 验证批次号唯一性
    existing_batch = db.exec(
        select(InventoryBatch).where(InventoryBatch.batch_number == item_data.batch_number)
    ).first()
    if existing_batch:
        raise HTTPException(status_code=400, detail="批次号已存在")
    
    # 开始事务
    try:
        # 创建库存批次
        current_time = datetime.now()
        new_batch = InventoryBatch(
            batch_number=item_data.batch_number,
            material_id=item_data.material_id,
            supplier_id=order.supplier_id,
            production_date=item_data.production_date,
            unit_price=item_data.unit_price,
            inbound_date=current_time.date(),  # 入库日期设置为当前日期
            creator=current_user.username,      # 操作员设置为当前用户
            create_time=current_time,           # 创建时间设置为当前时间
            update_time=current_time           # 修改时间设置为当前时间
        )
        db.add(new_batch)
        
        # 使用db.flush()获取自增ID，但不提交事务
        db.flush()
        
        # 创建入库明细
        new_item = InboundOrderItem(
            order_id=order_id,
            material_id=item_data.material_id,
            material_code=material.material_code,
            material_name=material.material_name,
            material_specification=material.material_specification if material.material_specification else "",
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            unit=item_data.unit,
            batch_id=new_batch.batch_id,
            bin_id=item_data.bin_id,
            production_date=item_data.production_date
        )
        db.add(new_item)
        
        # 创建库存明细
        new_detail = InventoryDetail(
            batch_id=new_batch.batch_id,
            material_id=item_data.material_id,
            bin_id=item_data.bin_id,
            quantity=item_data.quantity,
            last_updated=order.create_time
        )
        db.add(new_detail)
        
        # 创建库存变更流水记录
        create_inbound_transaction(
            db=db,
            material_id=item_data.material_id,
            batch_id=new_batch.batch_id,
            quantity_change=item_data.quantity,
            quantity_before=0,
            quantity_after=item_data.quantity,
            reference_id=order_id,
            creator=current_user.username
        )
        
        # 更新入库单总数量
        order.total_quantity += item_data.quantity
        
        # 一次性提交所有数据库操作
        db.commit()
        
        return {"message": "入库明细添加成功", "item_id": new_item.item_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加入库明细失败: {str(e)}")


@inbound_orders_router.put("/{order_id}/items/update/{item_id}")
async def update_inbound_order_item(
    order_id: int,
    item_id: int,
    update_data: InboundOrderItemUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/items/update"))
):
    """修改入库明细中某一条目的器材信息"""
    
    print(f"=== 开始更新入库明细 ===")
    print(f"订单ID: {order_id}, 明细ID: {item_id}")
    print(f"更新数据: {update_data}")
    
    # 获取入库明细项
    item = db.get(InboundOrderItem, item_id)
    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="入库明细项不存在")
    
    print(f"找到入库明细: {item}")
    
    # 检查该明细项是否已被出库单引用
    outbound_items = db.exec(
        select(OutboundOrderItem).where(OutboundOrderItem.batch_id == item.batch_id)
    ).all()
    if outbound_items:
        raise HTTPException(status_code=400, detail="该批次已被出库单引用，无法修改")
    
    try:
        print("=== 开始更新字段 ===")
        
        if update_data.batch_number is not None:
            # 验证批次号唯一性
            existing_batch = db.exec(
                select(InventoryBatch).where(InventoryBatch.batch_number == update_data.batch_number)
            ).first()
            if existing_batch and existing_batch.batch_id != item.batch_id:
                raise HTTPException(status_code=400, detail="批次号已存在")
            
            # 更新批次号
            batch = db.get(InventoryBatch, item.batch_id)
            if batch:
                if batch.batch_number != update_data.batch_number:
                    batch.batch_number = update_data.batch_number
                    batch.update_time = datetime.now()  # 更新修改时间
                    db.add(batch)  # 标记批次为脏数据
                    print(f"更新批次号: {update_data.batch_number}, 批次ID: {batch.batch_id}")
                else:
                    print("批次号未变化，跳过更新")
            else:
                print("警告: 未找到对应的批次信息")
        
        if update_data.material_id is not None:
            # 验证器材存在
            material = db.get(Material, update_data.material_id)
            if not material:
                raise HTTPException(status_code=400, detail="器材不存在")
            
            # 检查器材ID是否有变化
            if item.material_id != update_data.material_id:
                # 获取变更前的器材ID
                old_material_id = item.material_id
                
                # 更新入库明细中的器材ID、代码、名称、规格
                item.material_id = update_data.material_id
                item.material_code = material.material_code
                item.material_name = material.material_name
                item.material_specification = material.material_specification if material.material_specification else ""
                
                # 更新批次信息
                batch = db.get(InventoryBatch, item.batch_id)
                if batch:
                    batch.material_id = update_data.material_id
                    batch.update_time = datetime.now()
                    db.add(batch)
                
                # 更新库存明细
                detail = db.exec(
                    select(InventoryDetail).where(InventoryDetail.batch_id == item.batch_id)
                ).first()
                if detail:
                    detail.material_id = update_data.material_id
                    detail.last_updated = datetime.now()
                    db.add(detail)
                # 更新库存变更流水记录
                transaction = db.exec(
                    select(InventoryTransaction).where(InventoryTransaction.batch_id == item.batch_id , 
                                                    InventoryTransaction.reference_type == "inbound",
                                                    InventoryTransaction.reference_id == order_id)
                ).first()
                print(f"找到库存变更记录: {transaction}")
                if transaction:
                    transaction.material_id = update_data.material_id
                    db.add(transaction)

                print(f"更新器材ID: {update_data.material_id}")
            else:
                print("器材ID未变化，跳过更新")
        
        if update_data.bin_id is not None:
            # 验证货位存在（如果提供了货位ID）
            bin_info = db.get(Bin, update_data.bin_id)
            if not bin_info:
                raise HTTPException(status_code=400, detail="货位不存在")
            
            # 检查货位ID是否有变化
            if item.bin_id != update_data.bin_id:
                item.bin_id = update_data.bin_id
                
                # 更新库存明细
                detail = db.exec(
                    select(InventoryDetail).where(InventoryDetail.batch_id == item.batch_id)
                ).first()
                if detail:
                    detail.bin_id = update_data.bin_id
                    detail.last_updated = datetime.now()
                    db.add(detail)
                
                print(f"更新货位ID: {update_data.bin_id}")
            else:
                print("货位ID未变化，跳过更新")
        
        if update_data.production_date is not None:
            # 检查生产日期是否有变化
            if item.production_date != update_data.production_date:
                # 更新批次生产日期
                batch = db.get(InventoryBatch, item.batch_id)
                if batch:
                    batch.production_date = update_data.production_date
                    batch.update_time = datetime.now()
                    db.add(batch)
                
                item.production_date = update_data.production_date
                print(f"更新生产日期: {update_data.production_date}")
            else:
                print("生产日期未变化，跳过更新")
        
        if update_data.quantity is not None:
            # 检查数量是否有变化
            if item.quantity != update_data.quantity:
                print(f"开始更新数量: 原数量={item.quantity}, 新数量={update_data.quantity}")
                
                # 更新入库单总数量
                order = db.get(InboundOrder, order_id)
                if order:
                    old_total = order.total_quantity
                    order.total_quantity = order.total_quantity - item.quantity + update_data.quantity
                    db.add(order)  # 标记入库单为脏数据
                    print(f"更新入库单总数量: {old_total} -> {order.total_quantity}")
                else:
                    print("警告: 未找到对应的入库单")
                
                # 获取变更前的数量用于库存变更流水记录
                old_quantity = item.quantity
                
                # 更新入库明细项数量
                item.quantity = update_data.quantity
                
                # 更新库存明细
                detail = db.exec(
                    select(InventoryDetail).where(InventoryDetail.batch_id == item.batch_id)
                ).first()
                if detail:
                    detail.quantity = update_data.quantity
                    detail.last_updated = datetime.now()  # 更新最后修改时间
                    db.add(detail)  # 标记库存明细为脏数据
                    print(f"更新库存明细数量: {detail.quantity}, 批次ID: {detail.batch_id}")
                else:
                    print("警告: 未找到对应的库存明细")
                
                # 查找并更新对应的库存变更流水记录
                if old_quantity != update_data.quantity:
                    transaction = db.exec(
                        select(InventoryTransaction).where(
                            InventoryTransaction.batch_id == item.batch_id,
                            InventoryTransaction.reference_type == ReferenceType.INBOUND,
                            InventoryTransaction.reference_id == order_id
                        )
                    ).first()

                    if transaction:
                        # 更新现有记录
                        transaction.quantity_after = update_data.quantity
                        transaction.quantity_change = update_data.quantity - transaction.quantity_before  # 计算本次变更的数量差
                        transaction.transaction_time = datetime.now()
                        db.add(transaction)
                        print(f"更新数量变更库存变更流水记录: 变更前数量={transaction.quantity_before}, 变更后数量={transaction.quantity_after}, 数量变化={transaction.quantity_change}")
            else:
                print("数量未变化，跳过更新")
        
        if update_data.unit_price is not None:
            # 检查单价是否有变化
            if item.unit_price != update_data.unit_price:
                  # 更新单价
                item.unit_price = update_data.unit_price
                
                # 更新批次单价
                batch = db.get(InventoryBatch, item.batch_id)
                if batch:
                    batch.unit_price = update_data.unit_price
                    batch.update_time = datetime.now()
                    db.add(batch)
                
                print(f"更新单价: {update_data.unit_price}")
            else:
                print("单价未变化，跳过更新")
        
        if update_data.unit is not None:
            # 检查单位是否有变化
            if item.unit != update_data.unit:  
                # 更新单位
                item.unit = update_data.unit
                # 更新批次单位
                batch = db.get(InventoryBatch, item.batch_id)
                if batch:
                    batch.unit = update_data.unit
                    batch.update_time = datetime.now()
                    db.add(batch)
                
                print(f"更新单位: {update_data.unit}")
            else:
                print("单位未变化，跳过更新")

        # 提交事务
        db.commit()
        print("事务提交成功")
        
        db.refresh(item)
        print("刷新对象成功")
        
        print("=== 更新完成 ===")
        return item
        
    except Exception as e:
        print(f"=== 更新失败 ===")
        print(f"错误类型: {type(e)}")
        print(f"错误信息: {e}")
        db.rollback()
        print("事务已回滚")
        raise HTTPException(status_code=500, detail=f"更新入库明细失败: {str(e)}")


@inbound_orders_router.delete("/{order_id}/items/delete/{item_id}")
async def delete_inbound_order_item(
    order_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/items/delete"))
):
    """删除入库明细中某一条目的器材信息"""
    
    # 获取入库明细项
    item = db.get(InboundOrderItem, item_id)
    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="入库明细项不存在")
    
    # 检查该明细项是否已被出库单引用
    outbound_items = db.exec(
        select(OutboundOrderItem).where(OutboundOrderItem.batch_id == item.batch_id)
    ).all()
    
    if outbound_items:
        raise HTTPException(status_code=400, detail="该器材已有出库记录，无法删除")
    
    # 开始事务删除
    try:
        # 删除库存变更流水记录
        from models.material.inventory_transaction import InventoryTransaction
        db.exec(delete(InventoryTransaction).where(
            InventoryTransaction.batch_id == item.batch_id,
            InventoryTransaction.reference_id == order_id,
            InventoryTransaction.reference_type == "inbound"
        ))
        
        # 删除库存明细记录
        db.exec(delete(InventoryDetail).where(InventoryDetail.batch_id == item.batch_id))
        
        # 删除库存批次记录
        batch = db.get(InventoryBatch, item.batch_id)
        if batch:
            db.delete(batch)
        
        # 删除入库明细项
        db.delete(item)
        
        # 更新入库单总数量
        order = db.get(InboundOrder, order_id)
        if order:
            order.total_quantity -= item.quantity
        
        db.commit()
        
        return {"message": "入库明细删除成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除入库明细失败: {str(e)}")

@inbound_orders_router.delete("/{order_id}/items/batch-delete")
async def batch_delete_inbound_order_items(
    order_id: int,
    item_ids: list[int] = Query(..., description="需要删除的入库单明细项ID列表"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/items/delete"))
):
    """批量删除指定入库单的明细项"""
    
    if not item_ids:
        raise HTTPException(status_code=400, detail="请提供需要删除的入库单明细项ID列表")
    
    # 验证入库单存在
    order = db.get(InboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="入库单不存在")
    
    # 获取所有待删除的明细项，并验证属于该入库单
    items = db.exec(
        select(InboundOrderItem)
        .where(InboundOrderItem.item_id.in_(item_ids))
        .where(InboundOrderItem.order_id == order_id)
    ).all()
    
    if len(items) != len(item_ids):
        # 找出不存在的明细项ID
        existing_item_ids = {item.item_id for item in items}
        missing_item_ids = [item_id for item_id in item_ids if item_id not in existing_item_ids]
        raise HTTPException(
            status_code=404, 
            detail={
                "message": f"部分入库单明细项不存在或不属于入库单{order_id}，请检查明细项ID是否正确",
                "missing_item_ids": missing_item_ids,
                "order_id": order_id,
                "total_requested": len(item_ids),
                "total_found": len(items)
            }
        )
    
    # 检查是否有出库单引用了这些批次
    batch_ids = [item.batch_id for item in items]
    problematic_items = []
    for batch_id in batch_ids:
        outbound_items = db.exec(
            select(OutboundOrderItem).where(OutboundOrderItem.batch_id == batch_id)
        ).all()
        
        if outbound_items:
            # 获取相关的出库单编码和统计出库单数量
            outbound_order_numbers = []
            outbound_order_ids = set()  # 用于统计唯一的出库单数量
            
            for outbound_item in outbound_items:
                outbound_order = db.get(OutboundOrder, outbound_item.order_id)
                if outbound_order and outbound_order.order_number:
                    outbound_order_numbers.append(outbound_order.order_number)
                    outbound_order_ids.add(outbound_order.order_id)
            
            # 获取批次信息
            batch = db.get(InventoryBatch, batch_id)
            if batch:
                material = db.get(Material, batch.material_id)
                if material:
                    problematic_items.append({
                        "material_name": material.material_name,
                        "batch_number": batch.batch_number,
                        "outbound_order_numbers": outbound_order_numbers,
                        "outbound_count": len(outbound_order_ids)  # 计算唯一的出库单数量
                    })
    
    # 如果有出库引用，不允许删除
    if problematic_items:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "以下器材已有出库记录，无法删除入库单明细项",
                "problematic_items": problematic_items
            }
        )
    
    # 开始事务删除
    try:
        # 删除库存变更流水记录
        for item in items:
            db.exec(delete(InventoryTransaction).where(
                InventoryTransaction.reference_id == item.order_id,
                InventoryTransaction.reference_type == "inbound",
                InventoryTransaction.batch_id == item.batch_id
            ))
        
        # 删除库存明细记录
        for item in items:
            db.exec(delete(InventoryDetail).where(InventoryDetail.batch_id == item.batch_id))
        
        # 删除入库明细记录
        db.exec(delete(InboundOrderItem).where(InboundOrderItem.item_id.in_(item_ids)))
        
        # 删除库存批次记录
        for batch_id in batch_ids:
            db.exec(delete(InventoryBatch).where(InventoryBatch.batch_id == batch_id))
        
        # 更新入库单的总数量
        order_ids = {item.order_id for item in items}
        for order_id in order_ids:
            order = db.get(InboundOrder, order_id)
            if order:
                remaining_items = db.exec(
                    select(InboundOrderItem).where(InboundOrderItem.order_id == order_id)
                ).all()
                order.total_quantity = sum(item.quantity for item in remaining_items)
                db.add(order)
        
        db.commit()
        
        return {"message": "入库单明细项批量删除成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除入库单明细项失败: {str(e)}")


@inbound_orders_router.get("/generate-order-number/{date_str}")
async def generate_inbound_order_number(
    date_str: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/generate-order-number"))
):
    """根据日期生成未被使用的最小流水号入库单号"""
    
    # 验证日期格式为YYYYMMDD
    if len(date_str) != 8 or not date_str.isdigit():
        raise HTTPException(status_code=400, detail="日期格式不正确，应为YYYYMMDD格式")
    
    try:
        # 解析日期
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        
        # 验证日期有效性
        if month < 1 or month > 12 or day < 1 or day > 31:
            raise ValueError("日期无效")
            
        # 构建入库单号前缀：RK + 日期
        order_prefix = f"RK{date_str}-"
        
        # 查询系统中所有以该前缀开头的入库单号
        existing_orders = db.exec(
            select(InboundOrder.order_number)
            .where(InboundOrder.order_number.like(f"{order_prefix}%"))
        ).all()
        
        # 提取现有的流水号
        used_serial_numbers = []
        for order_number in existing_orders:
            # 提取流水号部分（最后3位数字）
            serial_part = order_number.replace(order_prefix, "")
            if serial_part.isdigit() and len(serial_part) == 3:
                used_serial_numbers.append(int(serial_part))
        
        # 找到最小的未被使用的流水号
        if not used_serial_numbers:
            # 如果没有现有订单，从001开始
            next_serial = 1
        else:
            # 找到最小的未被使用的流水号
            max_serial = max(used_serial_numbers)
            
            # 检查是否有空缺的流水号
            all_possible_serials = set(range(1, max_serial + 2))  # +2确保包含下一个
            used_set = set(used_serial_numbers)
            available_serials = all_possible_serials - used_set
            
            if available_serials:
                next_serial = min(available_serials)
            else:
                next_serial = max_serial + 1
        
        # 确保流水号不超过999
        if next_serial > 999:
            raise HTTPException(status_code=400, detail="当日入库单数量已达上限（999），无法生成新的入库单号")
        
        # 格式化流水号为3位数字
        serial_number = str(next_serial).zfill(3)
        
        # 生成完整的入库单号
        generated_order_number = f"{order_prefix}{serial_number}"
        
        return {
            "order_number": generated_order_number,
            "date": date_str,
            "serial_number": serial_number
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期无效: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成入库单号失败: {str(e)}")


@inbound_orders_router.get("/suppliers")
async def get_inbound_order_suppliers(
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/suppliers"))
):
    """获取所有入库单中出现的供应商ID和名称合集（去除重复项）"""
    
    try:
        # 查询所有入库单中的供应商信息，去除重复项
        suppliers = db.exec(
            select(InboundOrder.supplier_id, InboundOrder.supplier_name)
            .distinct()
            .order_by(InboundOrder.supplier_name)
        ).all()
        
        # 构建响应数据
        supplier_list = []
        for supplier_id, supplier_name in suppliers:
            supplier_list.append({
                "supplier_id": supplier_id,
                "supplier_name": supplier_name
            })
        
        return {
            "suppliers": supplier_list,
            "total": len(supplier_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取供应商列表失败: {str(e)}")


@inbound_orders_router.get("/pdf/{order_number}")
async def generate_inbound_order_pdf_route(
    order_number: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/inbound-orders/pdf"))
):
    """生成入库单PDF文件"""
    
    try:
        # 查询入库单基本信息
        order = db.exec(select(InboundOrder).where(InboundOrder.order_number == order_number)).first()
        if not order:
            raise HTTPException(status_code=404, detail="入库单不存在")
        
        # 查询入库单明细
        items_query = select(InboundOrderItem).where(InboundOrderItem.order_id == order.order_id)
        items = db.exec(items_query).all()
        
        # 构建订单数据
        order_data = {
            'order_number': order.order_number,
            'supplier': order.supplier_name,
            'inbound_date': order.create_time.strftime('%Y-%m-%d'),
            'creator': order.creator,
            'remark': ''  # 可以根据需要添加备注字段
        }
        
        # 构建明细数据
        items_data = []
        total_amount = 0
        
        for index, item in enumerate(items, 1):
            amount = item.quantity * item.unit_price
            total_amount += amount
            
            items_data.append({
                'index': index,
                'material_code': item.material_code,
                'material_name': item.material_name,
                'specification': item.material_specification or '',
                'unit': item.unit,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'amount': amount,
                'remark': ''  # 可以根据需要添加备注
            })
        
        # 生成PDF文件
        pdf_filename = f"inbound_order_{order_number}.pdf"
        success = generate_inbound_order_pdf(order_data, items_data, pdf_filename)
        
        if not success:
            raise HTTPException(status_code=500, detail="PDF生成失败")
        
        # 读取PDF文件内容
        with open(pdf_filename, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
        
        # 删除临时文件
        os.remove(pdf_filename)
        
        # 返回PDF文件
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={pdf_filename}",
                "Content-Type": "application/pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成PDF失败: {str(e)}")

