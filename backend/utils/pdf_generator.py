"""
PDF生成器模块
基于FPDF2的PDF生成工具，集成字体管理功能
"""
from fpdf import FPDF
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
from datetime import datetime

from .font_manager import get_font_manager

logger = logging.getLogger(__name__)


class PDFGenerator(FPDF):
    """PDF生成器类，继承自FPDF"""
    
    def __init__(self, orientation='P', unit='mm', format='A4'):
        """初始化PDF生成器"""
        super().__init__(orientation=orientation, unit=unit, format=format)
        
        # 启用Unicode支持
        self.set_auto_page_break(auto=True, margin=15)
        
        self.font_manager = get_font_manager()
        self.default_fonts = {
            'title': '方正小标宋简体',
            'header': '黑体',
            'body': '仿宋_GB2312',
            'table_header': '黑体',
            'table_body': '仿宋_GB2312'
        }
        self._setup_fonts()
    
    def _setup_fonts(self) -> None:
        """设置默认字体"""
        # 添加项目字体
        for font_name in ['方正小标宋简体', '黑体', '仿宋_GB2312', '楷体_GB2312']:
            self.font_manager.add_font_to_fpdf(self, font_name)
    
    def set_font_by_name(self, font_name: str, size: int = 12, style: str = '') -> bool:
        """
        根据字体名称设置字体
        
        Args:
            font_name: 字体名称
            size: 字体大小
            style: 字体样式
            
        Returns:
            是否设置成功
        """
        try:
            # 首先尝试直接设置字体（如果已添加）
            self.set_font(font_name, style, size)
            return True
        except:
            # 如果字体未添加，先添加再使用
            try:
                if self.font_manager.add_font_to_fpdf(self, font_name):
                    self.set_font(font_name, style, size)
                    return True
            except Exception as e:
                logger.warning(f"字体设置失败 {font_name}: {e}")
        
        # 如果自定义字体失败，使用默认字体
        logger.warning(f"字体设置失败，使用默认字体: {font_name}")
        try:
            self.set_font('Arial', style, size)
            return True
        except:
            # 如果Arial也失败，使用内置字体
            self.set_font('helvetica', style, size)
            return True
    
    def header(self) -> None:
        """页眉设置"""
        # 空实现，子类可以重写
        pass
    
    def footer(self) -> None:
        """页脚设置"""
        # 空实现，子类可以重写
        pass


