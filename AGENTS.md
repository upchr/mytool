# ToolsPlus 项目 - AI 代理指令文档
## 📚 文档导航

| 文档 | 用途 |
|------|------|
| [AGENTS.md](AGENTS.md⭐) | 项目概览（本文档） |
| [AI开发规范文档.md](AI开发规范文档.md)  | ai 自主开发完整规范说明 |
| [通用组件使用规范.md](通用组件使用规范.md) | DialogForm 组件和全局方法使用详细说明 |

## 项目概述

ToolsPlus 是一个基于 Vue 3 和 Python 3 构建的轻量级多设备定时任务管理和通知系统。该项目为开发者和多设备用户提供集中式定时任务管理、个人备忘服务、AI 对话助手、SSL 证书自动续签、固定资产管理、工作流自动化、CPE 设备管理和 Docker 容器管理功能，解决了跨设备任务同步、通知和自动化问题。

> **🤖 AI 开发重要提示**：当 AI 代理需要为本项目开发新功能或模块时，**必须**遵循以下开发规范文档：
> - **[AI开发规范文档.md](AI开发规范文档.md)** - 详细的 AI 自主开发规范，包含前后端代码结构、注释规范、最佳实践和提示词模板
> - **[通用组件使用规范.md](通用组件使用规范.md)** - DialogForm 组件和全局方法的使用规范
>
> **参考模块**：AI 开发时应参考“证书管理”模块 `backend/app/modules/acme`（后端代码）和 `frontend/src/modules/ssl`（前端代码），这里展示了完整的代码结构和最佳实践。

### 核心技术栈

**前端：**
- Vue 3.4.x + Vite 5.0.0
- Naive UI 2.43.2 组件库
- Pinia 3.0.4 状态管理
- Vue Router 4.6.4 路由管理
- Monaco Editor 0.55.1 代码编辑器
- Axios 1.7.0 HTTP 客户端
- markdown-it 14.1.1 + highlight.js 11.11.1 内容渲染
- @vicons/ionicons5 图标库
- @vue-flow/core + @vue-flow/controls + @vue-flow/minimap + @vue-flow/background（工作流可视化）
- echarts 6.0.0 图表库
- @vueuse/core 14.1.0 Vue 工具函数

**后端：**
- Python 3.8+
- FastAPI 0.128.0 Web 框架
- Uvicorn 0.23.2 ASGI 服务器
- SQLAlchemy 2.0.22 ORM
- APScheduler 3.10.4 定时任务
- PyJWT 2.8.0+ JWT 认证
- WebSocket 实时通信
- ACME 协议（Let's Encrypt 证书管理）
- python-dotenv 1.0.1+ 环境变量管理
- paramiko 3.4.0 SSH 连接
- pyOpenSSL 25.3.0+ OpenSSL 加密
- cryptography 43.0.0+ 加密库
- bcrypt 4.0.1 密码加密
- httpx 0.27.0 HTTP 客户端
- dnspython 2.4.0+ DNS 操作

**部署：**
- Docker 多阶段构建（Node.js 18-alpine + Python 3.10-slim）
- Nginx 反向代理
- SQLite 数据库
- 支持 x86 和 arm 平台
- 支持飞牛（FNOS）打包

### 项目架构

项目采用前后端分离架构，通过 Docker 多阶段构建整合，支持 x86 和 arm 平台：

