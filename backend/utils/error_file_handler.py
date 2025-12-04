"""
通用错误文件处理模块
用于统一处理批量导入过程中的错误文件生成和管理

本模块整合了错误Excel文件生成功能，避免代码重复
"""

from typing import List, Dict, Any, Tuple, Optional
from pydantic import conset
import xlwt
import tempfile
import os
import time
from schemas.common.import_schemas import ImportError, ImportConfig


def generate_error_excel_file(
    error_data_list: List[Dict[str, Any]], 
    error_details: List[Dict[str, str]], 
    config: ImportConfig,
    filename_prefix: Optional[str] = None,
    entity_key: Optional[str] = None
) -> str:
    """生成错误数据Excel文件（与下载模板格式一致）
    
    Args:
        error_data_list: 错误数据列表，每个元素包含原始数据
        error_details: 错误详情列表，每个元素包含{'row_index': '行号', 'error_message': '错误原因'}
        config: 导入配置对象
        filename_prefix: 文件名前缀，默认使用entity_key
        entity_key: 实体类型键，用于创建对应的目录
    
    Returns:
        str: 生成的错误文件路径
    """
    error_workbook = xlwt.Workbook(encoding='utf-8')
    error_sheet = error_workbook.add_sheet(f"{config.entity_name}导入错误")
    
    # 创建样式
    header_style = xlwt.easyxf(
        'font: bold on; align: vertical center, horizontal center; pattern: pattern solid, fore_color gray25;'
    )
    normal_style = xlwt.easyxf('align: vertical center;')
    error_style = xlwt.easyxf('align: vertical center; font: color red;')
    
    # 根据配置动态生成标题行（与模板一致）
    headers = [field.label for field in config.template_fields]
    headers.append('错误原因')  # 添加错误原因列
    
    # 添加标题行
    for col_num, header in enumerate(headers):
        error_sheet.write(0, col_num, header, header_style)
        # 设置列宽
        if col_num < len(config.template_fields):
            # 根据字段类型设置列宽
            field = config.template_fields[col_num]
            if field.type == "string" and hasattr(field, 'max_length') and field.max_length:
                width = min(max(field.max_length + 2, 10), 30)
            else:
                width = 15
            error_sheet.col(col_num).width = 256 * width
        else:
            # 错误原因列设置更宽
            error_sheet.col(col_num).width = 256 * 25
    
    # 添加错误数据
    for row_num, (error_data, error_detail) in enumerate(zip(error_data_list, error_details), 1):
        # 获取该行的错误字段列表
        error_fields = []
        if error_detail.get('error_message'):
            # 从错误详情中提取有错误的字段
            error_message = error_detail.get('error_message', '')
            # 从错误消息中提取字段名：按分号分割，然后按冒号分割提取字段标签
            error_field_labels = []
            for error_part in error_message.split("; "):
                if ":" in error_part:
                    # 新的格式：{entity_name}:{字段标签}:"{值}"在...
                    # 提取第二个冒号前的字段标签
                    parts = error_part.split(":", 2)
                    if len(parts) >= 2:
                        field_label = parts[1].strip()
                        error_field_labels.append(field_label)
            
            # 将字段标签转换为字段键
            error_fields = []
            for field in config.template_fields:
                if field.label in error_field_labels:
                    error_fields.append(field.key)
        
        # 写入原始数据（按模板字段顺序）
        for col_num, field in enumerate(config.template_fields):
            value = error_data.get(field.key, '')
            # 检查该字段是否有错误
            style = error_style if field.key in error_fields else normal_style
            #调试最终颜色
            # print("写入数据，区分颜色",field.key,error_fields,style.font.colour_index);
            error_sheet.write(row_num, col_num, str(value) if value else '', style)
        
        # 写入错误原因（红色显示）
        error_message = error_detail.get('error_message', '未知错误')
        error_sheet.write(row_num, len(config.template_fields), error_message, error_style)
    
    # 保存文件到实体对应的专用目录
    temp_dir = tempfile.gettempdir()
    entity_dir = os.path.join(temp_dir, entity_key or config.entity_key)
    
    # 确保目录存在
    os.makedirs(entity_dir, exist_ok=True)
    
    prefix = filename_prefix or config.entity_key
    error_file_name = f"{prefix}_import_errors_{int(time.time())}.xls"
    error_file_path = os.path.join(entity_dir, error_file_name)
    
    error_workbook.save(error_file_path)
    return error_file_path


def generate_universal_error_file(
    error_rows: List[Tuple[int, tuple, List[ImportError]]], 
    all_errors: List[ImportError], 
    config: ImportConfig,
    entity_key: Optional[str] = None
) -> str:
    """通用错误数据文件生成（XLS格式）- 保持向后兼容"""
    # 转换为新格式
    error_data_list = []
    error_details = []
    
    for row_index, row_data, errors in error_rows:
        # 构建错误数据对象
        error_data = {}
        for i, field in enumerate(config.template_fields):
            error_data[field.key] = row_data[i] if i < len(row_data) else ''
        
        # 合并错误消息
        error_messages = [error.error_message for error in errors if error.row_index == row_index]
        
        error_data_list.append(error_data)
        error_details.append({
            'row_index': str(row_index),
            'error_message': '; '.join(error_messages)
        })
    
    return generate_error_excel_file(error_data_list, error_details, config, entity_key=entity_key)


