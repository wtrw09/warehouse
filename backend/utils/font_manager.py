"""
字体管理器模块
负责管理项目字体文件，支持自定义字体和系统字体
"""
import os
import platform
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FontManager:
    """字体管理器类"""
    
    def __init__(self, font_dir: str = "fonts"):
        """
        初始化字体管理器
        
        Args:
            font_dir: 字体文件目录路径
        """
        self.font_dir = Path(font_dir)
        self.project_fonts: Dict[str, str] = {}  # 字体名: 文件路径
        self.system_fonts: Dict[str, str] = {}  # 字体名: 文件路径
        
        # 初始化字体映射
        self.font_mapping = {
            "仿宋": "仿宋_GB2312",
            "楷体": "楷体_GB2312", 
            "黑体": "黑体",
            "方正小标宋": "方正小标宋简体",
            "宋体": "SimSun",
            "微软雅黑": "Microsoft YaHei",
            "Arial": "Arial",
            "Times New Roman": "Times New Roman",
            "Helvetica": "Helvetica"
        }
        
        self._load_project_fonts()
        self._scan_system_fonts()
    
    def _load_project_fonts(self) -> None:
        """加载项目字体文件"""
        if not self.font_dir.exists():
            logger.warning(f"字体目录不存在: {self.font_dir}")
            return
        
        # 支持的字体文件扩展名
        font_extensions = {'.ttf', '.otf', '.ttc'}
        
        for font_file in self.font_dir.iterdir():
            if font_file.is_file() and font_file.suffix.lower() in font_extensions:
                font_name = font_file.stem  # 去掉扩展名的文件名
                self.project_fonts[font_name] = str(font_file.absolute())
                # logger.info(f"加载项目字体: {font_name} -> {font_file}")
    
    def _scan_system_fonts(self) -> None:
        """扫描系统字体"""
        system = platform.system()
        
        if system == "Windows":
            self._scan_windows_fonts()
        elif system == "Darwin":  # macOS
            self._scan_macos_fonts()
        elif system == "Linux":
            self._scan_linux_fonts()
        else:
            logger.warning(f"不支持的操作系统: {system}")
    
    def _scan_windows_fonts(self) -> None:
        """扫描Windows系统字体"""
        font_dirs = [
            Path("C:/Windows/Fonts"),
            Path(os.environ.get('LOCALAPPDATA', 'C:/Users')) / "Microsoft" / "Windows" / "Fonts"
        ]
        
        for font_dir in font_dirs:
            if font_dir.exists():
                for font_file in font_dir.iterdir():
                    if font_file.is_file() and font_file.suffix.lower() in {'.ttf', '.otf'}:
                        font_name = font_file.stem
                        self.system_fonts[font_name] = str(font_file.absolute())
    
    def _scan_macos_fonts(self) -> None:
        """扫描macOS系统字体"""
        font_dirs = [
            Path("/Library/Fonts"),
            Path("/System/Library/Fonts"),
            Path.home() / "Library" / "Fonts"
        ]
        
        for font_dir in font_dirs:
            if font_dir.exists():
                for font_file in font_dir.iterdir():
                    if font_file.is_file() and font_file.suffix.lower() in {'.ttf', '.otf'}:
                        font_name = font_file.stem
                        self.system_fonts[font_name] = str(font_file.absolute())
    
    def _scan_linux_fonts(self) -> None:
        """扫描Linux系统字体"""
        font_dirs = [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".local" / "share" / "fonts"
        ]
        
        for font_dir in font_dirs:
            if font_dir.exists():
                for font_file in font_dir.rglob("*"):
                    if font_file.is_file() and font_file.suffix.lower() in {'.ttf', '.otf'}:
                        font_name = font_file.stem
                        self.system_fonts[font_name] = str(font_file.absolute())
    
    def get_font_path(self, font_name: str) -> Optional[str]:
        """
        获取字体文件路径，优先使用项目字体
        
        Args:
            font_name: 字体名称
            
        Returns:
            字体文件路径，如果找不到返回None
        """
        # 首先尝试字体映射
        mapped_name = self.font_mapping.get(font_name, font_name)
        
        # 优先在项目字体中查找
        for name, path in self.project_fonts.items():
            if mapped_name.lower() in name.lower() or name.lower() in mapped_name.lower():
                # logger.info(f"使用项目字体: {name} -> {path}")
                return path
        
        # 然后在系统字体中查找
        for name, path in self.system_fonts.items():
            if mapped_name.lower() in name.lower() or name.lower() in mapped_name.lower():
                # logger.info(f"使用系统字体: {name} -> {path}")
                return path
        
        logger.warning(f"未找到字体: {font_name}")
        return None
    
    def get_available_fonts(self) -> Dict[str, str]:
        """
        获取所有可用的字体列表
        
        Returns:
            字体名称到类型的映射
        """
        available_fonts = {}
        
        # 添加项目字体
        for font_name in self.project_fonts.keys():
            available_fonts[font_name] = "项目字体"
        
        # 添加系统字体
        for font_name in self.system_fonts.keys():
            if font_name not in available_fonts:  # 避免重复
                available_fonts[font_name] = "系统字体"
        
        return available_fonts
    
    def add_font_to_fpdf(self, fpdf_obj, font_name: str, alias: str = None) -> bool:
        """
        将字体添加到FPDF对象
        
        Args:
            fpdf_obj: FPDF对象
            font_name: 字体名称
            alias: 字体别名
            
        Returns:
            是否成功添加
        """
        font_path = self.get_font_path(font_name)
        if not font_path:
            return False
        
        try:
            # 添加常规字体
            if alias:
                fpdf_obj.add_font(family=alias, fname=font_path, uni=True)
            else:
                fpdf_obj.add_font(family=font_name, fname=font_path, uni=True)
            
            # 添加粗体字体（使用相同字体文件）
            if alias:
                fpdf_obj.add_font(family=alias, style='B', fname=font_path, uni=True)
            else:
                fpdf_obj.add_font(family=font_name, style='B', fname=font_path, uni=True)
                
            return True
        except Exception as e:
            logger.error(f"添加字体失败 {font_name}: {e}")
            return False


# 全局字体管理器实例
_font_manager: Optional[FontManager] = None


def get_font_manager() -> FontManager:
    """获取全局字体管理器实例"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager


def init_font_manager(font_dir: str = "fonts") -> FontManager:
    """初始化字体管理器"""
    global _font_manager
    _font_manager = FontManager(font_dir)
    return _font_manager