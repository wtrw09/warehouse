import tempfile
import os
import time
from contextlib import contextmanager
from typing import List, Dict, Any, Set, Tuple
from sqlmodel import Session, select
import xlwt

from schemas.common.import_schemas import ImportConfig, ImportError
from models.base.supplier import Supplier


@contextmanager
def batch_import_transaction(db: Session):
    """批量导入事务管理"""
    try:
        yield
        db.commit()
    except Exception as e:
        db.rollback()
        raise e


def build_entity_data(row: tuple, config: ImportConfig) -> Dict[str, Any]:
    """根据配置动态构建实体数据对象"""
    entity_data = {}
    for i, field in enumerate(config.template_fields):
        raw_value = row[i] if i < len(row) else ''
        
        # 根据字段类型进行类型转换
        if field.type == 'integer':
            try:
                entity_data[field.key] = int(raw_value) if raw_value and str(raw_value).strip() else None
            except (ValueError, TypeError):
                entity_data[field.key] = None
        else:
            # 字符串类型，去除空格
            entity_data[field.key] = str(raw_value).strip() if raw_value else ''
    
    return entity_data


async def get_existing_values(config: ImportConfig, fields: List[str], db: Session) -> Dict[str, Set[str]]:
    """根据配置获取数据库中指定字段的现有值"""
    existing_values = {}
    
    # 根据实体类型动态导入对应的模型
    if config.entity_key == 'supplier':
        from models.base.supplier import Supplier
        entities = db.exec(
            select(Supplier).where(Supplier.is_delete != True)
        ).all()
        
        for field in fields:
            if hasattr(Supplier, field):
                existing_values[field] = {
                    getattr(entity, field).strip().lower() 
                    for entity in entities 
                    if getattr(entity, field)
                }
    
    elif config.entity_key == 'customer':
        from models.base.customer import Customer
        entities = db.exec(
            select(Customer).where(Customer.is_delete != True)
        ).all()
        
        for field in fields:
            if hasattr(Customer, field):
                existing_values[field] = {
                    getattr(entity, field).strip().lower() 
                    for entity in entities 
                    if getattr(entity, field)
                }
    elif config.entity_key == 'warehouse':
        from models.base.warehouse import Warehouse
        entities = db.exec(
            select(Warehouse).where(Warehouse.is_delete != True)
        ).all()
        
        for field in fields:
            if hasattr(Warehouse, field):
                existing_values[field] = {
                    getattr(entity, field).strip().lower() 
                    for entity in entities 
                    if getattr(entity, field)
                }
    
    return existing_values


def get_field_label(field_key: str, config: ImportConfig) -> str:
    """根据字段键获取显示标签"""
    for field in config.template_fields:
        if field.key == field_key:
            return field.label
    return field_key


async def validate_entity_data(
    entity_data: List[Dict[str, Any]], 
    config: ImportConfig, 
    db: Session
) -> List[ImportError]:
    """
    通用验证实体数据，包括两步重复性检查：
    1. 检查输入数据内部的重复
    2. 检查与数据库现有数据的重复
    """
    errors = []
    entity_name = config.entity_name
    unique_fields = config.unique_fields or ['name']
    
    # 第一步：检查输入数据内部的重复
    for unique_field in unique_fields:
        field_values = [data.get(unique_field, '').strip() for data in entity_data]
        value_count = {}
        
        for i, value in enumerate(field_values):
            if value:  # 非空值才检查重复
                if value in value_count:
                    value_count[value].append(i)
                else:
                    value_count[value] = [i]
        
        # 找出重复的值
        for value, indices in value_count.items():
            if len(indices) > 1:
                for index in indices:
                    errors.append(ImportError(
                        row_index=index + 2,  # Excel行号（从第2行开始）
                        field=unique_field,
                        error_message=f'{entity_name}:{get_field_label(unique_field, config)}:"{value}"在输入数据中重复出现',
                        raw_data=entity_data[index]
                    ))
    
    # 第二步：检查与数据库现有数据的重复
    existing_values = await get_existing_values(config, unique_fields, db)
    
    for i, data in enumerate(entity_data):
        row_index = i + 2
        
        # 验证每个字段
        for rule in config.validation_rules:
            field_value = data.get(rule.field, '').strip() if isinstance(data.get(rule.field), str) else data.get(rule.field)
            
            # 基本验证
            if rule.type == 'required' and not field_value:
                errors.append(ImportError(
                    row_index=row_index,
                    field=rule.field,
                    error_message=rule.message,
                    raw_data=data
                ))
                continue
                
            if rule.type == 'max_length' and field_value and rule.value and len(str(field_value)) > rule.value:
                errors.append(ImportError(
                    row_index=row_index,
                    field=rule.field,
                    error_message=rule.message,
                    raw_data=data
                ))
                continue
            
            # 整数范围验证
            if rule.type == 'range' and field_value:
                # 检查是否为空值（None、空字符串、0等）
                if not field_value or str(field_value).strip() == '':
                    # 空值跳过验证（可选字段允许为空）
                    continue
                
                try:
                    int_value = int(field_value)
                    if int_value < 1 or int_value > (rule.value or 5):
                        errors.append(ImportError(
                            row_index=row_index,
                            field=rule.field,
                            error_message=rule.message,
                            raw_data=data
                        ))
                        continue
                except (ValueError, TypeError):
                    # 非整数值报错
                    errors.append(ImportError(
                        row_index=row_index,
                        field=rule.field,
                        error_message=f"{entity_name}:{get_field_label(rule.field, config)}:必须是整数",
                        raw_data=data
                    ))
                    continue
            # 检查是否与数据库现有数据重复（跳过已经在输入数据中重复的）
            if (rule.type == 'unique' and field_value and 
                field_value.lower() in existing_values.get(rule.field, set())):
                # 检查这个值是否已经在输入数据重复错误中报告过
                already_reported = any(
                    error.row_index == row_index and 
                    error.field == rule.field and 
                    '输入数据中重复' in error.error_message
                    for error in errors
                )
                
                if not already_reported:
                    errors.append(ImportError(
                        row_index=row_index,
                        field=rule.field,
                        error_message=f'{entity_name}:{get_field_label(rule.field, config)}:"{field_value}"在系统中已存在',
                        raw_data=data
                    ))
    
    return errors


