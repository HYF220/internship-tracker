# 📋 实习投递管理系统

一个全栈 Web 应用，帮助管理和追踪实习岗位的投递流程。

---

## ✨ 功能

- 🔐 **用户系统** — 注册、登录、JWT 鉴权
- 📌 **岗位管理** — 添加、编辑、删除、搜索实习岗位
- 🔄 **投递流程** — 追踪投递状态流转（已保存 → 已投递 → 测评 → 面试 → Offer / 已拒绝 / 已撤回）
- 📄 **简历管理** — 上传 PDF 简历，UUID 安全命名
- 📊 **数据仪表盘** — 实时统计岗位数、投递数、面试数、Offer 数
- 🏢 **大厂直通车** — 内置 30 家大厂招聘官网链接，一键跳转

---

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.11) |
| 数据库 | PostgreSQL 17 + SQLAlchemy ORM |
| 认证 | JWT (python-jose) + bcrypt 密码哈希 |
| 前端 | React 19 + TypeScript + Vite |
| 路由 | React Router 7 |
| 测试 | pytest (64 个测试) |
| 包管理 | uv (Python) / npm (Node.js) |
| 部署 | Docker Compose 一键编排 |

---

## 🏗 项目结构

```
实习投递管理系统/
├── start.bat                  # Windows 一键启动脚本
├── stop.bat                   # Windows 一键停止脚本
├── docker-compose.yml         # Docker 编排文件
├── CLAUDE.md                  # 开发文档
├── README.md                  # 本文件
│
├── backend/                   # FastAPI 后端
│   ├── app/
│   │   ├── main.py            # 入口：路由 + 异常处理
│   │   ├── auth.py            # JWT 生成/验证 + 密码哈希
│   │   ├── database.py        # 数据库连接 + 会话管理
│   │   ├── models.py          # ORM 模型（User, Job, Application, Resume）
│   │   ├── schemas.py         # Pydantic 请求/响应模式
│   │   └── crud.py            # 数据库增删改查操作
│   ├── tests/
│   │   ├── conftest.py        # 共享测试配置（CI 就绪）
│   │   ├── test_main.py       # 健康检查测试
│   │   ├── test_auth.py       # 认证测试（注册/登录/权限）
│   │   ├── test_jobs.py       # 岗位 CRUD 测试
│   │   ├── test_applications.py # 投递流程测试
│   │   ├── test_resumes.py    # 简历上传测试
│   │   ├── test_stats.py      # 统计接口测试
│   │   └── test_integration.py # 端到端集成测试
│   ├── uploads/               # 简历文件存储目录
│   ├── pyproject.toml         # Python 项目配置
│   ├── Dockerfile             # 后端 Docker 镜像
│   └── .env.example           # 环境变量模板
│
└── frontend/                  # React 前端
    ├── src/
    │   ├── main.tsx           # 入口
    │   ├── App.tsx            # 路由 + 导航栏
    │   ├── api.ts             # API 调用 + Token 管理
    │   ├── index.css          # 全局样式
    │   ├── components/
    │   │   ├── Loading.tsx    # 加载动画
    │   │   └── Modal.tsx      # 通用弹窗
    │   ├── pages/
    │   │   ├── Login.tsx      # 登录页
    │   │   ├── Register.tsx   # 注册页
    │   │   ├── Dashboard.tsx  # 仪表盘
    │   │   ├── JobsList.tsx   # 岗位列表
    │   │   ├── JobCreate.tsx  # 添加岗位
    │   │   └── CompanyLinks.tsx # 大厂直通车
    │   └── data/
    │       └── companies.ts   # 30 家大厂数据
    ├── index.html
    ├── vite.config.ts         # Vite + API 代理配置
    ├── nginx.conf             # Nginx 配置（Docker）
    ├── Dockerfile             # 前端 Docker 镜像（多阶段）
    └── package.json
```

---

## 🚀 启动方式

### Windows 一键启动（推荐）

双击 `start.bat`，浏览器自动打开。

停止时双击 `stop.bat`。

### 手动启动

**前置条件：** Python 3.11+ · Node.js 24+ · PostgreSQL 17

```bash
# 终端 1：PostgreSQL（端口 5433）
pg_ctl -D /d/pgdata -l /d/pgdata/logfile -o "-p 5433" start

# 终端 2：后端（端口 8000）
cd backend
cp .env.example .env
uv run uvicorn app.main:app --reload

# 终端 3：前端（端口 5173）
cd frontend
npm install
npm run dev
```

浏览器打开 **http://localhost:5173**

### Docker 一键启动

```bash
docker compose up -d
# 前端 http://localhost
# 后端 http://localhost:8000
```

---

## 📡 API 接口

| 方法 | 路径 | 说明 | 需登录 |
|------|------|------|------|
| GET | `/health` | 健康检查 | -- |
| POST | `/auth/register` | 注册 | -- |
| POST | `/auth/login` | 登录 | -- |
| GET | `/auth/me` | 当前用户信息 | 是 |
| POST | `/jobs` | 创建岗位 | 是 |
| GET | `/jobs` | 岗位列表 | 是 |
| GET | `/jobs/{id}` | 岗位详情 | 是 |
| PUT | `/jobs/{id}` | 更新岗位 | 是 |
| DELETE | `/jobs/{id}` | 删除岗位 | 是 |
| POST | `/applications` | 创建投递 | 是 |
| GET | `/applications` | 投递列表 | 是 |
| PUT | `/applications/{id}` | 更新投递 | 是 |
| POST | `/resumes/upload` | 上传简历 | 是 |
| GET | `/resumes` | 简历列表 | 是 |
| GET | `/stats/summary` | 数据统计 | 是 |

启动后端后访问 **http://localhost:8000/docs** 查看完整 API 文档。

---

## 🧪 测试

```bash
cd backend
uv run pytest -v
```

**64 个测试**，覆盖所有 15 个 API 接口的正常和异常路径。

CI 就绪：
```bash
export TEST_DATABASE_URL=postgresql://user:pass@host:5432/test_db
uv run pytest -v
```
