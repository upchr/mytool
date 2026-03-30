# mytool-java

ToolsPlus Java 版本 - 多设备定时任务管理与工作流引擎

## 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| Spring Boot | 3.2.5 | 基础框架 |
| MyBatis Plus | 3.5.5 | ORM 框架 |
| SQLite | 3.45.2 | 嵌入式数据库（兼容原 Python 版本） |
| Redis | - | 缓存 |
| JWT | 0.12.5 | 认证 |
| Quartz | - | 定时任务 |
| JSch | 0.1.55 | SSH 客户端 |
| Hutool | 5.8.26 | 工具库 |

## 项目结构

```
src/main/java/com/upchr/mytool/
├── MytoolApplication.java          # 启动类
├── config/                          # 配置类
│   ├── ThreadPoolConfig.java       # 统一线程池
│   ├── RedisConfig.java            # Redis 配置
│   ├── WebMvcConfig.java           # Web MVC 配置
│   ├── AuthInterceptor.java        # 认证拦截器
│   ├── MybatisPlusConfig.java      # MyBatis Plus 配置
│   └── QuartzConfig.java           # Quartz 配置
├── common/                          # 公共模块
│   ├── result/BaseResponse.java    # 统一响应
│   ├── exception/                  # 异常
│   └── utils/                      # 工具类
├── core/                            # 核心模块
│   └── ssh/SSHClient.java          # SSH 客户端
└── modules/                         # 业务模块
    ├── sys/                        # 系统模块
    ├── note/                       # 便签模块
    ├── node/                       # 节点管理
    ├── cron/                       # 定时任务
    ├── workflow/                   # 工作流引擎
    └── notify/                     # 通知模块
```

## API 列表

### 系统模块 `/sys`
- `GET /sys/init/check` - 检查初始化状态
- `POST /sys/init/setup` - 初始化系统
- `POST /sys/login` - 登录
- `POST /sys/resetPassword` - 重置密码
- `GET /sys/runtime` - 获取运行时长

### 便签模块 `/notes`
- `GET /notes` - 获取所有便签
- `POST /notes` - 创建便签
- `PUT /notes/{id}` - 更新便签
- `DELETE /notes/{id}` - 删除便签
- `POST /notes/deleteBatch` - 批量删除

### 节点模块 `/nodes`
- `POST /nodes` - 创建节点
- `GET /nodes/only_active/{activeOnly}` - 获取节点列表
- `GET /nodes/{id}` - 获取节点详情
- `PUT /nodes/{id}` - 更新节点
- `DELETE /nodes/{id}` - 删除节点
- `PATCH /nodes/{id}/toggle` - 切换状态
- `POST /nodes/{id}/test` - 测试连接

### 定时任务模块 `/cron`
- `POST /cron/jobs` - 创建任务
- `POST /cron/jobsList` - 获取任务列表
- `PUT /cron/jobs/{id}` - 更新任务
- `DELETE /cron/jobs/{id}` - 删除任务
- `PATCH /cron/jobs/{id}/toggle` - 切换状态
- `POST /cron/jobs/execute` - 手动执行
- `GET /cron/jobs/{id}/executions` - 获取执行记录
- `POST /cron/jobs/crons` - 计算下次执行时间

### 工作流模块 `/workflows`
- `POST /workflows` - 创建工作流
- `GET /workflows` - 获取工作流列表
- `GET /workflows/{workflowId}` - 获取工作流详情
- `PUT /workflows/{workflowId}` - 更新工作流
- `DELETE /workflows/{workflowId}` - 删除工作流
- `POST /workflows/trigger` - 触发工作流
- `GET /workflows/executions/{executionId}` - 获取执行记录
- `POST /workflows/validate` - 验证工作流格式

### 通知模块 `/notifications`
- `GET /notifications/services` - 获取所有服务配置
- `PUT /notifications/services/{id}` - 更新服务配置
- `POST /notifications/test/{id}` - 测试服务

## 快速开始

### 1. 环境要求

- JDK 17+
- Maven 3.6+
- Redis（可选）

### 2. 运行

```bash
# 编译
mvn clean package -DskipTests

# 运行
java -jar target/mytool-1.0.0.jar
```

### 3. 访问

- API 文档: http://localhost:8000/doc.html
- 端口: 8000（与 Python 版本一致）

## 与 Python 版本的兼容性

1. **数据库**：完全兼容 SQLite 数据库，无需迁移
2. **API 路径**：保持一致，前端无需修改
3. **响应格式**：BaseResponse 结构一致
4. **认证方式**：JWT + BCrypt，与原版本兼容

## 核心特性

### 统一线程池
所有异步任务使用统一线程池，便于监控和追溯。

### 工作流引擎
支持多种节点类型：start、end、task、condition、wait、notification。

### SSH 远程执行
支持密码和 SSH Key 两种认证方式。
