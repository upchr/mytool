# ToolsPlus 项目 - AI 代理指令文档

## 项目概述

ToolsPlus 是一个基于 Vue 3 和 Python 3 构建的轻量级多设备定时任务管理和通知系统。该项目为开发者和多设备用户提供集中式定时任务管理、个人备忘服务以及 SSL 证书自动续签功能，解决了跨设备任务同步和通知问题。

### 核心技术栈

**前端：**
- Vue 3 + Vite
- Naive UI 组件库
- Pinia 状态管理
- Vue Router 路由管理
- Monaco Editor 代码编辑器
- Axios HTTP 客户端

**后端：**
- Python 3.8+
- FastAPI Web 框架
- SQLAlchemy ORM
- APScheduler 定时任务
- JWT 认证
- WebSocket 支持
- ACME 协议（Let's Encrypt）

**部署：**
- Docker 容器化部署
- Nginx 反向代理
- SQLite 数据库

### 项目架构

项目采用前后端分离架构，通过 Docker 多阶段构建整合：

```
mytool/
├── frontend/          # Vue 3 前端应用
│   ├── src/
│   │   ├── modules/   # 功能模块（便签、定时任务、节点等）
│   │   ├── api/       # API 接口定义
│   │   ├── stores/    # Pinia 状态管理
│   │   ├── router/    # 路由配置
│   │   └── components/# 公共组件
│   └── package.json
├── backend/           # Python 后端应用
│   ├── app/
│   │   ├── main.py    # 应用入口
│   │   ├── core/      # 核心功能（数据库、日志、调度器等）
│   │   └── modules/   # 功能模块（与前端模块对应）
│   └── requirements.txt
└── docker/            # Docker 配置
    ├── Dockerfile
    ├── docker-compose.yaml
    ├── nginx.conf
    └── start.sh
```

### 核心功能模块

1. **便签管理（Note）** - 快速创建、编辑、删除文本便签
2. **定时任务（Cron）** - 基于 Cron 表达式的任务管理，支持多设备任务收集和执行日志
3. **节点管理（Node）** - 多设备节点管理和配置
4. **消息通知（Notify）** - 多通道通知（企业微信、Bark、Webhook 等），支持连续失败预警
5. **证书管理（ACME/SSL）** - 自动申请 Let's Encrypt 证书，支持 DNS-01 验证和自动续签
6. **数据管理（Database）** - 模块级备份还原、数据导出导入
7. **系统管理（Sys）** - 用户设置、系统配置
8. **版本管理（Version）** - 版本检查和升级推送

## 构建和运行

### 本地开发

**后端开发：**
```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

后端服务运行在 `http://localhost:8000`，支持热重载。

**前端开发：**
```bash
cd frontend
npm install
npm run dev
```

前端服务运行在 `http://localhost:5173`（Vite 默认端口）。

**构建生产版本：**
```bash
cd frontend
npm run build
```

构建产物输出到 `frontend/dist/` 目录。

### Docker 部署

**构建镜像：**
```bash
git clone https://github.com/upchr/mytool.git
cd mytool
docker build -t toolsplus:latest -f docker/Dockerfile .
```

**使用 Docker Compose 启动：**
```bash
cd docker
docker-compose up -d
```

**手动启动容器：**
```bash
docker run -d \
  --name toolsplus \
  -p 80:80 \
  -v ./data:/toolsplus/data \
  -e TZ=Asia/Shanghai \
  -e JWT_SECRET_KEY=your_secret_key \
  --restart unless-stopped \
  toolsplus:latest
```

服务启动后访问 `http://localhost`。

### 环境变量

- `TZ` - 时区设置（默认：Asia/Shanghai）
- `JWT_SECRET_KEY` - JWT 密钥（如未设置会自动生成）
- `DATABASE_URL` - 数据库连接字符串（默认：SQLite）
- `OS_ENV` - 运行环境（prod/dev）

## 开发规范

### 后端开发规范

