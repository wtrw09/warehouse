from fastapi import APIRouter, Depends, Security, HTTPException
from sqlmodel import Session, select, func
from typing import List
import logging
from datetime import datetime
import re
import pypinyin

logger = logging.getLogger(__name__)

from models.base.sub_major import SubMajor
from models.base.major import Major
from schemas.base.sub_major import (
    SubMajorCreate, SubMajorUpdate, SubMajorResponse,
    BatchSubMajorDelete, SubMajorListResponse, SubMajorQueryParams, SubMajorStatistics,
    SubMajorAddDescription, SubMajorAddDescriptionResult
)
from schemas.account.user import UserResponse
from core.security import get_current_active_user, get_required_scopes_for_route
from database import get_db

sub_major_router = APIRouter(tags=["二级专业管理"], prefix="/sub-majors")

def validate_sub_major_code_format(code: str):
    """验证二级专业代码格式：必须是两个字符"""
    if not re.match(r'^.{2}$', code):
        raise HTTPException(status_code=400, detail="二级专业代码格式错误，必须是两个字符，如'AB'或'01'")
    
    # 自动转换为大写
    return code.upper()

def generate_sub_major_code(sub_major_name: str) -> str:
    """
    根据二级专业名称自动生成专业代码
    - 取二级专业名称前两个首字母，不足2个用0补充
    """
    # 提取中文字符的首字母拼音
    import pypinyin
    
    # 获取每个字符的首字母拼音
    pinyin_list = pypinyin.lazy_pinyin(sub_major_name, style=pypinyin.STYLE_FIRST_LETTER)
    
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

# 获取所有二级专业列表
@sub_major_router.get("", response_model=SubMajorListResponse)
async def get_sub_majors(
    params: SubMajorQueryParams = Depends(),
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/sub-majors"))
):
    """获取所有二级专业列表（不分页，支持多关键词搜索）"""
    try:
        # 构建查询条件
        query = select(SubMajor).where(SubMajor.is_delete != True)
        
        # 按一级专业ID筛选
        if params.major_id is not None:
            query = query.where(SubMajor.major_id == params.major_id)
        
        # 处理多关键词搜索
        if params.search and params.search.strip():
            keywords = params.search.strip().split()
            
            # 每个关键词在二级专业名称、代码、一级专业名称和描述字段中查找，使用AND逻辑
            for keyword in keywords:
                query = query.where(
                    (getattr(SubMajor, 'sub_major_name').ilike(f"%{keyword}%")) |
                    (getattr(SubMajor, 'sub_major_code').ilike(f"%{keyword}%")) |
                    (getattr(SubMajor, 'major_name').ilike(f"%{keyword}%")) |
                    (getattr(SubMajor, 'description').ilike(f"%{keyword}%"))
                )
        
        # 默认按ID升序排序
        query = query.order_by(SubMajor.id.asc())
        
        # 执行查询
        sub_majors = db.exec(query).all()
        
        # 将数据库模型转换为响应模型
        sub_major_responses = [SubMajorResponse.model_validate(sub_major) for sub_major in sub_majors]
        
        return SubMajorListResponse(
            data=sub_major_responses,
            total=len(sub_major_responses)
        )
    except Exception as e:
        logger.error(f"获取二级专业列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取二级专业列表失败")

# 获取单个二级专业
@sub_major_router.get("/get/{sub_major_id}", response_model=SubMajorResponse)
async def get_sub_major(
    sub_major_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/sub-majors/get"))
):
    """根据ID获取单个二级专业"""
    try:
        sub_major = db.exec(
            select(SubMajor).where(SubMajor.id == sub_major_id, SubMajor.is_delete != True)
        ).first()
        
        if not sub_major:
            raise HTTPException(status_code=404, detail="二级专业不存在")
        
        return sub_major
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取二级专业失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取二级专业失败")

# 获取二级专业统计信息
@sub_major_router.get("/statistics", response_model=SubMajorStatistics)
async def get_sub_major_statistics(
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/sub-majors/statistics"))
):
    """获取二级专业统计信息"""
    try:
        # 统计总数量
        total_count = db.exec(
            select(func.count(SubMajor.id)).where(SubMajor.is_delete != True)
        ).one()
        
        # 按一级专业分布统计
        major_distribution = {}
        
        # 获取所有一级专业
        majors = db.exec(select(Major).where(Major.is_delete != True)).all()
        
        for major in majors:
            count = db.exec(
                select(func.count(SubMajor.id)).where(
                    SubMajor.major_id == major.id,
                    SubMajor.is_delete != True
                )
            ).one()
            major_distribution[major.major_name] = count
        
        return SubMajorStatistics(
            total_count=total_count,
            major_distribution=major_distribution
        )
    except Exception as e:
        logger.error(f"获取二级专业统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取二级专业统计信息失败")

