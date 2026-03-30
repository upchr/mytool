# MyTool 部署指南

## 架构

```
GitHub Pages (前端) ──API请求──> Railway (后端)
https://upchr.github.io/mytool/    https://xxx.railway.app
```

---

## 一、后端部署到 Railway

### 1. 注册 Railway
访问 https://railway.app/，用 GitHub 账号登录

### 2. 创建新项目
```
New Project → Deploy from GitHub repo → 选择 mytool 仓库
```

### 3. 配置 Root Directory
```
Settings → Root Directory → 设置为 backend
```

### 4. 设置环境变量
在 Railway Dashboard → Variables 中添加：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `PORT` | `8000` | 服务端口 |
| `CORS_ORIGINS` | `https://upchr.github.io` | 允许的前端地址 |

### 5. 添加持久化存储（重要！）
```
Settings → Volumes → Add Volume
Mount Path: /app/data
```

### 6. 获取后端 URL
部署成功后，Railway 会给你一个 URL：
```
https://mytool-backend-xxx.up.railway.app
```

---

## 二、前端部署到 GitHub Pages

### 1. 设置 GitHub Secrets
仓库 → Settings → Secrets and variables → Actions → New repository secret

| Secret 名称 | 值 |
|-------------|-----|
| `RAILWAY_BACKEND_URL` | `https://你的railway后端地址` |

### 2. 开启 GitHub Pages
仓库 → Settings → Pages → Source → 选择 `GitHub Actions`

### 3. 推送代码触发部署
```bash
git add .
git commit -m "feat: 添加 Railway 和 GitHub Pages 部署配置"
git push
```

### 4. 访问前端
```
https://upchr.github.io/mytool/
```

---

## 三、常见问题

### Q: 前端访问后端 API 报 CORS 错误？
A: 检查后端 `CORS_ORIGINS` 环境变量是否包含 GitHub Pages 地址

### Q: 数据库数据丢失？
A: 确保添加了 Railway Volume 持久化存储

### Q: 后端冷启动慢？
A: Railway 免费版会休眠，首次访问需要 30 秒左右唤醒

### Q: 如何查看后端日志？
A: Railway Dashboard → Deployments → 点击最新部署 → View Logs

---

## 四、本地开发

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```
