from fastapi import APIRouter, Depends, HTTPException, Security
from sqlmodel import Session, select, or_
from typing import List, Optional
import re
import json

from database import get_db
from models.system.material_code_level import MaterialCodeLevel
from schemas.system.material_code_level import (
    MaterialCodeLevelCreate, MaterialCodeLevelUpdate, MaterialCodeLevelResponse,
    MaterialCodeLevelQueryParams,MaterialCodeLevelStatistics, BatchMaterialCodeLevelDelete, MaterialCodeLevelAddDescription,
    MaterialCodeLevelAddDescriptionResult
)
from core.security import get_current_active_user, get_required_scopes_for_route
from schemas.account.user import UserResponse

material_code_level_router = APIRouter(tags=["器材编码分类层级管理"], prefix="/material-code-levels")

def build_query_conditions(params: MaterialCodeLevelQueryParams, query):
    """构建查询条件"""
    # 关键词搜索
    if params.search:
        search_conditions = []
        search_conditions.append(MaterialCodeLevel.level_code.ilike(f"%{params.search}%"))
        search_conditions.append(MaterialCodeLevel.level_name.ilike(f"%{params.search}%"))
        search_conditions.append(MaterialCodeLevel.code.ilike(f"%{params.search}%"))
        search_conditions.append(MaterialCodeLevel.description.ilike(f"%{params.search}%"))
        query = query.where(or_(*search_conditions))
    
    # 特定字段筛选
    if params.level_code:
        query = query.where(MaterialCodeLevel.level_code.ilike(f"%{params.level_code}%"))
    if params.level_name:
        query = query.where(MaterialCodeLevel.level_name.ilike(f"%{params.level_name}%"))
    
    return query

def validate_level_code_format(level_code: str):
    """验证层级路径码格式"""
    if not re.match(r'^\d+(\-\d+)*$', level_code):
        raise HTTPException(status_code=400, detail="层级路径码格式错误，应为数字和短横线组合，如'1', '1-1'")
    
    # 检查层级深度，最多允许2个层级
    depth = len(level_code.split('-'))
    if depth > 2:
        raise HTTPException(status_code=400, detail="层级路径码最多只能有2个层级，如'1', '1-1'")

def validate_professional_code_format(code: str):
    """验证专业代码格式：必须是两个英文字母"""
    if not re.match(r'^[A-Za-z]{2}$', code):
        raise HTTPException(status_code=400, detail="专业代码格式错误，必须是两个英文字母，如'AB'")
    
    # 自动转换为大写
    return code.upper()

def validate_description_format(description: Optional[str]) -> Optional[str]:
    """验证描述字段格式"""
    if description is None or description.strip() == '':
        return None
    
    # 检查是否为有效的JSON数组格式
    import json
    try:
        # 尝试解析JSON
        parsed = json.loads(description)
        # 确保是列表且每个元素都是字符串
        if not isinstance(parsed, list):
            raise HTTPException(status_code=400, detail="描述字段格式错误：必须是字符串列表格式")
        
        for item in parsed:
            if not isinstance(item, str):
                raise HTTPException(status_code=400, detail="描述字段格式错误：列表中的每个元素必须是字符串")
        
        # 返回原始JSON字符串
        return description
    except json.JSONDecodeError:
        # 如果不是JSON格式，则视为普通字符串，将其转换为单元素列表的JSON格式
        try:
            return json.dumps([description.strip()], ensure_ascii=False)
        except Exception:
            raise HTTPException(status_code=400, detail="描述字段格式错误：无法处理描述内容")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"描述字段格式错误：{str(e)}")

def check_level_code_unique(db: Session, level_code: str, exclude_id: int = None):
    """检查层级路径码是否唯一"""
    statement = select(MaterialCodeLevel).where(
        MaterialCodeLevel.level_code == level_code
    )
    if exclude_id:
        statement = statement.where(MaterialCodeLevel.id != exclude_id)
    
    if db.exec(statement).first():
        raise HTTPException(status_code=400, detail=f"层级路径码 '{level_code}' 已存在")