async def batch_insert_entities(
    valid_data: List[Tuple[int, Dict[str, Any]]], 
    config: ImportConfig, 
    db: Session, 
    creator: str
) -> int:
    """根据配置批量插入实体数据"""
    success_count = 0
    entity_key = config.entity_key
    
    # 根据实体类型动态导入对应的模型
    if entity_key == 'supplier':
        from models.base.supplier import Supplier
        for row_index, entity_data in valid_data:
            db_entity = Supplier(**entity_data, creator=creator)
            db.add(db_entity)
            success_count += 1
    
    elif entity_key == 'customer':
        from models.base.customer import Customer
        for row_index, entity_data in valid_data:
            db_entity = Customer(**entity_data, creator=creator)
            db.add(db_entity)
            success_count += 1
    
    elif entity_key == 'warehouse':
        from models.base.warehouse import Warehouse
        for row_index, entity_data in valid_data:
            db_entity = Warehouse(**entity_data, creator=creator)
            db.add(db_entity)
            success_count += 1
    
    return success_count


def generate_error_excel_file(
    error_data_list: List[Dict[str, Any]], 
    error_details: List[Dict[str, str]], 
    config: ImportConfig,
    filename_prefix: str | None = None
) -> str:
    """生成错误数据Excel文件（与下载模板格式一致）
    
    Args:
        error_data_list: 错误数据列表，每个元素包含原始数据
        error_details: 错误详情列表，每个元素包含{'row_index': '行号', 'error_message': '错误原因'}
        config: 导入配置对象
        filename_prefix: 文件名前缀，默认使用entity_key
    
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
            if field.type == "string" and field.max_length:
                width = min(max(field.max_length + 2, 10), 30)
            else:
                width = 15
            error_sheet.col(col_num).width = 256 * width
        else:
            # 错误原因列设置更宽
            error_sheet.col(col_num).width = 256 * 25
    
    # 添加错误数据
    for row_num, (error_data, error_detail) in enumerate(zip(error_data_list, error_details), 1):
        # 写入原始数据（按模板字段顺序）
        for col_num, field in enumerate(config.template_fields):
            value = error_data.get(field.key, '')
            error_sheet.write(row_num, col_num, str(value) if value else '', normal_style)
        
        # 写入错误原因（红色显示）
        error_message = error_detail.get('error_message', '未知错误')
        error_sheet.write(row_num, len(config.template_fields), error_message, error_style)
    
    # 保存文件
    temp_dir = tempfile.gettempdir()
    prefix = filename_prefix or config.entity_key
    error_file_name = f"{prefix}_import_errors_{int(time.time())}.xls"
    error_file_path = os.path.join(temp_dir, error_file_name)
    
    error_workbook.save(error_file_path)
    return error_file_path


def generate_universal_error_file(
    error_rows: List[Tuple[int, tuple, List[ImportError]]], 
    all_errors: List[ImportError], 
    config: ImportConfig
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
    
    return generate_error_excel_file(error_data_list, error_details, config)