**项目结构：**
- 每个功能模块是一个独立的包，位于 `backend/app/modules/` 下
- 每个模块包含：`api.py`（路由）、`models.py`（数据模型）、`schemas.py`（Pydantic 模式）、`services.py`（业务逻辑）
- 路由通过 `RouterManager` 自动发现和注册，无需手动导入
- 所有路由会自动注册到 FastAPI 应用

**代码规范：**
- 使用 FastAPI 依赖注入进行数据库会话管理
- 使用 Pydantic 进行请求验证和响应序列化
- 使用 SQLAlchemy ORM 进行数据库操作
- 异常处理通过 `exception_handler.py` 统一处理
- 日志记录使用 Python 标准库 logging 模块

**数据库：**
- 使用 SQLite 作为默认数据库，数据存储在 `/toolsplus/data/` 目录
- 数据库初始化通过 `init_db.py` 自动执行
- 支持 SQLite 的线程安全配置（`check_same_thread=False`）

**定时任务：**
- 使用 APScheduler 进行任务调度
- 任务配置和执行逻辑位于 `core/scheduler/` 目录
- 支持 Cron 表达式和间隔任务

**安全：**
- JWT 认证通过中间件 `jwt_auth_middleware` 实现
- 密码使用 bcrypt 加密
- 敏感操作需要 JWT token 验证

### 前端开发规范

**项目结构：**
- 每个功能模块对应一个 Vue 组件，位于 `frontend/src/modules/` 下
- 公共组件位于 `frontend/src/components/` 下
- API 接口定义位于 `frontend/src/api/` 下
- 状态管理使用 Pinia，位于 `frontend/src/stores/` 下

**代码规范：**
- 使用 Composition API 编写组件
- 使用 `<script setup>` 语法糖
- 组件命名使用 PascalCase
- API 调用统一使用 axios 封装（`utils/request.js`）
- 路由配置使用动态导入优化性能

**UI 组件：**
- 使用 Naive UI 组件库
- 图标使用 @vicons/ionicons5
- 代码编辑器使用 Monaco Editor
- 支持深色模式切换

**路由管理：**
- 路由配置位于 `frontend/src/router/index.js`
- 支持嵌套路由和多级菜单
- 侧边栏菜单通过 `routeLabels` 配置

### 模块开发指南

**添加新模块：**

1. 后端模块：
   - 在 `backend/app/modules/` 下创建新目录
   - 创建 `api.py`，定义路由（使用 FastAPI Router）
   - 创建 `models.py`，定义 SQLAlchemy 模型
   - 创建 `schemas.py`，定义 Pydantic 模式
   - 创建 `services.py`，实现业务逻辑
   - 路由会自动被 `RouterManager` 发现并注册

2. 前端模块：
   - 在 `frontend/src/modules/` 下创建新组件
   - 在 `frontend/src/api/` 下创建对应的 API 文件
   - 在 `frontend/src/router/index.js` 中添加路由配置
   - 在 `routeLabels` 中添加菜单项

**示例模块结构：**
```
modules/
└── mymodule/
    ├── __init__.py
    ├── api.py           # FastAPI 路由
    ├── models.py        # SQLAlchemy 模型
    ├── schemas.py       # Pydantic 模式
    └── services.py      # 业务逻辑
```

### API 设计规范

- RESTful API 设计
- 统一响应格式（`pojo/response.py`）
- 错误处理使用标准 HTTP 状态码
- 支持 CORS 跨域请求
- WebSocket 支持（用于实时通知）

### 数据库迁移

- 数据库初始化通过 `init_db.py` 自动执行
- 数据库升级通过 `db_upgrade.py` 处理
- 支持数据导出和导入功能

### 日志规范

- 使用 Python logging 模块
- 日志配置在 `core/log/log.py` 中
- 支持不同级别的日志输出
- 日志文件存储在 `/toolsplus/data/logs/` 目录

## 测试

### 后端测试

```bash
cd backend
pytest tests/
```

### 前端测试

```bash
cd frontend
npm run test
```

## 部署注意事项

