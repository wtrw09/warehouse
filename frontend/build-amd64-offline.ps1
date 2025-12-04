# AMD64 离线构建脚本 - 使用本地已有镜像
# 适用于网络受限但已有基础镜像的环境

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== AMD64 离线构建工具 ===" -ForegroundColor Green
Write-Host ""

$IMAGE_NAME = "warehouse-frontend"
$TAG = "latest"
$OUTPUT_FILE = "$IMAGE_NAME-amd64-$TAG.tar"

# 检查本地是否有必要的基础镜像
Write-Host "检查本地镜像..." -ForegroundColor Cyan

$hasNode = docker images node:22-alpine-amd64 --format "{{.Repository}}" 2>$null
$hasNginx = docker images nginx:alpine-amd64 --format "{{.Repository}}" 2>$null

if ([string]::IsNullOrWhiteSpace($hasNode)) {
    Write-Host "✗ 缺少 node:22-alpine-amd64 镜像" -ForegroundColor Red
    Write-Host "请先拉取: docker pull --platform linux/amd64 node:22-alpine" -ForegroundColor Yellow
    Write-Host "然后打标签: docker tag node:22-alpine node:22-alpine-amd64" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ node:22-alpine-amd64 镜像已存在" -ForegroundColor Green
}

if ([string]::IsNullOrWhiteSpace($hasNginx)) {
    Write-Host "✗ 缺少 nginx:alpine-amd64 镜像" -ForegroundColor Red
    Write-Host "请先拉取: docker pull --platform linux/amd64 nginx:alpine" -ForegroundColor Yellow
    Write-Host "然后打标签: docker tag nginx:alpine nginx:alpine-amd64" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ nginx:alpine-amd64 镜像已存在" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 方案选择 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. 直接构建 AMD64 镜像 (推荐)" -ForegroundColor Green
Write-Host "   - 本机架构构建，速度快"
Write-Host "   - 使用本地镜像缓存"
Write-Host "   - 构建时间较短（约 2-5 分钟）"
Write-Host "   - 适合 x86_64 架构的机器"
Write-Host ""
Write-Host "2. 使用 buildx 构建 AMD64 (兼容性)" -ForegroundColor Yellow
Write-Host "   - 明确指定 AMD64 平台"
Write-Host "   - 确保构建正确的架构"
Write-Host "   - 使用本地缓存"
Write-Host ""
Write-Host "3. 准备源代码包 (跨机器部署)" -ForegroundColor Yellow
Write-Host "   - 将源代码打包传输到目标服务器"
Write-Host "   - 在目标机器上直接构建"
Write-Host "   - 适合在其他 AMD64 机器上构建"
Write-Host ""

$choice = Read-Host "请选择方案 (1-3)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "=== 直接构建 AMD64 镜像 ===" -ForegroundColor Cyan
        Write-Host ""
        
        Write-Host "开始构建 AMD64 镜像..." -ForegroundColor Yellow
        Write-Host ""
        
        # 使用传统 docker build，指定架构后缀
        docker build --build-arg NODE_ARCH_SUFFIX=-amd64 --build-arg NGINX_ARCH_SUFFIX=-amd64 -t "$IMAGE_NAME`:$TAG-amd64" .
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✓ AMD64 镜像构建成功！" -ForegroundColor Green
            Write-Host ""
            Write-Host "导出镜像到文件..." -ForegroundColor Yellow
            
            docker save "$IMAGE_NAME`:$TAG-amd64" -o $OUTPUT_FILE
            
            if ($LASTEXITCODE -eq 0) {
                $fileSize = (Get-Item $OUTPUT_FILE).Length / 1MB
                Write-Host ""
                Write-Host "✓ 导出成功！" -ForegroundColor Green
                Write-Host ""
                Write-Host "=== 构建结果 ===" -ForegroundColor Cyan
                Write-Host "镜像名称: $IMAGE_NAME`:$TAG-amd64"
                Write-Host "目标架构: AMD64"
                Write-Host "输出文件: $OUTPUT_FILE"
                Write-Host "文件大小: $([math]::Round($fileSize, 2)) MB"
                Write-Host ""
                Write-Host "=== 使用说明 ===" -ForegroundColor Cyan
                Write-Host "1. 传输到 AMD64 服务器:"
                Write-Host "   scp $OUTPUT_FILE user@server:/path/"
                Write-Host ""
                Write-Host "2. 在 AMD64 服务器上加载:"
                Write-Host "   docker load -i $OUTPUT_FILE"
                Write-Host ""
                Write-Host "3. 运行容器:"
                Write-Host "   docker run -d -p 8080:80 $IMAGE_NAME`:$TAG-amd64"
            } else {
                Write-Host "✗ 导出失败" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host ""
            Write-Host "✗ 构建失败" -ForegroundColor Red
            exit 1
        }
    }
    
    "2" {
        Write-Host ""
        Write-Host "=== 使用 Buildx 构建 AMD64 ===" -ForegroundColor Cyan
        Write-Host ""
        
        Write-Host "开始构建 AMD64 镜像..." -ForegroundColor Yellow
        Write-Host ""
        
        # 使用 buildx 明确指定平台和架构后缀
        docker buildx build --platform linux/amd64 --build-arg NODE_ARCH_SUFFIX=-amd64 --build-arg NGINX_ARCH_SUFFIX=-amd64 --load -t "$IMAGE_NAME`:$TAG-amd64" .
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "✓ 构建成功！" -ForegroundColor Green
            Write-Host "导出镜像..." -ForegroundColor Yellow
            
            docker save "$IMAGE_NAME`:$TAG-amd64" -o $OUTPUT_FILE
            
            if ($LASTEXITCODE -eq 0) {
                $fileSize = (Get-Item $OUTPUT_FILE).Length / 1MB
                Write-Host "✓ 导出成功！文件大小: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green
            }
        } else {
            Write-Host ""
            Write-Host "✗ 此方案不可用" -ForegroundColor Red
            Write-Host "请尝试方案 1" -ForegroundColor Yellow
            exit 1
        }
    }
    
    "3" {
        Write-Host ""
        Write-Host "=== 准备源代码包 ===" -ForegroundColor Cyan
        Write-Host ""
        
        $sourcePackage = "$IMAGE_NAME-source.tar.gz"
        
        Write-Host "正在打包源代码..." -ForegroundColor Yellow
        
        # 使用 tar 打包（排除不必要的文件）
        $excludePattern = @(
            "node_modules",
            "dist",
            "*.tar",
            "*.tar.gz",
            ".git",
            ".vscode"
        )
        
        # 创建临时目录列表文件
        Get-ChildItem -Recurse | Where-Object {
            $item = $_
            $exclude = $false
            foreach ($pattern in $excludePattern) {
                if ($item.FullName -like "*$pattern*") {
                    $exclude = $true
                    break
                }
            }
            -not $exclude
        } | Select-Object -ExpandProperty FullName | Out-File -FilePath "temp_files.txt" -Encoding UTF8
        
        # 使用 PowerShell 压缩
        $sourceFiles = @(
            "src",
            "public",
            "package.json",
            "package-lock.json",
            "Dockerfile",
            "nginx.conf",
            "vite.config.ts",
            "tsconfig.json",
            "tsconfig.node.json",
            "index.html",
            "vite-env.d.ts"
        )
        
        Compress-Archive -Path $sourceFiles -DestinationPath "warehouse-frontend-source.zip" -Force
        
        if (Test-Path "warehouse-frontend-source.zip") {
            $packageSize = (Get-Item "warehouse-frontend-source.zip").Length / 1MB
            Write-Host ""
            Write-Host "✓ 源代码打包完成！" -ForegroundColor Green
            Write-Host ""
            Write-Host "=== 源代码包信息 ===" -ForegroundColor Cyan
            Write-Host "文件名: warehouse-frontend-source.zip"
            Write-Host "大小: $([math]::Round($packageSize, 2)) MB"
            Write-Host ""
            Write-Host "=== 在 AMD64 机器上构建步骤 ===" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "1. 传输源代码包到 AMD64 服务器:"
            Write-Host "   scp warehouse-frontend-source.zip user@server:/path/" -ForegroundColor White
            Write-Host ""
            Write-Host "2. 在 AMD64 服务器上解压:"
            Write-Host "   unzip warehouse-frontend-source.zip -d warehouse-frontend" -ForegroundColor White
            Write-Host "   cd warehouse-frontend" -ForegroundColor White
            Write-Host ""
            Write-Host "3. 在 AMD64 服务器上构建:"
            Write-Host "   docker build -t warehouse-frontend:latest ." -ForegroundColor White
            Write-Host ""
            Write-Host "4. 运行容器:"
            Write-Host "   docker run -d -p 8080:80 warehouse-frontend:latest" -ForegroundColor White
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
        
        # 清理临时文件
        if (Test-Path "temp_files.txt") {
            Remove-Item "temp_files.txt"
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
