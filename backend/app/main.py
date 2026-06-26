"""
实习投递管理系统 - 后端入口

这是整个后端应用的"大门"。
所有请求都会先经过这个文件。
"""

import os
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# ==================== 启动前加载 ====================

# ⚠️ 必须在导入 app.* 模块之前加载 .env！
# 因为 auth.py、database.py 等模块在导入时就会读取环境变量。
# 如果 .env 还没加载，它们会拿到空值并使用不安全的默认值。
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.database import engine, Base, get_db
from app.models import User
from app.schemas import (
    JobCreate,
    JobUpdate,
    JobResponse,
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    ResumeResponse,
    StatsResponse,
)
from app.auth import verify_password, create_access_token, get_current_user
from app import crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用的生命周期管理。
    启动时自动创建所有数据库表（如果不存在的话）。
    """
    Base.metadata.create_all(bind=engine)
    yield


# ==================== 创建 FastAPI 应用 ====================

app = FastAPI(
    title="实习投递管理系统",
    description="管理实习投递的 Web API",
    version="0.3.0",
    lifespan=lifespan,
)

# ==================== CORS 跨域 ====================

# 允许前端从任何地址访问后端 API
# 本地开发：localhost:5173
# 生产部署：Render 自动分配的域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境可以改为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 全局异常处理 ====================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    统一处理 422 验证错误。

    把 Pydantic 的复杂错误格式转成简单的：
    {"detail": "字段 'email' 的值不是合法的邮箱格式"}
    """
    # 提取第一个验证错误
    errors = exc.errors()
    if errors:
        first = errors[0]
        field = first.get("loc", ["unknown"])[-1]
        msg = first.get("msg", "请求数据格式不正确")
        return JSONResponse(
            status_code=422,
            content={"detail": f"字段 '{field}' 验证失败: {msg}"},
        )
    return JSONResponse(
        status_code=422,
        content={"detail": "请求数据格式不正确"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    统一处理 500 服务器内部错误。

    防止将内部错误详情暴露给前端（安全考虑）。
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )


# ==================== 健康检查 ====================

@app.get("/health")
def health_check():
    """GET /health → {"status": "ok"}"""
    return {"status": "ok"}


# ==================== 认证接口 ====================

@app.post("/auth/register", response_model=UserResponse, status_code=201)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    注册新用户。

    POST /auth/register
    请求体：{"email": "...", "password": "至少6位"}
    返回：用户信息（不含密码）
    """
    # 检查邮箱是否已被注册
    existing = crud.get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(status_code=409, detail="该邮箱已被注册")

    return crud.create_user(db, user_data)


@app.post("/auth/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录，返回 JWT token。

    POST /auth/login
    请求体：{"email": "...", "password": "..."}
    返回：{"access_token": "...", "token_type": "bearer"}
    """
    # 查找用户
    user = crud.get_user_by_email(db, user_data.email)
    if user is None:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    # 验证密码
    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    # 生成 JWT token
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@app.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的信息。

    GET /auth/me
    请求头：Authorization: Bearer <token>
    返回：当前用户的 id、email、注册时间
    """
    return current_user


# ==================== Jobs CRUD 接口（需登录） ====================

@app.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建新岗位（需要登录）。

    POST /jobs
    请求头：Authorization: Bearer <token>
    请求体：{"company_name": "字节跳动", "title": "前端实习生"}
    """
    return crud.create_job(db, job_data, user_id=current_user.id)


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询当前用户的岗位列表（需要登录）。

    GET /jobs
    请求头：Authorization: Bearer <token>
    只返回当前登录用户自己的岗位。
    """
    return crud.get_jobs(db, user_id=current_user.id)


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询单个岗位（需要登录，只能查自己的）。

    GET /jobs/{id}
    请求头：Authorization: Bearer <token>
    """
    job = crud.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此岗位")
    return job


@app.put("/jobs/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    update_data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新岗位（需要登录，只能改自己的）。

    PUT /jobs/{id}
    请求头：Authorization: Bearer <token>
    请求体：{"status": "applied"}（只传要改的字段）
    """
    job = crud.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改此岗位")
    return crud.update_job(db, job, update_data)


@app.delete("/jobs/{job_id}", status_code=204)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除岗位（需要登录，只能删自己的）。

    DELETE /jobs/{id}
    请求头：Authorization: Bearer <token>
    """
    job = crud.get_job(db, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="岗位不存在")
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此岗位")
    try:
        crud.delete_job(db, job)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="该岗位存在关联的投递记录，请先删除投递记录",
        )
    return None


# ==================== Applications 投递接口（需登录） ====================

@app.post("/applications", response_model=ApplicationResponse, status_code=201)
def create_application(
    app_data: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建投递记录（需要登录）。

    POST /applications
    请求头：Authorization: Bearer <token>
    请求体：{"job_id": 1, "status": "applied"}
    """
    try:
        return crud.create_application(db, app_data, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@app.get("/applications", response_model=list[ApplicationResponse])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询当前用户的所有投递记录（需要登录）。

    GET /applications
    请求头：Authorization: Bearer <token>
    只返回当前用户的投递（通过岗位关联过滤）。
    """
    return crud.get_applications(db, user_id=current_user.id)


@app.put("/applications/{app_id}", response_model=ApplicationResponse)
def update_application(
    app_id: int,
    update_data: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新投递状态（需要登录，只能改自己的）。

    PUT /applications/{id}
    请求头：Authorization: Bearer <token>
    请求体：{"status": "interview", "interview_date": "2026-07-01T10:00:00"}
    """
    application = crud.get_application(db, app_id)
    if application is None:
        raise HTTPException(status_code=404, detail="投递记录不存在")
    if application.job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此投递记录")
    return crud.update_application(db, application, update_data)


# ==================== Resumes 简历接口（需登录） ====================

# 简历文件存储目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
# 把相对路径转成绝对路径，并确保目录存在
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 允许的文件类型
ALLOWED_CONTENT_TYPES = {"application/pdf"}


@app.post("/resumes/upload", response_model=ResumeResponse, status_code=201)
async def upload_resume(
    name: str = Form(..., description="简历名称（如 '前端实习简历v2'）"),
    file: UploadFile = File(..., description="PDF 文件"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传简历 PDF（需要登录）。

    POST /resumes/upload
    请求头：Authorization: Bearer <token>
    表单字段：
        name: 简历名称
        file: PDF 文件

    规则：
        - 只接受 PDF 文件
        - 文件名用 UUID 重命名（防止冲突）
        - 存储到 backend/uploads/ 目录
    """
    # 1. 检查文件类型
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"只允许上传 PDF 文件，当前类型：{file.content_type}",
        )

    # 2. 生成 UUID 文件名
    ext = ".pdf"
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # 3. 保存文件到磁盘
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 4. 数据库记录（存相对路径，方便以后迁移）
    relative_path = f"uploads/{unique_name}"
    return crud.save_resume(db, current_user.id, name, relative_path)


@app.get("/resumes", response_model=list[ResumeResponse])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    查询当前用户的所有简历（需要登录）。

    GET /resumes
    请求头：Authorization: Bearer <token>
    """
    return crud.get_resumes(db, user_id=current_user.id)


# ==================== Dashboard 统计接口（需登录） ====================

@app.get("/stats/summary", response_model=StatsResponse)
def get_stats_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dashboard 统计接口（需要登录）。

    GET /stats/summary
    请求头：Authorization: Bearer <token>

    返回当前用户的数据统计：
    - total_jobs:      岗位总数
    - total_applied:   已投递数
    - total_interview: 面试中数
    - total_offer:     已获 offer 数
    - total_rejected:  已拒绝数
    """
    return crud.get_stats(db, user_id=current_user.id)