```
mytool/
├── frontend/                 # Vue 3 前端应用
│   ├── src/
│   │   ├── modules/         # 功能模块（便签、定时任务、AI 聊天、SSL 证书、固定资产、工作流等）
│   │   ├── api/             # API 接口定义（ai-chat.ts、asset.ts、note.ts、plugin.ts、task-template.ts、workflow.ts）
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── router/          # 路由配置
│   │   ├── components/      # 公共组件
│   │   ├── assets/          # 静态资源
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── vite.config.js       # Vite 配置
├── backend/                  # Python 后端应用
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── core/            # 核心功能（数据库、日志、调度器、路由管理等）
│   │   │   ├── routers.py   # 路由自动发现和注册
│   │   │   ├── config/      # 配置管理
│   │   │   ├── db/          # 数据库管理
│   │   │   ├── log/         # 日志配置
│   │   │   ├── scheduler/   # 定时任务调度
│   │   │   ├── middleware/  # 中间件（JWT 认证等）
│   │   │   ├── exception/   # 异常处理
│   │   │   ├── pojo/        # 数据对象（响应等）
│   │   │   ├── utils/       # 工具函数
│   │   │   ├── ws/          # WebSocket 管理
│   │   │   └── sh/          # Shell 工具
│   │   └── modules/         # 功能模块（acme、ai_chat、asset、cpe、cron、database、docker、example、node、note、notify、sys、version、workflow）
│   ├── requirements.txt
│   └── version.txt          # 版本信息
├── docker/                   # Docker 配置
│   ├── Dockerfile           # 多阶段构建镜像
│   ├── docker-compose.yaml  # Docker Compose 配置
│   ├── nginx.conf           # Nginx 配置
│   ├── start.sh             # 启动脚本
│   └── fnfpk/               # 飞牛打包配置
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

#### 9. AI 聊天助手（ai_chat）⭐
- 多 AI 配置管理（支持多个 API Key 和模型）
- 对话历史管理
- 流式响应（SSE）
- 知识库管理（文档上传、分片、检索）
- 上下文对话

#### 10. 固定资产管理（Asset）⭐
- 资产信息管理（名称、类别、价格、购买日期等）
- 自动计算使用天数、日均成本、质保期等
- 资产报废管理（单个和批量报废）
- 统计分析功能：
  - 资产摘要（总数、总价值、按类别和年份统计）
  - 类别分布（饼图）
  - 年度购买趋势（柱状图）
  - 价值排行榜
  - 即将过质保资产提醒

#### 11. 工作流管理（Workflow）⭐
- 可视化工作流编辑器（基于 Vue Flow）
- 工作流创建、编辑、删除
- 工作流执行和监控
- 节点执行记录查看
- 版本管理（创建版本、版本列表、恢复版本、设置默认版本）
- 工作流格式验证
- 支持手动触发工作流执行

#### 12. CPE 设备管理（CPE）⭐
- 烽火 5G CPE 路由器管理
- CPE 配置管理（设备 IP、用户名、密码等）
- 自动监控功能（信号强度、流量统计）
- 实时流量统计和告警
- 信号质量监控和预警
- 配置的启用/禁用管理

#### 13. Docker 容器管理（Docker）⭐
- 多节点 Docker 容器管理
- 容器列表查看（运行中/已停止）
- 容器操作（启动、停止、重启、删除）
- 容器日志实时查看（支持 WebSocket）
- 容器终端访问（支持 WebSocket）
- 镜像管理
- 网络和卷管理

## 构建和运行

### 本地开发

**后端：**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m app.main
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

**构建：**
```bash
cd frontend
npm run build
```

### Docker 部署

```bash
# 构建镜像
docker build -t toolsplus:latest -f docker/Dockerfile .

# 使用 Docker Compose
cd docker
docker-compose up -d

