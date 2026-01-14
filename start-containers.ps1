# Windows PowerShell 容器启动脚本 (AMD64)
# 用于启动仓库管理系统的所有容器

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== 仓库管理系统容器启动脚本 (AMD64) ===" -ForegroundColor Green
Write-Host ""

# 检查 Docker 是否运行
Write-Host "检查 Docker 服务..." -ForegroundColor Cyan
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host " Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    exit 1
}
Write-Host " Docker 服务正常运行" -ForegroundColor Green
Write-Host ""

# 检查必要的镜像是否存在
Write-Host "检查必要的镜像..." -ForegroundColor Cyan

$requiredImages = @(
    @{Name="warehouse-frontend:latest-amd64"; Description="前端镜像"},
    @{Name="warehouse-backend:latest-amd64"; Description="后端镜像"},
    @{Name="redis:7.2-alpine-amd64"; Description="Redis缓存"}
)

$missingImages = @()
foreach ($img in $requiredImages) {
    $format = '{{.Repository}}:{{.Tag}}'
    $exists = docker images $img.Name --format $format 2>$null
    if ([string]::IsNullOrWhiteSpace($exists)) {
        Write-Host " 缺少 $($img.Name) - $($img.Description)" -ForegroundColor Red
        $missingImages += $img.Name
    } else {
        Write-Host " $($img.Name) 已存在" -ForegroundColor Green
    }
}

if ($missingImages.Count -gt 0) {
    Write-Host ""
    Write-Host "缺少以下镜像，请先构建或加载:" -ForegroundColor Yellow
    foreach ($img in $missingImages) {
        Write-Host "  - $img" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "提示: 使用构建脚本或 docker load 加载镜像文件" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "所有必要的镜像都已就绪！" -ForegroundColor Green
Write-Host ""

# 创建必要的目录
Write-Host "创建数据目录..." -ForegroundColor Cyan

# 后端数据目录
$backendDir = "warehouseBackend"
$backendDirs = @("data", "logs", "backups")

if (-not (Test-Path $backendDir)) {
    New-Item -ItemType Directory -Path $backendDir -Force | Out-Null
}

foreach ($dir in $backendDirs) {
    $path = Join-Path $backendDir $dir
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "✓ 创建目录: $path" -ForegroundColor Green
    }
}

# 前端配置和日志目录
$frontendDirs = @("config", "logs/nginx")
foreach ($dir in $frontendDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "✓ 创建目录: $dir" -ForegroundColor Green
    }
}

# 检查nginx配置文件是否存在，不存在或无效时从源码复制
$nginxConfPath = "config/nginx.conf"
$nginxConfSource = "frontend/config/nginx.conf"

if ((-not (Test-Path $nginxConfPath)) -or ((Get-Item $nginxConfPath).Length -eq 0)) {
    # 从 frontend 源码复制默认配置
    if (Test-Path $nginxConfSource) {
        Copy-Item -Path $nginxConfSource -Destination $nginxConfPath -Force
        Write-Host "✓ 从源码复制nginx配置文件: $nginxConfPath" -ForegroundColor Green
    } else {
        Write-Host "⚠ 未找到nginx配置模板，容器启动时将自动从镜像复制" -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ nginx配置文件已存在: $nginxConfPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "设置目录权限..." -ForegroundColor Cyan
# Windows 不需要特殊权限设置,但确保目录可写
try {
    icacls $backendDir /grant Everyone:F /T /Q > $null 2>&1
    icacls "logs" /grant Everyone:F /T /Q > $null 2>&1
    icacls "config" /grant Everyone:F /T /Q > $null 2>&1
    Write-Host "✓ 权限设置完成" -ForegroundColor Green
} catch {
    Write-Host "⚠ 权限设置失败,可能需要管理员权限" -ForegroundColor Yellow
}

Write-Host ""

# 检查环境变量文件
if (-not (Test-Path ".env")) {
    Write-Host " 未找到 .env 文件，使用默认配置" -ForegroundColor Yellow
    Write-Host "  可以创建 .env 文件来自定义配置（如 REDIS_PASSWORD）" -ForegroundColor Cyan
} else {
    Write-Host " 找到 .env 配置文件" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 启动容器 ===" -ForegroundColor Cyan
Write-Host ""

# 停止并移除旧容器（如果存在）
Write-Host "清理旧容器..." -ForegroundColor Yellow
docker-compose down 2>$null | Out-Null

# 为 AMD64 平台设置镜像标签
$env:ARCH_SUFFIX = "-amd64"

# 启动容器
Write-Host "启动服务容器..." -ForegroundColor Yellow
Write-Host ""

# 直接使用 docker-compose，环境变量会自动替换
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host " 容器启动成功！" -ForegroundColor Green
    Write-Host ""
    Write-Host "=== 服务信息 ===" -ForegroundColor Cyan
    Write-Host "前端地址: http://localhost:8081" -ForegroundColor White
    Write-Host "后端地址: http://localhost:8000" -ForegroundColor White
    Write-Host "Redis端口: 6379" -ForegroundColor White
    Write-Host ""
    Write-Host "=== 常用命令 ===" -ForegroundColor Cyan
    Write-Host "查看日志: docker-compose logs -f" -ForegroundColor White
    Write-Host "停止服务: docker-compose down" -ForegroundColor White
    Write-Host "重启服务: docker-compose restart" -ForegroundColor White
    Write-Host ""
    
    # 显示容器状态
    Write-Host "=== 容器状态 ===" -ForegroundColor Cyan
    docker-compose ps
    
} else {
    Write-Host ""
    Write-Host " 容器启动失败" -ForegroundColor Red
    Write-Host "请检查日志: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "完成！" -ForegroundColor Green
