#!/bin/bash
# Docker 容器启动脚本
# 用于在容器启动时检查nginx配置文件,并自动同步模板到挂载目录
set -e

echo "=========================================="
echo "🚀 仓库管理系统前端容器启动"
echo "=========================================="

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# nginx配置文件路径定义(按优先级从高到低)
EXTERNAL_NGINX_CONF="/etc/nginx/conf-external/nginx.conf"  # 挂载目录中的配置
TEMPLATE_NGINX_CONF="/etc/nginx/nginx.conf.template"      # 镜像内的模板
DEFAULT_NGINX_CONF="/etc/nginx/nginx.conf.default"       # 镜像内的默认配置
NGINX_ACTIVE_CONF="/etc/nginx/nginx.conf"                # nginx实际使用的配置
echo ""
echo "🔍 检查nginx配置文件..."

# 检查挂载目录是否存在并决定配置策略
if [ ! -d "/etc/nginx/conf-external" ]; then
    echo -e "${YELLOW}⚠️  挂载目录不存在,使用默认配置${NC}"
    cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
else
    # 检查挂载目录中的配置文件是否存在
    if [ -f "$EXTERNAL_NGINX_CONF" ]; then
        # 检查文件大小(如果文件存在但为空或过小,说明是首次挂载或未初始化)
        # 使用跨平台的stat命令获取文件大小
        FILE_SIZE=$(stat -f%z "$EXTERNAL_NGINX_CONF" 2>/dev/null || stat -c%s "$EXTERNAL_NGINX_CONF" 2>/dev/null || echo 0)
        
        if [ "$FILE_SIZE" -gt 100 ]; then
            # 文件有内容,验证并使用
            echo -e "${GREEN}✅ 发现有效nginx配置文件${NC}"
            echo "   路径: $EXTERNAL_NGINX_CONF"
            echo "   大小: $FILE_SIZE bytes"
            
            # 验证配置文件语法
            if nginx -t -c "$EXTERNAL_NGINX_CONF" 2>/dev/null; then
                echo -e "${GREEN}✅ nginx配置语法验证通过${NC}"
                # 复制到nginx实际使用的路径
                cp "$EXTERNAL_NGINX_CONF" "$NGINX_ACTIVE_CONF"
            else
                echo -e "${YELLOW}⚠️  nginx配置语法错误${NC}"
                echo -e "${YELLOW}   尝试使用模板覆盖${NC}"
                # 如果语法错误,用模板覆盖损坏的配置
                if [ -f "$TEMPLATE_NGINX_CONF" ]; then
                    cp "$TEMPLATE_NGINX_CONF" "$EXTERNAL_NGINX_CONF" 2>/dev/null || true
                    cp "$TEMPLATE_NGINX_CONF" "$NGINX_ACTIVE_CONF"
                    echo -e "${GREEN}✅ 已从模板恢复nginx配置文件${NC}"
                fi
            fi
        else
            # 配置文件存在但大小过小或为空,需要从模板初始化
            echo -e "${YELLOW}⚠️  挂载配置文件过小或为空${NC}"
            echo "   配置文件大小: $FILE_SIZE bytes"
            
            # 尝试从镜像内的模板复制配置到挂载目录
            if [ -f "$TEMPLATE_NGINX_CONF" ]; then
                if cp "$TEMPLATE_NGINX_CONF" "$EXTERNAL_NGINX_CONF" 2>/dev/null; then
                    echo -e "${GREEN}✅ 已从模板生成nginx配置文件到挂载目录${NC}"
                    echo "   源: $TEMPLATE_NGINX_CONF"
                    echo "   目标: $EXTERNAL_NGINX_CONF"
                    # 同时复制到nginx实际使用的路径
                    cp "$TEMPLATE_NGINX_CONF" "$NGINX_ACTIVE_CONF"
                else
                    echo -e "${YELLOW}⚠️  无法写入挂载配置文件,权限不足${NC}"
                    echo -e "${YELLOW}   暂时使用默认配置${NC}"
                    cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
                fi
            else
                echo -e "${YELLOW}⚠️  镜像内模板不存在,使用默认配置${NC}"
                cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
            fi
        fi
    else
        # 挂载配置文件不存在,需要首次创建
        echo -e "${YELLOW}⚠️  挂载nginx配置文件不存在,尝试首次创建${NC}"
        
        if [ -f "$TEMPLATE_NGINX_CONF" ]; then
            # 检查挂载目录是否有写权限
            if [ ! -w "/etc/nginx/conf-external" ]; then
                echo -e "${YELLOW}⚠️  /etc/nginx/conf-external 目录无写权限${NC}"
                echo "   当前用户: $(whoami) (UID: $(id -u))"
                echo "   目录权限: $(ls -ld /etc/nginx/conf-external)"
                echo -e "${YELLOW}   使用默认配置${NC}"
                cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
            else
                # 尝试创建配置文件到挂载目录
                if cp "$TEMPLATE_NGINX_CONF" "$EXTERNAL_NGINX_CONF" 2>/dev/null; then
                    echo -e "${GREEN}✅ 已从模板生成nginx配置文件到挂载目录${NC}"
                    echo "   源: $TEMPLATE_NGINX_CONF"
                    echo "   目标: $EXTERNAL_NGINX_CONF"
                    # 同时复制到nginx实际使用的路径
                    cp "$TEMPLATE_NGINX_CONF" "$NGINX_ACTIVE_CONF"
                else
                    echo -e "${YELLOW}⚠️  无法创建配置文件到挂载目录,写入失败${NC}"
                    echo -e "${YELLOW}   使用默认配置${NC}"
                    cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
                fi
            fi
        else
            echo -e "${YELLOW}⚠️  镜像内模板不存在,使用默认配置${NC}"
            cp "$DEFAULT_NGINX_CONF" "$NGINX_ACTIVE_CONF" 2>/dev/null || true
        fi
    fi
fi

echo ""
echo "🔍 检查nginx配置..."
nginx -t -c "$NGINX_ACTIVE_CONF"

echo ""
echo "🚀 启动nginx服务..."
exec "$@"
