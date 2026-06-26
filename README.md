# 📋 实习投递管理系统

一个帮助管理实习投递全流程的 Web 应用。从发现岗位 → 投递简历 → 跟踪面试 → 拿到 Offer，一站式管理。

## ✨ 功能

- 🔐 **用户系统** — 注册 / 登录 / JWT 鉴权
- 📄 **岗位管理** — 增删改查，搜索过滤，状态追踪
- 📮 **投递流程** — 完整的 saved → applied → oa → interview → offer 状态流转
- 📎 **简历管理** — PDF 上传，UUID 重命名防冲突
- 📊 **Dashboard** — SQL 聚合统计，数据卡片一览
- 🏢 **大厂直通车** — 收录 30 家大厂校招官网直达链接
- 🐳 **Docker 部署** — docker compose up 一键启动

## 🛠 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | FastAPI (Python 3.11) |
| 数据库 | PostgreSQL 17 + SQLAlchemy ORM |
| 认证 | JWT (python-jose) + bcrypt |
| 包管理 | uv |
| 前端框架 | React 19 + TypeScript |
| 构建工具 | Vite 8 |
| 路由 | React Router 7 |
| 测试 | pytest (64 tests) |
| 部署 | Docker + docker-compose |

## 🏗 项目结构

```
backend/
├── app/
│   ├── main.py          # FastAPI 入口 + 全部路由
│   ├── auth.py          # JWT 生成/验证 + 密码哈希
│   ├── database.py      # 数据库引擎 + 会话管理
│   ├── models.py        # SQLAlchemy 模型 (User, Job, Application, Resume)
│   ├── schemas.py       # Pydantic 请求/响应验证
│   └── crud.py          # 数据库 CRUD 操作
├── tests/
│   ├── conftest.py      # 共享测试 fixtures
│   ├── test_main.py     # 健康检查
│   ├── test_auth.py     # 认证 (注册/登录/鉴权)
│   ├── test_jobs.py     # 岗位 CRUD
│   ├── test_applications.py  # 投递流程
│   ├── test_resumes.py  # 简历上传
│   ├── test_stats.py    # 统计
│   └── test_integration.py   # 端到端集成测试
├── uploads/             # PDF 简历存储
├── .env.example         # 环境变量模板
├── Dockerfile
└── pyproject.toml

frontend/
├── src/
│   ├── App.tsx          # 路由 + 导航栏
│   ├── api.ts           # API 封装 + Token 管理
│   ├── index.css        # 全局样式
│   ├── components/      # 通用组件 (Modal, Loading)
│   ├── data/            # 大厂数据
│   └── pages/           # 页面 (Login, Register, Dashboard, JobsList, JobCreate, CompanyLinks)
├── nginx.conf           # Nginx 反向代理配置
├── Dockerfile
└── package.json

docker-compose.yml       # 一键编排 postgres + backend + frontend
start.bat               # Windows 一键启动脚本
stop.bat                # Windows 停止脚本
```

## 🚀 快速开始

### 前置条件

- Python 3.11+
- Node.js 24+
- PostgreSQL 17

### Windows 一键启动（推荐）

双击项目根目录的 **`start.bat`**，浏览器自动打开 `http://localhost:5173`。

停止服务双击 **`stop.bat`**。

### 手动启动

```bash
# 终端 1：启动 PostgreSQL
pg_ctl -D /path/to/pgdata -l /path/to/logfile -o "-p 5433" start

# 终端 2：启动后端
cd backend
cp .env.example .env       # 首次运行
uv sync
uv run uvicorn app.main:app --reload

# 终端 3：启动前端
cd frontend
npm install                # 首次运行
npm run dev

# 浏览器打开 http://localhost:5173
```

### Docker 一键启动

```bash
docker compose up -d

# 前端：http://localhost
# 后端：http://localhost:8000
# API 文档：http://localhost:8000/docs
```

## 🧪 测试

```bash
cd backend
uv run pytest -v          # 64 个测试

# CI 环境
export TEST_DATABASE_URL=postgresql://user:pass@host:5432/test_db
uv run pytest -v
```

测试覆盖：认证、岗位 CRUD、投递流程、简历上传、统计、多用户隔离、错误格式。

## 📖 API 文档

启动后端后访问 **http://localhost:8000/docs** 查看 Swagger 自动生成的交互式 API 文档。

### 接口总览

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/auth/register` | 注册 | - |
| POST | `/auth/login` | 登录 | - |
| GET | `/auth/me` | 获取当前用户 | Token |
| POST | `/jobs` | 创建岗位 | Token |
| GET | `/jobs` | 岗位列表 | Token |
| GET | `/jobs/{id}` | 岗位详情 | Token |
| PUT | `/jobs/{id}` | 更新岗位 | Token |
| DELETE | `/jobs/{id}` | 删除岗位 | Token |
| POST | `/applications` | 创建投递 | Token |
| GET | `/applications` | 投递列表 | Token |
| PUT | `/applications/{id}` | 更新投递 | Token |
| POST | `/resumes/upload` | 上传简历 | Token |
| GET | `/resumes` | 简历列表 | Token |
| GET | `/stats/summary` | Dashboard 统计 | Token |
| GET | `/health` | 健康检查 | - |

## 🌐 免费部署到公网（让别人也能用）

使用 **Neon**（永久免费 PostgreSQL）+ **Render**（免费 Web 服务）。

### 准备

1. 注册 [GitHub](https://github.com) 账号，把项目 push 上去
2. 注册 [Render](https://render.com) 账号，用 GitHub 登录
3. 注册 [Neon](https://neon.tech) 账号

### 步骤

#### 1. 在 Neon 创建数据库

- 登录 Neon → New Project → 起个名 → Create
- 复制 **Connection string**（格式：`postgresql://user:pass@host/db`）

#### 2. 在 Render 部署

- Render → New → **PostgreSQL** → 粘贴 Neon 的 Connection string
- Render → New → **Web Service** → 选 GitHub 仓库 → 选择 backend 目录
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Environment: 添加 `DATABASE_URL` = Neon 的 Connection string
  - 添加 `SECRET_KEY` = 随便填一串英文数字
  - 添加 `PYTHON_VERSION` = `3.11.0`
- Render → New → **Static Site** → 选 GitHub 仓库 → 选择 frontend 目录
  - Build Command: `npm install && npm run build`
  - Publish Directory: `dist`
  - Environment: 添加 `VITE_API_URL` = 上面 Backend 的 URL（如 `https://xxx.onrender.com`）
  - Rewrite Rules: `/*` → `/index.html`

#### 3. 完成

等 3-5 分钟部署完毕，访问 Static Site 的 URL（如 `https://xxx.onrender.com`）。

别人就能通过这个链接使用你的系统了！

## 📄 License

MIT
