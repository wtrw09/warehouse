# ARM64 离线构建脚本 - 使用本地已有镜像
# 适用于网络受限但已有基础镜像的环境

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== ARM64 后端离线构建工具 ===" -ForegroundColor Green
Write-Host ""

$IMAGE_NAME = "warehouse-backend"
$TAG = "latest"
$OUTPUT_FILE = "$IMAGE_NAME-arm64-$TAG.tar"

# 检查本地是否有必要的基础镜像
Write-Host "检查本地镜像..." -ForegroundColor Cyan

$hasPython = docker images python:3.13-slim-arm64 --format "{{.Repository}}" 2>$null

if ([string]::IsNullOrWhiteSpace($hasPython)) {
    Write-Host "✗ 缺少 python:3.13-slim-arm64 镜像" -ForegroundColor Red
    Write-Host "请先拉取: docker pull --platform linux/arm64 python:3.13-slim" -ForegroundColor Yellow
    Write-Host "然后打标签: docker tag python:3.13-slim python:3.13-slim-arm64" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ python:3.13-slim-arm64 镜像已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 方案选择 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 使用 QEMU 模拟构建 ARM64 (慢但完整)" -ForegroundColor Yellow
Write-Host "   - 在 x86_64 上模拟 ARM64 环境"
Write-Host "   - 使用本地镜像缓存"
Write-Host "   - 构建时间较长（约 10-15 分钟）"
Write-Host "   - 需要安装 QEMU 支持"
Write-Host ""
Write-Host "2. 使用 buildx 导出构建环境 (实验性)" -ForegroundColor Yellow
Write-Host "   - 尝试强制使用本地缓存"
Write-Host "   - 可能仍需网络连接"
Write-Host ""
Write-Host "3. 在目标 ARM64 机器上构建 (推荐)" -ForegroundColor Green
Write-Host "   - 将源代码打包传输到 ARM64 服务器"
Write-Host "   - 在目标机器上直接构建"
Write-Host "   - 速度快且可靠"
Write-Host ""

$choice = Read-Host "请选择方案 (1-3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "=== QEMU 模拟构建 ===" -ForegroundColor Cyan
        Write-Host ""
        
        # 检查 QEMU 支持
        Write-Host "检查 QEMU 支持..." -ForegroundColor Yellow
        
        $qemuCheck = docker run --rm --privileged multiarch/qemu-user-static --reset -p yes 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ QEMU 初始化失败" -ForegroundColor Red
            Write-Host "这可能需要网络下载 QEMU 镜像" -ForegroundColor Yellow
            Write-Host "建议使用方案 3" -ForegroundColor Yellow
            exit 1
        }
        
        Write-Host "✓ QEMU 支持已启用" -ForegroundColor Green
        Write-Host ""
        Write-Host "开始构建 ARM64 后端镜像（这可能需要较长时间）..." -ForegroundColor Yellow
        Write-Host ""
        
        # 使用传统 docker build，指定平台和架构后缀
        docker build --platform linux/arm64 --build-arg PYTHON_ARCH_SUFFIX=-arm64 -t "$IMAGE_NAME`:$TAG-arm64" .
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✓ ARM64 后端镜像构建成功！" -ForegroundColor Green
            Write-Host ""
            Write-Host "导出镜像到文件..." -ForegroundColor Yellow
            
            docker save "$IMAGE_NAME`:$TAG-arm64" -o $OUTPUT_FILE
            
            if ($LASTEXITCODE -eq 0) {
                $fileSize = (Get-Item $OUTPUT_FILE).Length / 1MB
                Write-Host ""
                Write-Host "✓ 导出成功！" -ForegroundColor Green
                Write-Host ""
                Write-Host "=== 构建结果 ===" -ForegroundColor Cyan
                Write-Host "镜像名称: $IMAGE_NAME`:$TAG-arm64"
                Write-Host "目标架构: ARM64"
                Write-Host "输出文件: $OUTPUT_FILE"
                Write-Host "文件大小: $([math]::Round($fileSize, 2)) MB"
                Write-Host ""
                Write-Host "=== 使用说明 ===" -ForegroundColor Cyan
                Write-Host "1. 传输到 ARM64 服务器:"
                Write-Host "   scp $OUTPUT_FILE user@arm-server:/path/"
                Write-Host ""
                Write-Host "2. 在 ARM64 服务器上加载:"
                Write-Host "   docker load -i $OUTPUT_FILE"
                Write-Host ""
                Write-Host "3. 运行容器:"
                Write-Host "   docker run -d -p 8000:8000 --env-file .env $IMAGE_NAME`:$TAG-arm64"
            } else {
                Write-Host "✗ 导出失败" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host ""
            Write-Host "✗ 构建失败" -ForegroundColor Red
            Write-Host "可能是 QEMU 模拟环境问题，建议使用方案 3" -ForegroundColor Yellow
            exit 1
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "=== 使用 Buildx 强制本地缓存 ===" -ForegroundColor Cyan
        Write-Host ""
        
        # 切换回 default 构建器
        docker buildx use default 2>&1 | Out-Null
        
        Write-Host "尝试使用本地构建器..." -ForegroundColor Yellow
        Write-Host ""
        
        # 尝试使用 buildx 但不导出到 tar（先加载到本地）
        docker buildx build --platform linux/arm64 --build-arg PYTHON_ARCH_SUFFIX=-arm64 --load -t "$IMAGE_NAME`:$TAG-arm64" . 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✓ 构建成功！" -ForegroundColor Green
            Write-Host "导出镜像..." -ForegroundColor Yellow
            
            docker save "$IMAGE_NAME`:$TAG-arm64" -o $OUTPUT_FILE
            
            if ($LASTEXITCODE -eq 0) {
                $fileSize = (Get-Item $OUTPUT_FILE).Length / 1MB
                Write-Host "✓ 导出成功！文件大小: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green
            }
        } else {
            Write-Host ""
            Write-Host "✗ 此方案不可用" -ForegroundColor Red
            Write-Host "默认构建器可能不支持 ARM64 构建" -ForegroundColor Yellow
            Write-Host "建议使用方案 1 或方案 3" -ForegroundColor Yellow
            exit 1
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "=== 准备源代码包 ===" -ForegroundColor Cyan
        Write-Host ""
        
        $sourcePackage = "$IMAGE_NAME-source.tar.gz"
        
        Write-Host "正在打包源代码..." -ForegroundColor Yellow
        
        # 使用 PowerShell 压缩
        $sourceFiles = @(
            "backup",
            "config",
            "core",
            "database",
            "initialize",
            "models",
            "routes",
            "schemas",
            "utils",
            "main.py",
            "requirements.txt",
            "Dockerfile",
            ".dockerignore"
        )
        
        Compress-Archive -Path $sourceFiles -DestinationPath "warehouse-backend-source.zip" -Force
        
        if (Test-Path "warehouse-backend-source.zip") {
            $packageSize = (Get-Item "warehouse-backend-source.zip").Length / 1MB
            Write-Host ""
            Write-Host "✓ 源代码打包完成！" -ForegroundColor Green
            Write-Host ""
            Write-Host "=== 源代码包信息 ===" -ForegroundColor Cyan
            Write-Host "文件名: warehouse-backend-source.zip"
            Write-Host "大小: $([math]::Round($packageSize, 2)) MB"
            Write-Host ""
            Write-Host "=== 在 ARM64 机器上构建步骤 ===" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "1. 传输源代码包到 ARM64 服务器:"
            Write-Host "   scp warehouse-backend-source.zip user@arm-server:/path/" -ForegroundColor White
            Write-Host ""
            Write-Host "2. 在 ARM64 服务器上解压:"
            Write-Host "   unzip warehouse-backend-source.zip -d warehouse-backend" -ForegroundColor White
            Write-Host "   cd warehouse-backend" -ForegroundColor White
            Write-Host ""
            Write-Host "3. 在 ARM64 服务器上构建:"
            Write-Host "   docker build -t warehouse-backend:latest ." -ForegroundColor White
            Write-Host ""
            Write-Host "4. 运行容器:"
            Write-Host "   docker run -d -p 8000:8000 --env-file .env warehouse-backend:latest" -ForegroundColor White
            Write-Host ""
            Write-Host "优势:" -ForegroundColor Green
            Write-Host "  ✓ 无需跨平台编译，速度快"
            Write-Host "  ✓ 直接使用目标架构，兼容性好"
            Write-Host "  ✓ 可以使用目标机器的本地镜像缓存"
            Write-Host ""
        } else {
            Write-Host "✗ 打包失败" -ForegroundColor Red
            exit 1
        }
    }
    
    default {
        Write-Host ""
        Write-Host "无效的选项" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "完成！" -ForegroundColor Green
