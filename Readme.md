## 项目说明
主要功能为个人便签速记，轻量级多设备定时任务管理和相应消息提醒。它基于 Vue 3 和 Python3 构建，旨在为开发、多设备用户提供集中定时任务管理、以及事项备忘。
并动态构建fn-fpk。
## 项目功能
- 便签
- 多设备定时任务管理
- 消息通知
- 数据备份
- 升级脚本

### 待开发
- SSL申请续签
- 任务连续失败消息通知
- 版本升级消息提醒


## 🐳 Docker 部署
### 构建镜像
```bash
git clone git@github.com:upchr/mytool.git
cd mytool && docker build -t toolsplus:latest -f docker/Dockerfile .
```
### 启动容器
```bash
docker run -d \
  --name toolsplus \
  -p 80:80 \
  -v ./data:/data \
  -e TZ=Asia/Shanghai \
  --restart unless-stopped \
  chrplus/toolsplus:latest
```
```bash
services:
  note-app:
    image: chrplus/toolsplus:latest
    container_name: toolsplus
    ports:
      - "80:80"
    volumes:
      - ./data:/data
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
```
