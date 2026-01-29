# ======================
# 第一阶段：构建 Vue 前端
# ======================
FROM node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ======================
# 第二阶段：最终运行镜像
# ======================
FROM python:3.10-slim

RUN apt-get update && apt-get install -y nginx \
    && rm -rf /var/lib/apt/lists/*

COPY --from=frontend-builder /frontend/dist /var/www/html

WORKDIR /toolsplus

# action 构建替换写入
ARG VERSION=unknow
# 启动docker环境
ENV OS_ENV=prod
ENV TZ=Asia/Shanghai

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app

# action 构建替换写入
RUN echo "${VERSION}" > /toolsplus/version.txt

# 复制配置文件（从 docker/ 目录）
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 80
CMD ["/start.sh"]
