# Dockerfile for FastAPI Application (Production)
# 支持多架构：amd64, arm64
# 使用构建参数指定基础镜像架构后缀
ARG PYTHON_ARCH_SUFFIX=
FROM python:3.13-slim${PYTHON_ARCH_SUFFIX} as builder

# 设置工作目录
WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai

# 使用国内镜像源加速系统包安装
RUN echo 'deb http://mirrors.aliyun.com/debian/ bookworm main' > /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian/ bookworm-updates main' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian-security bookworm-security main' >> /etc/apt/sources.list

# 安装系统依赖和交叉编译工具
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖（使用国内镜像源加速）
RUN pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs data backups data_template

# 清理不需要的文件，并将 system_config.db 保存为模板
RUN rm -f data/warehouse.db data/warehouse.db.backup && \
    rm -f logs/*.log && \
    rm -rf backups/* && \
    # 将 system_config.db 复制到模板目录（供容器启动时使用）\
    if [ -f data/system_config.db ]; then \
        cp data/system_config.db data_template/system_config.db && \
        echo "✓ 已保存 system_config.db 为模板" ; \
    else \
        echo "警告: system_config.db 不存在，需要初始化！" ; \
    fi && \
    # 清空 data 目录（让挂载卷决定使用哪个数据库）\
    rm -f data/*.db

# 设置环境变量
ENV PYTHONPATH=/app

# 设置非root用户运行（安全最佳实践）
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# 最终运行时镜像
ARG PYTHON_ARCH_SUFFIX=
FROM python:3.13-slim${PYTHON_ARCH_SUFFIX}

# 设置工作目录
WORKDIR /app

# 设置时区
ENV TZ=Asia/Shanghai

# 使用国内镜像源加速系统包安装
RUN echo 'deb http://mirrors.aliyun.com/debian/ bookworm main' > /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian/ bookworm-updates main' >> /etc/apt/sources.list && \
    echo 'deb http://mirrors.aliyun.com/debian-security bookworm-security main' >> /etc/apt/sources.list

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的Python包和应用代码
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /app /app

# 复制并设置 entrypoint 脚本（在创建用户前，以 root 身份执行）
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 设置非root用户运行
RUN useradd -m -u 1000 appuser

# 创建必要的目录并设置权限
RUN mkdir -p /app/logs /app/data /app/backups && \
    chown -R appuser:appuser /app

USER appuser

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 使用 entrypoint 脚本
ENTRYPOINT ["/docker-entrypoint.sh"]

# 启动命令（使用uvicorn生产服务器）
CMD ["python", "main.py"]