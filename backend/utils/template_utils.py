"""
通用模板下载工具
提供统一的Excel模板生成和下载功能（XLS格式）
"""

import os
import tempfile
import time
from typing import Optional
import xlwt
from fastapi import HTTPException
from fastapi.responses import FileResponse

from config.import_config import get_import_config
from schemas.common.import_schemas import ImportConfig


async def download_import_template(
    entity_type: str,
    filename_prefix: Optional[str] = None,
    display_filename: Optional[str] = None
) -> FileResponse:
    """
    通用的导入模板下载功能（XLS格式）
    
    Args:
        entity_type: 实体类型（如 'supplier', 'customer', 'warehouse', 'bin'）
        filename_prefix: 文件名前缀，默认使用 entity_type
        display_filename: 下载时显示的文件名，默认为 "{实体名称}导入模板.xls"
    
    Returns:
        FileResponse: Excel模板文件响应
        
    Raises:
        HTTPException: 当实体类型不支持时抛出400错误
    """
    # 获取导入配置
    config = get_import_config(entity_type)
    if not config:
        raise HTTPException(status_code=400, detail=f"不支持的实体类型: {entity_type}")
    
    # 生成模板文件
    template_file_path = generate_template_file(config, filename_prefix or entity_type)
    
    # 确定显示文件名
    if not display_filename:
        display_filename = f"{config.entity_name}导入模板.xls"
    
    return FileResponse(
        path=template_file_path,
        filename=display_filename,
        media_type="application/vnd.ms-excel"
    )


def generate_template_file(config: ImportConfig, filename_prefix: str) -> str:
    """
    根据配置生成Excel模板文件（XLS格式）
    
    Args:
        config: 导入配置对象
        filename_prefix: 文件名前缀
        
    Returns:
        str: 生成的模板文件路径
    """
    # 创建模板工作簿
    template_workbook = xlwt.Workbook(encoding='utf-8')
    
    # 创建工作表
    template_sheet = template_workbook.add_sheet(f"{config.entity_name}导入模板")
    
    # 创建样式
    header_style = xlwt.easyxf(
        'font: bold on; align: vertical center, horizontal center; pattern: pattern solid, fore_color gray25;'
    )
    normal_style = xlwt.easyxf('align: vertical center;')
    
    # 添加标题行
    for col_num, field in enumerate(config.template_fields):
        template_sheet.write(0, col_num, field.label, header_style)
        
        # 设置列宽
        if field.type == "string" and field.max_length:
            width = min(max(len(field.label), field.max_length // 2), 50)
        else:
            width = max(len(field.label), 15)
        template_sheet.col(col_num).width = 256 * width  # xlwt中1个字符宽度约等于256
    
    # 添加示例数据行
    for col_num, field in enumerate(config.template_fields):
        example_value = field.example or ''
        template_sheet.write(1, col_num, example_value, normal_style)
    
    # 保存到临时文件
    temp_dir = tempfile.gettempdir()
    template_file_name = f"{filename_prefix}_import_template_{int(time.time())}.xls"
    template_file_path = os.path.join(temp_dir, template_file_name)
    
    template_workbook.save(template_file_path)
    
    return template_file_path


def create_template_route_handler(entity_type: str, required_scope: str):
    """
    创建标准的模板下载路由处理函数
    
    Args:
        entity_type: 实体类型
        required_scope: 所需权限范围
        
    Returns:
        callable: 可以直接用作路由处理函数的异步函数
    """
    from core.security import get_current_active_user, get_required_scopes_for_route
    from schemas.account.user import UserResponse
    from fastapi import Security
    
    async def template_handler(
        current_user: UserResponse = Security(
            get_current_active_user, 
            scopes=get_required_scopes_for_route(required_scope)
        )
    ):
        """下载导入模板文件"""
        return await download_import_template(entity_type)
    
    # 设置函数名和文档字符串
    config = get_import_config(entity_type)
    if config:
        template_handler.__name__ = f"download_{entity_type}_import_template"
        template_handler.__doc__ = f"下载{config.entity_name}导入模板文件（需要相应权限）"
    
    return template_handler