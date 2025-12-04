#!/bin/bash
# Linux Bash 容器启动脚本
# 自动检测 CPU 架构（ARM64/AMD64）并启动相应的容器

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 仓库管理系统容器启动脚本 ===${NC}"
echo ""

# 检测 CPU 架构
echo -e "${CYAN}检测 CPU 架构...${NC}"
ARCH=$(uname -m)

case $ARCH in
    x86_64)
        PLATFORM="amd64"
        echo -e "${GREEN}✓ 检测到 AMD64 (x86_64) 架构${NC}"
        ;;
    aarch64|arm64)
        PLATFORM="arm64"
        echo -e "${GREEN}✓ 检测到 ARM64 架构${NC}"
        ;;
    *)
        echo -e "${RED}✗ 不支持的架构: $ARCH${NC}"
        echo -e "${YELLOW}仅支持 x86_64 (AMD64) 和 aarch64 (ARM64)${NC}"
        exit 1
        ;;
esac

echo ""

# 检查 Docker 是否安装
echo -e "${CYAN}检查 Docker 服务...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker 未安装${NC}"
    echo -e "${YELLOW}请先安装 Docker: https://docs.docker.com/engine/install/${NC}"
    exit 1
fi

# 检查 Docker 是否运行
# 尝试使用 sudo 权限检查（如果需要）
if ! docker info &> /dev/null; then
    if ! sudo docker info &> /dev/null; then
        echo -e "${RED}✗ Docker 服务未运行${NC}"
        echo -e "${YELLOW}请启动 Docker 服务: sudo systemctl start docker${NC}"
        exit 1
    else
        echo -e "${YELLOW}⚠ 检测到需要 sudo 权限运行 Docker${NC}"
        echo -e "${CYAN}提示: 建议将用户添加到 docker 组: sudo usermod -aG docker \$USER${NC}"
        # 设置使用 sudo 的标志
        USE_SUDO=true
    fi
else
    USE_SUDO=false
fi

echo -e "${GREEN}✓ Docker 服务正常运行${NC}"
echo ""

# 检查 docker-compose 是否安装
echo -e "${CYAN}检查 Docker Compose...${NC}"
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    [ "$USE_SUDO" = true ] && COMPOSE_CMD="sudo docker-compose"
    echo -e "${GREEN}✓ 使用 docker-compose 命令${NC}"
elif docker compose version &> /dev/null 2>&1 || sudo docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
    [ "$USE_SUDO" = true ] && COMPOSE_CMD="sudo docker compose"
    echo -e "${GREEN}✓ 使用 docker compose 插件${NC}"
else
    echo -e "${RED}✗ Docker Compose 未安装${NC}"
    echo -e "${YELLOW}请安装 Docker Compose${NC}"
    exit 1
fi

echo ""

# 检查必要的镜像是否存在
echo -e "${CYAN}检查必要的镜像 ($PLATFORM)...${NC}"

declare -A REQUIRED_IMAGES=(
    ["warehouse-frontend:latest-$PLATFORM"]="前端镜像"
    ["warehouse-backend:latest-$PLATFORM"]="后端镜像"
    ["redis:7.2-alpine-$PLATFORM"]="Redis缓存"
)

MISSING_IMAGES=()
DOCKER_CMD="docker"
[ "$USE_SUDO" = true ] && DOCKER_CMD="sudo docker"

for IMAGE in "${!REQUIRED_IMAGES[@]}"; do
    if $DOCKER_CMD images "$IMAGE" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -q "$IMAGE"; then
        echo -e "${GREEN}✓ $IMAGE 已存在${NC}"
    else
        echo -e "${RED}✗ 缺少 $IMAGE - ${REQUIRED_IMAGES[$IMAGE]}${NC}"
        MISSING_IMAGES+=("$IMAGE")
    fi
done