1. **数据持久化：** 确保 `/toolsplus/data/` 目录正确挂载到宿主机
2. **端口映射：** 默认使用 80 端口，可根据需要修改
3. **环境变量：** 生产环境建议设置 `JWT_SECRET_KEY`
4. **时区设置：** 根据实际部署位置设置正确的时区
5. **数据库备份：** 定期备份 SQLite 数据库文件

## 故障排查

### 常见问题

1. **数据库连接失败：** 检查 `/toolsplus/data/` 目录权限
2. **定时任务不执行：** 检查 APScheduler 日志，确认调度器正常启动
3. **SSL 证书申请失败：** 检查 DNS 配置和网络连接
4. **WebSocket 连接失败：** 检查 Nginx 配置中的 WebSocket 代理设置

### 日志查看

```bash
# 容器日志
docker logs toolsplus

# 进入容器查看日志
docker exec -it toolsplus bash
ls -la /toolsplus/data/logs/
```

## 版本信息

- 当前版本：v3.x
- Python 要求：3.8+
- Node.js 要求：18+
- Docker 要求：支持多阶段构建

## 贡献指南

1. Fork 项目仓库
2. 创建功能分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 相关链接

- 项目仓库：https://github.com/upchr/mytool
- Bug 反馈：https://github.com/upchr/mytool/issues
- 个人飞牛仓库：https://github.com/upchr/Fndepot

---

## 项目分析报告

### 分析日期
2026年3月17日

### 项目状态

**Git 状态：**
- 当前分支：有未提交的修改
- 未暂存文件：`frontend/vite.config.js`
- 未跟踪文件：大量 `__pycache__` 目录和 `.DS_Store` 文件

**Python 环境：**
- 系统已安装 Python 3.10.6
- 后端使用虚拟环境：`backend/venv/`
- 虚拟环境 Python 版本：3.10

**前端环境：**
- Node.js 依赖已安装（node_modules 存在）
- 使用 Vite 5.0.0 作为构建工具

### 架构特点总结

1. **模块化设计**
   - 前后端模块一一对应
   - RouterManager 自动发现和注册路由
   - 组件化前端开发

2. **核心功能模块**
   - 便签管理（Note）
   - 定时任务（Cron）
   - 节点管理（Node）
   - 消息通知（Notify）
   - 证书管理（ACME/SSL）
   - 数据管理（Database）
   - 系统管理（Sys）
   - 版本管理（Version）
   - AI 聊天（ai_chat）

3. **关键技术特性**
   - 统一异常处理机制
   - JWT 认证中间件
   - WebSocket 实时通知
   - 模块级数据备份
   - 多通道通知系统

### 开发环境配置

**操作系统：** Windows 10 (build 26200)

**开发工具：**
- Git 2.47.0
- Curl 8.18.0
- Python 3.10.6

**后端启动方式：**
```bash
cd backend
.\venv\Scripts\activate
python -m app.main
```

**前端启动方式：**
```bash
cd frontend
npm run dev
```

### 潜在改进建议

1. **版本控制优化**
   - 清理 `__pycache__` 文件，确保 `.gitignore` 配置正确
   - 提交或还原 `frontend/vite.config.js` 的修改

2. **代码质量提升**
   - 添加单元测试和集成测试
   - 配置代码格式化工具（black, prettier）
   - 添加 ESLint/Pylint 静态代码检查

3. **文档完善**
   - API 文档使用 FastAPI 自动生成的 Swagger UI
   - 添加模块级别的开发文档

4. **开发体验优化**
   - 配置 Python 在系统 PATH 中，或使用虚拟环境激活脚本
   - 添加开发环境配置文件（.env.example）

### 项目优势

- 结构清晰，模块化良好
- 前后端分离，便于独立开发和部署
- Docker 支持完整，部署便捷
- 功能模块丰富，覆盖多设备任务管理场景
- 支持多平台（x86、arm）

### 适用场景

- 多设备定时任务管理
- 跨设备便签同步
- SSL 证书自动管理
- 系统运维自动化
- 消息通知聚合