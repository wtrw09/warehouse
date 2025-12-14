#!/bin/sh
# 前端容器启动脚本
# 支持nginx配置文件双向同步:优先使用外部配置,不存在时从镜像复制到外部

set -e

echo "=========================================="
echo "🚀 仓库管理系统前端容器启动"
echo "=========================================="

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# nginx配置文件路径
EXTERNAL_NGINX_CONF="/etc/nginx/nginx.conf"
TEMPLATE_NGINX_CONF="/etc/nginx/nginx.conf.template"
DEFAULT_NGINX_CONF="/etc/nginx/nginx.conf.default"

echo ""
echo "🔍 检查nginx配置文件..."

# 检查外部挂载的配置文件是否存在
if [ -f "$EXTERNAL_NGINX_CONF" ]; then
    # 检查文件大小,判断是否是有效的配置文件(不是空文件或目录)
    # 兼容不同系统的stat命令格式
    FILE_SIZE=$(stat -f%z "$EXTERNAL_NGINX_CONF" 2>/dev/null || stat -c%s "$EXTERNAL_NGINX_CONF" 2>/dev/null || echo 0)
    
    if [ "$FILE_SIZE" -gt 100 ]; then
        # 宿主机已有配置文件
        echo -e "${GREEN}✅ 使用宿主机的nginx配置文件${NC}"
        echo "   路径: $EXTERNAL_NGINX_CONF"
        echo "   大小: $FILE_SIZE bytes"
        
        # 验证配置文件语法
        if nginx -t -c "$EXTERNAL_NGINX_CONF" 2>/dev/null; then
            echo -e "${GREEN}✅ nginx配置语法验证通过${NC}"
        else
            echo -e "${YELLOW}⚠️  nginx配置语法错误${NC}"
            echo -e "${YELLOW}   将使用镜像模板覆盖${NC}"
            # 语法错误时,用模板覆盖
            if [ -f "$TEMPLATE_NGINX_CONF" ]; then
                cat "$TEMPLATE_NGINX_CONF" > "$EXTERNAL_NGINX_CONF"
                echo -e "${GREEN}✅ 已从镜像模板覆盖nginx配置文件${NC}"
            fi
        fi
    else
        # 文件存在但无效(可能是Docker自动创建的空文件/目录)
        echo -e "${YELLOW}⚠️  外部配置文件无效,从镜像复制${NC}"
        echo "   文件大小: $FILE_SIZE bytes"
        
        # 检查文件是否可写
        if [ ! -w "$EXTERNAL_NGINX_CONF" ]; then
            echo -e "${YELLOW}⚠️  配置文件不可写,权限可能有问题${NC}"
            echo "   当前用户: $(whoami) (UID: $(id -u))"
            echo "   文件权限: $(ls -l $EXTERNAL_NGINX_CONF)"
        fi
        
        # 从镜像模板复制配置文件到外部(写入内容而不是覆盖文件)
        if [ -f "$TEMPLATE_NGINX_CONF" ]; then
            if cat "$TEMPLATE_NGINX_CONF" > "$EXTERNAL_NGINX_CONF" 2>/dev/null; then
                echo -e "${GREEN}✅ 已从镜像复制nginx配置文件${NC}"
                echo "   源: $TEMPLATE_NGINX_CONF"
                echo "   目标: $EXTERNAL_NGINX_CONF"
            else
                echo -e "${YELLOW}⚠️  无法写入配置文件(权限不足)${NC}"
                echo -e "${YELLOW}   将使用默认配置${NC}"
                cat "$DEFAULT_NGINX_CONF" > "$EXTERNAL_NGINX_CONF" 2>/dev/null || true
            fi
        else
            echo -e "${YELLOW}⚠️  镜像中没有模板,使用默认配置${NC}"
            cat "$DEFAULT_NGINX_CONF" > "$EXTERNAL_NGINX_CONF" 2>/dev/null || true
        fi
    fi
else
    echo -e "${YELLOW}⚠️  外部nginx配置文件不存在,使用默认配置${NC}"
    cp "$DEFAULT_NGINX_CONF" "$EXTERNAL_NGINX_CONF"
fi

echo ""
echo "🔍 检查nginx配置..."
nginx -t

echo ""
echo "🚀 启动nginx服务..."
exec "$@"