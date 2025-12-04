"""
全局日志配置模块
为整个应用程序提供统一的日志配置
"""

import logging
import logging.config
from pathlib import Path


def setup_global_logging():
    """设置全局日志配置"""
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 全局日志配置字典
    LOGGING_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'file_debug': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': str(log_dir / 'app_debug.log'),
                'encoding': 'utf-8',
                'mode': 'a'  # 改为追加模式，保留历史日志
            },
            'file_info': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'formatter': 'standard',
                'filename': str(log_dir / 'app_info.log'),
                'encoding': 'utf-8',
                'mode': 'a'  # 改为追加模式，保留历史日志
            },
            'file_error': {
                'class': 'logging.FileHandler',
                'level': 'ERROR',
                'formatter': 'standard',
                'filename': str(log_dir / 'app_error.log'),
                'encoding': 'utf-8',
                'mode': 'a'  # 改为追加模式，保留历史日志
            },
            'file_restore': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': str(log_dir / 'restore_processor.log'),
                'encoding': 'utf-8',
                'mode': 'a'  # 恢复日志保持追加模式，保留历史记录
            }
        },
        'loggers': {
            '': {  # 根日志记录器 - 捕获所有日志
                'level': 'DEBUG',
                'handlers': ['console', 'file_debug', 'file_info', 'file_error'],
                'propagate': True
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console', 'file_info'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'INFO',
                'handlers': ['console', 'file_info'],
                'propagate': False
            },
            'backup.restore_processor': {
                'level': 'DEBUG',
                'handlers': ['console', 'file_restore', 'file_debug'],
                'propagate': False
            },
            'backup': {
                'level': 'DEBUG',
                'handlers': ['console', 'file_debug', 'file_info'],
                'propagate': False
            },
            'routes': {
                'level': 'INFO',
                'handlers': ['console', 'file_info'],
                'propagate': False
            },
            'database': {
                'level': 'INFO',
                'handlers': ['console', 'file_info'],
                'propagate': False
            },
            'core': {
                'level': 'INFO',
                'handlers': ['console', 'file_info'],
                'propagate': False
            }
        }
    }
    
    # 应用全局日志配置
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # 获取根日志记录器并记录初始化信息
    root_logger = logging.getLogger()
    root_logger.info("全局日志配置已初始化")
    
    return root_logger


def get_logger(name: str):
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    return logging.getLogger(name)


# 模块导入时自动设置全局日志配置
setup_global_logging()

# 提供默认的日志记录器
logger = get_logger(__name__)


if __name__ == "__main__":
    # 测试日志配置
    test_logger = get_logger("test_module")
    test_logger.debug("调试信息测试")
    test_logger.info("信息级别测试")
    test_logger.warning("警告级别测试")
    test_logger.error("错误级别测试")
    
    print("日志配置测试完成，请检查 logs/ 目录下的日志文件")