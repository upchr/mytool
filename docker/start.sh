#!/bin/sh

if [ -z "$JWT_SECRET_KEY" ]; then
  export JWT_SECRET_KEY=$(openssl rand -base64 32)
fi

# 启动 Uvicorn（后台）
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 &

# 启动 Nginx（前台，保持容器运行）
nginx -g 'daemon off;'