# 手动启动
docker run -d --name toolsplus -p 80:80 -v ./data:/data toolsplus:latest
```

### 环境变量

- `TZ` - 时区（默认：Asia/Shanghai）
- `JWT_SECRET_KEY` - JWT 密钥（自动生成）
- `OS_ENV` - 运行环境（prod/dev）
- `DATABASE_URL` - 数据库连接（默认：SQLite）

## 开发规范

> **🤖 AI 开发重要提示**：本项目提供完整的开发规范文档，确保代码质量和开发效率。
>
> **必读文档：**
> - **[AI开发规范文档.md](AI开发规范文档.md)** ⭐ - 完整的 AI 开发规范，包含前后端代码结构、注释规范、最佳实践和提示词模板
> - **[通用组件使用规范.md](通用组件使用规范.md)** - DialogForm 组件和全局方法的使用规范
>
> **参考模块：**
> - 后端：`backend/app/modules/acme`（证书管理）
> - 前端：`frontend/src/modules/ssl`（SSL 管理）
>
> **AI 开发工作流：**
> 1. 阅读 [AGENTS.md](AGENTS.md) 了解项目
> 2. 学习 [AI开发规范文档.md](AI开发规范文档.md)
> 3. 参考 [通用组件使用规范.md](通用组件使用规范.md)
> 4. 使用提示词模板生成代码
> 5. 使用检查清单验证代码

### 后端开发规范

**项目结构：**
- 每个功能模块是一个独立的包，位于 `backend/app/modules/` 下
- 每个模块包含：`api.py`（路由）、`models.py`（数据模型）、`schemas.py`（Pydantic 模式）、`services.py`（业务逻辑）
- 路由通过 `RouterManager` 自动发现和注册，无需手动导入
- 所有路由会自动注册到 FastAPI 应用
- 当前已注册模块：acme、ai_chat、asset、cpe、cron、database、docker、example、node、note、notify、sys、version、workflow

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

> **💡 前端开发提示**：前端开发应重点参考以下文档：
> - **[通用组件使用规范.md](通用组件使用规范.md)** - DialogForm 组件和全局方法的详细使用规范
> - **[AI开发规范文档.md](AI开发规范文档.md)** 第三章 - 前端开发详细规范
>
> **参考组件：** `frontend/src/modules/ssl/DNS.vue` 展示了完整的前端组件开发模式

**项目结构：**
- 每个功能模块对应一个 Vue 组件，位于 `frontend/src/modules/` 下
- 公共组件位于 `frontend/src/components/` 下
- API 接口定义位于 `frontend/src/api/` 下（当前包括 ai-chat.ts、asset.ts、note.ts、plugin.ts、task-template.ts、workflow.ts，新增功能模块可在相应 Vue 组件中直接定义 API 调用）
- 状态管理使用 Pinia，位于 `frontend/src/stores/` 下

**代码规范：**
- 使用 Composition API 编写组件
- 使用 `<script setup>` 语法糖
- 组件命名使用 PascalCase
- API 调用统一使用 `window.$request` 封装
- 路由配置使用动态导入优化性能
- 使用 `unplugin-vue-components` 30.0.0 自动按需引入 Naive UI 组件

**UI 组件：**
- 使用 Naive UI 2.43.2 组件库
- 图标使用 `@vicons/ionicons5`
- 代码编辑器使用 Monaco Editor 0.55.1
- 支持深色模式切换

**路由管理：**
- 路由配置位于 `frontend/src/router/index.js`
- 支持嵌套路由和多级菜单
- 侧边栏菜单通过 `routeLabels` 配置
- 当前支持的主要路由：`/`（便签）、`/nodes`（节点）、`/jobs`（任务）、`/workflows`（工作流）、`/workflow-execution-log`（工作流执行日志）、`/notify`（通知）、`/database`（数据）、`/versions`（版本）、`/sys`（系统）、`/asset`（固定资产）、`/ai-chat`（AI 聊天）、`/ai-config`（AI 配置）、`/ai-knowledge`（知识库）、`/ssl-apply`（证书申请）、`/ssl-dns`（DNS 授权）、`/ssl-store`（证书仓库）、`/cpe`（CPE 设备）、`/docker`（Docker 管理）

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

```bash
# 后端测试
cd backend
pytest tests/

# 前端测试
cd frontend
npm run test
```

## 部署注意事项

- 确保 `/data/` 目录正确挂载到宿主机
- 生产环境建议设置 `JWT_SECRET_KEY`
- 定期备份 SQLite 数据库文件
- 证书文件存储在 `/data/certs/` 目录

## 故障排查

### 常见问题

- **数据库连接失败**：检查 `/data/` 目录权限和挂载
- **定时任务不执行**：检查 APScheduler 日志
- **API 404 错误**：可能是后端多实例导致，清理占用8000端口的进程

### 日志查看

```bash
docker logs toolsplus
docker exec -it toolsplus bash
ls -la /data/logs/
```

### 已知问题：后端多实例导致 API 404 错误

**原因**：uvicorn 热重载可能导致旧进程未完全关闭

**解决方案**：
```powershell
# 检查端口占用
Get-NetTCPConnection -LocalPort 8000 -State Listen

# 清理旧进程
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
  ForEach-Object { Get-Process -Id $_.OwningProcess } | 
  Stop-Process -Force