class InboundOrderPDF(PDFGenerator):
    """入库单PDF生成器"""
    
    def __init__(self):
        super().__init__()
        # 设置自动分页边距为15mm，以适应新的页脚高度
        self.set_auto_page_break(auto=True, margin=15)
        # 启用总页数计算功能
        self.alias_nb_pages()
        self.order_data = None
        self.items_data = None
        self.total_amount = 0.0
    
    def set_order_data(self, order_data: Dict[str, Any]) -> None:
        """设置订单数据"""
        self.order_data = order_data
    
    def set_items_data(self, items_data: List[Dict[str, Any]]) -> None:
        """设置物品数据"""
        self.items_data = items_data
        # 计算总金额
        self.total_amount = sum(item.get('amount', 0.0) for item in items_data)
    
    def header(self) -> None:
        """入库单页眉"""
        if self.page_no() == 1:
            # 第一页显示标题
            self.set_font_by_name(self.default_fonts['title'], 16, 'B')
            self.cell(0, 10, '入库单', 0, 1, 'C')
            
            # 单位信息 - 设置合适的右对齐位置，距离右边距20mm
            self.set_font_by_name(self.default_fonts['body'], 10)
            self.set_x(210 - 60)  # A4纸宽度210mm，距离右边40mm
            self.cell(30, 6, '金额单位：元', 0, 1, 'R')
            self.ln(5)
            
            # 订单基本信息
            self._add_order_header()
        else:
            # 后续页面只显示表头
            self._add_table_header()
    
    def footer(self) -> None:
        """页脚"""
        # 设置页脚区域高度为15mm，只包含页码
        self.set_y(-15)  # 距离页面底部15mm
        
        # 添加页码
        self.set_font_by_name(self.default_fonts['body'], 8)
        self.cell(0, 10, f'第 {self.page_no()} 页 / 共 {{nb}} 页', 0, 0, 'C')
    
    def generate_inbound_order(self, filename: str) -> bool:
        """生成入库单PDF"""
        try:
            self.add_page()
            
            # 注意：header()方法已经调用了_add_order_header()，这里不需要重复调用
            # 直接添加物品表格
            self._add_items_table()
            
            # 在所有物品数据添加完成后，在最后一页添加合计行和签字区域
            self._add_total_row()
            self._add_signature_area()
            
            self.output(filename)
            return True
            
        except Exception as e:
            logger.error(f"生成入库单PDF失败: {e}")
            return False
    
    def _add_order_header(self) -> None:
        """添加订单基本信息头"""
        if not self.order_data:
            return
        
        self.set_font_by_name(self.default_fonts['header'], 10)
        
        # 订单基本信息行 - 增加列宽避免重叠
        col_widths = [60, 80, 40]
        
        order_info = [
            f"入库单号：{self.order_data.get('order_number', '')}",
            f"供应商：{self.order_data.get('supplier', '')}",
            f"入库日期：{self.order_data.get('inbound_date', '')}"
        ]
        
        # 居中对齐
        total_width = sum(col_widths)
        x_start = (210 - total_width) / 2  # A4纸宽度210mm
        self.set_x(x_start)
        
        for i, info in enumerate(order_info):
            self.cell(col_widths[i], 8, info, 0, 0, 'L')
        self.ln(10)
    
    def _add_table_header(self) -> None:
        """添加表格表头"""
        # 表格列定义 - 增加列宽以充分利用页面宽度
        headers = ['序号', '器材编码', '器材名称', '器材规格', '单位', '数量', '单价', '金额', '备注']
        col_widths = self._get_table_col_widths()
        
        # 表格居中对齐
        total_width = sum(col_widths)
        x_start = (210 - total_width) / 2  # A4纸宽度210mm
        self.set_x(x_start)
        
        # 表头 - 使用智能换行逻辑，参考单元格换行实现
        self.set_font_by_name(self.default_fonts['table_header'], 10, 'B')
        
        # 计算表头行高度（基于最长表头文本）
        max_lines = 1
        for i, header in enumerate(headers):
            text = str(header)
            if len(text) > 0:
                # 使用get_string_width精确计算文本宽度
                text_width = self.get_string_width(text)
                cell_width = col_widths[i] - 2  # 减去单元格边距
                
                # 计算需要的行数
                if text_width > cell_width:
                    lines = (text_width + cell_width - 1) // cell_width
                    max_lines = max(max_lines, min(lines, 2))  # 最多显示2行
        
        # 表头行高 = 基础行高 + (行数-1) * 行间距
        header_row_height = 8 + (max_lines - 1) * 6
        
        for i, header in enumerate(headers):
            text = str(header)
            
            # 使用get_string_width精确计算文本宽度
            text_width = self.get_string_width(text)
            cell_width = col_widths[i] - 2  # 减去单元格边距
            
            # 如果文本宽度超过单元格宽度，进行换行处理
            if text_width > cell_width:
                # 计算需要的行数
                lines = (text_width + cell_width - 1) // cell_width
                lines = min(lines, 2)  # 最多显示2行
                
                if lines == 1:
                    # 单行显示
                    self.cell(col_widths[i], header_row_height, text, 1, 0, 'C')
                else:
                    # 多行显示 - 使用智能文本截取方法
                    # 基于字符宽度进行精确截取
                    avg_char_width = text_width / len(text)
                    chars_per_line = int(cell_width / avg_char_width)
                    
                    # 确保每行至少显示1个字符
                    chars_per_line = max(1, chars_per_line)
                    
                    # 第一行显示
                    first_line = text[:chars_per_line]
                    # 第二行显示剩余部分（最多显示相同字符数）
                    second_line = text[chars_per_line:chars_per_line * 2]
                    
                    # 保存当前位置
                    current_x = self.get_x()
                    current_y = self.get_y()
                    
                    # 绘制第一行（上边框和左右边框）
                    self.cell(col_widths[i], 8, first_line, 'LTR', 2, 'C')
                    # 移动到第二行位置（减去边框重叠部分，确保单元格对齐）
                    self.set_xy(current_x, current_y + 6)
                    # 绘制第二行（下边框和左右边框）
                    self.cell(col_widths[i], 8, second_line, 'LBR', 0, 'C')
                    # 恢复位置
                    self.set_xy(current_x + col_widths[i], current_y)
            else:
                # 单行显示
                self.cell(col_widths[i], header_row_height, text, 1, 0, 'C')
        
        # 移动到下一行
        self.ln()
    
    def _add_items_table(self) -> None:
        """添加物品表格"""
        if not self.items_data:
            return
        
        # 表格列定义
        headers = ['序号', '器材编码', '器材名称', '器材规格', '单位', '数量', '单价', '金额', '备注']
        col_widths = self._get_table_col_widths()
        
        # 添加表头（仅在第一页，因为header()方法会自动处理后续页）
        if self.page_no() == 1:
            self._add_table_header()
        
        # 表格内容
        self.set_font_by_name(self.default_fonts['table_body'], 10)
        
        for idx, item in enumerate(self.items_data, 1):
            # 表格居中对齐
            total_width = sum(col_widths)
            x_start = (210 - total_width) / 2  # A4纸宽度210mm
            self.set_x(x_start)
            
            row = [
                str(idx),
                item.get('material_code', ''),
                item.get('material_name', ''),
                item.get('specification', ''),
                item.get('unit', ''),
                str(item.get('quantity', 0)),
                f"{item.get('unit_price', 0):.2f}",
                f"{item.get('amount', 0):.2f}",
                item.get('remark', '')
            ]
            
            # 先计算该行中所有单元格的最大行数
            max_lines = 1
            for i, cell in enumerate(row):
                text = str(cell)
                text_width = self.get_string_width(text)
                # 使用当前单元格的实际宽度计算
                cell_width = col_widths[i] - 2  # 减去单元格边距
                
                if text_width > cell_width:
                    # 计算需要的行数
                    lines = (text_width + cell_width - 1) // cell_width
                    lines = min(lines, 2)  # 最多显示2行
                    max_lines = max(max_lines, lines)
            
            # 根据文字数量确定行高：如果文字需要显示两行，则高度为16，否则为8
            row_height = 16 if max_lines > 1 else 8
            
            # 检查是否需要换页（使用FPDF自动分页功能）
            # 在换页之前，先检查当前页面是否有足够的空间显示当前行和签字区域
            # 签字区域高度约为18mm（5mm空行 + 8mm签字行 + 5mm空行）
            signature_area_height = 18
            if self.get_y() + row_height + signature_area_height > 297 - 15:  # A4纸高度297mm，底部边距15mm
                # 当前页面空间不足，先添加签字区域再换页
                self._add_signature_area_for_page()
                self.add_page()
                # 注意：add_page()会自动调用header()方法，header()中会添加表头
                # 重新设置表格内容字体
                self.set_font_by_name(self.default_fonts['table_body'], 10)
                # 重新设置起始位置（与出库单保持一致）
                self.set_x(x_start)
            
            # 使用cell绘制单元格，支持精确换行控制
            for i, cell in enumerate(row):
                text = str(cell)
                
                # 使用get_string_width精确计算文本宽度
                text_width = self.get_string_width(text)
                cell_width = col_widths[i] - 2  # 减去单元格边距
                
                # 如果文本宽度超过单元格宽度，进行换行处理
                if text_width > cell_width:
                    # 计算需要的行数
                    lines = (text_width + cell_width - 1) // cell_width
                    lines = min(lines, 2)  # 最多显示2行
                    
                    if lines == 1:
                        # 单行显示
                        self.cell(col_widths[i], row_height, text, 1, 0, 'C')
                    else:
                        # 计算每行大致能容纳的字符数（基于平均字符宽度）
                        avg_char_width = text_width / len(text)
                        chars_per_line = int(cell_width / avg_char_width)
                        
                        # 确保每行至少显示1个字符
                        chars_per_line = max(1, chars_per_line)
                        
                        # 第一行显示
                        first_line = text[:chars_per_line]
                        # 第二行显示剩余部分（最多显示相同字符数）
                        second_line = text[chars_per_line:chars_per_line * 2]
                        
                        # 保存当前位置
                        current_x = self.get_x()
                        current_y = self.get_y()
                        
                        # 绘制第一行（上边框和左右边框）
                        self.cell(col_widths[i], 8, first_line, 'LTR', 2, 'C')
                        # 移动到第二行位置（减去边框重叠部分，确保单元格对齐）
                        self.set_xy(current_x, current_y + 8)
                        # 绘制第二行（下边框和左右边框）
                        self.cell(col_widths[i], 8, second_line, 'LBR', 0, 'C')
                        # 恢复位置到下一列，但Y坐标保持在当前行的起始位置
                        self.set_xy(current_x + col_widths[i], current_y)
                else:
                    # 单行显示
                    self.cell(col_widths[i], row_height, text, 1, 0, 'C')
            
            # 移动到下一行，使用row_height确保正确的行高
            self.set_y(self.get_y() + row_height)
    
    def _get_table_col_widths(self) -> list:
        """获取表格列宽定义"""
        # 统一的列宽定义：序号,器材编码,器材名称,器材规格,单位,数量,单价,金额,备注
        return [12, 25, 30, 30, 12, 12, 18, 22, 15]
    
    def _add_total_row(self) -> None:
        """添加合计行并确保签字行空间"""
        # 计算所需空间：合计行(2行) + 签字行
        total_row_height = 12 * 2 + 5  # 2行合计行 + 5mm间距
        signature_row_height = 25  # 签字行高度，增加余量确保完整显示
        required_space = total_row_height + signature_row_height
        
        # 检查当前页剩余空间是否足够容纳合计行和签字行
        if self.get_y() + required_space > 297 - 15:  # A4纸高度297mm，底部边距15mm
            # 添加当前页签字行
            self._add_signature_area_for_page()
            # 新建页面
            self.add_page()
            # 重置字体样式
            self.set_font_by_name(self.default_fonts['table_header'], 10, 'B')
        
        # 添加合计行
        # 使用与物品表格相同的列宽定义
        col_widths = self._get_table_col_widths()
        
        # 使用与物品表格相同的居中对齐计算
        total_width = sum(col_widths)
        x_start = (210 - total_width) / 2  # A4纸宽度210mm
        
        # 第一行：合计和金额信息
        self.set_x(x_start)  # 设置正确的起始位置
        
        # 将金额转换为中文大写
        amount_chinese = self._amount_to_chinese(self.total_amount)
        
        # 单元格1："合计"
        self.cell(col_widths[0], 12, '合计', 1, 0, 'C')
        
        # 合并单元格2-7：人民币（大写）+ 金额中文大写
        merged_width_2_7 = sum(col_widths[1:7])
        self.cell(merged_width_2_7, 12, f'人民币（大写）{amount_chinese}', 1, 0, 'L')
        
        # 合并单元格8-9：（小写）+ 金额数字
        merged_width_8_9 = sum(col_widths[7:9])
        self.cell(merged_width_8_9, 12, f'（小写）{self.total_amount:.2f}', 1, 0, 'L')
        
        self.ln()
        
        # 第二行：备注
        self.set_x(x_start)  # 设置正确的起始位置，与第一行对齐
        
        # 单元格1："备注"
        self.cell(col_widths[0], 12, '备注', 1, 0, 'C')
        
        # 合并单元格2-9：空内容
        merged_width_2_9 = sum(col_widths[1:9])
        self.cell(merged_width_2_9, 12, '', 1, 0, 'C')
        
        self.ln()
    
    def _add_signature_area_for_page(self) -> None:
        # 签字位置 - 在表格下一行
        self.ln(5)  # 空一行，减少间距
        
        # 签字行：审批人、经办人、保管员
        col_widths = [60, 60, 60]
        sign_labels = ['审批人：', '经办人：', '保管员：']
        
        total_width = sum(col_widths)
        x_start = (210 - total_width) / 2  # A4纸宽度210mm
        self.set_x(x_start)
        
        self.set_font_by_name(self.default_fonts['body'], 10)
        for i, label in enumerate(sign_labels):
            self.cell(col_widths[i], 8, label, 0, 0, 'L')
        self.ln(5)  # 减少空行间距
    
    def _add_signature_area(self) -> None:
        """添加签字位置（最后一页使用）"""
        # 签字位置 - 在表格下一行
        self.ln(10)  # 空一行
        
        # 签字行：审批人、经办人、保管员
        col_widths = [60, 60, 60]
        sign_labels = ['审批人：', '经办人：', '保管员：']
        
        total_width = sum(col_widths)
        x_start = (210 - total_width) / 2  # A4纸宽度210mm
        self.set_x(x_start)
        
        self.set_font_by_name(self.default_fonts['body'], 10)
        for i, label in enumerate(sign_labels):
            self.cell(col_widths[i], 8, label, 0, 0, 'L')
        self.ln(10)
    
    def _amount_to_chinese(self, amount: float) -> str:
        """将金额转换为中文大写"""
        # 使用与出库单相同的金额转换逻辑
        if amount == 0:
            return "零元整"
        
        # 这里可以扩展更完整的金额转换逻辑
        # 目前使用简化版本
        integer_part = int(amount)
        decimal_part = round((amount - integer_part) * 100)
        
        chinese_digits = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
        chinese_units = ['', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿']
        
        result = ''
        
        # 整数部分转换
        if integer_part > 0:
            integer_str = str(integer_part)
            for i, digit in enumerate(integer_str):
                digit_int = int(digit)
                unit_index = len(integer_str) - i - 1
                result += chinese_digits[digit_int] + chinese_units[unit_index]
            result += '元'
        
        # 小数部分转换
        if decimal_part > 0:
            if decimal_part < 10:
                result += chinese_digits[decimal_part] + '角'
            else:
                jiao = decimal_part // 10
                fen = decimal_part % 10
                result += chinese_digits[jiao] + '角'
                if fen > 0:
                    result += chinese_digits[fen] + '分'
        else:
            result += '整'
        
        return result


class MaterialLedgerPDF(PDFGenerator):
    """器材分类账页PDF生成器"""
    
    def __init__(self):
        # 使用A4横向页面，左边距30mm，其他边距15mm
        super().__init__(orientation='L', unit='mm', format='A4')
        
        # 设置页面边距（左边距30mm足够大，后续布局使用相对边距坐标）
        self.set_margins(left=30, top=10, right=10)
        self.set_auto_page_break(auto=True, margin=15)
        
        self.order_data = None
        self.material_items = []
        self.creator_department = ""
    
    def set_inbound_order_data(self, order_data: Dict[str, Any]) -> None:
        """设置入库单数据"""
        self.order_data = order_data
    
    def set_material_items(self, items: List[Dict[str, Any]]) -> None:
        """设置器材明细数据"""
        self.material_items = items
    
    def set_creator_department(self, department: str) -> None:
        """设置保管单位"""
        self.creator_department = department
    
    def generate_material_ledger(self, filename: str) -> bool:
        """生成器材分类账页PDF（每个器材输出两页）"""
        try:
            # 为每个器材生成两页账页
            for idx, material_item in enumerate(self.material_items):
                # 每个器材都生成两页
                if idx == 0:
                    # 第一个器材：创建第一页（奇数页，左边距30，右边距10）
                    self.add_page()
                    # 设置第一页边距
                    self.set_margins(left=30, top=10, right=10)
                else:
                    # 后续器材：创建新页（第一页，奇数页，左边距30，右边距10）
                    self.add_page()
                    # 设置第一页边距
                    self.set_margins(left=30, top=10, right=10)
                
                # 第一页：基本信息表格 + 6行出库记录
                self._generate_single_material_page(material_item)
                
                # 第二页：只包含出库记录表格（充满整页，偶数页，左边距10，右边距30）
                self.add_page()
                self._generate_second_page()
            
            self.output(filename)
            return True
            
        except Exception as e:
            logger.error(f"生成器材分类账页PDF失败: {e}")
            return False
    
    def _generate_single_material_page(self, material_item: Dict[str, Any]) -> None:
        """生成单个器材的第一页（基本信息表格 + 6行出库记录）"""
        # 确保第一页使用奇数页边距（左边距30，右边距10）
        self.set_margins(left=30, top=10, right=10)
        
        # 标题
        self.set_font_by_name(self.default_fonts['title'], 16, 'B')
        self.cell(0, 12, '器材分类账', 0, 1, 'C')
        
        # 金额单位信息
        self.set_font_by_name(self.default_fonts['body'], 10)
        self.cell(0, 6, '金额单位：元', 0, 1, 'R')
        self.ln(2)
        
        # 第一个表格：器材基本信息
        self._add_material_info_table(material_item)
        
        # 间距（改为2mm）
        self.ln(2)
        
        # 第二个表格：出库记录（6行）
        self._add_outbound_records_table()
    
    def _generate_second_page(self) -> None:
        """生成单个器材的第二页（只包含出库记录表格，增加行数充满整页）"""
        # 设置第二页边距：左边距10mm，右边距30mm（正反面打印适配）
        self.set_margins(left=10, top=10, right=30)
        
        # 标题
        self.set_font_by_name(self.default_fonts['title'], 16, 'B')
        self.cell(0, 12, '器材分类账（续页）', 0, 1, 'C')
        
        # 金额单位信息
        self.set_font_by_name(self.default_fonts['body'], 10)
        self.cell(0, 6, '金额单位：元', 0, 1, 'R')
        self.ln(2)
        
        # 出库记录表格（增加行数充满整页）
        self._add_outbound_records_table_full_page()
    
    def _draw_table_row(self, row_data: List[str], col_widths: List[int], 
                       is_header: bool = False, field_name_indices: List[int] = None) -> None:
        """绘制表格行（支持多行显示）
        
        Args:
            row_data: 行数据列表
            col_widths: 列宽列表
            is_header: 是否为表头行
            field_name_indices: 字段名称列的索引列表（这些列将使用黑体显示）
        """
        
        # 计算行高度（基于最长单元格文本）
        max_lines = 1
        for i, cell_text in enumerate(row_data):
            text = str(cell_text)
            if len(text) > 0:
                # 使用get_string_width精确计算文本宽度
                text_width = self.get_string_width(text)
                cell_width = col_widths[i] - 2  # 减去单元格边距
                
                # 计算需要的行数
                if text_width > cell_width:
                    lines = (text_width + cell_width - 1) // cell_width
                    max_lines = max(max_lines, min(lines, 2))  # 最多显示2行
        
        # 行高 = 12
        row_height = 12
        
        # 绘制行
        for i, cell_text in enumerate(row_data):
            # 设置字体：如果是表头或者字段名称列，使用黑体
            if is_header or (field_name_indices and i in field_name_indices):
                self.set_font_by_name(self.default_fonts['table_header'], 10, 'B')
            else:
                self.set_font_by_name(self.default_fonts['table_body'], 10)
            
            text = str(cell_text)
            
            # 使用get_string_width精确计算文本宽度
            text_width = self.get_string_width(text)
            cell_width = col_widths[i] - 2  # 减去单元格边距
            
            # 如果文本宽度超过单元格宽度，进行换行处理
            if text_width > cell_width:
                # 计算需要的行数
                lines = (text_width + cell_width - 1) // cell_width
                lines = min(lines, 2)  # 最多显示2行
                
                if lines == 1:
                    # 单行显示
                    self.cell(col_widths[i], row_height, text, 1, 0, 'C')
                else:
                    # 多行显示 - 使用智能文本截取方法
                    # 基于字符宽度进行精确截取
                    avg_char_width = text_width / len(text)
                    chars_per_line = int(cell_width / avg_char_width)
                    
                    # 确保每行至少显示1个字符
                    chars_per_line = max(1, chars_per_line)
                    
                    # 第一行显示
                    first_line = text[:chars_per_line]
                    # 第二行显示剩余部分（最多显示相同字符数）
                    second_line = text[chars_per_line:chars_per_line * 2]
                    
                    # 保存当前位置
                    current_x = self.get_x()
                    current_y = self.get_y()
                    
                    # 绘制第一行（上边框和左右边框）
                    self.cell(col_widths[i], 6, first_line, 'LTR', 2, 'C')
                    # 移动到第二行位置（减去边框重叠部分，确保单元格对齐）
                    self.set_xy(current_x, current_y + 6)
                    # 绘制第二行（下边框和左右边框）
                    self.cell(col_widths[i], 6, second_line, 'LBR', 0, 'C')
                    # 恢复位置
                    self.set_xy(current_x + col_widths[i], current_y)
            else:
                # 单行显示
                self.cell(col_widths[i], row_height, text, 1, 0, 'C')
        
        # 移动到下一行
        self.ln(row_height)
    
    def _add_material_info_table(self, material: Dict[str, Any]) -> None:
        """添加器材基本信息表格"""
        # 表格列定义 - 8列，调整列宽以适应A4页面宽度（297mm），保证左边距充足
        # 总宽度控制在257mm以内，左边距30mm，右边距10mm
        col_widths = [25, 30, 25, 50, 25, 50, 25, 27]
        
        # 设置字体
        self.set_font_by_name(self.default_fonts['table_body'], 10)
        
        # 第一行：保管单位(固定) + 器材名称(数据库) + 器材型号(数据库) + 器材来源(空)
        row1 = [
            '保管单位', self.creator_department,  # 字段名 + 固定值
            '器材名称', material.get('material_name', ''),  # 字段名 + 数据库值
            '器材型号', material.get('specification', ''),  # 字段名 + 数据库值
            '器材来源', ''  # 字段名 + 空值（用户手工填写）
        ]
        self._draw_table_row(row1, col_widths, is_header=False, field_name_indices=[0, 2, 4, 6])
        
        # 第二行：入库单号(数据库) + 器材编码(数据库) + 批次号(数据库) + 供应商(数据库)
        row2 = [
            '入库单号', self.order_data.get('order_number', '') if self.order_data else '',
            '器材编码', material.get('material_code', ''),
            '批次号', material.get('batch_number', ''),
            '供应商', self.order_data.get('supplier', '') if self.order_data else ''
        ]
        self._draw_table_row(row2, col_widths, is_header=False, field_name_indices=[0, 2, 4, 6])
        
        # 第三行：专业(数据库) + 装备名称(数据库) + 装备型号(数据库) + 入库时间(数据库)
        row3 = [
            '专业', material.get('major', ''),
            '装备名称', material.get('equipment_name', ''),
            '装备型号', material.get('equipment_model', ''),
            '入库时间', self.order_data.get('inbound_date', '') if self.order_data else ''
        ]
        self._draw_table_row(row3, col_widths, is_header=False, field_name_indices=[0, 2, 4, 6])
        
        # 第四行：入库数量(数据库) + 单价(数据库) + 金额(数据库) + 计量单位(数据库)
        quantity = material.get('quantity', 0)
        unit_price = material.get('unit_price', 0)
        amount = quantity * unit_price
        
        row4 = [
            '入库数量', str(quantity),
            '单价', f"{unit_price:.2f}",
            '金额', f"{amount:.2f}",
            '计量单位', material.get('unit', '')
        ]
        self._draw_table_row(row4, col_widths, is_header=False, field_name_indices=[0, 2, 4, 6])
        
        # 第五行：合同号(数据库) + 调拨单号(数据库) + 存放货位(空) + 存放仓库(空)
        row5 = [
            '合同号', self.order_data.get('contract_number', '') if self.order_data else '',
            '调拨单号', self.order_data.get('transfer_number', '') if self.order_data else '',
            '存放货位', '',  # 空值（用户手工填写）
            '存放仓库', ''   # 空值（用户手工填写）
        ]
        self._draw_table_row(row5, col_widths, is_header=False, field_name_indices=[0, 2, 4, 6])
        
        # 第六行：质量状况(空) + 备注(空) + 空 + 空
        row6 = [
            '质量状况', '',  # 空值（用户手工填写）
            '备注', '',     # 空值（用户手工填写）
            '', '',
            '', ''
        ]
        self._draw_table_row(row6, col_widths, is_header=False, field_name_indices=[0, 2])
    
    def _add_outbound_records_table(self) -> None:
        """添加出库记录表格（6行）"""
        # 表格列定义 - 8列，调整列宽以适应A4页面宽度（297mm），保证左边距充足
        # 总宽度控制在257mm以内，左边距30m，右边距10mm
        col_widths = [20, 80, 20, 20, 30, 37, 20, 30]
        
        # 表头
        self.set_font_by_name(self.default_fonts['table_header'], 10, 'B')
        headers = ['序号', '出库单号', '支出数量', '结存数量', '出库日期', '领取单位', '保管员', '备注']
        self._draw_table_row(headers, col_widths, is_header=True)
        
        # 表格内容（空行）- 不显示"空"字，留空给用户填写
        self.set_font_by_name(self.default_fonts['table_body'], 10)
        
        # 添加6行空数据
        for i in range(6):
            empty_row = ['', '', '', '', '', '', '', '']  # 全部留空，不显示"空"字
            self._draw_table_row(empty_row, col_widths, is_header=False)
    
    def _add_outbound_records_table_full_page(self) -> None:
        """添加充满整页的出库记录表格（约20行）"""
        # 表格列定义 - 8列，调整列宽以适应A4页面宽度（297mm），左边距10mm，右边距30mm
        # 总宽度控制在257mm以内
        col_widths = [20, 80, 20, 20, 30, 37, 20, 30]
        
        # 表头
        self.set_font_by_name(self.default_fonts['table_header'], 10, 'B')
        headers = ['序号', '出库单号', '支出数量', '结存数量', '出库日期', '领取单位', '保管员', '备注']
        self._draw_table_row(headers, col_widths, is_header=True)
        
        # 表格内容（空行）- 不显示"空"字，留空给用户填写
        self.set_font_by_name(self.default_fonts['table_body'], 10)
        
        # 计算页面可用高度（A4横向页面高度210mm，减去顶部边距10mm和底部边距15mm）
        available_height = 210 - 10 - 15  # 185mm
        
        # 计算每行高度（表头行高12mm，数据行高12mm）
        header_height = 12
        row_height = 12
        
        # 计算可以容纳的行数（减去表头高度）
        rows_available = int((available_height - header_height) / row_height)-2
        
        # 添加足够的空行充满整页（约20行）
        for i in range(rows_available):
            empty_row = ['', '', '', '', '', '', '', '']  # 全部留空，不显示"空"字
            self._draw_table_row(empty_row, col_widths, is_header=False)
    
    def header(self) -> None:
        """页眉设置（器材分类账不需要页眉）"""
        pass
    
    def footer(self) -> None:
        """页脚设置（器材分类账不需要页脚）"""
        pass


class OutboundOrderPDF(PDFGenerator):
    """出库单PDF生成器"""
    
    def __init__(self):
        super().__init__()
        # 设置自动分页边距为15mm，以适应每页加签字
        self.set_auto_page_break(auto=True, margin=15)
        # 启用总页数计算功能
        self.alias_nb_pages()
        self.order_data = None
        self.items_data = None
        self.total_amount = 0.0
        self.current_page_items = 0
        self.max_items_per_page = 20  # 每页最多显示20行物品
    
    def set_order_data(self, order_data: Dict[str, Any]) -> None:
        """设置订单数据"""
        self.order_data = order_data
    
    def set_items_data(self, items_data: List[Dict[str, Any]]) -> None:
        """设置物品数据"""
        self.items_data = items_data
        # 计算总金额
        self.total_amount = sum(item.get('amount', 0.0) for item in items_data)
    
    def header(self) -> None:
        """出库单页眉"""
        if self.page_no() == 1:
            # 第一页显示标题
            self.set_font_by_name(self.default_fonts['title'], 16, 'B')
            self.cell(0, 10, '出库单', 0, 1, 'C')
            
            # 单位信息 - 设置合适的右对齐位置，距离右边距20mm
            self.set_font_by_name(self.default_fonts['body'], 10)
            self.set_x(210 - 60)  # A4纸宽度210mm，距离右边40mm
            self.cell(30, 6, '金额单位：元', 0, 1, 'R')
            self.ln(5)
            
            # 订单基本信息
            self._add_order_header()
        else:
            # 后续页面只显示表头
            self._add_table_header()
    
    def footer(self) -> None:
        """页脚"""
        # 将页码放到页面最下方
        self.set_y(-15)  # 距离页面底部15mm
        self.set_font_by_name(self.default_fonts['body'], 8)
        self.cell(0, 10, f'第 {self.page_no()} 页 / 共 {{nb}} 页', 0, 0, 'C')
    
    def generate_outbound_order(self, filename: str) -> bool:
        """生成出库单PDF"""
        try:
            self.add_page()
            
            # 注意：header()方法已经调用了_add_order_header()，这里不需要重复调用
            # 直接添加物品表格
            self._add_items_table()
            
            # 在所有物品数据添加完成后，在最后一页添加合计行和签字区域
            self._add_total_row()
            
            # 确保最后一页有足够空间显示签字区域
            # 检查是否需要换页来显示签字区域
            signature_space_needed = 18 
            if self.get_y() + signature_space_needed > 297 - 15:  # A4纸高度297mm，底部边距15mm
                # 如果空间不足，添加一页再显示签字区域
                self.add_page()
            
            self._add_signature_area()
            
            self.output(filename)
            return True
            
        except Exception as e:
            logger.error(f"生成出库单PDF失败: {e}")
            return False
    
    def _add_order_header(self) -> None:
        """添加订单基本信息头"""
        if not self.order_data:
            return
        
        self.set_font_by_name(self.default_fonts['header'], 10)
        
        # 订单基本信息行 - 增加列宽避免重叠
        col_widths = [60, 80, 40]
        
        order_info = [
            f"出库单号：{self.order_data.get('order_number', '')}",
            f"收货单位：{self.order_data.get('customer_name', '')}",
            f"出库日期：{self.order_data.get('outbound_date', '')}"
        ]
        
        # 居中对齐
        total_width = sum(col_widths)
        x_start = (210 - total_width) / 2  # A4纸宽度210mm
        self.set_x(x_start)
        
        for i, info in enumerate(order_info):
            self.cell(col_widths[i], 8, info, 0, 0, 'L')
        self.ln(10)
    
    def _add_table_header(self) -> None:
        """添加表格表头"""
        # 表格列定义 - 增加列宽以充分利用页面宽度
        headers = ['序号', '器材编码', '器材名称', '器材规格', '单位', '数量', '单价', '金额', '备注']
        col_widths = self._get_table_col_widths()
        
        # 表格居中对齐
        total_width = sum(col_widths)
        x_start = (210 - total_width) / 2  # A4纸宽度210mm
        self.set_x(x_start)
        
        # 表头 - 使用固定行高，不需要检查文本超出
        self.set_font_by_name(self.default_fonts['table_header'], 10, 'B')
        
        # 表头行高 = 8
        header_row_height = 8
        
        # 直接绘制表头单元格，不需要检查文本宽度
        for i, header in enumerate(headers):
            self.cell(col_widths[i], header_row_height, str(header), 1, 0, 'C')
        
        # 移动到下一行
        self.ln()
    
    def _add_items_table(self) -> None:
        """添加物品表格"""
        if not self.items_data:
            return
        
        # 表格列定义
        headers = ['序号', '器材编码', '器材名称', '器材规格', '单位', '数量', '单价', '金额', '备注']
        col_widths = self._get_table_col_widths()
        
        # 添加表头（仅在第一页，因为header()方法会自动处理后续页）
        if self.page_no() == 1:
            self._add_table_header()
        
        # 表格内容
        self.set_font_by_name(self.default_fonts['table_body'], 10)
        
        # 签字行所需最小空间：签字行高度 + 间距
        signature_required_space = 18  # 与入库单保持一致的18mm空间
        
        for idx, item in enumerate(self.items_data, 1):
            # 表格居中对齐
            total_width = sum(col_widths)
            x_start = (210 - total_width) / 2  # A4纸宽度210mm
            self.set_x(x_start)
            
            row = [
                str(idx),
                item.get('material_code', ''),
                item.get('material_name', ''),
                item.get('specification', ''),
                item.get('unit', ''),
                str(item.get('quantity', 0)),
                f"{item.get('unit_price', 0):.2f}",
                f"{item.get('amount', 0):.2f}",
                item.get('remark', '')
            ]
            
            # 计算当前行需要的高度（基于最长单元格内容）
            max_lines = 1
            for i, cell in enumerate(row):
                text = str(cell)
                if len(text) > 0:
                    # 使用get_string_width精确计算文本宽度
                    text_width = self.get_string_width(text)
                    cell_width = col_widths[i] - 2  # 减去单元格边距
                    
                    # 计算需要的行数
                    if text_width > cell_width:
                        lines = (text_width + cell_width - 1) // cell_width
                        max_lines = max(max_lines, min(lines, 2))  # 最多显示2行
            
            # 根据文字数量确定行高：如果需要显示两行，则高度为16，否则为8
            row_height = 16 if max_lines > 1 else 8
            
            # 更准确的分页检查：检查当前行和签字行所需空间
            if self.get_y() + row_height + signature_required_space > 297 - 15:  # A4纸高度297mm，底部边距15mm
                # 当前页面空间不足，先添加签字区域再换页
                self._add_signature_area_for_page()
                self.add_page()
                # 注意：add_page()会自动调用header()方法，header()中会添加表头
                # 重新设置表格内容字体
                self.set_font_by_name(self.default_fonts['table_body'], 10)
                # 重新设置起始位置
                self.set_x(x_start)
            
            # 使用cell绘制单元格，支持精确换行控制
            for i, cell in enumerate(row):
                text = str(cell)
                
                # 使用get_string_width精确计算文本宽度
                text_width = self.get_string_width(text)
                cell_width = col_widths[i] - 2  # 减去单元格边距
                
                # 如果文本宽度超过单元格宽度，进行换行处理
                if text_width > cell_width:
                    # 计算需要的行数
                    lines = (text_width + cell_width - 1) // cell_width
                    lines = min(lines, 2)  # 最多显示2行
                    
                    if lines == 1:
                        # 单行显示
                        self.cell(col_widths[i], row_height, text, 1, 0, 'C')
                    else:
                        # 计算每行大致能容纳的字符数（基于平均字符宽度）
                        avg_char_width = text_width / len(text)
                        chars_per_line = int(cell_width / avg_char_width)
                        
                        # 确保每行至少显示1个字符
                        chars_per_line = max(1, chars_per_line)
                        
                        # 第一行显示
                        first_line = text[:chars_per_line]
                        # 第二行显示剩余部分（最多显示相同字符数）
                        second_line = text[chars_per_line:chars_per_line * 2]
                        
                        # 保存当前位置
                        current_x = self.get_x()
                        current_y = self.get_y()
                        
                        # 绘制第一行（上边框和左右边框）
                        self.cell(col_widths[i], 8, first_line, 'LTR', 0, 'C')
                        # 移动到第二行位置（保持X坐标不变，Y坐标下移）
                        self.set_xy(current_x, current_y + 8)
                        # 绘制第二行（下边框和左右边框）
                        self.cell(col_widths[i], 8, second_line, 'LBR', 0, 'C')
                        # 恢复位置到下一列，但Y坐标保持在当前行的起始位置
                        # 注意：这里必须保持Y坐标为current_y，因为这一行的其他单元格也在这个Y坐标
                        # 最后的ln()会统一移动到下一行
                        self.set_xy(current_x + col_widths[i], current_y)
                else:
                    # 单行显示
                    self.cell(col_widths[i], row_height, text, 1, 0, 'C')
            
            # 移动到下一行，使用row_height确保正确的行高
            self.set_y(self.get_y() + row_height)
    
    def _get_table_col_widths(self) -> list:
        """获取表格列宽定义"""
        # 统一的列宽定义：序号,器材编码,器材名称,器材规格,单位,数量,单价,金额,备注
        return [12, 25, 30, 30, 12, 12, 18, 22, 15]
    
    def _add_total_row(self) -> None:
        """添加合计行并确保签字行空间"""
        # 计算所需空间：合计行(2行) + 签字行
        total_row_height = 12 * 2 + 5  # 2行合计行 + 5mm间距
        signature_row_height = 18  # 与入库单保持一致的签字行高度
        required_space = total_row_height + signature_row_height
        
        # 检查当前页剩余空间是否足够容纳合计行和签字行
        if self.get_y() + required_space > 297 - 15:  # A4纸高度297mm，底部边距15mm
            # 添加当前页签字行
            self._add_signature_area_for_page()
            # 新建页面
            self.add_page()
            # 重置字体样式
            self.set_font_by_name(self.default_fonts['table_header'], 10, 'B')
        
        # 合计行
        self.set_font_by_name(self.default_fonts['table_header'], 10, 'B')
        
        # 使用与物品表格相同的列宽定义
        col_widths = self._get_table_col_widths()
        
        # 使用与物品表格相同的居中对齐计算
        total_width = sum(col_widths)
        x_start = (210 - total_width) / 2  # A4纸宽度210mm
        
        # 第一行：合计和金额信息
        self.set_x(x_start)  # 设置正确的起始位置
        
        # 将金额转换为中文大写
        amount_chinese = self._amount_to_chinese(self.total_amount)
        
        # 单元格1："合计"
        self.cell(col_widths[0], 12, '合计', 1, 0, 'C')
        
        # 合并单元格2-7：人民币（大写）+ 金额中文大写
        merged_width_2_7 = sum(col_widths[1:7])
        self.cell(merged_width_2_7, 12, f'人民币（大写）{amount_chinese}', 1, 0, 'L')
        
        # 合并单元格8-9：（小写）+ 金额数字
        merged_width_8_9 = sum(col_widths[7:9])
        self.cell(merged_width_8_9, 12, f'（小写）{self.total_amount:.2f}', 1, 0, 'L')
        
        self.ln()
        
        # 第二行：备注
        self.set_x(x_start)  # 设置正确的起始位置，与第一行对齐
        
        # 单元格1："备注"
        self.cell(col_widths[0], 12, '备注', 1, 0, 'C')
        
        # 合并单元格2-9：空内容
        merged_width_2_9 = sum(col_widths[1:9])
        self.cell(merged_width_2_9, 12, '', 1, 0, 'C')
        
        self.ln()
    
    def _add_signature_area_for_page(self) -> None:
        """添加签字位置（除最后一页外使用）"""
        # 签字位置 - 在表格下一行
        self.ln(10)  # 空一行
        
        # 签字行：审批人、领取人、保管员
        col_widths = [60, 60, 60]
        sign_labels = ['审批人：', '领取人：', '保管员：']
        
        total_width = sum(col_widths)
        x_start = (210 - total_width) / 2  # A4纸宽度210mm
        self.set_x(x_start)
        
        self.set_font_by_name(self.default_fonts['body'], 10)
        for i, label in enumerate(sign_labels):
            self.cell(col_widths[i], 8, label, 0, 0, 'L')
        
        self.ln(10)  # 签字行后空一行，与入库单保持一致
    
    def _add_signature_area(self) -> None:
        """添加签字位置（最后一页使用）"""
        # 签字位置 - 在表格下一行
        self.ln(10)  # 空一行
        
        # 签字行：审批人、领取人、保管员
        col_widths = [60, 60, 60]
        sign_labels = ['审批人：', '领取人：', '保管员：']
        
        total_width = sum(col_widths)
        x_start = (210 - total_width) / 2  # A4纸宽度210mm
        self.set_x(x_start)
        
        self.set_font_by_name(self.default_fonts['body'], 10)
        for i, label in enumerate(sign_labels):
            self.cell(col_widths[i], 8, label, 0, 0, 'L')
        self.ln(10)
    
    def _amount_to_chinese(self, amount: float) -> str:
        """将金额转换为中文大写"""
        # 简单的金额转换实现
        if amount == 0:
            return "零元整"
        
        # 这里可以扩展更完整的金额转换逻辑
        # 目前使用简化版本
        integer_part = int(amount)
        decimal_part = round((amount - integer_part) * 100)
        
        chinese_digits = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖']
        chinese_units = ['', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿']
        
        result = ''
        
        # 整数部分转换
        if integer_part > 0:
            integer_str = str(integer_part)
            for i, digit in enumerate(integer_str):
                digit_int = int(digit)
                unit_index = len(integer_str) - i - 1
                result += chinese_digits[digit_int] + chinese_units[unit_index]
            result += '元'
        
        # 小数部分转换
        if decimal_part > 0:
            if decimal_part < 10:
                result += chinese_digits[decimal_part] + '角'
            else:
                jiao = decimal_part // 10
                fen = decimal_part % 10
                result += chinese_digits[jiao] + '角'
                if fen > 0:
                    result += chinese_digits[fen] + '分'
        else:
            result += '整'
        
        return result

def get_available_fonts() -> Dict[str, str]:
    """获取可用字体列表"""
    font_manager = get_font_manager()
    return font_manager.get_available_fonts()



def generate_inbound_order_pdf(order_data: Dict[str, Any], items_data: List[Dict[str, Any]], 
                               output_path: str) -> bool:
    """生成入库单PDF"""
    pdf = InboundOrderPDF()
    pdf.set_order_data(order_data)
    pdf.set_items_data(items_data)
    return pdf.generate_inbound_order(output_path)


def generate_outbound_order_pdf(order_data: Dict[str, Any], items_data: List[Dict[str, Any]], 
                                output_path: str) -> bool:
    """生成出库单PDF"""
    pdf = OutboundOrderPDF()
    pdf.set_order_data(order_data)
    pdf.set_items_data(items_data)
    return pdf.generate_outbound_order(output_path)





def generate_material_ledger_pdf(order_data: Dict[str, Any], items_data: List[Dict[str, Any]], 
                                  creator_department: str, output_path: str) -> bool:
    """生成器材分类账页PDF"""
    pdf = MaterialLedgerPDF()
    pdf.set_inbound_order_data(order_data)
    pdf.set_material_items(items_data)
    pdf.set_creator_department(creator_department)
    return pdf.generate_material_ledger(output_path)


