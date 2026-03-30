# mytool-java

ToolsPlus Java 版本 - 多设备定时任务管理与工作流引擎

## 项目结构

```
mytool-java/
├── backend/                    # Java 后端
│   ├── src/main/java/
│   │   └── com/upchr/mytool/
│   │       ├── config/        # 配置类
│   │       ├── common/        # 公共模块
│   │       ├── core/          # 核心模块
│   │       └── modules/       # 业务模块
│   │           ├── sys/       # 系统模块
│   │           ├── note/      # 便签模块
│   │           ├── node/      # 节点管理
│   │           ├── cron/      # 定时任务
│   │           ├── workflow/  # 工作流引擎
│   │           └── notify/    # 通知模块
│   ├── pom.xml
│   └── README.md
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── modules/           # 页面模块
│   │   ├── router/            # 路由配置
│   │   └── ...
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

## 技术栈

### 后端
| 组件 | 版本 | 说明 |
|------|------|------|
| Spring Boot | 3.2.5 | 基础框架 |
| MyBatis Plus | 3.5.5 | ORM 框架 |
| SQLite | 3.45.2 | 嵌入式数据库 |
| Redis | - | 缓存 |
| JWT | 0.12.5 | 认证 |
| Quartz | - | 定时任务 |
| JSch | 0.1.55 | SSH 客户端 |

### 前端
| 组件 | 版本 | 说明 |
|------|------|------|
| Vue | 3.4.0 | 前端框架 |
| Vite | 5.0.0 | 构建工具 |
| Naive UI | 2.43.2 | UI 组件库 |
| Vue Flow | 1.48.2 | 工作流编辑器 |

## 快速开始

### 后端启动

```bash
cd backend
mvn spring-boot:run
```

访问：http://localhost:8000

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问：http://localhost:5173

## API 文档

后端启动后访问：http://localhost:8000/doc.html

## 与 Python 版本的兼容性

| 项目 | 状态 |
|------|------|
| 数据库 | ✅ 完全兼容 SQLite |
| API 路径 | ✅ 一致，前端无需修改 |
| 响应格式 | ✅ BaseResponse 结构一致 |
| 认证方式 | ✅ JWT + BCrypt 兼容 |
| 端口 | ✅ 8000 |
