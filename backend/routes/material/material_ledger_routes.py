"""
器材分类账页生成路由
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Security
from sqlmodel import Session, select
from typing import List, Dict, Any
import tempfile
import os
from pathlib import Path

from database import get_db
from core.security import get_current_active_user, get_required_scopes_for_route
from schemas.account.user import UserResponse
from models.material.inbound_order import InboundOrder
from models.material.inbound_order_item import InboundOrderItem
from models.material.material import Material
from models.material.inventory_batch import InventoryBatch
from utils.pdf_generator import generate_material_ledger_pdf

material_ledger_router = APIRouter(prefix="/material-ledger", tags=["器材分类账页"])


@material_ledger_router.get("/pdf/{order_number}")
async def generate_material_ledger_pdf_by_order_number(
    order_number: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/material-ledger/pdf"))
):
    """
    根据入库单号生成器材分类账页PDF
    
    Args:
        order_number: 入库单号
        session: 数据库会话
        
    Returns:
        PDF文件流
    """
    try:
        # 查询入库单信息
        statement = select(InboundOrder).where(InboundOrder.order_number == order_number)
        inbound_order = db.exec(statement).first()
        
        if not inbound_order:
            raise HTTPException(status_code=404, detail=f"入库单 {order_number} 不存在")
        
        # 查询入库单明细
        statement = select(InboundOrderItem).where(InboundOrderItem.order_id == inbound_order.order_id)
        items = db.exec(statement).all()
        
        if not items:
            raise HTTPException(status_code=404, detail=f"入库单 {order_number} 没有明细数据")
        
        # 查询创建人的部门信息
        from models.account.user import User
        creator_user = db.exec(select(User).where(User.username == inbound_order.creator)).first()
        creator_department = creator_user.department if creator_user else ""
        
        # 构建器材分类账页数据
        order_data = {
            "order_number": inbound_order.order_number,
            "supplier": inbound_order.supplier_name,  # 使用supplier_name字段
            "inbound_date": inbound_order.create_time.strftime("%Y-%m-%d") if inbound_order.create_time else "",
            "contract_number": inbound_order.contract_reference or "",  # 使用contract_reference字段
            "transfer_number": inbound_order.requisition_reference or "",  # 使用requisition_reference字段
            "creator": creator_department  # 使用创建人所在的单位（部门）
        }
        
        # 构建器材明细数据
        material_items = []
        for item in items:
            # 查询器材信息
            material = db.get(Material, item.material_id)
            if not material:
                continue
            
            # 查询批次信息
            batch = db.get(InventoryBatch, item.batch_id) if item.batch_id else None
            
            material_item = {
                "material_code": material.material_code,
                "material_name": material.material_name,
                "specification": material.material_specification or "",
                "unit": item.unit,  # 使用InboundOrderItem中的unit字段
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "batch_number": batch.batch_number if batch else "",
                "major": material.major_name or "",  # 使用Material中的major_name字段
                "equipment_name": material.equipment_name or "",
                "equipment_model": ""  # Material模型中没有equipment_model字段，设为空字符串
            }
            material_items.append(material_item)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = temp_file.name
        
        # 生成PDF
        success = generate_material_ledger_pdf(
            order_data=order_data,
            items_data=material_items,
            creator_department=order_data["creator"],  # 使用order_data中的部门信息作为保管单位
            output_path=temp_path
        )
        
        if not success:
            os.unlink(temp_path)
            raise HTTPException(status_code=500, detail="PDF生成失败")
        
        # 读取PDF文件内容
        with open(temp_path, "rb") as f:
            pdf_content = f.read()
        
        # 删除临时文件
        os.unlink(temp_path)
        
        # 返回PDF文件流
        from fastapi.responses import Response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=material_ledger_{order_number}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 清理临时文件
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"生成器材分类账页PDF失败: {str(e)}")