def process_import_errors_and_generate_file(
    all_errors: List[ImportError],
    original_rows: List[Tuple[int, tuple]],
    config: ImportConfig,
    entity_key: str,
    username: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    处理导入错误并生成错误文件
    
    Args:
        all_errors: 所有错误列表
        original_rows: 原始行数据列表 [(row_index, row_data), ...]
        config: 导入配置
        entity_key: 实体类型键（如'supplier'）
        username: 当前用户名
    
    Returns:
        Tuple[error_file_path, error_file_url]: 错误文件路径和下载URL
    """
    if not all_errors:
        return None, None
    
    # 构建错误行数据
    error_rows = []
    
    # 按行分组错误
    errors_by_row = {}
    for error in all_errors:
        if error.row_index not in errors_by_row:
            errors_by_row[error.row_index] = []
        errors_by_row[error.row_index].append(error)
    
    # 为每个有错误的行构建错误行数据
    for row_index, errors in errors_by_row.items():
        # 找到对应的原始行数据
        orig_row = None
        for orig_row_index, orig_row_data in original_rows:
            if orig_row_index == row_index:
                orig_row = orig_row_data
                break
        
        # 如果找不到原始行，从错误数据中构造
        if orig_row is None:
            # 尝试从第一个错误的raw_data构造行数据
            first_error = errors[0]
            if hasattr(first_error, 'raw_data') and first_error.raw_data:
                orig_row = tuple(str(first_error.raw_data.get(field.key, '')) for field in config.template_fields)
            else:
                # 创建空行数据
                orig_row = tuple('' for _ in config.template_fields)
        
        error_rows.append((row_index, orig_row, errors))
    
    # 生成错误文件
    if error_rows:
        error_file_path = generate_universal_error_file(error_rows, all_errors, config, entity_key=entity_key)
        # 只返回文件名，不返回完整路径
        error_file_name = os.path.basename(error_file_path)
        error_file_url = f"/{entity_key}s/download-error-file?file_name={error_file_name}"
        return error_file_path, error_file_url
    
    return None, None


def add_insert_errors_to_error_list(
    insert_errors: List[Dict[str, Any]],
    all_errors: List[ImportError],
    original_rows: List[Tuple[int, tuple]],
    error_rows: List[Tuple[int, tuple, List[ImportError]]]
) -> None:
    """
    将插入错误添加到错误列表和错误行中
    
    Args:
        insert_errors: 插入错误字典列表
        all_errors: 所有错误列表（会被修改）
        original_rows: 原始行数据列表
        error_rows: 错误行列表（会被修改）
    """
    if not insert_errors:
        return
    
    # 转换为ImportError对象
    import_errors = [ImportError(**error) for error in insert_errors]
    all_errors.extend(import_errors)
    
    # 将插入错误添加到错误行中
    for error in insert_errors:
        # 找到对应的原始行数据
        orig_row = None
        for orig_row_index, orig_row_data in original_rows:
            if orig_row_index == error['row_index']:
                orig_row = orig_row_data
                break
        
        if orig_row is None:
            continue
        
        # 检查是否已经存在该行的错误记录
        existing_error_row = None
        for err_row in error_rows:
            if err_row[0] == error['row_index']:
                existing_error_row = err_row
                break
        
        if existing_error_row:
            # 添加到现有错误行
            existing_error_row[2].append(ImportError(**error))
        else:
            # 创建新的错误行
            error_rows.append((error['row_index'], orig_row, [ImportError(**error)]))


def generate_error_file_from_all_errors(
    all_errors: List[ImportError],
    original_rows: List[Tuple[int, tuple]],
    config: ImportConfig,
    entity_key: Optional[str] = None
) -> Optional[str]:
    """
    从所有错误中强制生成错误文件
    
    Args:
        all_errors: 所有错误列表
        original_rows: 原始行数据列表
        config: 导入配置
        entity_key: 实体类型键，用于创建对应的目录
    
    Returns:
        error_file_path: 错误文件路径，如果没有错误则返回None
    """
    if not all_errors:
        return None
    
    error_rows = []
    
    # 按行分组错误
    errors_by_row = {}
    for error in all_errors:
        if error.row_index not in errors_by_row:
            errors_by_row[error.row_index] = []
        errors_by_row[error.row_index].append(error)
    
    # 为每个有错误的行构建错误行数据
    for row_index, errors in errors_by_row.items():
        # 找到对应的原始行数据
        orig_row = None
        for orig_row_index, orig_row_data in original_rows:
            if orig_row_index == row_index:
                orig_row = orig_row_data
                break
        
        # 如果找不到原始行，从错误数据中构造
        if orig_row is None:
            # 尝试从第一个错误的raw_data构造行数据
            first_error = errors[0]
            if hasattr(first_error, 'raw_data') and first_error.raw_data:
                orig_row = tuple(str(first_error.raw_data.get(field.key, '')) for field in config.template_fields)
            else:
                # 创建空行数据
                orig_row = tuple('' for _ in config.template_fields)
        
        error_rows.append((row_index, orig_row, errors))
    
    # 生成错误文件
    if error_rows:
        return generate_universal_error_file(error_rows, all_errors, config, entity_key=entity_key)
    
    return None