def generate_professional_code(level_name: str) -> str:
    """
    根据层级名称自动生成专业代码
    - 如果层级名称为'默认'，则返回'00'
    - 否则取层级名称前两个首字母，不足2个用0补充
    """
    if level_name.strip().lower() == '默认':
        return '00'
    
    # 提取中文字符的首字母拼音
    import pypinyin
    
    # 获取每个字符的首字母拼音
    pinyin_list = pypinyin.lazy_pinyin(level_name, style=pypinyin.STYLE_FIRST_LETTER)
    
    # 合并所有首字母
    initials = ''.join(pinyin_list)
    
    # 只保留字母，过滤掉非字母字符
    letters = ''.join(filter(str.isalpha, initials))
    
    # 如果字母不足2个，用0补充
    if len(letters) < 2:
        letters = letters.ljust(2, '0')
    
    # 取前两个字母并转换为大写
    code = letters[:2].upper()
    
    return code



@material_code_level_router.get("/all", response_model=List[MaterialCodeLevelResponse])
def read_all_material_code_levels(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取所有器材编码分类层级（不分页）"""
    statement = select(MaterialCodeLevel).order_by(MaterialCodeLevel.id)
    items = db.exec(statement).all()
    return items

@material_code_level_router.get("/get/{id}", response_model=MaterialCodeLevelResponse)
def read_material_code_level(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取单个器材编码分类层级详情"""
    statement = select(MaterialCodeLevel).where(
        MaterialCodeLevel.id == id
    )
    item = db.exec(statement).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="器材编码分类层级不存在")
    
    return item

