from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.all_routes import router
from database import get_engine, get_db, close_database
from contextlib import asynccontextmanager

from initialize.initialize_system import initialize_all, is_system_initialized
from core.font_config import setup_fonts_on_startup
from core.logging_config import get_logger
from backup.scheduled_backup import ScheduledBackupManager
from core.scheduler import Scheduler

# 获取应用程序日志记录器
logger = get_logger(__name__)

# 定义lifespan事件处理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 检查系统初始化状态并执行完整初始化
    logger.info("="*50)
    logger.info("应用程序启动中...")
    logger.info("="*50)
    try:
        # 从配置中加载数据库URL并设置
        from core.config import settings
        from database import set_database_url
        set_database_url(settings.DATABASE_URL)

        # 获取数据库引擎确保连接正常
        engine = get_engine()
        
        # 检查系统是否需要初始化
        if not is_system_initialized():
            # 系统未初始化时，执行完整初始化（包括数据库表创建）
            initialize_all()  # 初始化系统数据
        else:
            # 测试数据库连接
            db_gen = get_db()
            next(db_gen)  # 触发数据库连接测试
    except Exception as e:
        import traceback
        traceback.print_exc()
    
    # 初始化字体配置
    try:
        if setup_fonts_on_startup():
            pass
        else:
            pass
    except Exception as e:
        pass
    
    # 启动定时备份调度器（后台运行）
    backup_scheduler = None
    try:
        backup_scheduler = ScheduledBackupManager()
        backup_scheduler.start_scheduler(background=True)
    except Exception as e:
        logger.error(f"定时备份调度器启动异常: {e}")
    
    # 启动定时任务管理器（登录记录清理等）
    scheduler = None
    try:
        scheduler = Scheduler()
        await scheduler.start()
    except Exception as e:
        logger.error(f"定时任务管理器启动异常: {e}")
    
    # 程序运行中
    logger.info("="*50)
    logger.info("应用程序启动完成，开始接收请求")
    logger.info("="*50)
    yield
    
    # 关闭时执行的代码
    logger.info("="*50)
    logger.info("收到关闭信号，开始优雅关闭...")
    logger.info("="*50)
    # 停止定时备份调度器
    if backup_scheduler:
        try:
            logger.info("正在停止定时备份调度器...")
            backup_scheduler.stop_scheduler()
            logger.info("✓ 定时备份调度器已停止")
        except Exception as e:
            logger.error(f"停止定时备份调度器失败: {e}")
            
    # 停止定时任务管理器
    if scheduler:
        try:
            logger.info("正在停止定时任务管理器...")
            await scheduler.stop()
            logger.info("✓ 定时任务管理器已停止")
        except Exception as e:
            logger.error(f"停止定时任务管理器失败: {e}")
            
    # 关闭数据库引擎，执行 WAL checkpoint
    try:
        logger.info("正在关闭数据库引擎...")
        close_database()
        logger.info("✓ 数据库引擎已正常关闭")
    except Exception as e:
        logger.error(f"关闭数据库引擎失败: {e}")
        
    logger.info("="*50)
    logger.info("应用程序已完全关闭")
    logger.info("="*50)

# 创建FastAPI应用并传入lifespan参数
app = FastAPI(title="仓库管理系统", version="1.0", lifespan=lifespan)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许前端的源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

app.include_router(router)



if __name__ == "__main__":
    from core.server_config import start_server
    start_server()