# 创建二级专业
@sub_major_router.post("", response_model=SubMajorResponse)
async def create_sub_major(
    sub_major_data: SubMajorCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/sub-majors/new"))
):
    """创建新二级专业"""
    try:
        # 检查二级专业名称是否已存在
        existing_sub_major = db.exec(
            select(SubMajor).where(
                SubMajor.sub_major_name == sub_major_data.sub_major_name.strip(),
                SubMajor.is_delete != True
            )
        ).first()
        
        if existing_sub_major:
            raise HTTPException(status_code=400, detail="二级专业名称已存在")
        
        # 如果指定了一级专业ID，验证一级专业是否存在并获取专业名称
        major_name = None
        if sub_major_data.major_id:
            major = db.exec(
                select(Major).where(Major.id == sub_major_data.major_id, Major.is_delete != True)
            ).first()
            
            if not major:
                raise HTTPException(status_code=400, detail="指定的一级专业不存在")
            
            major_name = major.major_name
        
        # 处理二级专业代码：如果用户提供了则验证格式，否则自动生成
        if sub_major_data.sub_major_code and sub_major_data.sub_major_code.strip() != '':
            # 用户提供了二级专业代码，验证格式并转换为大写
            validated_code = validate_sub_major_code_format(sub_major_data.sub_major_code)
        else:
            # 用户没有提供二级专业代码，自动生成
            validated_code = generate_sub_major_code(sub_major_data.sub_major_name)
        
        # 创建二级专业记录
        sub_major = SubMajor(
            sub_major_name=sub_major_data.sub_major_name.strip(),
            sub_major_code=validated_code,
            description=sub_major_data.description,
            major_id=sub_major_data.major_id,
            major_name=major_name,  # 通过major_id自动获取
            reserved=None,  # 保留字段，不要求输入
            creator=current_user.username,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        
        db.add(sub_major)
        db.commit()
        db.refresh(sub_major)
        
        return sub_major
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建二级专业失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建二级专业失败")

# 更新二级专业
@sub_major_router.put("/update/{sub_major_id}", response_model=SubMajorResponse)
async def update_sub_major(
    sub_major_id: int,
    sub_major_data: SubMajorUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/sub-majors/update"))
):
    """更新二级专业信息"""
    try:
        sub_major = db.exec(
            select(SubMajor).where(SubMajor.id == sub_major_id, SubMajor.is_delete != True)
        ).first()
        
        if not sub_major:
            raise HTTPException(status_code=404, detail="二级专业不存在")
        
        # 如果更新二级专业名称，检查是否与其他二级专业冲突
        if sub_major_data.sub_major_name and sub_major_data.sub_major_name.strip() != sub_major.sub_major_name:
            existing_sub_major = db.exec(
                select(SubMajor).where(
                    SubMajor.sub_major_name == sub_major_data.sub_major_name.strip(),
                    SubMajor.is_delete != True,
                    SubMajor.id != sub_major_id
                )
            ).first()
            
            if existing_sub_major:
                raise HTTPException(status_code=400, detail="二级专业名称已存在")
            
            sub_major.sub_major_name = sub_major_data.sub_major_name.strip()
        
        # 处理二级专业代码更新
        if sub_major_data.sub_major_code is not None:
            # 如果用户提供了二级专业代码
            if sub_major_data.sub_major_code.strip() != '':
                # 用户提供了二级专业代码，验证格式并转换为大写
                validated_code = validate_sub_major_code_format(sub_major_data.sub_major_code)
                
                # 设置二级专业代码
                sub_major.sub_major_code = validated_code
            else:
                # 用户提供了空字符串，根据二级专业名称自动生成专业代码
                # 如果同时更新了二级专业名称，使用新的二级专业名称，否则使用现有的二级专业名称
                sub_major_name = sub_major_data.sub_major_name if sub_major_data.sub_major_name else sub_major.sub_major_name
                sub_major.sub_major_code = generate_sub_major_code(sub_major_name)
        
        # 更新描述
        if sub_major_data.description is not None:
            sub_major.description = sub_major_data.description
        # 处理空字符串描述：当描述为空字符串时清空描述内容
        elif sub_major_data.description == '':
            sub_major.description = ''
        
        # 更新一级专业关联
        if sub_major_data.major_id is not None:
            if sub_major_data.major_id != sub_major.major_id:
                # 验证新的一级专业是否存在
                major = db.exec(
                    select(Major).where(Major.id == sub_major_data.major_id, Major.is_delete != True)
                ).first()
                
                if not major:
                    raise HTTPException(status_code=400, detail="指定的一级专业不存在")
                
                sub_major.major_id = sub_major_data.major_id
                sub_major.major_name = major.major_name  # 通过major_id自动获取专业名称
        
        sub_major.update_time = datetime.now()
        
        db.add(sub_major)
        db.commit()
        db.refresh(sub_major)
        
        return sub_major
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新二级专业失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新二级专业失败")

# 删除二级专业
@sub_major_router.delete("/delete/{sub_major_id}")
async def delete_sub_major(
    sub_major_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/sub-majors/delete"))
):
    """软删除二级专业"""
    try:
        sub_major = db.exec(
            select(SubMajor).where(SubMajor.id == sub_major_id, SubMajor.is_delete != True)
        ).first()
        
        if not sub_major:
            raise HTTPException(status_code=404, detail="二级专业不存在")
        
        sub_major.is_delete = True
        sub_major.update_time = datetime.now()
        
        db.add(sub_major)
        db.commit()
        
        return {"message": "二级专业删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除二级专业失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除二级专业失败")

# 批量删除二级专业
@sub_major_router.post("/batch-delete")
async def batch_delete_sub_majors(
    delete_data: BatchSubMajorDelete,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/sub-majors/delete"))
):
    """批量软删除多个二级专业"""
    try:
        if not delete_data.sub_major_ids:
            raise HTTPException(status_code=400, detail="请选择要删除的二级专业")
        
        # 查询所有要删除的二级专业
        sub_majors = db.exec(
            select(SubMajor).where(
                SubMajor.id.in_(delete_data.sub_major_ids),
                SubMajor.is_delete != True
            )
        ).all()
        
        if len(sub_majors) != len(delete_data.sub_major_ids):
            raise HTTPException(status_code=404, detail="部分二级专业不存在")
        
        # 批量软删除
        current_time = datetime.now()
        for sub_major in sub_majors:
            sub_major.is_delete = True
            sub_major.update_time = current_time
            db.add(sub_major)
        
        db.commit()
        
        return {"message": f"成功删除 {len(sub_majors)} 个二级专业"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"批量删除二级专业失败: {str(e)}")
        raise HTTPException(status_code=500, detail="批量删除二级专业失败")

# 向二级专业添加描述项
@sub_major_router.post("/add-description", response_model=SubMajorAddDescriptionResult)
async def add_description_to_sub_major(
    add_description: SubMajorAddDescription,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/sub-majors/add-description"))
):
    """
    向二级专业添加描述项
    
    参数:
    - sub_major_id: 二级专业ID，用于定位要添加描述的二级专业
    - description: 要添加的描述内容
    
    返回:
    - 更新后的描述列表
    """
    try:
        # 根据二级专业ID查找记录
        sub_major = db.exec(
            select(SubMajor).where(SubMajor.id == add_description.sub_major_id, SubMajor.is_delete != True)
        ).first()
        
        if not sub_major:
            raise HTTPException(status_code=404, detail=f"ID为 '{add_description.sub_major_id}' 的二级专业不存在")
        
        # 添加新的描述项
        sub_major.add_description(add_description.description)
        sub_major.update_time = datetime.now()
        
        # 保存到数据库
        db.add(sub_major)
        db.commit()
        db.refresh(sub_major)
        
        # 获取更新后的描述列表
        updated_description_list = sub_major.get_description_list()
        
        return SubMajorAddDescriptionResult(
            message=f"成功向二级专业 '{sub_major.sub_major_name}' 添加描述项",
            sub_major_id=add_description.sub_major_id,
            new_description_list=updated_description_list
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"向二级专业添加描述项失败: {str(e)}")
        raise HTTPException(status_code=500, detail="向二级专业添加描述项失败")