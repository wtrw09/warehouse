"""
字体配置模块
系统启动时自动初始化字体管理器
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional

from utils.font_manager import init_font_manager, get_font_manager

logger = logging.getLogger(__name__)


class FontConfig:
    """字体配置类"""
    
    def __init__(self, font_dir: str = "fonts"):
        """
        初始化字体配置
        
        Args:
            font_dir: 字体目录路径
        """
        self.font_dir = Path(font_dir)
        self.font_manager = None
        self.is_initialized = False
    
    def initialize(self) -> bool:
        """初始化字体管理器"""
        try:
            # 检查字体目录是否存在
            if not self.font_dir.exists():
                # logger.warning(f"字体目录不存在: {self.font_dir}")
                # 创建字体目录
                self.font_dir.mkdir(parents=True, exist_ok=True)
                # logger.info(f"已创建字体目录: {self.font_dir}")
            
            # 初始化字体管理器
            self.font_manager = init_font_manager(str(self.font_dir))
            self.is_initialized = True
            
            # 记录初始化结果
            available_fonts = self.font_manager.get_available_fonts()
            # logger.info(f"字体管理器初始化完成，找到 {len(available_fonts)} 种字体")
            
            # 记录项目字体
            project_fonts = [name for name, font_type in available_fonts.items() 
                           if font_type == "项目字体"]
            if project_fonts:
                # logger.info(f"项目字体: {', '.join(project_fonts)}")
                pass
            return True
            
        except Exception as e:
            # logger.error(f"字体管理器初始化失败: {e}")
            self.is_initialized = False
            return False
    
    def get_font_manager(self):
        """获取字体管理器"""
        if not self.is_initialized:
            self.initialize()
        return self.font_manager
    
    def get_available_fonts(self) -> Dict[str, str]:
        """获取可用字体列表"""
        if not self.is_initialized:
            self.initialize()
        
        if self.font_manager:
            return self.font_manager.get_available_fonts()
        return {}
    
    def validate_font(self, font_name: str) -> bool:
        """验证字体是否可用"""
        if not self.is_initialized:
            self.initialize()
        
        if self.font_manager:
            return self.font_manager.get_font_path(font_name) is not None
        return False
    
    def get_recommended_fonts(self) -> Dict[str, str]:
        """获取推荐字体配置"""
        return {
            "title": "方正小标宋简体",
            "header": "黑体", 
            "body": "仿宋_GB2312",
            "table_header": "黑体",
            "table_body": "仿宋_GB2312",
            "signature": "楷体_GB2312"
        }
    
    def get_font_config(self, font_type: str) -> str:
        """
        根据字体类型获取字体名称
        
        Args:
            font_type: 字体类型 (title, header, body, table_header, table_body, signature)
            
        Returns:
            字体名称，如果找不到则返回默认字体
        """
        recommended_fonts = self.get_recommended_fonts()
        font_name = recommended_fonts.get(font_type, "仿宋_GB2312")
        
        # 验证字体是否可用
        if self.validate_font(font_name):
            return font_name
        
        # 如果推荐字体不可用，尝试备用字体
        backup_fonts = {
            "title": "黑体",
            "header": "黑体",
            "body": "仿宋_GB2312", 
            "table_header": "黑体",
            "table_body": "仿宋_GB2312",
            "signature": "仿宋_GB2312"
        }
        
        backup_font = backup_fonts.get(font_type, "仿宋_GB2312")
        if self.validate_font(backup_font):
            return backup_font
        
        # 如果备用字体也不可用，返回系统默认字体
        return "Arial"


# 全局字体配置实例
_font_config: Optional[FontConfig] = None


def init_font_config(font_dir: str = "fonts") -> FontConfig:
    """初始化全局字体配置"""
    global _font_config
    _font_config = FontConfig(font_dir)
    _font_config.initialize()
    return _font_config


def get_font_config() -> FontConfig:
    """获取全局字体配置"""
    global _font_config
    if _font_config is None:
        _font_config = FontConfig()
        _font_config.initialize()
    return _font_config


def setup_fonts_on_startup() -> bool:
    """系统启动时设置字体"""
    try:
        config = get_font_config()
        
        if config.is_initialized:
            # logger.info("字体系统启动完成")
            
            # 记录字体配置信息
            available_fonts = config.get_available_fonts()
            # logger.info(f"可用字体数量: {len(available_fonts)}")
            
            # 记录推荐字体状态
            recommended_fonts = config.get_recommended_fonts()
            for font_type, font_name in recommended_fonts.items():
                status = "✓" if config.validate_font(font_name) else "✗"
                # logger.info(f"推荐字体 [{font_type}]: {font_name} {status}")
            
            return True
        else:
            logger.error("字体系统启动失败")
            return False
            
    except Exception as e:
        logger.error(f"字体系统启动异常: {e}")
        return False