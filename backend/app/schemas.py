"""
Pydantic 模式（Schemas）

这个文件定义了"请求和响应的格式"。
- 前端发来的数据长什么样？（Create / Update）
- 后端返回的数据长什么样？（Response）

Pydantic 会自动做数据验证：
    比如 age 定义为 int，前端传了 "abc" → 自动返回 422 错误

和 models.py 的区别：
    models.py  → 定义数据库表结构（和 PostgreSQL 打交道）
    schemas.py → 定义 API 接口格式（和前端打交道）
"""

from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from app.models import ApplicationStatus


# ==================== 认证相关 ====================

class UserRegister(BaseModel):
    """
    注册时前端需要发送的字段。
    """
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=128, description="密码（至少6位）")


class UserLogin(BaseModel):
    """
    登录时前端需要发送的字段。
    """
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """
    返回用户信息（永远不包含密码）。
    """
    id: int
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """
    登录成功后返回的 JWT 令牌。
    """
    access_token: str
    token_type: str = "bearer"


# ==================== 岗位相关 ====================

class JobCreate(BaseModel):
    """
    创建岗位时前端需要发送的字段。
    user_id 不再需要手动传，由登录 token 自动确定。
    """
    company_name: str = Field(..., min_length=1, max_length=255, description="公司名称")
    title: str = Field(..., min_length=1, max_length=255, description="岗位名称")
    location: str | None = Field(None, max_length=255, description="工作地点")
    job_url: str | None = Field(None, max_length=1024, description="岗位链接")
    jd_text: str | None = Field(None, description="岗位描述全文")
    salary_range: str | None = Field(None, max_length=100, description="薪资范围")
    status: str = Field(default="saved", max_length=50, description="投递状态")


class JobUpdate(BaseModel):
    """
    更新岗位时前端发送的字段。
    所有字段都是可选的（只传要改的字段即可）。
    """
    company_name: str | None = Field(None, min_length=1, max_length=255, description="公司名称")
    title: str | None = Field(None, min_length=1, max_length=255, description="岗位名称")
    location: str | None = Field(None, max_length=255, description="工作地点")
    job_url: str | None = Field(None, max_length=1024, description="岗位链接")
    jd_text: str | None = Field(None, description="岗位描述全文")
    salary_range: str | None = Field(None, max_length=100, description="薪资范围")
    status: str | None = Field(None, max_length=50, description="投递状态")


class JobResponse(BaseModel):
    """
    返回岗位时包含的字段（可能是多个或单个）。
    """
    id: int
    user_id: int
    company_name: str
    title: str
    location: str | None = None
    job_url: str | None = None
    jd_text: str | None = None
    salary_range: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ==================== 投递记录相关 ====================

class ApplicationCreate(BaseModel):
    """
    创建投递记录时前端需要发送的字段。
    """
    job_id: int = Field(..., description="关联的岗位 ID")
    status: ApplicationStatus = Field(
        default=ApplicationStatus.SAVED, description="投递状态"
    )
    applied_at: datetime | None = Field(None, description="投递时间")
    interview_date: datetime | None = Field(None, description="面试时间")
    notes: str | None = Field(None, description="备注")


class ApplicationUpdate(BaseModel):
    """
    更新投递记录。
    所有字段可选，只传要改的。
    """
    status: ApplicationStatus | None = Field(None, description="投递状态")
    applied_at: datetime | None = Field(None, description="投递时间")
    interview_date: datetime | None = Field(None, description="面试时间")
    notes: str | None = Field(None, description="备注")


class ApplicationResponse(BaseModel):
    """
    返回投递记录。
    """
    id: int
    job_id: int
    status: str
    applied_at: datetime | None = None
    interview_date: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ==================== 简历相关 ====================

class ResumeResponse(BaseModel):
    """
    返回简历信息。
    """
    id: int
    user_id: int
    name: str
    file_path: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== Dashboard 统计 ====================

class StatsResponse(BaseModel):
    """
    Dashboard 统计数据。
    """
    total_jobs: int
    total_applied: int
    total_interview: int
    total_offer: int
    total_rejected: int
