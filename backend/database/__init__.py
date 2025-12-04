"""
数据库管理模块
包含主业务数据库和系统配置数据库的管理功能
"""

from .main_database import (
    get_engine, 
    get_db, 
    get_session, 
    init_db, 
    check_database_exists,
    set_database_url,
    get_database_url,
    create_database_engine
)

from .system_config_database import (
    get_system_config_engine,
    get_system_config_session,
    init_system_config_db,
    check_system_config_db_exists
)

# 导出所有函数
__all__ = [
    # 主数据库函数
    'get_engine',
    'get_db', 
    'get_session',
    'init_db',
    'check_database_exists',
    'set_database_url',
    'get_database_url',
    'create_database_engine',
    
    # 系统配置数据库函数
    'get_system_config_engine',
    'get_system_config_session',
    'init_system_config_db',
    'check_system_config_db_exists'
]