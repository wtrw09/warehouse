# 简化的 Docker 镜像构建和导出脚本
# 专注于解决网络问题和跨平台构建

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== Docker 镜像快速构建工具 ===" -ForegroundColor Green
Write-Host ""

# 配置
$IMAGE_NAME = "warehouse-frontend"
$TAG = "latest"

# 显示菜单
Write-Host "请选择构建模式：" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 本地快速构建 (AMD64)" -ForegroundColor Yellow
Write-Host "   - 使用传统 docker build"
Write-Host "   - 构建当前平台镜像"
Write-Host "   - 自动导出为 tar 文件"
Write-Host "   - 推荐用于快速测试"
Write-Host ""
Write-Host "2. ARM64 构建 (需要良好的网络)" -ForegroundColor Yellow
Write-Host "   - 使用 buildx 多架构构建"
Write-Host "   - 自动预拉取所需镜像"
Write-Host "   - 导出为 tar 文件"
Write-Host "   - 需要配置镜像加速器"
Write-Host ""
Write-Host "3. 仅导出现有镜像" -ForegroundColor Yellow
Write-Host "   - 将已构建的镜像导出为 tar"
Write-Host "   - 无需重新构建"
Write-Host ""
Write-Host "4. 查看镜像信息" -ForegroundColor Yellow
Write-Host "   - 显示所有相关镜像"
Write-Host "   - 显示镜像大小和架构"
Write-Host ""

