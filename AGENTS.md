# ToolsPlus 项目 - AI 代理指令文档

## 项目概述

ToolsPlus 是一个基于 Vue 3 和 Python 3 构建的轻量级多设备定时任务管理和通知系统。该项目为开发者和多设备用户提供集中式定时任务管理、个人备忘服务、AI 对话助手、任务模板市场、工作流编排以及 SSL 证书自动续签功能，解决了跨设备任务同步、通知和自动化问题。

### 核心技术栈

**前端：**
- Vue 3 + Vite 5.0
- Naive UI 组件库
- Pinia 状态管理
- Vue Router 4.x 路由管理
- Monaco Editor 代码编辑器
- Axios HTTP 客户端
- @vue-flow/* 工作流可视化
- markdown-it + highlight.js 内容渲染

**后端：**
- Python 3.8+
- FastAPI 0.128.0 Web 框架
- SQLAlchemy 2.0 ORM
- APScheduler 3.10 定时任务
- JWT 认证
- WebSocket 支持
- ACME 协议（Let's Encrypt）

**部署：**
- Docker 多阶段构建
- Nginx 反向代理
- SQLite 数据库

### 项目架构

项目采用前后端分离架构，通过 Docker 多阶段构建整合，支持 x86 和 arm 平台：

```
mytool/
├── frontend/                 # Vue 3 前端应用
│   ├── src/
│   │   ├── modules/         # 功能模块（便签、定时任务、AI 聊天、工作流等）
│   │   ├── api/             # API 接口定义
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── router/          # 路由配置
│   │   ├── components/      # 公共组件
│   │   ├── assets/          # 静态资源
│   │   └── utils/           # 工具函数
│   └── package.json
├── backend/                  # Python 后端应用
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── core/            # 核心功能（数据库、日志、调度器、路由管理等）
│   │   │   ├── routers.py   # 路由自动发现和注册
│   │   │   ├── db/          # 数据库管理
│   │   │   ├── log/         # 日志配置
│   │   │   ├── scheduler/   # 定时任务调度
│   │   │   ├── middleware/  # 中间件（JWT 认证等）
│   │   │   ├── exception/   # 异常处理
│   │   │   └── utils/       # 工具函数
│   │   └── modules/         # 功能模块（与前端模块对应）
│   └── requirements.txt
├── docker/                   # Docker 配置
│   ├── Dockerfile           # 多阶段构建镜像
│   ├── docker-compose.yaml  # Docker Compose 配置
│   ├── nginx.conf           # Nginx 配置
│   └── start.sh             # 启动脚本
└── data/                     # 数据持久化目录
    ├── certs/               # SSL 证书
    └── logs/                # 日志文件
```

### 核心功能模块

#### 1. 便签管理（Note）
- 快速创建、编辑、删除文本便签
- 支持富文本格式
- 多设备同步

#### 2. 定时任务（Cron）
- 基于 Cron 表达式的任务管理
- 支持多设备任务收集和执行日志
- 任务模板一键导入
- 连续失败预警

#### 3. 节点管理（Node）
- 多设备节点管理和配置
- 节点健康监控
- 自动发现和注册

#### 4. 消息通知（Notify）
- 多通道通知（企业微信、Bark、Webhook 等）
- 连续失败预警机制
- 通知历史记录

#### 5. 证书管理（ACME/SSL）
- 自动申请 Let's Encrypt 证书
- 支持 DNS-01 验证（多种 DNS 提供商）
- 自动续签和到期提醒
- 多域名证书管理

#### 6. 数据管理（Database）
- 模块级备份还原
- 数据导出导入
- 加密存储

#### 7. 系统管理（Sys）
- 用户设置和认证
- 系统配置管理
- 初始化向导

#### 8. 版本管理（Version）
- 版本检查和升级推送
- 升级脚本支持

#### 9. AI 聊天助手（ai_chat）⭐ 新增
- 多 AI 配置管理（支持多个 API Key 和模型）
- 对话历史管理
- 流式响应（SSE）
- 知识库管理（文档上传、分片、检索）
- 上下文对话

#### 10. 任务模板市场（task_template）⭐ 新增
- 官方和社区模板
- 模板分类和标签
- 模板评分和下载统计
- 一键导入模板为定时任务
- Cron 表达式建议

#### 11. 工作流编排（workflow）⭐ 新增
- 可视化工作流编辑器（基于 @vue-flow）
- 节点编排和连接
- 工作流版本控制
- 执行历史和日志
- 手动和自动触发

#### 12. 插件市场（plugin）⭐ 新增
- 内置插件管理
- 插件热加载
- 插件依赖管理

## 构建和运行

### 本地开发

**后端开发：**

创建并激活虚拟环境：
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

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
  -v ./data:/data \
  -e TZ=Asia/Shanghai \
  -e JWT_SECRET_KEY=your_secret_key \
  --restart unless-stopped \
  toolsplus:latest
```

服务启动后访问 `http://localhost`。

### 环境变量

- `TZ` - 时区设置（默认：Asia/Shanghai）
- `JWT_SECRET_KEY` - JWT 密钥（如未设置会自动生成）
- `OS_ENV` - 运行环境（prod/dev）
- `DATABASE_URL` - 数据库连接字符串（默认：SQLite）

## 开发规范

### 后端开发规范

**项目结构：**
- 每个功能模块是一个独立的包，位于 `backend/app/modules/` 下
- 每个模块包含：`api.py`（路由）、`models.py`（数据模型）、`schemas.py`（Pydantic 模式）、`services.py`（业务逻辑）
- 路由通过 `RouterManager` 自动发现和注册，无需手动导入
- 所有路由会自动注册到 FastAPI 应用

**代码规范：**
- 使用 FastAPI 依赖注入进行数据库会话管理
- 使用 Pydantic v2 进行请求验证和响应序列化
- 使用 SQLAlchemy 2.0 ORM 进行数据库操作
- 异常处理通过 `exception_handler.py` 统一处理
- 日志记录使用 Python 标准库 logging 模块

**数据库：**
- 使用 SQLite 作为默认数据库，数据存储在 `/data/` 目录
- 数据库初始化通过 `core/db/init_db.py` 自动执行
- 支持 SQLite 的线程安全配置（`check_same_thread=False`）

**定时任务：**
- 使用 APScheduler 进行任务调度
- 任务配置和执行逻辑位于 `core/scheduler/` 目录
- 支持 Cron 表达式和间隔任务

**安全：**
- JWT 认证通过中间件 `jwt_auth_middleware` 实现
- 密码使用 bcrypt 加密
- 敏感操作需要 JWT token 验证
- 初始化检查中间件 `check_initialization_middleware`

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
- API 调用统一使用 `window.$request` 封装
- 路由配置使用动态导入优化性能
- 使用 `unplugin-vue-components` 自动按需引入 Naive UI 组件

**UI 组件：**
- 使用 Naive UI 组件库
- 图标使用 `@vicons/ionicons5`
- 代码编辑器使用 Monaco Editor
- 工作流编辑器使用 `@vue-flow/*`
- 支持深色模式切换

**路由管理：**
- 路由配置位于 `frontend/src/router/index.js`
- 支持嵌套路由和多级菜单
- 侧边栏菜单通过 `routeLabels` 配置

**全局方法：**
- `window.$request` - 统一的 HTTP 请求工具（已封装认证和错误处理）
- `window.$message` - 消息提示
- `window.$notification` - 通知提示
- `window.$dialog` - 对话框
- `window.$copyCode` - 复制到剪贴板
- `window.$themeStore` - 主题管理

### 模块开发指南

**添加新模块：**

1. **后端模块：**
   - 在 `backend/app/modules/` 下创建新目录
   - 创建 `api.py`，定义路由（使用 FastAPI Router，必须包含 `prefix` 和 `tags`）
   - 创建 `models.py`，定义 SQLAlchemy 模型（使用 Table 定义）
   - 创建 `schemas.py`，定义 Pydantic v2 模式
   - 创建 `services.py`，实现业务逻辑
   - 路由会自动被 `RouterManager` 发现并注册

2. **前端模块：**
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
- 统一响应格式（`core/pojo/response.py`）
- 错误处理使用标准 HTTP 状态码
- 支持 CORS 跨域请求
- WebSocket 支持（用于实时通知和 AI 流式响应）
- 使用 Pydantic v2 进行请求/响应验证

### 数据库迁移

- 数据库初始化通过 `core/db/init_db.py` 自动执行
- 数据库升级通过 `db_upgrade.py` 处理
- 支持数据导出和导入功能

### 日志规范

- 使用 Python logging 模块
- 日志配置在 `core/log/log.py` 中
- 支持不同级别的日志输出
- 日志文件存储在 `/data/logs/` 目录

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

1. **数据持久化：** 确保 `/data/` 目录正确挂载到宿主机
2. **端口映射：** 默认使用 80 端口，可根据需要修改
3. **环境变量：** 生产环境建议设置 `JWT_SECRET_KEY`
4. **时区设置：** 根据实际部署位置设置正确的时区
5. **数据库备份：** 定期备份 SQLite 数据库文件
6. **SSL 证书：** 证书文件存储在 `/data/certs/` 目录

## 故障排查

### 常见问题

1. **数据库连接失败：** 检查 `/data/` 目录权限和挂载
2. **定时任务不执行：** 检查 APScheduler 日志，确认调度器正常启动
3. **SSL 证书申请失败：** 检查 DNS 配置和网络连接
4. **WebSocket 连接失败：** 检查 Nginx 配置中的 WebSocket 代理设置
5. **AI 服务不可用：** 检查 API Key 配置和网络连接

### 日志查看

```bash
# 容器日志
docker logs toolsplus

# 进入容器查看日志
docker exec -it toolsplus bash
ls -la /data/logs/
```

### 已知问题：后端多实例导致 API 404 错误

**问题描述：**
在开发过程中，前端请求某些 API 路由（如 `/ai-chat/*`）时返回 404 错误，即使后端路由已经正确注册。

**根本原因：**
1. uvicorn 的热重载功能在开发模式下会自动重启服务
2. 有时旧的进程没有完全关闭，导致后端启动了多个实例
3. 前端连接到了旧的后端实例，该实例没有最新的路由配置
4. 端口冲突或多次启动也可能导致多个后端实例同时运行

**解决方案：**

1. **检查端口占用情况：**
   ```powershell
   Get-NetTCPConnection -LocalPort 8000 -State Listen
   ```

2. **清理旧进程：**
   ```powershell
   Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
     ForEach-Object { Get-Process -Id $_.OwningProcess } | 
     Stop-Process -Force
   ```

3. **确保只启动一个后端实例：**
   - 启动前检查是否有其他后端进程在运行
   - 留意控制台输出，确认只有一个 uvicorn 进程
   - 使用 `ps` 或任务管理器检查进程列表

**预防措施：**
- 避免重复启动后端服务
- 定期检查并清理僵死的后端进程
- 使用明确的启动脚本，确保启动前清理旧进程
- 在开发环境中使用进程管理工具（如 PM2）来管理后端服务

**相关日志：**
- 后端启动日志会显示注册的路由模块
- 查看日志确认路由是否已注册
- 确认只有一条 "Uvicorn running on http://0.0.0.0:8000" 日志

## 版本信息

- **当前版本：** v2.2.9
- **Python 要求：** 3.8+
- **Node.js 要求：** 18+
- **Docker 要求：** 支持多阶段构建
- **支持平台：** x86、arm

## 贡献指南

1. Fork 项目仓库
2. 创建功能分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 相关链接

- **项目仓库：** https://github.com/upchr/mytool
- **Bug 反馈：** https://github.com/upchr/mytool/issues
- **个人飞牛仓库：** https://github.com/upchr/Fndepot

## 项目分析报告

### 分析日期
2026年3月18日

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
   - 插件化架构

2. **核心功能模块**
   - 便签管理（Note）
   - 定时任务（Cron）
   - 节点管理（Node）
   - 消息通知（Notify）
   - 证书管理（ACME/SSL）
   - 数据管理（Database）
   - 系统管理（Sys）
   - 版本管理（Version）
   - AI 聊天（ai_chat）⭐
   - 任务模板（task_template）⭐
   - 工作流编排（workflow）⭐
   - 插件市场（plugin）⭐

3. **关键技术特性**
   - 统一异常处理机制
   - JWT 认证中间件
   - WebSocket 实时通知
   - 模块级数据备份
   - 多通道通知系统
   - AI 流式响应（SSE）
   - 工作流可视化编辑
   - 自动路由注册

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
   - 完善通用组件使用规范

4. **开发体验优化**
   - 配置 Python 在系统 PATH 中，或使用虚拟环境激活脚本
   - 添加开发环境配置文件（.env.example）
   - 优化开发环境的热重载机制

### 项目优势

- 结构清晰，模块化良好
- 前后端分离，便于独立开发和部署
- Docker 支持完整，部署便捷
- 功能模块丰富，覆盖多设备任务管理场景
- 支持多平台（x86、arm）
- AI 助手和知识库增强智能化
- 工作流编排支持复杂业务流程
- 模板市场降低使用门槛

### 适用场景

- 多设备定时任务管理
- 跨设备便签同步
- SSL 证书自动管理
- 系统运维自动化
- 消息通知聚合
- AI 对话和知识检索
- 复杂工作流编排
- 任务模板复用和共享

## 附录：通用组件使用规范

项目提供了详细的通用组件使用规范文档，位于 `通用组件使用规范.md`，包含：

### DialogForm 组件
- 基于 Naive UI 的表单对话框组件
- 支持平铺模式和分组模式
- 丰富的表单字段类型和验证功能
- 完整的使用示例和最佳实践

### 全局方法
- `window.$request` - 统一请求工具
- `window.$message` - 消息提示
- `window.$notification` - 通知提示
- `window.$dialog` - 对话框
- `window.$copyCode` - 复制工具
- `window.$themeStore` - 主题管理

### 最佳实践
- API 调用规范
- 错误处理规范
- 消息提示规范
- 数据处理规范
- UI 优化建议

---

**文档版本：** v2.0
**最后更新：** 2026年3月18日
**维护者：** iFlow CLI AI Assistant