if [ ${#MISSING_IMAGES[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}缺少以下镜像，请先构建或加载:${NC}"
    for IMAGE in "${MISSING_IMAGES[@]}"; do
        echo -e "${YELLOW}  - $IMAGE${NC}"
    done
    echo ""
    echo -e "${CYAN}提示: 使用构建脚本或 docker load 加载镜像文件${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}所有必要的镜像都已就绪！${NC}"
echo ""

# 创建必要的目录
echo -e "${CYAN}创建数据目录...${NC}"

# 支持两种目录结构：warehouseBackend 或 backend
if [ -d "backend" ]; then
    DATA_DIR="backend"
    echo -e "${GREEN}✓ 使用 backend 目录结构${NC}"
else
    DATA_DIR="warehouseBackend"
    echo -e "${GREEN}✓ 使用 warehouseBackend 目录结构${NC}"
fi

DIRS=("data" "logs" "backups")

mkdir -p "$DATA_DIR"

for DIR in "${DIRS[@]}"; do
    DIR_PATH="$DATA_DIR/$DIR"
    if [ ! -d "$DIR_PATH" ]; then
        mkdir -p "$DIR_PATH"
        echo -e "${GREEN}✓ 创建目录: $DIR_PATH${NC}"
    else
        echo -e "${GREEN}✓ 目录已存在: $DIR_PATH${NC}"
    fi
done

# 设置目录权限（确保容器内的 appuser UID 1000 可以访问）
echo -e "${CYAN}设置目录权限 (UID 1000:1000)...${NC}"

# 显示修复前的权限
echo -e "${CYAN}修复前的权限:${NC}"
ls -la "$DATA_DIR" 2>/dev/null | grep -E "data|logs|backups" || echo -e "${YELLOW}无法显示详细权限${NC}"
echo ""

if [ "$USE_SUDO" = true ]; then
    # 使用 sudo 修复权限
    echo -e "${CYAN}使用 sudo 修复权限...${NC}"
    if sudo chown -R 1000:1000 "$DATA_DIR/data" "$DATA_DIR/logs" "$DATA_DIR/backups" 2>/dev/null; then
        sudo chmod -R 755 "$DATA_DIR/data" "$DATA_DIR/logs" "$DATA_DIR/backups" 2>/dev/null || true
        echo -e "${GREEN}✓ 权限设置完成 (使用 sudo)${NC}"
    else
        echo -e "${YELLOW}⚠ 需要 root 权限，请输入密码${NC}"
        sudo chown -R 1000:1000 "$DATA_DIR/data" "$DATA_DIR/logs" "$DATA_DIR/backups"
        sudo chmod -R 755 "$DATA_DIR/data" "$DATA_DIR/logs" "$DATA_DIR/backups"
        echo -e "${GREEN}✓ 权限设置完成${NC}"
    fi
    
    # 如果有数据库文件，确保权限正确
    if [ -f "$DATA_DIR/data/system_config.db" ]; then
        echo -e "${CYAN}修复数据库文件权限...${NC}"
        sudo chown 1000:1000 "$DATA_DIR/data/system_config.db"
        sudo chmod 644 "$DATA_DIR/data/system_config.db"
        echo -e "${GREEN}✓ 数据库文件权限已修复${NC}"
    fi
else
    # 不使用 sudo
    if chown -R 1000:1000 "$DATA_DIR/data" "$DATA_DIR/logs" "$DATA_DIR/backups" 2>/dev/null && \
       chmod -R 755 "$DATA_DIR/data" "$DATA_DIR/logs" "$DATA_DIR/backups" 2>/dev/null; then
        echo -e "${GREEN}✓ 权限设置完成${NC}"
        
        # 如果有数据库文件，确保权限正确
        if [ -f "$DATA_DIR/data/system_config.db" ]; then
            chown 1000:1000 "$DATA_DIR/data/system_config.db" 2>/dev/null || true
            chmod 644 "$DATA_DIR/data/system_config.db" 2>/dev/null || true
        fi
    else
        echo -e "${YELLOW}⚠ 无法设置精确权限，尝试设置为 777${NC}"
        if chmod -R 777 "$DATA_DIR/data" "$DATA_DIR/logs" "$DATA_DIR/backups" 2>/dev/null; then
            echo -e "${YELLOW}✓ 已设置为 777 权限（宽松模式）${NC}"
        else
            echo -e "${RED}✗ 无法修改权限，容器可能无法正常写入文件${NC}"
            echo -e "${YELLOW}建议: 使用 sudo 运行此脚本或手动修复权限${NC}"
        fi
    fi
fi

# 显示修复后的权限
echo ""
echo -e "${CYAN}修复后的权限:${NC}"
ls -lah "$DATA_DIR" 2>/dev/null | grep -E "data|logs|backups" || echo -e "${YELLOW}无法显示详细权限${NC}"

echo ""

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ 未找到 .env 文件，使用默认配置${NC}"
    echo -e "${CYAN}  可以创建 .env 文件来自定义配置（如 REDIS_PASSWORD）${NC}"
else
    echo -e "${GREEN}✓ 找到 .env 配置文件${NC}"
fi

echo ""
echo -e "${CYAN}=== 启动容器 ($PLATFORM) ===${NC}"
echo ""

# 停止并移除旧容器（如果存在）
echo -e "${YELLOW}清理旧容器...${NC}"
$COMPOSE_CMD down 2>/dev/null || true

# 设置环境变量
echo -e "${YELLOW}设置架构环境变量: -$PLATFORM${NC}"
export ARCH_SUFFIX="-$PLATFORM"

echo -e "${YELLOW}启动服务容器...${NC}"
echo ""

# 直接使用 docker-compose，环境变量会自动替换
if $COMPOSE_CMD up -d; then
    echo ""
    echo -e "${GREEN}✓ 容器启动成功！${NC}"
    echo ""
    echo -e "${CYAN}=== 服务信息 ===${NC}"
    echo -e "${WHITE}前端地址: http://localhost:8081${NC}"
    echo -e "${WHITE}后端地址: http://localhost:8000${NC}"
    echo -e "${WHITE}Redis端口: 6379${NC}"
    echo -e "${WHITE}架构平台: $PLATFORM${NC}"
    echo ""
    echo -e "${CYAN}=== 常用命令 ===${NC}"
    echo -e "${WHITE}查看日志: $COMPOSE_CMD logs -f${NC}"
    echo -e "${WHITE}停止服务: $COMPOSE_CMD down${NC}"
    echo -e "${WHITE}重启服务: $COMPOSE_CMD restart${NC}"
    echo -e "${WHITE}查看状态: $COMPOSE_CMD ps${NC}"
    echo ""
    
    # 显示容器状态
    echo -e "${CYAN}=== 容器状态 ===${NC}"
    $COMPOSE_CMD ps
    
else
    echo ""
    echo -e "${RED}✗ 容器启动失败${NC}"
    echo -e "${YELLOW}请检查日志: $COMPOSE_CMD logs${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}完成！${NC}"
