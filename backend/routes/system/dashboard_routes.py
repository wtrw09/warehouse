"""
主页仪表板路由 - 提供系统主页数据统计和监控功能
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func, and_, or_
from typing import Optional
from datetime import  date, timedelta
from database import get_db
from models.account.user import User
from models.material.material import Material
from models.material.inbound_order import InboundOrder
from models.material.outbound_order import OutboundOrder
from models.material.inventory_detail import InventoryDetail
from models.material.inventory_transaction import InventoryTransaction, ChangeType
from models.material.inventory_batch import InventoryBatch
from core.security import get_current_user

dashboard_router = APIRouter(tags=["主页仪表板"])


@dashboard_router.get("/api/dashboard/statistics")
async def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取主页核心统计数据
    
    返回数据：
    - today_inbound: 今日入库统计（单数、器材数量、环比）
    - today_outbound: 今日出库统计（单数、器材数量、环比）
    - total_inventory: 当前库存总量（数量、品类数、总价值）
    - warning_count: 库存预警数量（缺货、库存紧张）
    """
    try:
        # 获取今天和昨天的日期
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # ===== 今日入库统计 =====
        # 今日入库单数量
        today_inbound_count = db.exec(
            select(func.count(InboundOrder.order_id))
            .where(func.date(InboundOrder.create_time) == today)
        ).one()
        
        # 今日入库器材总数量
        today_inbound_quantity = db.exec(
            select(func.sum(InboundOrder.total_quantity))
            .where(func.date(InboundOrder.create_time) == today)
        ).one() or 0
        
        # 昨日入库单数量（用于计算环比）
        yesterday_inbound_count = db.exec(
            select(func.count(InboundOrder.order_id))
            .where(func.date(InboundOrder.create_time) == yesterday)
        ).one()
        
        # 计算入库环比
        if yesterday_inbound_count > 0:
            inbound_change_percent = round(
                ((today_inbound_count - yesterday_inbound_count) / yesterday_inbound_count) * 100, 
                1
            )
        else:
            inbound_change_percent = 100 if today_inbound_count > 0 else 0
        
        # ===== 今日出库统计 =====
        # 今日出库单数量
        today_outbound_count = db.exec(
            select(func.count(OutboundOrder.order_id))
            .where(func.date(OutboundOrder.create_time) == today)
        ).one()
        
        # 今日出库器材总数量
        today_outbound_quantity = db.exec(
            select(func.sum(OutboundOrder.total_quantity))
            .where(func.date(OutboundOrder.create_time) == today)
        ).one() or 0
        
        # 昨日出库单数量（用于计算环比）
        yesterday_outbound_count = db.exec(
            select(func.count(OutboundOrder.order_id))
            .where(func.date(OutboundOrder.create_time) == yesterday)
        ).one()
        
        # 计算出库环比
        if yesterday_outbound_count > 0:
            outbound_change_percent = round(
                ((today_outbound_count - yesterday_outbound_count) / yesterday_outbound_count) * 100,
                1
            )
        else:
            outbound_change_percent = 100 if today_outbound_count > 0 else 0
        
        # ===== 库存总量统计 =====
        # 当前库存总数量
        total_inventory_quantity = db.exec(
            select(func.sum(InventoryDetail.quantity))
        ).one() or 0
        
        # 库存器材品类数量（非删除的器材）
        material_types_count = db.exec(
            select(func.count(Material.id))
            .where(Material.is_delete == False)
        ).one()
        
        # 库存总价值计算（基于批次单价和库存数量）
        total_value_result = db.exec(
            select(func.sum(InventoryDetail.quantity * InventoryBatch.unit_price))
            .select_from(InventoryDetail)
            .join(InventoryBatch, InventoryDetail.batch_id == InventoryBatch.batch_id)
            .where(InventoryBatch.is_delete == False)
            .where(InventoryDetail.quantity > 0)
        ).one()
        
        total_value = float(total_value_result) if total_value_result else 0.0
        
        # ===== 库存预警统计 =====
        # 缺货预警（库存为0的器材）
        out_of_stock_count = db.exec(
            select(func.count(Material.id))
            .select_from(Material)
            .outerjoin(
                InventoryDetail,
                Material.id == InventoryDetail.material_id
            )
            .where(
                and_(
                    Material.is_delete == False,
                    or_(
                        InventoryDetail.material_id.is_(None),
                        select(func.sum(InventoryDetail.quantity))
                        .where(InventoryDetail.material_id == Material.id)
                        .correlate(Material)
                        .scalar_subquery() == 0
                    )
                )
            )
        ).one()
        
        # 库存紧张预警（0 < 当前库存 < 安全库存）
        low_stock_materials = db.exec(
            select(Material.id)
            .where(
                and_(
                    Material.is_delete == False,
                    Material.safety_stock.isnot(None),
                    Material.safety_stock > 0
                )
            )
        ).all()
        
        low_stock_count = 0
        for material_id in low_stock_materials:
            current_stock = db.exec(
                select(func.sum(InventoryDetail.quantity))
                .where(InventoryDetail.material_id == material_id)
            ).one() or 0
            
            material = db.exec(
                select(Material.safety_stock)
                .where(Material.id == material_id)
            ).one()
            
            if current_stock > 0 and current_stock < material:
                low_stock_count += 1
        
        total_warning_count = out_of_stock_count + low_stock_count
        
        # 构建返回数据
        return {
            "today_inbound": {
                "order_count": today_inbound_count,
                "material_count": int(today_inbound_quantity),
                "change_percent": inbound_change_percent
            },
            "today_outbound": {
                "order_count": today_outbound_count,
                "material_count": int(today_outbound_quantity),
                "change_percent": outbound_change_percent
            },
            "total_inventory": {
                "quantity": int(total_inventory_quantity),
                "material_types": material_types_count,
                "total_value": total_value
            },
            "warning_count": {
                "total": total_warning_count,
                "out_of_stock": out_of_stock_count,
                "low_stock": low_stock_count
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取主页统计数据失败: {str(e)}")


@dashboard_router.get("/api/dashboard/monthly-trend")
async def get_monthly_trend(
    year: Optional[int] = None,
    month: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定月份的出入库趋势数据
    
    参数：
    - year: 年份，不传则为当前年份
    - month: 月份（1-12），不传则为当前月份
    
    返回数据：
    - daily_data: 每日出入库数据列表
    - total_inbound: 本月入库总数量
    - total_outbound: 本月出库总数量
    - query_year: 查询的年份
    - query_month: 查询的月份
    """
    try:
        # 获取当前日期
        today = date.today()
        
        # 如果未指定年月，默认使用当前年月
        query_year = year if year is not None else today.year
        query_month = month if month is not None else today.month
        
        # 验证月份范围
        if not 1 <= query_month <= 12:
            raise HTTPException(status_code=400, detail="月份必须在1-12之间")
        
        # 获取指定月份的第一天和最后一天
        first_day = date(query_year, query_month, 1)
        if query_month == 12:
            last_day = date(query_year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(query_year, query_month + 1, 1) - timedelta(days=1)
        
        # 如果是当前月份，只统计到今天
        is_current_month = (query_year == today.year and query_month == today.month)
        end_day = min(last_day, today) if is_current_month else last_day
        
        # 初始化每日数据
        daily_data = []
        current_day = first_day
        
        total_inbound = 0
        total_outbound = 0
        
        while current_day <= end_day:
            # 查询当天入库数量
            day_inbound = db.exec(
                select(func.sum(InboundOrder.total_quantity))
                .where(func.date(InboundOrder.create_time) == current_day)
            ).one() or 0
            
            # 查询当天出库数量
            day_outbound = db.exec(
                select(func.sum(OutboundOrder.total_quantity))
                .where(func.date(OutboundOrder.create_time) == current_day)
            ).one() or 0
            
            daily_data.append({
                "date": current_day.strftime("%Y-%m-%d"),
                "inbound": int(day_inbound),
                "outbound": int(day_outbound)
            })
            
            total_inbound += int(day_inbound)
            total_outbound += int(day_outbound)
            
            current_day += timedelta(days=1)
        
        
        return {
            "daily_data": daily_data,
            "total_inbound": total_inbound,
            "total_outbound": total_outbound,
            "query_year": query_year,
            "query_month": query_month,
            "is_current_month": is_current_month
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取当月趋势数据失败: {str(e)}")


@dashboard_router.get("/api/dashboard/recent-transactions")
async def get_recent_transactions(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取最近的出入库记录
    
    参数：
    - limit: 返回记录数量，默认10条
    
    返回数据：
    - transactions: 最近的流水记录列表
    """
    try:
        # 查询最近的库存变更流水
        statement = (
            select(
                InventoryTransaction.transaction_id,
                InventoryTransaction.transaction_time,
                InventoryTransaction.change_type,
                InventoryTransaction.quantity_change,
                InventoryTransaction.reference_id,
                InventoryTransaction.creator,
                Material.material_code,
                Material.material_name,
                Material.material_specification
            )
            .join(Material, InventoryTransaction.material_id == Material.id)
            .order_by(InventoryTransaction.transaction_time.desc())
            .limit(limit)
        )
        
        results = db.exec(statement).all()
        
        transactions = []
        for row in results:
            # 根据变更类型确定单据号前缀
            if row.change_type == ChangeType.IN:
                # 查询入库单号
                inbound_order = db.exec(
                    select(InboundOrder.order_number)
                    .where(InboundOrder.order_id == row.reference_id)
                ).first()
                reference_number = inbound_order if inbound_order else f"RK-{row.reference_id}"
            elif row.change_type == ChangeType.OUT:
                # 查询出库单号
                outbound_order = db.exec(
                    select(OutboundOrder.order_number)
                    .where(OutboundOrder.order_id == row.reference_id)
                ).first()
                reference_number = outbound_order if outbound_order else f"CK-{row.reference_id}"
            else:
                reference_number = f"TZ-{row.reference_id}"
            
            transactions.append({
                "transaction_id": row.transaction_id,
                "transaction_time": row.transaction_time.strftime("%Y-%m-%d %H:%M:%S"),
                "change_type": row.change_type.value,
                "material_code": row.material_code,
                "material_name": row.material_name,
                "material_specification": row.material_specification or "",
                "quantity_change": row.quantity_change,
                "reference_number": reference_number,
                "creator": row.creator
            })
        
        return {"transactions": transactions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近记录失败: {str(e)}")


@dashboard_router.get("/api/dashboard/inventory-warnings")
async def get_inventory_warnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取库存预警信息
    
    返回数据：
    - out_of_stock: 缺货预警列表（库存为0）
    - low_stock: 库存紧张预警列表（0 < 库存 < 安全库存）
    - summary: 预警汇总统计
    """
    try:
        # ===== 缺货预警查询 =====
        out_of_stock_materials = db.exec(
            select(Material)
            .where(Material.is_delete == False)
        ).all()
        
        out_of_stock = []
        for material in out_of_stock_materials:
            # 计算当前库存
            current_stock = db.exec(
                select(func.sum(InventoryDetail.quantity))
                .where(InventoryDetail.material_id == material.id)
            ).one() or 0
            
            if current_stock == 0:
                shortage = material.safety_stock or 0  # 缺货时，缺货数量等于安全库存
                out_of_stock.append({
                    "material_id": material.id,
                    "material_code": material.material_code,
                    "material_name": material.material_name,
                    "material_specification": material.material_specification or "",
                    "current_stock": 0,
                    "safety_stock": material.safety_stock or 0,
                    "shortage": shortage,
                    "major_name": material.major_name or "",
                    "equipment_name": material.equipment_name or ""
                })
        
        # ===== 库存紧张预警查询 =====
        low_stock_materials = db.exec(
            select(Material)
            .where(
                and_(
                    Material.is_delete == False,
                    Material.safety_stock.isnot(None),
                    Material.safety_stock > 0
                )
            )
        ).all()
        
        low_stock = []
        for material in low_stock_materials:
            # 计算当前库存
            current_stock = db.exec(
                select(func.sum(InventoryDetail.quantity))
                .where(InventoryDetail.material_id == material.id)
            ).one() or 0
            
            # 判断是否库存紧张（0 < 当前库存 < 安全库存）
            if 0 < current_stock < material.safety_stock:
                shortage = material.safety_stock - current_stock
                low_stock.append({
                    "material_id": material.id,
                    "material_code": material.material_code,
                    "material_name": material.material_name,
                    "material_specification": material.material_specification or "",
                    "current_stock": int(current_stock),
                    "safety_stock": material.safety_stock,
                    "shortage": shortage,
                    "major_name": material.major_name or "",
                    "equipment_name": material.equipment_name or ""
                })
        
        # 按缺口数量倒序排序（缺口越大越靠前）
        low_stock.sort(key=lambda x: x["shortage"], reverse=True)
        
        return {
            "out_of_stock": out_of_stock,
            "low_stock": low_stock,
            "summary": {
                "out_of_stock_count": len(out_of_stock),
                "low_stock_count": len(low_stock),
                "total_warning_count": len(out_of_stock) + len(low_stock)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取库存预警信息失败: {str(e)}")

#获取当年每个月的数据及库存变化趋势
