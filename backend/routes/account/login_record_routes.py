"""
用户登录记录查询路由
支持分页查询、多条件筛选、联合搜索等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Security
from sqlmodel import Session, select, and_, or_
from typing import Annotated, Optional, List
from datetime import datetime, timedelta

from models.account.user_login_record import UserLoginRecord, UserLoginHistory
from schemas.account.login_record import LoginRecordResponse, PaginatedLoginRecords
from core.security import get_current_user, get_required_scopes_for_route
from database import get_db
import logging

logger = logging.getLogger(__name__)

# 创建用户登录记录查询路由
login_record_router = APIRouter(prefix="", tags=["用户登录记录查询"])

class BaseLoginRecordQueryParams:
    """基础查询参数类（不包含用户名）"""
    def __init__(
        self,
        ip_address: Optional[str] = Query(None, description="IP地址"),
        start_time: Optional[datetime] = Query(None, description="开始时间"),
        end_time: Optional[datetime] = Query(None, description="结束时间"),
        search: Optional[str] = Query(None, description="搜索关键词（空格分隔多关键词）"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, description="每页数量")
    ):
        self.ip_address = ip_address
        self.start_time = start_time
        self.end_time = end_time
        self.search = search
        self.page = page
        self.page_size = page_size


class LoginRecordQueryParams(BaseLoginRecordQueryParams):
    """用户登录记录查询参数类（包含用户名）"""
    def __init__(
        self,
        username: Optional[str] = Query(None, description="用户名"),
        ip_address: Optional[str] = Query(None, description="IP地址"),
        start_time: Optional[datetime] = Query(None, description="开始时间"),
        end_time: Optional[datetime] = Query(None, description="结束时间"),
        search: Optional[str] = Query(None, description="搜索关键词（空格分隔多关键词）"),
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(20, ge=1, description="每页数量")
    ):
        super().__init__(
            ip_address=ip_address,
            start_time=start_time,
            end_time=end_time,
            search=search,
            page=page,
            page_size=page_size
        )
        self.username = username


class MyLoginRecordQueryParams(BaseLoginRecordQueryParams):
    """当前用户登录记录查询参数类（不包含用户名）"""
    pass

async def _get_login_records_core(db: Session, query_params: LoginRecordQueryParams, force_user_id: int = None) -> PaginatedLoginRecords:
    """
    登录记录查询核心逻辑 - 可复用的内部函数
    
    Args:
        force_user_id: 强制过滤的用户ID，用于确保只能查询指定用户的数据
    """
    # 构建基础查询条件 - 默认查询近3个月的数据
    cutoff_time = datetime.now() - timedelta(days=90)
    
    # 计算查询的实际开始时间
    actual_start_time = query_params.start_time if query_params.start_time else cutoff_time
    
    # 检查是否需要查询历史表
    need_history_query = actual_start_time < cutoff_time
    
    # 构建查询条件（通用函数，适用于两个表）
    def build_conditions_for_table(table, additional_conditions=None):
        conds = [] if additional_conditions is None else additional_conditions.copy()
        
        # 强制用户ID过滤（最高优先级）
        if force_user_id:
            conds.append(table.user_id == force_user_id)
        
        # 添加用户名筛选条件（如果未强制用户ID）
        if query_params.username and not force_user_id:
            conds.append(table.username.ilike(f"%{query_params.username}%"))
        
        # 添加IP地址筛选条件
        if query_params.ip_address:
            conds.append(table.ip_address.ilike(f"%{query_params.ip_address}%"))
        
        # 添加时间范围筛选条件
        if query_params.start_time:
            # 如果开始时间只精确到日（没有时分秒），则设置为当天的 00:00:00
            if query_params.start_time.hour == 0 and query_params.start_time.minute == 0 and query_params.start_time.second == 0:
                start_time_with_time = query_params.start_time.replace(hour=0, minute=0, second=0)
                conds.append(table.login_time >= start_time_with_time)
            else:
                conds.append(table.login_time >= query_params.start_time)
        
        if query_params.end_time:
            # 如果结束时间只精确到日（没有时分秒），则设置为当天的 23:59:59
            if query_params.end_time.hour == 0 and query_params.end_time.minute == 0 and query_params.end_time.second == 0:
                end_time_with_time = query_params.end_time.replace(hour=23, minute=59, second=59)
                conds.append(table.login_time <= end_time_with_time)
            else:
                conds.append(table.login_time <= query_params.end_time)
        
        # 处理多关键词联合搜索
        if query_params.search:
            search_conditions = []
            keywords = query_params.search.strip().split()
            
            for keyword in keywords:
                if keyword:
                    # 在每个字段中搜索关键词
                    keyword_conditions = [
                        table.username.ilike(f"%{keyword}%"),
                        table.ip_address.ilike(f"%{keyword}%"),
                        table.user_agent.ilike(f"%{keyword}%")
                    ]
                    search_conditions.append(or_(*keyword_conditions))
            
            if search_conditions:
                conds.append(or_(*search_conditions))
        
        return conds
    
    # 查询活跃表（近3个月）
    active_conditions = build_conditions_for_table(UserLoginRecord, [UserLoginRecord.login_time >= cutoff_time])
    active_query = select(UserLoginRecord).where(and_(*active_conditions))
    active_records = db.exec(active_query).all()
    
    all_records = []
    
    # 如果需要查询历史表
    if need_history_query:
        # 查询历史表（超过3个月）
        history_conditions = build_conditions_for_table(UserLoginHistory, [UserLoginHistory.login_time < cutoff_time])
        history_query = select(UserLoginHistory).where(and_(*history_conditions))
        history_records = db.exec(history_query).all()
        
        # 将历史记录转换为与活跃记录相同的结构（添加is_active字段）
        # 注意：历史表没有is_active字段，默认为False
        converted_history_records = []
        for record in history_records:
            # 将历史记录转换为类似活跃记录的对象
            class ConvertedHistoryRecord:
                def __init__(self, history_record):
                    self.id = history_record.id
                    self.user_id = history_record.user_id
                    self.username = history_record.username
                    self.ip_address = history_record.ip_address
                    self.user_agent = history_record.user_agent
                    self.login_time = history_record.login_time
                    self.logout_time = history_record.logout_time
                    self.is_active = False  # 历史记录默认为非活跃
            
            converted_history_records.append(ConvertedHistoryRecord(record))
        
        # 合并活跃记录和历史记录
        all_records = list(active_records) + converted_history_records
    else:
        # 只需要活跃记录
        all_records = list(active_records)
    
    # 按登录时间倒序排序
    all_records.sort(key=lambda x: x.login_time, reverse=True)
    
    # 计算总数
    total_records = len(all_records)
    
    # 分页处理
    offset = (query_params.page - 1) * query_params.page_size
    paginated_records = all_records[offset:offset + query_params.page_size]
    
    # 计算总页数
    total_pages = (total_records + query_params.page_size - 1) // query_params.page_size
    
    # 构建响应
    response_records = [
            LoginRecordResponse(
                id=record.id,
                user_id=record.user_id,
                username=record.username,
                ip_address=record.ip_address,
                user_agent=record.user_agent,
                login_time=record.login_time,
                logout_time=record.logout_time,
                is_active=record.is_active
            ) for record in paginated_records
        ]
    
    return PaginatedLoginRecords(
        total=total_records,
        page=query_params.page,
        page_size=query_params.page_size,
        total_pages=total_pages,
        records=response_records
    )

@login_record_router.get("/login-records", response_model=PaginatedLoginRecords)
async def get_login_records(
    db: Session = Depends(get_db),
    current_user: dict = Security(get_current_user, scopes=get_required_scopes_for_route("/login-records")),
    query_params: LoginRecordQueryParams = Depends()
):
    """
    查询用户登录记录
    
    权限要求: AUTH_READ
    默认查询近3个月的数据（user_login_records表）
    """
    
    try:
        result = await _get_login_records_core(db, query_params)
        
        logger.info(f"用户 {current_user.get('username', 'unknown')} 查询登录记录: "
                   f"页码={query_params.page}, 数量={len(result.records)}")
        
        return result
        
    except Exception as e:
        logger.error(f"查询登录记录失败: {e}")
        raise HTTPException(status_code=500, detail="查询失败")

@login_record_router.get("/login-records/stats/summary")
async def get_login_statistics_summary(
    db: Session = Depends(get_db),
    current_user: dict = Security(get_current_user, scopes=get_required_scopes_for_route("/login-records/stats/summary")),
    days: int = Query(90, ge=1, le=365, description="统计天数，默认90天")
):
    """
    获取登录统计摘要
    
    权限要求: AUTH_READ
    """
    
    try:
        cutoff_time = datetime.now() - timedelta(days=days)
        three_months_ago = datetime.now() - timedelta(days=90)
        
        # 检查是否需要查询历史表
        need_history_query = cutoff_time < three_months_ago
        
        # 初始化统计数据
        total_logins = 0
        user_ids = set()
        ip_addresses = set()
        today_logins = 0
        
        # 查询活跃表（近3个月）
        active_conds = [UserLoginRecord.login_time >= max(cutoff_time, three_months_ago)]
        
        # 总登录次数 - 活跃表
        active_total_logins_query = select(UserLoginRecord).where(
            and_(*active_conds)
        )
        total_logins += len(db.exec(active_total_logins_query).all())
        
        # 活跃用户数 - 活跃表
        active_users_query = select(UserLoginRecord.user_id).where(
            and_(*active_conds)
        ).distinct()
        active_user_ids = db.exec(active_users_query).all()
        user_ids.update(active_user_ids)
        
        # 不同IP数量 - 活跃表
        active_ips_query = select(UserLoginRecord.ip_address).where(
            and_(*active_conds)
        ).distinct()
        active_ips = db.exec(active_ips_query).all()
        ip_addresses.update(active_ips)
        
        # 如果需要查询历史表
        if need_history_query:
            # 历史表查询条件
            history_conds = [UserLoginHistory.login_time >= cutoff_time, UserLoginHistory.login_time < three_months_ago]
            
            # 总登录次数 - 历史表
            history_total_logins_query = select(UserLoginHistory).where(
                and_(*history_conds)
            )
            total_logins += len(db.exec(history_total_logins_query).all())
            
            # 活跃用户数 - 历史表
            history_users_query = select(UserLoginHistory.user_id).where(
                and_(*history_conds)
            ).distinct()
            history_user_ids = db.exec(history_users_query).all()
            user_ids.update(history_user_ids)
            
            # 不同IP数量 - 历史表
            history_ips_query = select(UserLoginHistory.ip_address).where(
                and_(*history_conds)
            ).distinct()
            history_ips = db.exec(history_ips_query).all()
            ip_addresses.update(history_ips)
        
        # 今日登录次数（只需要查询活跃表，因为历史表只包含超过3个月的数据）
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_logins_query = select(UserLoginRecord).where(
            UserLoginRecord.login_time >= today_start
        )
        today_logins = len(db.exec(today_logins_query).all())
        
        return {
            "total_logins": total_logins,
            "active_users": len(user_ids),
            "distinct_ips": len(ip_addresses),
            "today_logins": today_logins,
            "analysis_period_days": days
        }
        
    except Exception as e:
        logger.error(f"获取登录统计摘要失败: {e}")
        raise HTTPException(status_code=500, detail="统计失败")

@login_record_router.get("/login-records/my", response_model=List[LoginRecordResponse])
async def get_my_login_records(
    db: Session = Depends(get_db),
    current_user: dict = Security(get_current_user, scopes=get_required_scopes_for_route("/login-records/my")),
    query_params: MyLoginRecordQueryParams = Depends()
):
    """
    获取当前用户自己的登录记录
    
    权限要求: AUTH_OWN
    自动将查询条件限制为当前用户
    """
    try:
        # 获取当前用户信息
        username = current_user.get("username")
        user_id = current_user.get("id")
        if not username:
            # 如果username不存在，尝试使用user_id作为用户名
            if user_id:
                username = str(user_id)
            else:
                raise HTTPException(status_code=400, detail="用户信息不完整")
        
        # 如果user_id不存在，但username存在，可以继续处理
        # 因为核心查询函数会使用username进行过滤
        
        # 创建新的查询参数，强制设置当前用户信息
        # 使用LoginRecordQueryParams来包含用户名参数
        my_query_params = LoginRecordQueryParams(
            username=username,  # 固定为当前用户名
            ip_address=query_params.ip_address,  # 保留其他筛选条件
            start_time=query_params.start_time,
            end_time=query_params.end_time,
            search=query_params.search,
            page=query_params.page,
            page_size=query_params.page_size
        )
        
        # 调用 get_login_records 的核心查询逻辑，强制过滤当前用户ID
        paginated_result = await _get_login_records_core(db, my_query_params, force_user_id=user_id)
        
        logger.info(f"用户 {username} 查询自己的登录记录: "
                   f"页码={query_params.page}, 数量={len(paginated_result.records)}")
        
        return paginated_result.records
        
    except Exception as e:
        logger.error(f"获取用户登录记录失败: {e}")
        raise HTTPException(status_code=500, detail="查询失败")