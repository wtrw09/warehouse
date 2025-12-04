#!/usr/bin/env python3
"""
SQLite WAL模式配置脚本
用于启用SQLite的预写日志（WAL）模式，提升数据库并发性能和数据安全性
"""

import sqlite3
import os
from datetime import datetime

def enable_wal_mode():
    """启用SQLite WAL模式"""
    db_path = "data/warehouse.db"
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"[ERROR] 数据库文件不存在: {db_path}")
        print("请先确保数据库已初始化")
        return False
    
    try:
        # 连接到数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("SQLite WAL模式配置")
        print("=" * 60)
        
        # 1. 检查当前日志模式
        cursor.execute("PRAGMA journal_mode;")
        current_mode = cursor.fetchone()[0]
        print(f"当前日志模式: {current_mode}")
        
        # 2. 启用WAL模式
        cursor.execute("PRAGMA journal_mode=WAL;")
        new_mode = cursor.fetchone()[0]
        print(f"新日志模式: {new_mode}")
        
        # 3. 配置WAL相关参数
        # 设置自动检查点（每1000页）
        cursor.execute("PRAGMA wal_autocheckpoint=1000;")
        print("WAL自动检查点设置: 1000")
        
        # 设置同步模式（平衡性能和数据安全）
        cursor.execute("PRAGMA synchronous=NORMAL;")
        print("同步模式: NORMAL")
        
        # 4. 验证配置
        cursor.execute("PRAGMA journal_mode;")
        final_mode = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA wal_autocheckpoint;")
        final_checkpoint = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA synchronous;")
        final_sync = cursor.fetchone()[0]
        
        print("-" * 60)
        print("最终配置验证:")
        print(f"  日志模式: {final_mode}")
        print(f"  自动检查点: {final_checkpoint}")
        print(f"  同步模式: {final_sync}")
        
        # 5. 提交更改
        conn.commit()
        
        print("-" * 60)
        if final_mode.upper() == "WAL":
            print("✅ WAL模式配置成功！")
            print("✅ 数据库现在支持并发读写操作")
            print("✅ 预写日志已启用，数据安全性提升")
        else:
            print("❌ WAL模式配置失败")
            return False
            
        # 6. 显示WAL文件信息
        wal_file = db_path + "-wal"
        shm_file = db_path + "-shm"
        
        print("-" * 60)
        print("WAL相关文件:")
        print(f"  主数据库文件: {db_path}")
        print(f"  WAL日志文件: {wal_file}")
        print(f"  共享内存文件: {shm_file}")
        
        # 检查WAL文件是否存在
        if os.path.exists(wal_file):
            wal_size = os.path.getsize(wal_file)
            print(f"  WAL文件大小: {wal_size} 字节")
        
        conn.close()
        
        print("=" * 60)
        print("配置完成时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 配置WAL模式时出错: {e}")
        return False

def check_wal_status():
    """检查WAL模式状态"""
    db_path = "data/warehouse.db"
    
    if not os.path.exists(db_path):
        print(f"[ERROR] 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("SQLite WAL模式状态检查")
        print("=" * 60)
        
        # 检查日志模式
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        print(f"日志模式: {mode}")
        
        # 检查WAL相关参数
        cursor.execute("PRAGMA wal_autocheckpoint;")
        checkpoint = cursor.fetchone()[0]
        print(f"自动检查点: {checkpoint}")
        
        cursor.execute("PRAGMA synchronous;")
        sync = cursor.fetchone()[0]
        print(f"同步模式: {sync}")
        
        # 检查WAL文件
        wal_file = db_path + "-wal"
        if os.path.exists(wal_file):
            wal_size = os.path.getsize(wal_file)
            print(f"WAL文件大小: {wal_size} 字节")
        else:
            print("WAL文件: 不存在")
        
        # 检查数据库页面大小
        cursor.execute("PRAGMA page_size;")
        page_size = cursor.fetchone()[0]
        print(f"页面大小: {page_size} 字节")
        
        # 检查数据库大小
        db_size = os.path.getsize(db_path)
        print(f"数据库大小: {db_size} 字节")
        
        conn.close()
        
        print("=" * 60)
        if mode.upper() == "WAL":
            print("✅ WAL模式已启用")
        else:
            print("❌ WAL模式未启用")
        
        return mode.upper() == "WAL"
        
    except Exception as e:
        print(f"[ERROR] 检查WAL状态时出错: {e}")
        return False

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        action = sys.argv[1]
    else:
        action = "enable"
    
    if action == "enable":
        print("正在启用WAL模式...")
        success = enable_wal_mode()
        if not success:
            sys.exit(1)
    elif action == "status":
        print("正在检查WAL状态...")
        check_wal_status()
    elif action == "help":
        print("""
SQLite WAL模式配置工具

用法:
  python configure_wal_mode.py [command]

命令:
  enable   - 启用WAL模式（默认）
  status   - 检查当前WAL状态
  help     - 显示帮助信息

示例:
  python configure_wal_mode.py enable
  python configure_wal_mode.py status
        """)
    else:
        print(f"未知命令: {action}")
        print("使用 'python configure_wal_mode.py help' 查看帮助")

if __name__ == "__main__":
    main()