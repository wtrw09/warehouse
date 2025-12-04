"""
独立恢复脚本 - 从restore_status.json读取路径并执行恢复
支持通过状态文件路径作为参数调用
"""

import os
import sys
import json
from pathlib import Path

# 导入固定恢复脚本的功能
sys.path.insert(0, str(Path(__file__).parent))

from manual_recovery_fixed import FixedManualRecovery

def restore_from_status_file(status_file_path: str):
    """
    从状态文件读取路径并执行恢复
    
    Args:
        status_file_path: 状态文件路径
        
    Returns:
        bool: 恢复是否成功
    """
    try:
        # 读取状态文件
        status_file = Path(status_file_path)
        if not status_file.exists():
            print(f"错误: 状态文件不存在: {status_file_path}")
            return False
        
        with open(status_file, 'r', encoding='utf-8') as f:
            status_data = json.load(f)
        
        # 获取备份文件路径
        backup_path = status_data.get("backup_path")
        if not backup_path:
            print("错误: 状态文件中缺少备份文件路径")
            return False
        
        # 创建恢复处理器并执行恢复
        processor = FixedManualRecovery(backup_path, status_file_path)
        success = processor.execute_restore()
        
        return success
        
    except Exception as e:
        print(f"恢复过程中发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python backup/restore_from_status.py <status_file_path>")
        print("示例: python backup/restore_from_status.py temp_recovery/restore_status.json")
        print("\n状态文件应包含以下结构:")
        print("{")
        print('  "backup_path": "backup/warehouse_20251108_195654.db",')
        print('  "status": "in_progress",')
        print('  ...')
        print("}")
        sys.exit(1)
    
    status_file_path = sys.argv[1]
    
    print(f"开始从状态文件恢复: {status_file_path}")
    success = restore_from_status_file(status_file_path)
    
    if success:
        print("恢复操作成功完成")
        sys.exit(0)
    else:
        print("恢复操作失败")
        sys.exit(1)

if __name__ == "__main__":
    main()