$choice = Read-Host "请输入选项 (1-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "=== 本地快速构建 ===" -ForegroundColor Cyan
        Write-Host "正在构建 AMD64 镜像..." -ForegroundColor Yellow
        
        docker build -t "$IMAGE_NAME`:$TAG" .
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 构建成功！" -ForegroundColor Green
            
            $outputFile = "$IMAGE_NAME-amd64-$TAG.tar"
            Write-Host ""
            Write-Host "正在导出镜像到文件: $outputFile" -ForegroundColor Yellow
            
            docker save "$IMAGE_NAME`:$TAG" -o $outputFile
            
            if ($LASTEXITCODE -eq 0) {
                $fileSize = (Get-Item $outputFile).Length / 1MB
                Write-Host ""
                Write-Host "✓ 导出成功！" -ForegroundColor Green
                Write-Host ""
                Write-Host "=== 构建结果 ===" -ForegroundColor Cyan
                Write-Host "镜像名称: $IMAGE_NAME`:$TAG"
                Write-Host "目标架构: AMD64"
                Write-Host "输出文件: $outputFile"
                Write-Host "文件大小: $([math]::Round($fileSize, 2)) MB"
                Write-Host ""
                Write-Host "=== 使用说明 ===" -ForegroundColor Cyan
                Write-Host "传输到服务器:"
                Write-Host "  scp $outputFile user@server:/path/to/destination/"
                Write-Host ""
                Write-Host "加载镜像:"
                Write-Host "  docker load -i $outputFile"
                Write-Host ""
                Write-Host "运行容器:"
                Write-Host "  docker run -d -p 8080:80 $IMAGE_NAME`:$TAG"
            } else {
                Write-Host "✗ 导出失败" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "✗ 构建失败" -ForegroundColor Red
            exit 1
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "=== ARM64 跨平台构建 ===" -ForegroundColor Cyan
        Write-Host ""
        
        # 检查网络连接
        Write-Host "正在测试 Docker Hub 连接..." -ForegroundColor Yellow
        $testPull = docker pull --platform linux/arm64 nginx:alpine 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "✗ 无法连接到 Docker Hub" -ForegroundColor Red
            Write-Host ""
            Write-Host "=== 解决建议 ===" -ForegroundColor Yellow
            Write-Host "1. 配置 Docker 镜像加速器:"
            Write-Host "   - 打开 Docker Desktop -> Settings -> Docker Engine"
            Write-Host "   - 添加镜像源到 registry-mirrors"
            Write-Host ""
            Write-Host "2. 检查网络代理设置:"
            Write-Host "   - Docker Desktop -> Settings -> Resources -> Proxies"
            Write-Host ""
            Write-Host "3. 使用选项 1 进行本地构建（AMD64）"
            Write-Host ""
            Write-Host "详细说明请查看: ARM64_BUILD_GUIDE_CN.md"
            exit 1
        }
        
        Write-Host "✓ 网络连接正常" -ForegroundColor Green
        Write-Host ""
        
        # 拉取必要的镜像
        Write-Host "正在预拉取 ARM64 基础镜像..." -ForegroundColor Yellow
        docker pull --platform linux/arm64 node:22-alpine
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ 拉取 node:22-alpine 失败" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "✓ 基础镜像已准备" -ForegroundColor Green
        Write-Host ""
        
        # 切换构建器
        Write-Host "正在配置构建器..." -ForegroundColor Yellow
        docker buildx use multiarch-builder 2>&1 | Out-Null
        
        # 构建
        $outputFile = "$IMAGE_NAME-arm64-$TAG.tar"
        Write-Host "正在构建 ARM64 镜像..." -ForegroundColor Yellow
        Write-Host ""
        
        docker buildx build `
            --platform linux/arm64 `
            --tag "$IMAGE_NAME`:$TAG" `
            --output type=docker,dest="$outputFile" .
        
        if ($LASTEXITCODE -eq 0) {
            $fileSize = (Get-Item $outputFile).Length / 1MB
            Write-Host ""
            Write-Host "✓ ARM64 构建成功！" -ForegroundColor Green
            Write-Host ""
            Write-Host "=== 构建结果 ===" -ForegroundColor Cyan
            Write-Host "镜像名称: $IMAGE_NAME`:$TAG"
            Write-Host "目标架构: ARM64"
            Write-Host "输出文件: $outputFile"
            Write-Host "文件大小: $([math]::Round($fileSize, 2)) MB"
            Write-Host ""
            Write-Host "=== 使用说明 ===" -ForegroundColor Cyan
            Write-Host "此镜像可在 ARM64 设备上使用（树莓派、Apple Silicon Mac 等）"
            Write-Host ""
            Write-Host "传输到 ARM64 服务器:"
            Write-Host "  scp $outputFile user@arm-server:/path/to/destination/"
            Write-Host ""
            Write-Host "在 ARM64 机器上加载:"
            Write-Host "  docker load -i $outputFile"
            Write-Host ""
            Write-Host "运行容器:"
            Write-Host "  docker run -d -p 8080:80 $IMAGE_NAME`:$TAG"
        } else {
            Write-Host ""
            Write-Host "✗ ARM64 构建失败" -ForegroundColor Red
            Write-Host "详细排查请查看: ARM64_BUILD_GUIDE_CN.md"
            exit 1
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "=== 导出现有镜像 ===" -ForegroundColor Cyan
        
        # 列出可用镜像
        $images = docker images "$IMAGE_NAME" --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -ne "<none>:<none>" }
        
        if ($images.Count -eq 0) {
            Write-Host "✗ 未找到 $IMAGE_NAME 镜像" -ForegroundColor Red
            Write-Host "请先使用选项 1 或 2 构建镜像" -ForegroundColor Yellow
            exit 1
        }
        
        Write-Host "找到以下镜像:" -ForegroundColor Yellow
        $images | ForEach-Object { Write-Host "  - $_" }
        Write-Host ""
        
        $imageName = Read-Host "请输入要导出的镜像名称（例如: $IMAGE_NAME`:$TAG）"
        
        if ([string]::IsNullOrWhiteSpace($imageName)) {
            $imageName = "$IMAGE_NAME`:$TAG"
        }
        
        # 获取架构信息
        $arch = docker image inspect $imageName --format='{{.Architecture}}' 2>$null
        
        if ([string]::IsNullOrWhiteSpace($arch)) {
            $arch = "unknown"
        }
        
        $outputFile = "$IMAGE_NAME-$arch-export.tar"
        Write-Host ""
        Write-Host "正在导出镜像到: $outputFile" -ForegroundColor Yellow
        
        docker save $imageName -o $outputFile
        
        if ($LASTEXITCODE -eq 0) {
            $fileSize = (Get-Item $outputFile).Length / 1MB
            Write-Host ""
            Write-Host "✓ 导出成功！" -ForegroundColor Green
            Write-Host ""
            Write-Host "文件名: $outputFile"
            Write-Host "大小: $([math]::Round($fileSize, 2)) MB"
            Write-Host "架构: $arch"
        } else {
            Write-Host "✗ 导出失败" -ForegroundColor Red
            exit 1
        }
    }
    
    "4" {
        Write-Host ""
        Write-Host "=== 镜像信息 ===" -ForegroundColor Cyan
        Write-Host ""
        
        # 显示 Docker 镜像
        Write-Host "Docker 镜像列表:" -ForegroundColor Yellow
        docker images $IMAGE_NAME
        
        Write-Host ""
        Write-Host "详细信息:" -ForegroundColor Yellow
        docker images "$IMAGE_NAME`:$TAG" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.ID}}" 2>$null
        
        # 显示架构信息
        $arch = docker image inspect "$IMAGE_NAME`:$TAG" --format='{{.Architecture}}' 2>$null
        if (-not [string]::IsNullOrWhiteSpace($arch)) {
            Write-Host ""
            Write-Host "架构: $arch" -ForegroundColor Green
        }
        
        # 显示 tar 文件
        Write-Host ""
        Write-Host "导出的镜像文件:" -ForegroundColor Yellow
        Get-ChildItem -Filter "*.tar" | ForEach-Object {
            $sizeMB = [math]::Round($_.Length / 1MB, 2)
            Write-Host "  - $($_.Name) ($sizeMB MB)"
        }
    }
    
    default {
        Write-Host ""
        Write-Host "无效的选项，请重新运行脚本" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "完成！" -ForegroundColor Green
