from fastapi import APIRouter, Depends, HTTPException, status, Query, Security, Response
from sqlmodel import Session, select, func, and_, or_
from typing import Optional
from datetime import date, datetime
import os

from database import get_db
from core.security import get_current_active_user, Permission, get_required_scopes_for_route
from schemas.account.user import UserResponse
from schemas.material import (
    OutboundOrderCreate, OutboundOrderResponse, OutboundOrderDetailResponse, 
    OutboundOrderPaginationResult, OutboundOrderListResponse,
    OutboundOrderStatistics, OutboundOrderNumberUpdate, OutboundTransferNumberUpdate,
    CustomerUpdate, CreateTimeUpdate, OutboundOrderItemUpdate, OutboundOrderItemCreate, 
    OutboundOrderItemResponse, OutboundOrderItemBatchDelete, BatchDeleteResponse
)
from models.material.outbound_order import OutboundOrder
from models.material.outbound_order_item import OutboundOrderItem
from models.base.customer import Customer
from models.material.material import Material
from models.base.bin import Bin
from models.material.inventory_batch import InventoryBatch
from models.material.inventory_detail import InventoryDetail
from models.material.inventory_transaction import InventoryTransaction, ReferenceType
from utils import create_outbound_transaction
from utils.inventory_transaction_utils import (
    delete_inventory_transaction, get_inventory_transactions_by_criteria, update_inventory_transaction
)
from utils.pdf_generator import generate_outbound_order_pdf

# 创建出库单管理路由
outbound_orders_router = APIRouter(tags=["出库单管理"], prefix="/outbound-orders")


@outbound_orders_router.get("", response_model=OutboundOrderPaginationResult)
async def read_outbound_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（出库单号、客户名称、调拨单号）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    sort_by: str = Query("create_time", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向（asc/desc）"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/"))
):
    """获取出库单分页列表"""
    
    # 构建查询条件
    query = select(OutboundOrder)
    
    # 关键词搜索
    if keyword:
        # 分割关键词，支持多关键词搜索（空格分隔，AND关系）
        keywords = keyword.strip().split()
        if keywords:
            # 为每个关键词创建OR条件（在单个字段内搜索）
            keyword_filters = []
            for kw in keywords:
                kw_filter = or_(
                    OutboundOrder.order_number.contains(kw),
                    OutboundOrder.customer_name.contains(kw),
                    OutboundOrder.requisition_reference.contains(kw)
                )
                keyword_filters.append(kw_filter)
            
            # 将所有关键词的OR条件用AND连接
            query = query.where(and_(*keyword_filters))
    
    # 日期筛选
    if start_date:
        query = query.where(OutboundOrder.create_time >= start_date)
    if end_date:
        query = query.where(OutboundOrder.create_time <= end_date)
    
    # 客户筛选
    if customer_id:
        query = query.where(OutboundOrder.customer_id == customer_id)
    
    # 排序
    sort_field = getattr(OutboundOrder, sort_by, OutboundOrder.create_time)
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
        order_responses.append(OutboundOrderResponse(
            order_id=order.order_id,
            order_number=order.order_number,
            requisition_reference=order.requisition_reference,
            customer_id=order.customer_id,
            customer_name=order.customer_name,
            total_quantity=order.total_quantity,
            creator=order.creator,
            create_time=order.create_time
        ))
    
    return OutboundOrderPaginationResult(
        total=total,
        page=page,
        page_size=page_size,
        data=order_responses
    )


@outbound_orders_router.get("/all", response_model=OutboundOrderListResponse)
async def get_all_outbound_orders(
    keyword: Optional[str] = Query(None, description="关键词搜索（出库单号、客户名称、调拨单号）"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    sort_by: str = Query("create_time", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向（asc/desc）"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/all"))
):
    """获取所有出库单列表（不分页）"""
    
    # 构建查询条件
    query = select(OutboundOrder)
    
    # 关键词搜索
    if keyword:
        # 分割关键词，支持多关键词搜索（空格分隔，AND关系）
        keywords = keyword.strip().split()
        if keywords:
            # 为每个关键词创建OR条件（在单个字段内搜索）
            keyword_filters = []
            for kw in keywords:
                kw_filter = or_(
                    OutboundOrder.order_number.contains(kw),
                    OutboundOrder.customer_name.contains(kw),
                    OutboundOrder.requisition_reference.contains(kw)
                )
                keyword_filters.append(kw_filter)
            
            # 将所有关键词的OR条件用AND连接
            query = query.where(and_(*keyword_filters))
    
    # 日期筛选
    if start_date:
        query = query.where(OutboundOrder.create_time >= start_date)
    if end_date:
        query = query.where(OutboundOrder.create_time <= end_date)
    
    # 客户筛选
    if customer_id:
        query = query.where(OutboundOrder.customer_id == customer_id)
    
    # 排序
    sort_field = getattr(OutboundOrder, sort_by, OutboundOrder.create_time)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    # 执行查询
    orders = db.exec(query).all()
    
    # 构建响应数据
    order_responses = []
    for order in orders:
        order_responses.append(OutboundOrderResponse(
            order_id=order.order_id,
            order_number=order.order_number,
            requisition_reference=order.requisition_reference,
            customer_id=order.customer_id,
            customer_name=order.customer_name,
            total_quantity=order.total_quantity,
            creator=order.creator,
            create_time=order.create_time
        ))
    
    return OutboundOrderListResponse(
        total=len(orders),
        data=order_responses
    )


