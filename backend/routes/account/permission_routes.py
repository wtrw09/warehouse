from fastapi import APIRouter, Depends, Security
from sqlmodel import Session, select
from models.account.permission import Permission
from models.account.user import User
from core.security import get_current_user, get_required_scopes_for_route
from database import get_db

permission_router = APIRouter(tags=["权限管理"])

# 获取权限表
@permission_router.get("/permissions", response_model=list[Permission])
def read_permissions(
    db: Session = Depends(get_db),
    _: User = Security(get_current_user, scopes=get_required_scopes_for_route("/permissions"))
):
    """获取所有权限信息（需要AUTH_READ权限）"""
    permissions = db.exec(select(Permission).where(Permission.is_delete != True)).all()
    return permissions