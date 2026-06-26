# CLAUDE.md

你正在帮助我开发一个 Internship Tracker 项目。

## 我的水平

我是 Python 初学者，只大概了解 Python。
请在完成代码后，用新手能懂的方式解释关键代码。

## 技术栈

- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Frontend: React + Vite + TypeScript
- Tests: pytest
- Deployment: Docker

## 开发规则

1. 每次只实现一个小功能。
2. 不要一次性大规模重构。
3. 修改代码前先说明计划。
4. 每个核心功能都要写测试。
5. 不要把密钥写进代码。
6. 不要删除已有功能。
7. 修改完成后说明：
   - 改了哪些文件
   - 为什么这样改
   - 如何运行
   - 我需要理解哪些知识点

## 项目目标

做一个真实可用的实习投递管理系统，包括：
- 用户登录
- 岗位管理
- 投递状态管理
- 简历版本管理
- Dashboard 数据统计
- Docker 部署

## 项目状态

全部 11 个阶段已完成：
- ✅ 阶段 1: 最小 FastAPI 后端
- ✅ 阶段 2: 数据库 + Jobs CRUD
- ✅ 阶段 3: 用户系统 + JWT 鉴权
- ✅ 阶段 4: Applications 投递流程
- ✅ 阶段 5: Resumes 简历系统
- ✅ 阶段 6: Dashboard 统计
- ✅ 阶段 7: 前端 React
- ✅ 阶段 8: 前后端联调
- ✅ 阶段 9: Docker 部署
- ✅ 阶段 10: 测试强化 (64 tests)
- ✅ 阶段 11: 最终整理

## 本地开发

### 前置条件
- Python 3.11+
- Node.js 24+
- 无需本地 PostgreSQL！使用 Neon 云端数据库

### 启动方式

```bash
# 首次：配置环境变量
cd backend
cp .env.example .env  # 复制模板
# 编辑 .env，填入 Neon 连接字符串和 SECRET_KEY

# 终端 1：启动后端（端口 8000）
cd backend
uv run uvicorn app.main:app --reload

# 终端 2：启动前端（端口 5173）
cd frontend
npm run dev
```

浏览器打开 http://localhost:5173

### Windows 一键启动

双击项目根目录的 `start.bat`（停止用 `stop.bat`）。

### 运行测试

```bash
cd backend
uv run pytest -v    # 64 个测试
```

## Docker 部署（一键启动）

```bash
# 先配置 backend/.env（复制 .env.example 并填入 Neon 连接字符串）
# 项目根目录
docker compose up -d
```

启动后（只有 backend + frontend 两个容器，数据库连 Neon 云端）：
- 前端：http://localhost
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

```bash
docker compose down        # 停止
docker compose logs -f     # 查看日志
docker compose up -d --build  # 重新构建并启动
```