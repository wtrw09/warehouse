# 使用多架构兼容的Node.js基础镜像
# 使用构建参数指定架构后缀
ARG NODE_ARCH_SUFFIX=
FROM node:22-alpine${NODE_ARCH_SUFFIX} AS builder

# 设置工作目录
WORKDIR /app

# 配置国内镜像源
RUN npm config set registry https://registry.npmmirror.com/

# 复制package.json和package-lock.json
COPY package*.json ./

# 安装依赖（包括开发依赖，用于构建）
RUN npm ci

# 复制必要的源代码文件
COPY src/ ./src/
COPY public/ ./public/
COPY package.json ./
COPY package-lock.json ./
COPY vite.config.ts ./
COPY tsconfig.json ./
COPY tsconfig.node.json ./
COPY index.html ./
# 确保assets目录被复制
COPY src/assets/ ./src/assets/

# 构建应用
RUN npm run build

# 使用多架构兼容的nginx基础镜像
ARG NGINX_ARCH_SUFFIX=
FROM nginx:alpine${NGINX_ARCH_SUFFIX}

# 设置镜像元数据，支持多架构
LABEL org.opencontainers.image.title="MWSTest Frontend"
LABEL org.opencontainers.image.description="Multi-architecture compatible frontend application"
LABEL org.opencontainers.image.licenses="MIT"

# 安装logrotate工具用于日志轮转
RUN apk add --no-cache logrotate \
    && mkdir -p /etc/logrotate.d \
    && mkdir -p /var/lib/logrotate

# 复制默认nginx配置文件到容器内（两个副本：默认配置和模板）
COPY config/nginx.conf /etc/nginx/nginx.conf.default
COPY config/nginx.conf /etc/nginx/nginx.conf.template

# 复制构建好的文件到nginx目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 创建nginx配置目录并移除默认配置
RUN mkdir -p /etc/nginx/conf.d && \
    rm -f /etc/nginx/conf.d/default.conf

# 创建启动脚本，支持外部配置覆盖
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 创建必要的目录并设置权限
RUN mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

# 设置启动脚本（使用sh明确调用）
ENTRYPOINT ["/bin/sh", "/docker-entrypoint.sh"]

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]