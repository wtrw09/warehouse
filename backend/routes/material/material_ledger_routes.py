"""
器材分类账页生成路由
"""
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.responses import Response, StreamingResponse
from sqlmodel import Session, select
from typing import List, Any
import tempfile
import os
import json
import uuid
import time
import shutil
import asyncio
from datetime import datetime
from urllib.parse import quote
from pydantic import BaseModel, Field

from database import get_db, get_engine
from core.security import get_current_active_user, get_required_scopes_for_route
from schemas.account.user import UserResponse
from core.logging_config import get_logger

logger = get_logger(__name__)
from models.material.inbound_order import InboundOrder
from models.material.inbound_order_item import InboundOrderItem
from models.material.material import Material
from models.material.inventory_batch import InventoryBatch
from models.base.major import Major
from models.account.user import User
from utils.pdf_generator import generate_material_ledger_pdf

material_ledger_router = APIRouter(prefix="/material-ledger", tags=["器材分类账页"])

class BatchLedgerRequest(BaseModel):
    """批量生成请求模型"""
    order_numbers: List[str] = Field(..., max_length=100, description="入库单号列表，最多100个")

# 常量
SSE_HEARTBEAT_INTERVAL = 15  # SSE心跳间隔（秒）
TEMP_FILE_MAX_AGE = 30       # 临时文件最大保留时间（分钟）
def _get_temp_base_dir() -> str:
    """获取临时文件基础目录"""
    base_dir = os.path.join(tempfile.gettempdir(), "material_ledger")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _cleanup_old_temp_dirs():
    """清理过期的临时目录"""
    base_dir = _get_temp_base_dir()
    now = time.time()
    for entry in os.listdir(base_dir):
        dir_path = os.path.join(base_dir, entry)
        if os.path.isdir(dir_path):
            try:
                dir_age = now - os.path.getmtime(dir_path)
                if dir_age > TEMP_FILE_MAX_AGE * 60:
                    shutil.rmtree(dir_path, ignore_errors=True)
            except Exception:
                continue


def _build_single_ledger_data(db: Session, order_number: str) -> tuple:
    """
    构建单个器材分类账页的数据
    
    Returns:
        (order_data, material_items, creator_department)
    """
    statement = select(InboundOrder).where(InboundOrder.order_number == order_number)
    inbound_order = db.exec(statement).first()
    
    if not inbound_order:
        raise HTTPException(status_code=404, detail=f"入库单 {order_number} 不存在")
    
    statement = select(InboundOrderItem).where(InboundOrderItem.order_id == inbound_order.order_id)
    items = db.exec(statement).all()
    
    if not items:
        raise HTTPException(status_code=404, detail=f"入库单 {order_number} 没有明细数据")
    
    creator_user = db.exec(select(User).where(User.username == inbound_order.creator)).first()
    creator_department = creator_user.department if creator_user else ""
    
    order_data = {
        "order_number": inbound_order.order_number,
        "supplier": inbound_order.supplier_name,
        "inbound_date": inbound_order.create_time.strftime("%Y-%m-%d") if inbound_order.create_time else "",
        "contract_number": inbound_order.contract_reference or "",
        "transfer_number": inbound_order.requisition_reference or "",
        "creator": creator_department
    }
    
    material_items = []
    for item in items:
        material = db.get(Material, item.material_id)
        if not material:
            continue
        
        batch = db.get(InventoryBatch, item.batch_id) if item.batch_id else None
        
        major_name = ""
        if material.major_id:
            major = db.get(Major, material.major_id)
            if major:
                major_name = major.major_name
        
        material_item = {
            "material_code": material.material_code,
            "material_name": material.material_name,
            "specification": material.material_specification or "",
            "unit": item.unit,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "batch_number": batch.batch_number if batch else "",
            "major": major_name,
            "equipment_name": material.equipment_name or "",
            "equipment_model": ""
        }
        material_items.append(material_item)
    
    return order_data, material_items, creator_department


def _generate_single_ledger_pdf_to_path(order_number: str, output_path: str) -> None:
    """
    生成单个器材分类账页PDF并保存到指定路径
    在线程池中被调用，需自行创建数据库会话
    """
    engine = get_engine()
    with Session(engine) as db:
        order_data, material_items, creator_department = _build_single_ledger_data(db, order_number)
    
    success = generate_material_ledger_pdf(
        order_data=order_data,
        items_data=material_items,
        creator_department=creator_department,
        output_path=output_path
    )
    
    if not success:
        raise RuntimeError(f"PDF生成失败: {order_number}")


@material_ledger_router.get("/download/{order_number}")
async def generate_material_ledger_pdf_by_order_number(
    order_number: str,
    db: Session = Depends(get_db),
):
    """
    根据入库单号生成器材分类账页PDF
    注意：此路由无 Authorization 校验，供 IDM 等下载工具直接下载。
    认证由前端页面会话保护，生成的 PDF 即时生成即时删除。
    """
    try:
        order_data, material_items, creator_department = _build_single_ledger_data(db, order_number)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_path = temp_file.name
        
        success = generate_material_ledger_pdf(
            order_data=order_data,
            items_data=material_items,
            creator_department=creator_department,
            output_path=temp_path
        )
        
        if not success:
            os.unlink(temp_path)
            raise HTTPException(status_code=500, detail="PDF生成失败")
        
        with open(temp_path, "rb") as f:
            pdf_content = f.read()
        
        os.unlink(temp_path)
        
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
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise HTTPException(status_code=500, detail=f"生成器材分类账页PDF失败: {str(e)}")