@material_code_level_router.get("/statistics", response_model=MaterialCodeLevelStatistics)
def get_material_code_level_statistics(
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """获取器材编码分类层级统计信息"""
    # 总数量
    statement = select(MaterialCodeLevel)
    total_count = db.exec(statement).rowcount
    
    # 按层级深度统计
    items = db.exec(statement).all()
    
    level_count_by_depth = {}
    for item in items:
        depth = len(item.level_code.split('-'))
        level_count_by_depth[depth] = level_count_by_depth.get(depth, 0) + 1
    
    return MaterialCodeLevelStatistics(
        total_count=total_count,
        level_count_by_depth=level_count_by_depth
    )

# 数据操作类路由
@material_code_level_router.post("/", response_model=MaterialCodeLevelResponse)
def create_material_code_level(
    material_code_level: MaterialCodeLevelCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """创建器材编码分类层级"""
    # 验证层级路径码格式
    validate_level_code_format(material_code_level.level_code)
    
    # 检查层级路径码是否唯一
    check_level_code_unique(db, material_code_level.level_code)
    
    # 处理专业代码：如果用户提供了则验证格式，否则自动生成
    if material_code_level.code and material_code_level.code.strip() != '':
        # 用户提供了专业代码，验证格式并转换为大写
        validated_code = validate_professional_code_format(material_code_level.code)
    else:
        # 用户没有提供专业代码，自动生成
        validated_code = generate_professional_code(material_code_level.level_name)
    
    # 验证描述字段格式
    validated_description = validate_description_format(material_code_level.description)
    
    # 创建记录
    db_item = MaterialCodeLevel(
        level_code=material_code_level.level_code,
        level_name=material_code_level.level_name,
        code=validated_code,
        description=validated_description
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item

@material_code_level_router.put("/update/{id}", response_model=MaterialCodeLevelResponse)
def update_material_code_level(
    id: int,
    material_code_level_update: MaterialCodeLevelUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """更新器材编码分类层级"""
    # 获取现有记录
    statement = select(MaterialCodeLevel).where(
        MaterialCodeLevel.id == id
    )
    db_item = db.exec(statement).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="器材编码分类层级不存在")
    
    # 验证层级路径码格式（如果更新）
    if material_code_level_update.level_code:
        validate_level_code_format(material_code_level_update.level_code)
        
        # 检查层级路径码是否唯一（排除当前记录）
        check_level_code_unique(db, material_code_level_update.level_code, exclude_id=id)
    
    # 处理专业代码更新
    if material_code_level_update.code is not None:
        # 如果用户提供了专业代码
        if material_code_level_update.code.strip() != '':
            # 用户提供了专业代码，验证格式并转换为大写
            validated_code = validate_professional_code_format(material_code_level_update.code)
            material_code_level_update.code = validated_code
        else:
            # 用户提供了空字符串，根据层级名称自动生成专业代码
            # 如果同时更新了层级名称，使用新的层级名称，否则使用现有的层级名称
            level_name = material_code_level_update.level_name if material_code_level_update.level_name else db_item.level_name
            material_code_level_update.code = generate_professional_code(level_name)
    
    # 更新字段
    update_data = material_code_level_update.dict(exclude_unset=True)
    if update_data:
        # 如果更新了描述字段，验证格式
        if 'description' in update_data:
            update_data['description'] = validate_description_format(update_data['description'])
        
        for field, value in update_data.items():
            setattr(db_item, field, value)
    
    db.commit()
    db.refresh(db_item)
    
    return db_item

@material_code_level_router.delete("/delete/{id}")
def delete_material_code_level(
    id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """删除器材编码分类层级"""
    statement = select(MaterialCodeLevel).where(
        MaterialCodeLevel.id == id
    )
    db_item = db.exec(statement).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="器材编码分类层级不存在")
    
    # 硬删除
    db.delete(db_item)
    db.commit()
    
    return {"message": "删除成功"}

@material_code_level_router.post("/batch-delete")
def batch_delete_material_code_levels(
    batch_delete: BatchMaterialCodeLevelDelete,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """批量删除器材编码分类层级"""
    success_count = 0
    error_ids = []
    
    for item_id in batch_delete.ids:
        statement = select(MaterialCodeLevel).where(
            MaterialCodeLevel.id == item_id
        )
        db_item = db.exec(statement).first()
        
        if db_item:
            db.delete(db_item)
            success_count += 1
        else:
            error_ids.append(item_id)
    
    db.commit()
    
    return {
        "message": f"批量删除完成，成功删除 {success_count} 条记录",
        "error_ids": error_ids
    }

@material_code_level_router.post("/add-description", response_model=MaterialCodeLevelAddDescriptionResult)
def add_description_to_material_code_level(
    add_description: MaterialCodeLevelAddDescription,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_active_user)
):
    """
    向器材编码分类层级添加描述项
    
    参数:
    - level_code: 层级路径码，用于定位要添加描述的层级
    - description: 要添加的描述内容
    
    返回:
    - 更新后的描述列表
    """
    # 根据层级路径码查找记录
    statement = select(MaterialCodeLevel).where(
        MaterialCodeLevel.level_code == add_description.level_code
    )
    db_item = db.exec(statement).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail=f"层级路径码 '{add_description.level_code}' 对应的器材编码分类层级不存在")
    
    # 获取当前的描述列表
    current_description_list = db_item.get_description_list()
    
    # 添加新的描述项
    if add_description.description.strip():
        current_description_list.append(add_description.description.strip())
    
    # 更新描述字段
    db_item.set_description_list(current_description_list)
    
    # 保存到数据库
    db.commit()
    db.refresh(db_item)
    
    # 获取更新后的描述列表
    updated_description_list = db_item.get_description_list()
    
    return MaterialCodeLevelAddDescriptionResult(
        message=f"成功向层级路径码 '{add_description.level_code}' 添加描述项",
        level_code=add_description.level_code,
        new_description_list=updated_description_list
    )

@material_code_level_router.delete("/delete-all")
def delete_all_material_code_levels(
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/material-code-levels/delete-all"))
):
    """删除所有器材编码分类层级数据"""
    try:
        # 查询所有记录
        statement = select(MaterialCodeLevel)
        all_items = db.exec(statement).all()
        
        # 删除所有记录
        for item in all_items:
            db.delete(item)
        
        db.commit()
        
        return {
            "message": f"成功删除所有器材编码分类层级数据，共 {len(all_items)} 条记录",
            "deleted_count": len(all_items)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除所有数据时发生错误: {str(e)}")

@material_code_level_router.post("/generate-from-sub-majors")
def generate_material_code_levels_from_sub_majors(
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/material-code-levels/generate-from-sub-majors"))
):
    """根据二级专业数据生成器材编码分类层级数据"""
    try:
        # 导入二级专业模型
        from models.base.sub_major import SubMajor
        from models.base.major import Major
        
        # 先删除表格中所有数据
        statement = select(MaterialCodeLevel)
        all_items = db.exec(statement).all()
        for item in all_items:
            db.delete(item)
        db.commit()
        print(f"已删除 {len(all_items)} 条现有器材编码分类层级记录")
        
        # 查询所有二级专业数据，过滤掉名称为"默认"的记录
        statement = select(SubMajor).where(
            SubMajor.is_delete == False
        )
        sub_majors = db.exec(statement).all()
        
        if not sub_majors:
            raise HTTPException(status_code=404, detail="没有找到有效的二级专业数据")
        
        # 统计生成结果
        generated_count = 0
        updated_count = 0
        error_count = 0
        
        # 按一级专业分组二级专业
        major_groups = {}
        for sub_major in sub_majors:
            major_id = sub_major.major_id or 0
            if major_id not in major_groups:
                major_groups[major_id] = []
            major_groups[major_id].append(sub_major)
        
        # 生成器材编码分类层级数据
        for major_id, sub_majors_in_major in major_groups.items():
            # 获取一级专业信息
            major_name = "默认"
            major_code = "00"
            if major_id:
                major_statement = select(Major).where(Major.id == major_id)
                major = db.exec(major_statement).first()
                if major:
                    major_name = major.major_name
                    major_code = major.major_code
            
            # 生成一级层级（如果不存在）
            level_code_1 = str(major_id) if major_id else "0"
            level_name_1 = major_name
            
            # 检查一级层级是否已存在
            existing_level_1 = db.exec(
                select(MaterialCodeLevel).where(MaterialCodeLevel.level_code == level_code_1)
            ).first()
            
            if not existing_level_1:
                # 创建一级层级
                level_1 = MaterialCodeLevel(
                    level_code=level_code_1,
                    level_name=level_name_1,
                    code=major_code,
                    description=None
                )
                db.add(level_1)
                db.commit()
                db.refresh(level_1)
                generated_count += 1
            else:
                level_1 = existing_level_1
            
            # 生成二级层级
            for i, sub_major in enumerate(sub_majors_in_major, 1):
                level_code_2 = f"{level_code_1}-{i}"
                level_name_2 = sub_major.sub_major_name
                
                # 检查二级层级是否已存在
                existing_level_2 = db.exec(
                    select(MaterialCodeLevel).where(MaterialCodeLevel.level_code == level_code_2)
                ).first()
                
                # 获取二级专业的描述列表
                description_list = sub_major.get_description_list()
                description_json = json.dumps(description_list, ensure_ascii=False) if description_list else None
                
                if not existing_level_2:
                    # 创建二级层级
                    level_2 = MaterialCodeLevel(
                        level_code=level_code_2,
                        level_name=level_name_2,
                        code=sub_major.sub_major_code,
                        description=description_json
                    )
                    db.add(level_2)
                    generated_count += 1
                else:
                    # 更新现有二级层级
                    existing_level_2.level_name = level_name_2
                    existing_level_2.code = sub_major.sub_major_code
                    existing_level_2.description = description_json
                    updated_count += 1
        
        # 提交所有更改
        db.commit()
        
        return {
            "message": "成功根据二级专业数据生成器材编码分类层级数据",
            "generated_count": generated_count,
            "updated_count": updated_count,
            "error_count": error_count,
            "total_processed": len(sub_majors)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"生成器材编码分类层级数据时发生错误: {str(e)}")