@outbound_orders_router.get("/get/{order_id}", response_model=OutboundOrderDetailResponse)
async def get_outbound_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/get"))
):
    """获取单个出库单的详细信息"""
    
    # 查询出库单基本信息
    order = db.get(OutboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    
    # 查询出库单明细
    items_query = select(OutboundOrderItem).where(OutboundOrderItem.order_id == order_id)
    items = db.exec(items_query).all()
    
    # 构建明细响应数据
    item_responses = []
    for item in items:
        item_responses.append(OutboundOrderItemResponse(
            item_id=item.item_id,
            material_id=item.material_id,
            material_code=item.material_code,
            material_name=item.material_name,
            material_specification=item.material_specification,
            quantity=item.quantity,
            unit_price=item.unit_price,
            unit=item.unit,
            batch_id=item.batch_id,
            batch_number=item.batch.batch_number if item.batch else "",
            bin_id=item.bin_id,
            bin_name=item.bin.bin_name if item.bin else "",
            equipment_name=item.material.equipment_name if item.material else None
        ))
    
    # 构建出库单响应数据
    order_response = OutboundOrderResponse(
        order_id=order.order_id,
        order_number=order.order_number,
        requisition_reference=order.requisition_reference,
        customer_id=order.customer_id,
        customer_name=order.customer_name,
        total_quantity=order.total_quantity,
        creator=order.creator,
        create_time=order.create_time
    )
    
    return OutboundOrderDetailResponse(
        order=order_response,
        items=item_responses
    )


@outbound_orders_router.post("", response_model=OutboundOrderResponse)
async def create_outbound_order(
    order_data: OutboundOrderCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/"))
):
    """创建新出库单"""
    
    # 验证出库单号唯一性
    existing_order = db.exec(select(OutboundOrder).where(OutboundOrder.order_number == order_data.order_number)).first()
    if existing_order:
        raise HTTPException(status_code=400, detail="出库单号已存在")
    
    # 验证客户是否存在
    customer = db.get(Customer, order_data.customer_id)
    if not customer:
        raise HTTPException(status_code=400, detail="客户不存在")
    
    # 验证是否有明细项
    if not order_data.items or len(order_data.items) == 0:
        raise HTTPException(status_code=400, detail="出库单至少需要包含一个明细项")
    
    # 预验证所有明细数据，但不进行实际修改
    validated_items = []
    total_quantity = 0
    
    for item_data in order_data.items:
        # 验证批次信息，并从批次获取器材信息
        batch = db.get(InventoryBatch, item_data.batch_id)
        if not batch:
            raise HTTPException(status_code=400, detail=f"批次ID {item_data.batch_id} 不存在")
        
        # 从批次获取器材信息
        material = db.get(Material, batch.material_id)
        if not material:
            raise HTTPException(status_code=400, detail=f"批次对应的器材不存在")
        
        # 验证库存数量是否足够
        inventory_detail = db.exec(select(InventoryDetail).where(
            InventoryDetail.batch_id == item_data.batch_id
        )).first()
        
        if not inventory_detail or inventory_detail.quantity < item_data.quantity:
            raise HTTPException(status_code=400, detail=f"器材 {material.material_name} 库存不足")
        
        # 存储验证通过的项信息，后续再进行实际处理
        validated_items.append({
            'item_data': item_data,
            'batch': batch,
            'material': material,
            'inventory_detail': inventory_detail
        })
        
        total_quantity += item_data.quantity
    
    # 开始事务，只有当所有明细都验证通过后才创建出库单
    try:
        # 创建出库单记录
        new_order = OutboundOrder(
            order_number=order_data.order_number,
            requisition_reference=order_data.requisition_reference,
            customer_id=order_data.customer_id,
            customer_name=customer.customer_name,
            total_quantity=total_quantity,  # 直接设置总数量
            creator=current_user.username,
            create_time=datetime.now()
        )
        db.add(new_order)
        # 刷新以获取自动生成的order_id，但不提交事务
        db.flush()
        
        # 处理已验证的明细记录
        for validated in validated_items:
            item_data = validated['item_data']
            batch = validated['batch']
            material = validated['material']
            inventory_detail = validated['inventory_detail']
            
            # 创建出库明细记录
            new_item = OutboundOrderItem(
                order_id=new_order.order_id,
                material_id=batch.material_id,
                material_code=material.material_code,
                material_name=material.material_name,
                material_specification=material.material_specification if material.material_specification else "",
                quantity=item_data.quantity,
                unit_price=batch.unit_price,
                unit=batch.unit,
                batch_id=item_data.batch_id,
                bin_id=inventory_detail.bin_id if inventory_detail.bin_id is not None else None
            )
            db.add(new_item)
            
            # 更新库存明细数量
            inventory_detail.quantity -= item_data.quantity
            inventory_detail.last_updated = datetime.now().date()
            db.add(inventory_detail)
            
            # 记录库存变更流水
            transaction = create_outbound_transaction(
                db=db,
                material_id=batch.material_id,
                batch_id=item_data.batch_id,
                quantity_change=-item_data.quantity,  # 出库数量为负数
                quantity_before=inventory_detail.quantity + item_data.quantity,  # 出库前数量
                quantity_after=inventory_detail.quantity,  # 出库后数量
                reference_id=new_order.order_id,
                creator=current_user.username
            )
            db.add(transaction)
        
        db.commit()
        db.refresh(new_order)
        
        return OutboundOrderResponse(
            order_id=new_order.order_id,
            order_number=new_order.order_number,
            requisition_reference=new_order.requisition_reference,
            customer_id=new_order.customer_id,
            customer_name=new_order.customer_name,
            total_quantity=new_order.total_quantity,
            creator=new_order.creator,
            create_time=new_order.create_time
        )
        
    except Exception as e:
        db.rollback()
        # 提供更详细的错误信息
        raise HTTPException(status_code=500, detail=f"创建出库单失败: {str(e)}")


@outbound_orders_router.delete("/delete/{order_id}")
async def delete_outbound_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/delete"))
):
    """删除出库单"""
    
    # 查询出库单
    order = db.get(OutboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    
    # 开始事务
    try:
        # 查询出库单明细
        items_query = select(OutboundOrderItem).where(OutboundOrderItem.order_id == order_id)
        items = db.exec(items_query).all()
        
        # 恢复库存数量
        for item in items:
            # 查询库存明细（批次号已确定器材信息，只需根据batch_id和bin_id确定唯一记录）
            inventory_detail = db.exec(select(InventoryDetail).where(
                InventoryDetail.batch_id == item.batch_id
            )).first()
            
            if inventory_detail:
                inventory_detail.quantity += item.quantity
                db.add(inventory_detail)
            else:
                # 如果找不到对应的库存明细，记录警告信息
                print(f"警告：找不到对应的库存明细记录，batch_id={item.batch_id}, bin_id={item.bin_id}")
            
        # 删除库存变更流水（使用工具函数）
        transactions = get_inventory_transactions_by_criteria(
            db=db,
            reference_id=order.order_id,
            reference_type=ReferenceType.OUTBOUND
        )
        print(f"删除前库存变更流水数量: {len(transactions)}")
        for transaction in transactions:
            delete_inventory_transaction(db=db, transaction_id=transaction.transaction_id)
        
        # 删除出库单明细
        for item in items:
            db.delete(item)
        
        # 删除出库单
        db.delete(order)
        
        db.commit()
        
        return {"message": "出库单删除成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除出库单失败: {str(e)}")

@outbound_orders_router.put("/update-create-time/{order_id}")
async def update_outbound_create_time(
    order_id: int,
    update_data: CreateTimeUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/update-create-time"))
):
    """修改出库单创建时间"""
    
    # 查询出库单
    order = db.get(OutboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    
    # 更新创建时间
    order.create_time = update_data.create_time
    db.add(order)
    db.commit()
    
    return {"message": "出库单创建时间修改成功", "updated_fields": {
        "create_time": update_data.create_time
    }}


@outbound_orders_router.get("/statistics", response_model=OutboundOrderStatistics)
async def get_outbound_order_statistics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/statistics"))
):
    """获取出库单统计信息"""
    
    # 构建查询条件
    query = select(OutboundOrder)
    
    # 日期筛选
    if start_date:
        query = query.where(OutboundOrder.create_time >= start_date)
    if end_date:
        query = query.where(OutboundOrder.create_time <= end_date)
    
    # 执行查询
    orders = db.exec(query).all()
    
    # 统计信息
    total_orders = len(orders)
    total_quantity = sum(order.total_quantity for order in orders)
    total_amount = sum(
        sum(item.quantity * item.unit_price for item in order.items) 
        for order in orders
    )
    
    # 按客户统计
    customer_stats = {}
    for order in orders:
        if order.customer_name not in customer_stats:
            customer_stats[order.customer_name] = {
                "customer_name": order.customer_name,
                "order_count": 0,
                "total_quantity": 0,
                "total_amount": 0
            }
        customer_stats[order.customer_name]["order_count"] += 1
        customer_stats[order.customer_name]["total_quantity"] += order.total_quantity
        customer_stats[order.customer_name]["total_amount"] += sum(
            item.quantity * item.unit_price for item in order.items
        )
    
    # 按日期统计
    date_stats = {}
    for order in orders:
        date_str = order.create_time.date().isoformat()
        if date_str not in date_stats:
            date_stats[date_str] = {
                "date": date_str,
                "order_count": 0,
                "total_quantity": 0,
                "total_amount": 0
            }
        date_stats[date_str]["order_count"] += 1
        date_stats[date_str]["total_quantity"] += order.total_quantity
        date_stats[date_str]["total_amount"] += sum(
            item.quantity * item.unit_price for item in order.items
        )
    
    return OutboundOrderStatistics(
        total_orders=total_orders,
        total_quantity=total_quantity,
        total_amount=total_amount,
        customer_stats=list(customer_stats.values()),
        date_stats=list(date_stats.values())
    )


@outbound_orders_router.get("/generate-order-number/{date_str}")
async def generate_outbound_order_number(
    date_str: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/generate-order-number"))
):
    """根据日期生成出库单号"""
    
    # 验证日期格式
    if len(date_str) != 8 or not date_str.isdigit():
        raise HTTPException(status_code=400, detail="日期格式错误，应为YYYYMMDD格式")
    
    try:
        # 验证日期是否有效
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        datetime(year, month, day)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的日期")
    
    # 构建前缀：CK + 日期
    prefix = f"CK{date_str}"
    
    # 查询系统中包含该前缀的所有出库单号
    existing_orders = db.exec(
        select(OutboundOrder.order_number)
        .where(OutboundOrder.order_number.like(f"{prefix}%"))
    ).all()
    
    # 提取现有的流水号
    existing_sequence_numbers = []
    for order_number in existing_orders:
        if len(order_number) > len(prefix) + 1 and order_number[len(prefix)] == "-":
            try:
                sequence = int(order_number[len(prefix) + 1:])
                existing_sequence_numbers.append(sequence)
            except ValueError:
                continue
    
    # 计算最小未使用的流水号
    if existing_sequence_numbers:
        max_sequence = max(existing_sequence_numbers)
        next_sequence = max_sequence + 1
    else:
        next_sequence = 1
    
    # 格式化流水号为3位数字
    sequence_str = f"{next_sequence:03d}"
    
    # 生成完整的出库单号
    order_number = f"{prefix}-{sequence_str}"
    
    return {
        "order_number": order_number,
        "date": date_str,
        "sequence": next_sequence
    }


@outbound_orders_router.get("/customers")
async def get_outbound_order_customers(
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/customers"))
):
    """获取所有出库单中出现的客户ID和名称合集（去除重复项）"""
    
    try:
        # 查询所有出库单中的客户ID和名称，使用distinct去重
        customers = db.exec(
            select(OutboundOrder.customer_id, OutboundOrder.customer_name)
            .distinct()
            .where(OutboundOrder.customer_id.isnot(None))
            .order_by(OutboundOrder.customer_name)
        ).all()
        
        # 构建响应数据
        customer_list = []
        for customer_id, customer_name in customers:
            customer_list.append({
                "customer_id": customer_id,
                "customer_name": customer_name
            })
        
        return {
            "total": len(customer_list),
            "customers": customer_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户列表失败: {str(e)}")


@outbound_orders_router.get("/pdf/{order_number}")
async def generate_outbound_order_pdf_route(
    order_number: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/pdf"))
):
    """生成出库单PDF文件"""
    
    try:
        # 查询出库单基本信息
        order = db.exec(select(OutboundOrder).where(OutboundOrder.order_number == order_number)).first()
        if not order:
            raise HTTPException(status_code=404, detail="出库单不存在")
        
        # 查询出库单明细
        items_query = select(OutboundOrderItem).where(OutboundOrderItem.order_id == order.order_id)
        items = db.exec(items_query).all()
        
        # 构建订单数据
        order_data = {
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'outbound_date': order.create_time.strftime('%Y-%m-%d'),
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
        pdf_filename = f"outbound_order_{order_number}.pdf"
        success = generate_outbound_order_pdf(order_data, items_data, pdf_filename)
        
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


@outbound_orders_router.get("/excel/{order_number}")
async def generate_outbound_order_excel_route(
    order_number: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/excel"))
):
    """生成出库单Excel文件"""
    
    try:
        from utils.excel_generator import generate_outbound_order_excel
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"开始生成出库单Excel: {order_number}")
        
        # 查询出库单基本信息
        order = db.exec(select(OutboundOrder).where(OutboundOrder.order_number == order_number)).first()
        if not order:
            raise HTTPException(status_code=404, detail="出库单不存在")
        
        # 查询出库单明细
        items_query = select(OutboundOrderItem).where(OutboundOrderItem.order_id == order.order_id)
        items = db.exec(items_query).all()
        
        # 构建订单数据
        order_data = {
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'outbound_date': order.create_time.strftime('%Y-%m-%d'),
            'creator': order.creator
        }
        
        # 构建明细数据
        items_data = []
        for item in items:
            items_data.append({
                'material_code': item.material_code,
                'material_name': item.material_name,
                'material_specification': item.material_specification or '',
                'unit': item.unit,
                'quantity': item.quantity,
                'unit_price': item.unit_price
            })
        
        # 生成Excel文件
        excel_filename = f"outbound_order_{order_number}.xlsx"
        logger.info(f"准备生成Excel文件: {excel_filename}")
        success = generate_outbound_order_excel(order_data, items_data, excel_filename)
        
        if not success:
            logger.error(f"Excel生成失败: {excel_filename}")
            raise HTTPException(status_code=500, detail="Excel生成失败")
        
        logger.info(f"Excel文件生成成功: {excel_filename}")
        
        # 读取Excel文件内容
        with open(excel_filename, 'rb') as excel_file:
            excel_content = excel_file.read()
        
        # 删除临时文件
        os.remove(excel_filename)
        logger.info(f"临时文件已删除: {excel_filename}")
        
        # 返回Excel文件
        return Response(
            content=excel_content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={excel_filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            }
        )
        
    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"Excel模板文件不存在: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Excel模板文件不存在: {str(e)}")
    except Exception as e:
        logger.error(f"生成Excel失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成Excel失败: {str(e)}")

        
@outbound_orders_router.put("/{order_id}/update-order-number", response_model=OutboundOrderResponse)
async def update_outbound_order_number(
    order_id: int,
    update_data: OutboundOrderNumberUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/update-order-number"))
):
    """修改出库单号"""
    
    # 验证新出库单号唯一性
    existing_order = db.exec(select(OutboundOrder).where(OutboundOrder.order_number == update_data.order_number)).first()
    if existing_order and existing_order.order_id != order_id:
        raise HTTPException(status_code=400, detail="出库单号已存在")
    
    # 查询出库单
    order = db.get(OutboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    
    # 开始事务
    try:
        order.order_number = update_data.order_number
        db.add(order)
        
        # 注意：出库单号更新不会影响库存变更流水表中的reference_id
        # reference_id对应的是出库单ID，不是出库单号，因此不需要更新库存变更流水记录
        
        db.commit()
        db.refresh(order)
        
        return OutboundOrderResponse(
            order_id=order.order_id,
            order_number=order.order_number,
            requisition_reference=order.requisition_reference,
            customer_id=order.customer_id,
            customer_name=order.customer_name,
            total_quantity=order.total_quantity,
            creator=order.creator,
            create_time=order.create_time
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修改出库单号失败: {str(e)}")


@outbound_orders_router.put("/{order_id}/update-transfer-number", response_model=OutboundOrderResponse)
async def update_outbound_transfer_number(
    order_id: int,
    update_data: OutboundTransferNumberUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/update-transfer-number"))
):
    """修改调拨单号"""
    
    # 查询出库单
    order = db.get(OutboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    
    order.requisition_reference = update_data.requisition_reference
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return OutboundOrderResponse(
        order_id=order.order_id,
        order_number=order.order_number,
        requisition_reference=order.requisition_reference,
        customer_id=order.customer_id,
        customer_name=order.customer_name,
        total_quantity=order.total_quantity,
        creator=order.creator,
        create_time=order.create_time
    )


@outbound_orders_router.put("/{order_id}/update-customer", response_model=OutboundOrderResponse)
async def update_outbound_customer(
    order_id: int,
    update_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/update-customer"))
):
    """修改出库单客户"""
    
    # 验证客户是否存在
    customer = db.get(Customer, update_data.customer_id)
    if not customer:
        raise HTTPException(status_code=400, detail="客户不存在")
    
    # 查询出库单
    order = db.get(OutboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    
    order.customer_id = update_data.customer_id
    order.customer_name = customer.customer_name
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return OutboundOrderResponse(
        order_id=order.order_id,
        order_number=order.order_number,
        requisition_reference=order.requisition_reference,
        customer_id=order.customer_id,
        customer_name=order.customer_name,
        total_quantity=order.total_quantity,
        creator=order.creator,
        create_time=order.create_time
    )


@outbound_orders_router.post("/{order_id}/items", response_model=OutboundOrderItemResponse)
async def add_outbound_order_item(
    order_id: int,
    item_data: OutboundOrderItemCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/items"))
):
    """新增出库单明细中一条器材信息"""
    
    # 验证出库单是否存在
    order = db.get(OutboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    
    # 验证批次信息，并从批次获取器材信息
    batch = db.get(InventoryBatch, item_data.batch_id)
    if not batch:
        raise HTTPException(status_code=400, detail=f"批次ID {item_data.batch_id} 不存在")
    
    # 从批次获取器材信息
    material = db.get(Material, batch.material_id)
    if not material:
        raise HTTPException(status_code=400, detail=f"批次对应的器材不存在")
    
    # 验证库存数量是否足够
    inventory_detail = db.exec(select(InventoryDetail).where(
        InventoryDetail.batch_id == item_data.batch_id
    )).first()
    
    if not inventory_detail or inventory_detail.quantity < item_data.quantity:
        raise HTTPException(status_code=400, detail=f"器材 {material.material_name} 库存不足")
    
    # 开始事务
    try:
        # 创建出库明细记录
        new_item = OutboundOrderItem(
            order_id=order_id,
            material_id=batch.material_id,
            material_code=material.material_code,
            material_name=material.material_name,
            material_specification=material.material_specification if material.material_specification else "",
            quantity=item_data.quantity,
            unit_price=batch.unit_price,
            unit=batch.unit,  
            batch_id=item_data.batch_id,
            bin_id=inventory_detail.bin_id if inventory_detail.bin_id is not None else None
        )
        db.add(new_item)
        
        # 更新库存明细数量
        inventory_detail.quantity -= item_data.quantity
        db.add(inventory_detail)
        
        # 更新出库单总数量
        order.total_quantity += item_data.quantity
        db.add(order)
        
        # 记录库存变更流水
        transaction = create_outbound_transaction(
            db=db,
            material_id=batch.material_id,
            batch_id=item_data.batch_id,
            quantity_change=-item_data.quantity,
            quantity_before=inventory_detail.quantity + item_data.quantity,
            quantity_after=inventory_detail.quantity,
            reference_id=order.order_id,
            creator=current_user.username
        )
        db.add(transaction)
        
        db.commit()
        db.refresh(new_item)
        
        return OutboundOrderItemResponse(
            item_id=new_item.item_id,
            material_id=new_item.material_id,
            material_code=new_item.material_code,
            material_name=new_item.material_name,
            material_specification=new_item.material_specification,
            quantity=new_item.quantity,
            unit_price=new_item.unit_price,
            unit=new_item.unit,
            batch_id=new_item.batch_id,
            batch_number=batch.batch_number,
            bin_id=new_item.bin_id,
            bin_name=inventory_detail.bin.bin_name if inventory_detail.bin else "",
            equipment_name=material.equipment_name if material else None
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"添加出库明细失败: {str(e)}")


@outbound_orders_router.put("/{order_id}/items/update/{item_id}", response_model=OutboundOrderItemResponse)
async def update_outbound_order_item(
    order_id: int,
    item_id: int,
    update_data: OutboundOrderItemUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/items/update"))
):
    """修改出库明细中某一条目的器材信息"""
    
    # 查询出库明细
    item = db.get(OutboundOrderItem, item_id)
    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="出库明细不存在")
    
    # 开始事务
    try:
        # 保存更新前的数据
        old_quantity = item.quantity
        old_batch_id = item.batch_id
        old_material_id = item.material_id
        
        # 标记是否有变化
        has_changes = False
        
        # 更新出库明细
        if update_data.batch_id is not None and update_data.batch_id != old_batch_id:
            batch = db.get(InventoryBatch, update_data.batch_id)
            if not batch:
                raise HTTPException(status_code=400, detail="批次不存在")
 
            # 查询新批次对应的库存明细记录
            inventory_detail = db.exec(select(InventoryDetail).where(
                InventoryDetail.batch_id == update_data.batch_id
            )).first()
            
            if not inventory_detail:
                raise HTTPException(status_code=400, detail="该批次没有库存明细记录")
            
            # 获取新批次对应的器材信息
            new_material = db.get(Material, inventory_detail.material_id)
            if not new_material:
                raise HTTPException(status_code=400, detail="器材不存在")
            
            # 更新批次号、器材ID和相关信息
            item.batch_id = update_data.batch_id
            item.material_id = inventory_detail.material_id
            item.material_code = new_material.material_code
            item.material_name = new_material.material_name
            item.material_specification = new_material.material_specification if new_material.material_specification else ""
            item.unit_price = batch.unit_price
            item.bin_id = inventory_detail.bin_id if inventory_detail.bin_id is not None else None
            has_changes = True
            
            print(f"[DEBUG] 批次号变更: 旧批次={old_batch_id}, 新批次={update_data.batch_id}, 旧器材ID={old_material_id}, 新器材ID={inventory_detail.material_id}")
        
        if update_data.quantity is not None:
            # 验证库存数量是否足够
            # 使用当前批次号和器材ID进行验证
            current_batch_id = item.batch_id if update_data.batch_id is None else update_data.batch_id
            current_material_id = item.material_id
            
            inventory_detail = db.exec(select(InventoryDetail).where(
                    InventoryDetail.batch_id == current_batch_id
            )).first()
            
            if not inventory_detail or inventory_detail.quantity + old_quantity < update_data.quantity:
                raise HTTPException(status_code=400, detail="库存不足")
            
            # 保存修改前批次ID对应器材的数量（用于流水变更前数量计算）
            old_batch_inventory_quantity = inventory_detail.quantity
            
            item.quantity = update_data.quantity
            
            # 更新库存明细数量
            inventory_detail.quantity = inventory_detail.quantity + old_quantity - update_data.quantity
            db.add(inventory_detail)
            has_changes = True
            
            print(f"[DEBUG] 库存明细更新: 当前批次={current_batch_id}, 器材ID={current_material_id}, 旧批次库存数量={old_batch_inventory_quantity}, 旧出库数量={old_quantity}, 新出库数量={update_data.quantity}, 更新后库存数量={inventory_detail.quantity}")
        
        db.add(item)
        
        # 更新出库单总数量
        order = db.get(OutboundOrder, order_id)
        order.total_quantity = order.total_quantity - old_quantity + item.quantity
        db.add(order)
        
        # 只有有变化时才更新库存变更流水
        if has_changes:
            print(f"[DEBUG] 开始更新库存变更流水")
            print(f"[DEBUG] 查询条件: reference_id={order.order_id}, reference_type={ReferenceType.OUTBOUND}, batch_id={old_batch_id}, material_id={old_material_id}")
            
            # 使用更新前的批次号和器材ID查询库存变更流水
            transactions = get_inventory_transactions_by_criteria(
                db=db,
                reference_id=order.order_id,
                reference_type=ReferenceType.OUTBOUND,
                batch_id=old_batch_id
            )
            
            print(f"[DEBUG] 查询到的交易记录数量: {len(transactions)}")
            
            if transactions:
                transaction = transactions[0]  # 取第一条记录
                print(f"[DEBUG] 找到交易记录: transaction_id={transaction.transaction_id}, quantity_change={transaction.quantity_change}")
                
                # 检查批次是否发生变化
                if update_data.batch_id is not None and update_data.batch_id != old_batch_id:
                    # 如果批次发生变化，器材也发生变化，需要重新创建库存变更流水
                    print(f"[DEBUG] 批次发生变化，删除旧交易记录并创建新记录")
                    
                    # 删除旧的交易记录
                    delete_inventory_transaction(db=db, transaction_id=transaction.transaction_id)
                    
                    # 查询新批次的库存明细
                    new_inventory_detail = db.exec(select(InventoryDetail).where(
                        InventoryDetail.batch_id == item.batch_id
                    )).first()
                    
                    if new_inventory_detail:
                        # 创建新的库存变更流水
                        new_transaction = create_outbound_transaction(
                            db=db,
                            material_id=item.material_id,
                            batch_id=item.batch_id,
                            quantity_change=-item.quantity,  # 出库数量为负数
                            quantity_before=new_inventory_detail.quantity + item.quantity,  # 出库前数量
                            quantity_after=new_inventory_detail.quantity,  # 出库后数量
                            reference_id=order.order_id,
                            creator=current_user.username
                        )
                        db.add(new_transaction)
                        print(f"[DEBUG] 新交易记录创建完成")
                else:
                    # 批次未变化，只更新数量
                    print(f"[DEBUG] 批次未变化，只更新数量")
                    
                    # 查询当前批次的库存明细
                    current_inventory_detail = db.exec(select(InventoryDetail).where(
                        InventoryDetail.batch_id == item.batch_id
                    )).first()
                    
                    if current_inventory_detail:
                        # 正确的逻辑：数量变化就是修改后的器材出库数量
                        # 流水变更后数量 = 对应器材在库存明细表中的数量
                        # 流水变更前数量 = 流水变更后数量 - 数量变化
                        quantity_change = -item.quantity  # 出库数量为负数
                        quantity_after = current_inventory_detail.quantity  # 流水变更后数量
                        quantity_before = quantity_after - quantity_change  # 流水变更前数量
                        
                        update_data = {
                            "quantity_change": quantity_change,
                            "quantity_before": quantity_before,
                            "quantity_after": quantity_after
                        }
                        print(f"[DEBUG] 准备更新交易记录: 数量变化={quantity_change}, 变更前数量={quantity_before}, 变更后数量={quantity_after}")
                        
                        update_inventory_transaction(
                            db=db,
                            transaction_id=transaction.transaction_id,
                            update_data=update_data
                        )
                        print(f"[DEBUG] 交易记录更新完成")
            else:
                print(f"[DEBUG] 警告: 未找到匹配的交易记录，无法更新库存变更流水")
        else:
            print(f"[DEBUG] 没有变化，跳过库存变更流水更新")
        
        db.commit()
        db.refresh(item)
        
        return OutboundOrderItemResponse(
            item_id=item.item_id,
            material_id=item.material_id,
            material_code=item.material_code,
            material_name=item.material_name,
            material_specification=item.material_specification,
            quantity=item.quantity,
            unit_price=item.unit_price,
            unit=item.unit,
            batch_id=item.batch_id,
            batch_number=item.batch.batch_number if item.batch else "",
            bin_id=item.bin_id,
            bin_name=item.bin.bin_name if item.bin else "",
            equipment_name=item.material.equipment_name if item.material else None
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"修改出库明细失败: {str(e)}")


@outbound_orders_router.delete("/{order_id}/items/delete/{item_id}")
async def delete_outbound_order_item(
    order_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/items/delete"))
):
    """删除出库明细中某一条目的器材信息"""
    
    # 查询出库明细
    item = db.get(OutboundOrderItem, item_id)
    if not item or item.order_id != order_id:
        raise HTTPException(status_code=404, detail="出库明细不存在")
    
    # 开始事务
    try:
        # 查询出库单
        order = db.get(OutboundOrder, order_id)
        
        # 恢复库存明细数量
        inventory_detail = db.exec(select(InventoryDetail).where(
            and_(
                InventoryDetail.batch_id == item.batch_id,
                InventoryDetail.material_id == item.material_id
            )
        )).first()
        
        if inventory_detail:
            inventory_detail.quantity += item.quantity
            db.add(inventory_detail)
        
        # 更新出库单总数量
        order.total_quantity -= item.quantity
        db.add(order)
        
        # 删除库存变更流水（使用工具函数）
        transactions = get_inventory_transactions_by_criteria(
            db=db,
            reference_id=order.order_id,
            reference_type=ReferenceType.OUTBOUND,
            batch_id=item.batch_id,
            material_id=item.material_id
        )
        if transactions:
            transaction = transactions[0]  # 取第一条记录
            delete_inventory_transaction(db=db, transaction_id=transaction.transaction_id)
        
        # 删除出库明细
        db.delete(item)
        
        db.commit()
        
        return {"message": "出库明细删除成功"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除出库明细失败: {str(e)}")


@outbound_orders_router.delete("/{order_id}/items/batch-delete", response_model=BatchDeleteResponse)
async def batch_delete_outbound_order_items(
    order_id: int,
    delete_data: OutboundOrderItemBatchDelete,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/outbound-orders/items/batch-delete"))
):
    """批量删除指定出库单的明细项"""
    
    # 查询出库单
    order = db.get(OutboundOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="出库单不存在")
    
    # 开始事务 - 确保整个批量操作在一个事务中完成
    try:
        deleted_count = 0
        total_quantity_reduction = 0
        
        # 批量处理每个明细项
        for item_id in delete_data.item_ids:
            # 查询出库明细
            item = db.get(OutboundOrderItem, item_id)
            if not item or item.order_id != order_id:
                continue  # 跳过不存在的明细项
            
            # 恢复库存明细数量
            inventory_detail = db.exec(select(InventoryDetail).where(
                and_(
                    InventoryDetail.batch_id == item.batch_id,
                    InventoryDetail.material_id == item.material_id
                )
            )).first()
            
            if inventory_detail:
                inventory_detail.quantity += item.quantity
                db.add(inventory_detail)
            
            # 累加总数量减少
            total_quantity_reduction += item.quantity
            
            # 删除库存变更流水（使用工具函数）
            transactions = get_inventory_transactions_by_criteria(
                db=db,
                reference_id=order.order_id,
                reference_type=ReferenceType.OUTBOUND,
                batch_id=item.batch_id,
                material_id=item.material_id
            )
            if transactions:
                transaction = transactions[0]  # 取第一条记录
                delete_inventory_transaction(db=db, transaction_id=transaction.transaction_id)
            
            # 删除出库明细
            db.delete(item)
            deleted_count += 1
        
        # 更新出库单总数量
        order.total_quantity -= total_quantity_reduction
        db.add(order)
        
        # 在整个批量操作完成后一次性提交事务
        db.commit()
        
        return BatchDeleteResponse(
            success=True,
            deleted_count=deleted_count,
            message=f"成功删除 {deleted_count} 个明细项"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除出库明细失败: {str(e)}")


