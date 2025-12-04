from fastapi import APIRouter, Depends, Security, HTTPException
from sqlmodel import Session, select, func
from typing import List
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

from models.base.major import Major
from schemas.base.major import (
    MajorCreate, MajorUpdate, MajorResponse,
    BatchMajorDelete, MajorListResponse, MajorQueryParams
)
from schemas.account.user import UserResponse
from core.security import get_current_active_user, get_required_scopes_for_route
from database import get_db

major_router = APIRouter(tags=["专业管理"], prefix="/majors")

def validate_professional_code_format(code: str):
    """验证专业代码格式：必须是两个英文字母"""
    if not re.match(r'^[A-Za-z]{2}$', code):
        raise HTTPException(status_code=400, detail="专业代码格式错误，必须是两个英文字母，如'AB'")
    
    # 自动转换为大写
    return code.upper()

def generate_professional_code(major_name: str) -> str:
    """
    根据专业名称自动生成专业代码
    - 取专业名称前两个首字母，不足2个用0补充
    """
    # 提取中文字符的首字母拼音
    import pypinyin
    
    # 获取每个字符的首字母拼音
    pinyin_list = pypinyin.lazy_pinyin(major_name, style=pypinyin.STYLE_FIRST_LETTER)
    
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

# 获取所有专业列表
@major_router.get("", response_model=MajorListResponse)
async def get_majors(
    params: MajorQueryParams = Depends(),
    db: Session = Depends(get_db),
    _: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/majors"))
):
    """获取所有专业列表（不分页，支持多关键词搜索）"""
    try:
        # 构建查询条件
        query = select(Major).where(Major.is_delete != True)
        
        # 处理多关键词搜索
        if params.search and params.search.strip():
            keywords = params.search.strip().split()
            
            # 每个关键词在专业名称字段中查找，使用AND逻辑
            for keyword in keywords:
                query = query.where(
                    getattr(Major, 'major_name').ilike(f"%{keyword}%")
                )
        
        # 默认按ID升序排序
        query = query.order_by(Major.id.asc())
        
        # 执行查询
        majors = db.exec(query).all()
        
        # 将数据库模型转换为响应模型
        major_responses = [MajorResponse.model_validate(major) for major in majors]
        
        return MajorListResponse(
            data=major_responses,
            total=len(major_responses)
        )
    except Exception as e:
        logger.error(f"获取专业列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取专业列表失败")

# 获取单个专业
@major_router.get("/get/{major_id}", response_model=MajorResponse)
async def get_major(
    major_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/majors/get"))
):
    """根据ID获取单个专业"""
    try:
        major = db.exec(
            select(Major).where(Major.id == major_id, Major.is_delete != True)
        ).first()
        
        if not major:
            raise HTTPException(status_code=404, detail="专业不存在")
        
        return major
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取专业失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取专业失败")

# 创建专业
@major_router.post("/", response_model=MajorResponse)
async def create_major(
    major_data: MajorCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/majors/new"))
):
    """创建新专业"""
    try:
        # 检查专业名称是否已存在
        existing_major = db.exec(
            select(Major).where(
                Major.major_name == major_data.major_name.strip(),
                Major.is_delete != True
            )
        ).first()
        
        if existing_major:
            raise HTTPException(status_code=400, detail="专业名称已存在")
        
        # 处理专业代码：如果用户提供了则验证格式，否则自动生成
        if major_data.major_code and major_data.major_code.strip() != '':
            # 用户提供了专业代码，验证格式并转换为大写
            validated_code = validate_professional_code_format(major_data.major_code)
        else:
            # 用户没有提供专业代码，自动生成
            validated_code = generate_professional_code(major_data.major_name)
        
        # 专业代码可以重复，无需检查唯一性
        
        # 创建专业记录
        major = Major(
            major_name=major_data.major_name.strip(),
            major_code=validated_code,
            creator=current_user.username,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        
        db.add(major)
        db.commit()
        db.refresh(major)
        
        return major
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建专业失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建专业失败")

# 更新专业
@major_router.put("/update/{major_id}", response_model=MajorResponse)
async def update_major(
    major_id: int,
    major_data: MajorUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/majors/update"))
):
    """更新专业信息"""
    try:
        major = db.exec(
            select(Major).where(Major.id == major_id, Major.is_delete != True)
        ).first()
        
        if not major:
            raise HTTPException(status_code=404, detail="专业不存在")
        
        # 如果更新专业名称，检查是否与其他专业冲突
        if major_data.major_name and major_data.major_name.strip() != major.major_name:
            existing_major = db.exec(
                select(Major).where(
                    Major.major_name == major_data.major_name.strip(),
                    Major.is_delete != True,
                    Major.id != major_id
                )
            ).first()
            
            if existing_major:
                raise HTTPException(status_code=400, detail="专业名称已存在")
            
            major.major_name = major_data.major_name.strip()
        
        # 处理专业代码更新
        if major_data.major_code is not None:
            # 如果用户提供了专业代码
            if major_data.major_code.strip() != '':
                # 用户提供了专业代码，验证格式并转换为大写
                validated_code = validate_professional_code_format(major_data.major_code)
                
                # 专业代码可以重复，直接设置专业代码
                major.major_code = validated_code
            else:
                # 用户提供了空字符串，根据专业名称自动生成专业代码
                # 如果同时更新了专业名称，使用新的专业名称，否则使用现有的专业名称
                major_name = major_data.major_name if major_data.major_name else major.major_name
                major.major_code = generate_professional_code(major_name)
        
        major.update_time = datetime.now()
        
        db.add(major)
        db.commit()
        db.refresh(major)
        
        return major
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新专业失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新专业失败")

# 删除专业（软删除）
@major_router.delete("/delete/{major_id}")
async def delete_major(
    major_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/majors/delete"))
):
    """软删除专业"""
    try:
        major = db.exec(
            select(Major).where(Major.id == major_id, Major.is_delete != True)
        ).first()
        
        if not major:
            raise HTTPException(status_code=404, detail="专业不存在")
        
        major.is_delete = True
        major.update_time = datetime.now()
        
        db.add(major)
        db.commit()
        
        return {"message": "专业删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除专业失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除专业失败")

# 批量删除专业
@major_router.post("/batch-delete")
async def batch_delete_majors(
    delete_data: BatchMajorDelete,
    db: Session = Depends(get_db),
    current_user: UserResponse = Security(get_current_active_user, scopes=get_required_scopes_for_route("/majors/delete"))
):
    """批量软删除多个专业"""
    try:
        if not delete_data.major_ids:
            raise HTTPException(status_code=400, detail="请选择要删除的专业")
        
        # 查询所有要删除的专业
        majors = db.exec(
            select(Major).where(
                Major.id.in_(delete_data.major_ids),
                Major.is_delete != True
            )
        ).all()
        
        if len(majors) != len(delete_data.major_ids):
            raise HTTPException(status_code=404, detail="部分专业不存在")
        
        # 批量软删除
        current_time = datetime.now()
        for major in majors:
            major.is_delete = True
            major.update_time = current_time
            db.add(major)
        
        db.commit()
        
        return {"message": f"成功删除 {len(majors)} 个专业"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"批量删除专业失败: {str(e)}")
        raise HTTPException(status_code=500, detail="批量删除专业失败")