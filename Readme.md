## 📦 ToolsPlus 项目

![status](https://img.shields.io/badge/状态-稳定-success)
![version](https://img.shields.io/badge/version-v3.4.0-blue)
![vue](https://img.shields.io/badge/Vue-3.x-brightgreen)
![python](https://img.shields.io/badge/Python-3.8+-blue)

> 轻量级多设备定时任务管理、通知、AI 助手、固定资产管理、工作流自动化 + 个人便签速记

[![GitHub](https://img.shields.io/badge/项目源码-181717?logo=github)](https://github.com/upchr/FnDepot/tree/main/toolsplus)

### 🎯 项目背景
基于 Vue 3 和 Python 3 构建，为开发者和多设备用户提供集中式定时任务管理、个人备忘服务、AI 对话助手、SSL 证书自动续签、固定资产管理和工作流自动化功能，解决跨设备任务同步、通知和自动化问题。

### 多平台支持
- x86
- arm

### 📊 版本规划

| 版本   | 状态 | 主要功能 | 发布时间 |
|------|------|----------|----------|
| v2.0 | ✅ 已发布 | 便签 + 定时任务、通知等 | 已完成 |
| v2.1 | ✅ 已发布 | AI 聊天助手 + SSL 证书管理 | 已完成 |
| v2.2 | ✅ 已发布 | 固定资产管理 + 工作流管理 | 已完成 |
| v3.4 | ✅ 已发布 | 性能优化 + UI 改进 | 已完成 |
| v4.0 | 🚧 开发中 | 移动端适配 + 更多功能 |  |
| 未来版本 | 📝 规划中 | 企业版、多租户 |  |

### ✨ 功能特性
#### ✅ 已实现
- 📝 **便签速记**
    - 快速创建/编辑/删除便签
    - 支持富文本格式
    - 多设备同步

- ⏱️ **多设备定时任务**
    - 多设备任务收集管理
    - Cron 表达式支持
    - 任务执行日志
    - 任务模板一键导入
    - 连续失败预警

- 🔔 **智能通知**
    - 连续失败预警机制
    - 多通道通知（企业微信、Bark、Webhook 等）
    - 通知历史记录

- 💽 **数据安全**
    - 模块级备份还原
    - 手动导出/导入
    - 加密存储

- 🔄 **系统版本**
    - 提供升级脚本
    - 版本升级推送

- 🔒 **SSL 证书管理**
    - 自动申请 Let's Encrypt 证书
    - 支持 DNS-01 验证（多种 DNS 提供商）
    - 自动续签和到期提醒
    - 多域名证书管理

- 🤖 **AI 聊天助手** ⭐
    - 多 AI 配置管理（支持多个 API Key 和模型）
    - 对话历史管理
    - 流式响应（SSE）
    - 知识库管理（文档上传、分片、检索）
    - 上下文对话

- 📊 **固定资产管理** ⭐
    - 资产信息管理（名称、类别、价格、购买日期等）
    - 自动计算使用天数、日均成本、质保期等
    - 资产报废管理（单个和批量报废）
    - 统计分析功能：
      - 资产摘要（总数、总价值、按类别和年份统计）
      - 类别分布（饼图）
      - 年度购买趋势（柱状图）
      - 价值排行榜
      - 即将过质保资产提醒

- 🔄 **工作流管理** ⭐
    - 可视化工作流编辑器（基于 Vue Flow）
    - 工作流创建、编辑、删除
    - 工作流执行和监控
    - 节点执行记录查看
    - 版本管理（创建版本、版本列表、恢复版本、设置默认版本）
    - 工作流格式验证
    - 支持手动触发工作流执行

#### 🚧 开发中
- [ ] **插件系统**
    - 插件市场
    - 插件安装/卸载
    - 自定义插件开发

- [ ] **任务模板**
    - 模板管理
    - 模板应用
    - 模板分类

- [ ] **功能优化**
    - 性能优化
    - UI/UX 改进
    - 移动端适配

- [ ] **需求收集**
    - issues 提交

### 🛠️ 技术栈

**前端：**
- Vue 3.4.x + Vite 5.0.0
- Naive UI 2.43.2
- Pinia 3.0.4（状态管理）
- Vue Router 4.6.4（路由管理）
- Monaco Editor 0.55.1（代码编辑器）
- Vue Flow（工作流可视化）
- ECharts 6.0.0（图表库）

**后端：**
- Python 3.8+
- FastAPI 0.128.0
- SQLAlchemy 2.0.22（ORM）
- APScheduler 3.10.4（定时任务）
- WebSocket（实时通信）
- ACME 协议（Let's Encrypt）

**部署：**
- Docker 多阶段构建
- Nginx 反向代理
- SQLite 数据库
- 支持 x86 和 arm 平台

### 📚 开发文档
- [AGENTS.md](AGENTS.md) - 项目概览和开发指南
- [AI开发规范文档.md](AI开发规范文档.md) - AI 自主开发完整规范
- [通用组件使用规范.md](通用组件使用规范.md) - 组件和全局方法使用规范

### 📌 相关链接
- [🐛 Bug 反馈](https://github.com/upchr/mytool/issues)
- [💬 讨论区](https://github.com/upchr/mytool/issues/new)
- [📦 个人飞牛仓库](https://github.com/upchr/Fndepot)

## 🚀 快速开始

### 本地开发

**后端：**
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
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

## 🐳 Docker 部署

### 构建镜像
```bash
git clone https://gitee.com/upchr/mytool.git
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
  toolsplus:latest
```

### Docker Compose 部署
```bash
services:
  toolsplus:
    image: toolsplus:latest
    container_name: toolsplus
    ports:
      - "80:80"
    volumes:
      - ./data:/data
    environment:
      - TZ=Asia/Shanghai
    restart: unless-stopped
```

### 环境变量
- `TZ` - 时区（默认：Asia/Shanghai）
- `JWT_SECRET_KEY` - JWT 密钥（自动生成）
- `OS_ENV` - 运行环境（prod/dev）
- `DATABASE_URL` - 数据库连接（默认：SQLite）

## 📁 项目结构

```
mytool/
├── frontend/                 # Vue 3 前端应用
│   ├── src/
│   │   ├── modules/         # 功能模块
│   │   ├── api/             # API 接口定义
│   │   ├── components/      # 公共组件
│   │   └── router/          # 路由配置
│   └── package.json
├── backend/                  # Python 后端应用
│   ├── app/
│   │   ├── main.py          # 应用入口
│   │   ├── core/            # 核心功能
│   │   └── modules/         # 功能模块
│   └── requirements.txt
├── docker/                   # Docker 配置
└── data/                     # 数据持久化目录
```

## 🤝 贡献指南

1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🌟 Star History

如果这个项目对你有帮助，请给个 Star ⭐️

---

**项目仓库：**
- Gitee: https://gitee.com/upchr/mytool.git
- GitHub: https://github.com/upchr/mytool

**当前版本：** v3.4.0
**最后更新：** 2026-03-20