@material_ledger_router.post("/batch-progress")
async def batch_generate_material_ledger(
    request: BatchLedgerRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/material-ledger/download"))
):
    """
    批量生成器材分类账页PDF（SSE流式推送进度）
    
    请求体: {"order_numbers": ["ORD001", "ORD002", ...]}
    返回: text/event-stream 格式的SSE事件流
    """
    order_numbers = request.order_numbers
    if not order_numbers:
        raise HTTPException(status_code=400, detail="请提供要生成的入库单号列表")
    
    # 验证所有入库单是否存在
    for order_number in order_numbers:
        statement = select(InboundOrder).where(InboundOrder.order_number == order_number)
        if not db.exec(statement).first():
            raise HTTPException(status_code=404, detail=f"入库单 {order_number} 不存在")
    
    total = len(order_numbers)
    task_id = str(uuid.uuid4())
    task_dir = os.path.join(_get_temp_base_dir(), task_id)
    os.makedirs(task_dir, exist_ok=True)
    
    # 清理过期临时文件
    _cleanup_old_temp_dirs()
    
    async def event_generator():
        success_count = 0
        failed_count = 0
        last_heartbeat = time.time()
        batch_start_time = time.time()
        file_start_time = time.time()
        loop = asyncio.get_event_loop()
        
        for i, order_number in enumerate(order_numbers):
            current = i + 1
            
            yield f"event: progress\ndata: {json.dumps({'type': 'generating', 'order_number': order_number, 'current': current, 'total': total, 'elapsed_seconds': round(time.time() - batch_start_time, 1)})}\n\n"
            
            try:
                output_path = os.path.join(task_dir, f"{order_number}.pdf")
                await loop.run_in_executor(
                    None, _generate_single_ledger_pdf_to_path, order_number, output_path
                )
                
                file_elapsed = round(time.time() - file_start_time, 1)
                batch_elapsed = round(time.time() - batch_start_time, 1)
                print(f"[SSE] 账页 {order_number}({current}/{total}) 耗时 {file_elapsed}s，总耗时 {batch_elapsed}s")
                
                # 直接使用 temp-download URL，无需 token 中转
                # temp-download 路由无 Authorization 校验，IDM 可直连下载
                download_url = f"/material-ledger/temp-download/{task_id}/{order_number}.pdf"
                yield f"event: progress\ndata: {json.dumps({'type': 'completed', 'order_number': order_number, 'current': current, 'total': total, 'download_url': download_url, 'file_elapsed': file_elapsed, 'elapsed_seconds': batch_elapsed})}\n\n"
                success_count += 1
            except Exception as e:
                error_msg = str(e)[:200]
                print(f"[SSE] 账页 {order_number} 生成失败: {error_msg}")
                yield f"event: progress\ndata: {json.dumps({'type': 'failed', 'order_number': order_number, 'current': current, 'total': total, 'error': error_msg, 'elapsed_seconds': round(time.time() - batch_start_time, 1)})}\n\n"
                failed_count += 1
            
            file_start_time = time.time()
            
            # 每处理3个账页发送一次heartbeat
            if current % 3 == 0 or current == total:
                current_time = time.time()
                if current_time - last_heartbeat >= SSE_HEARTBEAT_INTERVAL or current == total:
                    yield f"event: heartbeat\ndata: {json.dumps({'time': datetime.now().isoformat()})}\n\n"
                    last_heartbeat = current_time
        
        total_elapsed = round(time.time() - batch_start_time, 1)
        print(f"[SSE] ===== 批量完成: {total}个账页, 成功{success_count}, 失败{failed_count}, 总耗时{total_elapsed}s =====")
        yield f"event: complete\ndata: {json.dumps({'total': total, 'success': success_count, 'failed': failed_count, 'total_elapsed': total_elapsed})}\n\n"
        
        # 安排延时清理临时目录（给前端留出下载时间）
        loop.call_later(60, shutil.rmtree, task_dir, True)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")



@material_ledger_router.get("/temp-download/{task_id}/{filename}")
async def download_temp_pdf(
    task_id: str,
    filename: str,
):
    """
    下载临时目录中的PDF文件
    注意：此路由无 Authorization 校验，供 IDM 等下载工具直接下载。
    认证由前端页面会话保护，临时文件 30 分钟自动清理。
    """
    # 安全验证：防止路径遍历攻击
    safe_filename = os.path.basename(filename)
    if safe_filename != filename:
        raise HTTPException(status_code=400, detail="非法文件名")
    if not safe_filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只允许下载PDF文件")
    
    # 验证解析后的路径在预期的临时目录内
    expected_base = os.path.realpath(os.path.join(_get_temp_base_dir(), task_id))
    file_path = os.path.join(expected_base, safe_filename)
    resolved_path = os.path.realpath(file_path)
    if not resolved_path.startswith(expected_base + os.sep):
        raise HTTPException(status_code=403, detail="非法路径访问")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在或已过期")
    
    try:
        with open(file_path, "rb") as f:
            pdf_content = f.read()
        
        download_filename = f"器材分类账页{filename.replace('.pdf', '')}.pdf"
        encoded_filename = quote(download_filename, encoding='utf-8')
        
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )
    except Exception as e:
        logger.error(f"读取PDF文件失败: {file_path}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"读取PDF文件失败: {str(e)}")
