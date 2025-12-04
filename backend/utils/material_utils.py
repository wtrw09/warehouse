import re
from typing import Optional
from pypinyin import pinyin, Style

def get_first_letters(text: str) -> str:
    """
    获取字符串中每个汉字的首字母，英文单词取前5个字符
    使用pypinyin库进行准确的汉字拼音首字母转换
    """
    if not text:
        return ""
    
    # 如果是纯英文，直接取前5个字符
    if all(ord(c) < 128 for c in text):
        return text[:5].upper()
    
    # 处理中英文混合的情况
    result = ""
    for char in text:
        if ord(char) < 128:  # 英文字符
            if char.isalpha():
                result += char.upper()
        else:  # 中文字符
            # 使用pypinyin获取汉字的首字母
            try:
                pinyin_result = pinyin(char, style=Style.FIRST_LETTER)
                if pinyin_result and pinyin_result[0]:
                    result += pinyin_result[0][0].upper()
                else:
                    # 如果无法获取拼音，使用'X'作为占位符
                    result += 'X'
            except Exception:
                # 如果出现异常，使用'X'作为占位符
                result += 'X'
    
    return result[:5] if result else ""

def generate_material_query_code(material_name: str, material_specification: Optional[str] = None) -> str:
    """
    生成器材查询码
    格式：器材名称前5个字符（英文直接取，中文取首字母）-器材规格前3个字符
    """
    # 处理器材名称
    name_part = get_first_letters(material_name)
    
    # 处理器材规格
    spec_part = ""
    if material_specification:
        spec_part = get_first_letters(material_specification)[:3]
    
    # 组合查询码
    if spec_part:
        return f"{name_part}-{spec_part}"
    else:
        return name_part

def validate_material_code_unique(
    db, material_code: str, exclude_id: Optional[int] = None
) -> bool:
    """
    验证器材编码的唯一性（仅检查is_delete=False的记录）
    """
    from sqlmodel import select
    from models.material.material import Material
    
    query = select(Material).where(
        Material.is_delete != True,
        Material.material_code == material_code
    )
    
    if exclude_id:
        query = query.where(Material.id != exclude_id)
    
    existing_material = db.exec(query).first()
    return existing_material is None