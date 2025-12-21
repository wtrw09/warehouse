from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import event
import os
from typing import Generator

# 默认数据库URL（避免循环导入）
DEFAULT_DATABASE_URL = "sqlite:///./data/warehouse.db"

# 全局引擎实例（延迟创建）
_engine = None
_database_url = None

def set_database_url(url: str):
    """设置数据库URL（用于动态配置）"""
    global _database_url, _engine
    _database_url = url
    # 如果引擎已创建，需要重置它
    _engine = None
    print(f"[DEBUG] 数据库URL已更新: {url}")

def get_database_url() -> str:
    """获取数据库URL"""
    global _database_url
    
    # 如果已设置URL，直接返回
    if _database_url:
        return _database_url
    
    # 首次访问时，使用默认值
    # 注意：不在这里从 core.config 加载，避免循环导入
    # 配置应该在系统启动后主动调用 set_database_url() 设置
    print(f"[DEBUG] 使用默认数据库URL: {DEFAULT_DATABASE_URL}")
    _database_url = DEFAULT_DATABASE_URL
    return _database_url

def _configure_sqlite_wal(dbapi_conn, connection_record):
    """配置SQLite WAL模式的回调函数"""
    cursor = dbapi_conn.cursor()
    
    # 启用WAL模式
    cursor.execute("PRAGMA journal_mode=WAL;")
    result = cursor.fetchone()
    
    # 配置WAL相关参数
    cursor.execute("PRAGMA wal_autocheckpoint=1000;")  # 每1000页自动检查点
    cursor.execute("PRAGMA synchronous=NORMAL;")  # 平衡性能和数据安全
    cursor.execute("PRAGMA cache_size=-102400;")  # 缓存大小100MB
    
    cursor.close()
    
    # 只在首次配置时输出日志
    if result and result[0].upper() != 'WAL':
        print(f"[INFO] SQLite WAL模式已启用: {result[0]}")

def create_database_engine():
    """创建数据库引擎"""
    database_url = get_database_url()
    print(f"[DEBUG] 创建数据库引擎: {database_url}")
    
    # 配置SQLite连接参数
    connect_args = {
        "check_same_thread": False,  # 允许多线程访问
        "timeout": 30,  # 连接超时时间（秒）
        "isolation_level": None,  # 自动提交模式
    }
    
    engine = create_engine(
        database_url, 
        echo=False,  # 关闭SQL日志输出，提升性能
        connect_args=connect_args
    )
    
    # 注册连接事件监听器，自动配置WAL模式
    event.listen(engine, "connect", _configure_sqlite_wal)
    print(f"[INFO] 已注册SQLite WAL模式自动配置")
    
    return engine

def get_engine():
    """获取数据库引擎实例（延迟创建）"""
    global _engine
    if _engine is None:
        _engine = create_database_engine()
        print(f"[DEBUG] 数据库引擎已创建")
    return _engine

def check_database_exists() -> bool:
    """检查数据库文件是否存在"""
    engine = get_engine()
    db_url = engine.url.database
    
    # 处理None的情况
    if db_url is None:
        print(f"[WARNING] 无法获取数据库URL")
        return False
    
    # 如果是相对路径，转换为绝对路径
    if not os.path.isabs(db_url):
        # 获取项目根目录（上一级目录）
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, db_url)
        db_path = os.path.normpath(db_path)
    else:
        db_path = db_url
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"[WARNING] 数据库文件不存在: {db_path}")
        print(f"[INFO] 当前工作目录: {os.getcwd()}")
        return False
    
    print(f"[INFO] 数据库文件存在: {db_path}")
    return True

def init_db():
    """初始化数据库，创建所有表"""
    engine = get_engine()
    print(f"[DEBUG] 开始创建数据库表...")
    #删除所有表
    SQLModel.metadata.drop_all(engine)
    print(f"[DEBUG] 所有数据库表已删除")
    # 创建业务相关的元数据，排除系统配置表
    from sqlmodel import MetaData
    from models import (
        Permission, Role, User, RolePermissionLink,
        Bin, Customer, Equipment, Major, SubMajor, Supplier, Warehouse,
        InboundOrder, InboundOrderItem, InventoryBatch, InventoryDetail, InventoryTransaction, Material, OutboundOrder, OutboundOrderItem,
        MaterialCodeLevel, SystemInit
    )
    from models.account.user_login_record import UserLoginRecord, UserLoginHistory
    
    # 创建新的元数据对象，只包含业务表
    business_metadata = MetaData()
    
    # 将业务模型添加到元数据中
    for model in [
        Permission, Role, User, RolePermissionLink,
        Bin, Customer, Equipment, Major, SubMajor, Supplier, Warehouse,
        InboundOrder, InboundOrderItem, InventoryBatch, InventoryDetail, InventoryTransaction, Material, OutboundOrder, OutboundOrderItem,
        MaterialCodeLevel, SystemInit, UserLoginRecord, UserLoginHistory
    ]:
        if hasattr(model, '__table__'):
            model.__table__.tometadata(business_metadata)
    
    # 只创建业务表
    business_metadata.create_all(engine)
    print(f"[DEBUG] 数据库表创建完成")

def get_db() -> Generator[Session, None, None]:
    """依赖项：获取数据库会话"""
    engine = get_engine()
    with Session(engine) as session:
        yield session

def get_session() -> Session:
    """获取数据库会话（非依赖注入方式）"""
    engine = get_engine()
    return Session(engine)