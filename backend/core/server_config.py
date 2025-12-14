"""
服务器配置模块
统一管理FastAPI服务器的启动参数，便于主程序和恢复模块使用相同的配置
"""

import os
from typing import Dict, Any


class ServerConfig:
    """服务器配置类"""
    
    def __init__(self):
        # 默认配置（生产环境）
        self._config = {
            "app_module": "main:app",
            "host": "0.0.0.0",
            "port": 8000,
            "log_level": "info",
            "reload": False,
            "workers": 1,
            "access_log": True
        }
        
        # 从环境变量加载配置（Docker部署时使用）
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mappings = {
            "HOST": "host",
            "PORT": "port",
            "LOG_LEVEL": "log_level",
            "RELOAD": "reload",
            "WORKERS": "workers",
            "ACCESS_LOG": "access_log"
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # 类型转换
                if config_key in ["port", "workers"]:
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif config_key in ["reload", "access_log"]:
                    value = value.lower() in ["true", "1", "yes"]
                
                self._config[config_key] = value
    
    def get_uvicorn_args(self) -> Dict[str, Any]:
        """获取uvicorn启动参数"""
        return {
            "app": self._config["app_module"],
            "host": self._config["host"],
            "port": self._config["port"],
            "log_level": self._config["log_level"],
            "reload": self._config["reload"],
            "workers": self._config["workers"],
            "access_log": self._config["access_log"]
        }
    
    def get_subprocess_args(self) -> list:
        """获取子进程启动参数（用于恢复模块）"""
        args = [
            "-m", "uvicorn",
            self._config["app_module"],
            "--host", self._config["host"],
            "--port", str(self._config["port"]),
            "--log-level", self._config["log_level"]
        ]
        
        if self._config["reload"]:
            args.append("--reload")
        
        if self._config["workers"] > 1:
            args.extend(["--workers", str(self._config["workers"])])
        
        if not self._config["access_log"]:
            args.append("--no-access-log")
        
        return args
    
    def get_config_dict(self) -> Dict[str, Any]:
        """获取完整的配置字典"""
        return self._config.copy()
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if key in self._config:
                self._config[key] = value


# 创建全局配置实例
server_config = ServerConfig()


def get_server_config() -> ServerConfig:
    """获取服务器配置实例"""
    return server_config


def start_server():
    """启动服务器（用于主程序）"""
    import uvicorn
    from core.logging_config import get_logger
    
    config = get_server_config()
    uvicorn_args = config.get_uvicorn_args()
    
    # 获取日志记录器
    logger = get_logger(__name__)
    
    logger.info(f"启动服务器配置:")
    logger.info(f"  应用模块: {uvicorn_args['app']}")
    logger.info(f"  主机地址: {uvicorn_args['host']}")
    logger.info(f"  端口号: {uvicorn_args['port']}")
    logger.info(f"  日志级别: {uvicorn_args['log_level']}")
    logger.info(f"  热重载: {uvicorn_args['reload']}")
    logger.info(f"  工作进程数: {uvicorn_args['workers']}")
    logger.info(f"  访问日志: {uvicorn_args['access_log']}")
    
    uvicorn.run(**uvicorn_args)


if __name__ == "__main__":
    # 测试配置
    config = get_server_config()
    print("当前服务器配置:")
    for key, value in config.get_config_dict().items():
        print(f"  {key}: {value}")
    
    print("\n子进程启动参数:")
    print(config.get_subprocess_args())