#!/bin/bash
# Docker 容器启动脚本
# 用于在容器启动时检查并初始化必要的文件

set -e

echo "=========================================="
echo "🚀 仓库管理系统后端容器启动"
echo "=========================================="

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 数据库文件路径
SYSTEM_CONFIG_DB="/app/data/system_config.db"
SYSTEM_CONFIG_DB_TEMPLATE="/app/data_template/system_config.db"

# 检查并复制系统配置数据库
echo ""
echo "🔍 检查系统配置数据库..."

if [ -f "$SYSTEM_CONFIG_DB" ]; then
    # 宿主机已有数据库文件
    FILE_SIZE=$(stat -f%z "$SYSTEM_CONFIG_DB" 2>/dev/null || stat -c%s "$SYSTEM_CONFIG_DB" 2>/dev/null)
    echo -e "${GREEN}✅ 使用宿主机的数据库文件${NC}"
    echo "   路径: $SYSTEM_CONFIG_DB"
    echo "   大小: $FILE_SIZE bytes"
    
    # 检查文件是否可读
    if [ ! -r "$SYSTEM_CONFIG_DB" ]; then
        echo -e "${YELLOW}⚠️  数据库文件不可读，权限可能有问题${NC}"
    fi
else
    # 宿主机没有数据库文件，从镜像模板复制
    if [ -f "$SYSTEM_CONFIG_DB_TEMPLATE" ]; then
        echo -e "${YELLOW}⚠️  宿主机没有数据库文件，从镜像复制${NC}"
        
        # 检查目标目录是否可写
        if [ ! -w "/app/data" ]; then
            echo -e "${YELLOW}⚠️  /app/data 目录不可写${NC}"
            echo "   当前用户: $(whoami) (UID: $(id -u))" 
            echo "   目录权限: $(ls -ld /app/data)"
            echo -e "${YELLOW}⚠️  将在应用启动时自动初始化数据库${NC}"
        else
            # 尝试复制文件
            if cp "$SYSTEM_CONFIG_DB_TEMPLATE" "$SYSTEM_CONFIG_DB" 2>/dev/null; then
                echo -e "${GREEN}✅ 已从镜像复制数据库文件${NC}"
                echo "   源: $SYSTEM_CONFIG_DB_TEMPLATE"
                echo "   目标: $SYSTEM_CONFIG_DB"
            else
                echo -e "${YELLOW}⚠️  无法复制数据库文件（权限不足）${NC}"
                echo -e "${YELLOW}   将在应用启动时自动初始化数据库${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  镜像中也没有数据库模板，将在首次运行时自动初始化${NC}"
    fi
fi

echo ""
echo "=========================================="
echo "🎬 启动应用程序"
echo "=========================================="

# 执行传入的命令（通常是 python main.py）
exec "$@"
