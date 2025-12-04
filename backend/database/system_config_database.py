"""
系统配置数据库管理模块
独立于主业务数据库，专门存储系统配置信息
"""
import os
from sqlmodel import create_engine, SQLModel, Session, MetaData
from sqlalchemy import Table, Column, Integer, Boolean, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path
from datetime import datetime

# 系统配置数据库文件路径
SYSTEM_CONFIG_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "data", "system_config.db"
)

# 系统配置数据库连接URL
SYSTEM_CONFIG_DB_URL = f"sqlite:///{SYSTEM_CONFIG_DB_PATH}"

# 全局系统配置引擎
_system_config_engine = None

def get_system_config_engine():
    """获取系统配置数据库引擎"""
    global _system_config_engine
    if _system_config_engine is None:
        _system_config_engine = create_engine(
            SYSTEM_CONFIG_DB_URL,
            echo=False,  # 生产环境设为False
            connect_args={"check_same_thread": False}
        )
    return _system_config_engine

def get_system_config_session():
    """获取系统配置数据库会话"""
    return Session(get_system_config_engine())

def init_system_config_db():
    """初始化系统配置数据库"""
    # 确保数据库文件目录存在
    db_dir = os.path.dirname(SYSTEM_CONFIG_DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # 创建独立的metadata用于系统配置表
    system_config_metadata = MetaData()
    
    # 定义系统配置表结构（不使用SQLModel的全局metadata）
    system_init_table = Table(
        '_system_init', system_config_metadata,
        Column('id', Integer, primary_key=True),
        Column('initialized', Boolean, default=False),
        Column('init_time', DateTime, nullable=True),
        Column('init_version', String(50), nullable=True)
    )
    
    system_config_table = Table(
        '_system_config', system_config_metadata,
        Column('id', Integer, primary_key=True),
        Column('config_key', String(100), unique=True),
        Column('config_value', Text),
        Column('config_type', String(20), default='string'),
        Column('description', Text, nullable=True),
        Column('created_time', DateTime, default=datetime.now),
        Column('updated_time', DateTime, default=datetime.now),
        Column('is_active', Boolean, default=True)
    )
    
    # 只创建系统配置相关的表
    engine = get_system_config_engine()
    
    # 在创建表之前先清空数据库中的所有表格
    print("正在清空系统配置数据库中的所有表格和数据...")
    
    # 使用SQLite连接直接删除所有非系统配置表
    import sqlite3
    conn = sqlite3.connect(SYSTEM_CONFIG_DB_PATH)
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    # 只保留系统配置相关的表
    system_tables = ['_system_init', '_system_config']
    tables_to_delete = [table[0] for table in tables if table[0] not in system_tables]
    
    # 删除非系统配置表
    for table in tables_to_delete:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"✓ 已删除表: {table}")
        except Exception as e:
            print(f"⚠️ 删除表 {table} 失败: {e}")
    
    conn.commit()
    conn.close()
    
    print("✓ 系统配置数据库中的非系统配置表格已清空")
    
    # 使用独立的metadata创建系统配置表
    system_config_metadata.create_all(engine)
    
    print(f"✓ 系统配置数据库已重新初始化: {SYSTEM_CONFIG_DB_PATH}")

def check_system_config_db_exists():
    """检查系统配置数据库是否存在"""
    return os.path.exists(SYSTEM_CONFIG_DB_PATH)