```

## 版本信息

- **当前版本：** v3.4.0
- **Python 要求：** 3.8+
- **Node.js 要求：** 18+
- **Docker 要求：** 支持多阶段构建
- **支持平台：** x86、arm

**项目仓库：**
- Gitee: https://gitee.com/upchr/mytool.git
- GitHub: https://github.com/upchr/mytool

## 贡献指南

1. Fork 项目仓库
2. 创建功能分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

## 相关链接

- **项目仓库（Gitee）：** https://gitee.com/upchr/mytool.git
- **项目仓库（GitHub）：** https://github.com/upchr/mytool
- **Bug 反馈：** https://github.com/upchr/mytool/issues
- **个人飞牛仓库：** https://github.com/upchr/Fndepot

## 附录：开发规范文档

### 📚 完整的开发文档体系

项目提供了完整的开发规范文档，确保代码质量和开发效率：

#### 1. **[AI开发规范文档.md](AI开发规范文档.md)** ⭐
**适用于 AI 代理开发的完整规范文档**

**内容包含：**
- **后端开发规范**
    - 目录结构（api.py、models.py、schemas.py、services.py、repository.py）
    - 路由定义规范（RESTful、响应格式、注释规范）
    - 数据模型规范（Table 定义、字段类型）
    - Pydantic 模式规范（Schema 层次结构、Field 使用）
    - 业务逻辑层规范（Service 类结构、方法命名）
    - 数据访问层规范（Repository 类、QueryBuilder 使用）
    - 统一响应格式（BaseResponse）
    - 异常处理规范

- **前端开发规范**
    - 目录结构
    - 组件结构（模板、脚本、样式）
    - 全局方法使用（window.$request、window.$message、window.$dialog）
    - DialogForm 组件使用
    - 表格列定义
    - 分页配置

- **代码注释规范**
    - 后端注释（类、方法、参数、返回值、异常）
    - 前端注释（组件、函数、状态）

- **最佳实践**
    - 后端最佳实践（依赖注入、异常处理、QueryBuilder、数据脱敏、批量操作）
    - 前端最佳实践（全局方法、错误处理、表单验证、表格渲染、分页配置）

- **AI 开发指南**
    - 后端模块开发提示词模板
    - 前端组件开发提示词模板
    - 代码生成检查清单

- **附录**
    - 常用代码片段
    - 相关文档链接

**参考模块：**
- 后端：`backend/app/modules/acme`（证书管理模块）
- 前端：`frontend/src/modules/ssl`（SSL 管理模块）

#### 2. **[通用组件使用规范.md](通用组件使用规范.md)** ⭐
**通用组件和全局方法的使用规范**

**内容包含：**
- **DialogForm 组件**
    - 组件概述和基础使用
    - Props 配置详解
    - 支持的字段类型（16种）
    - 字段配置示例
    - 分组模式配置
    - 验证规则（基础验证、动态验证）
    - 完整使用示例
    - 组件暴露方法
    - 常见问题解答

- **全局方法**
    - `window.$request` - 统一请求工具（GET、POST、PUT、DELETE、文件导出）
    - `window.$message` - 消息提示
    - `window.$notification` - 通知提示
    - `window.$dialog` - 对话框
    - `window.$copyCode` - 复制工具
    - `window.$themeStore` - 主题管理

- **最佳实践**
    - API 调用规范
    - 错误处理规范
    - 消息提示规范
    - 数据处理规范
    - UI 优化建议

### 🎯 AI 开发工作流

当 AI 代理需要为本项目开发新功能时，应遵循以下流程：

1. **阅读开发规范**
    - 首先阅读 [AI开发规范文档.md](AI开发规范文档.md)，了解整体开发规范
    - 根据需要参考 [通用组件使用规范.md](通用组件使用规范.md)

2. **参考示例模块**
    - 后端：研究 `backend/app/modules/acme` 模块
    - 前端：研究 `frontend/src/modules/ssl` 模块
    - 理解项目代码风格和架构模式

3. **使用提示词模板**
    - 从 AI开发规范文档中复制相应的提示词模板
    - 根据实际需求修改模板内容

4. **生成代码**
    - 按照规范生成代码
    - 确保代码包含详细的中文注释
    - 使用项目统一的全局方法和组件

5. **代码检查**
    - 使用"代码生成检查清单"验证代码质量
    - 确保符合项目统一风格

6. **测试和优化**
    - 进行功能测试
    - 根据测试结果优化代码

---

**文档版本：** v3.1
**最后更新：** 2026年3月31日
**维护者：** iFlow CLI AI Assistant
