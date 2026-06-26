"""
数据模型（Models）

这个文件定义"数据库表长什么样"。
每个类 = 一张表，每个属性 = 一个列。

SQLAlchemy 会自动把类翻译成 SQL 建表语句。
"""

import enum
from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ApplicationStatus(str, enum.Enum):
    """
    投递状态枚举

    严格规定只有这 7 种状态。
    如果前端传了其他值，Pydantic 会自动报错。
    """
    SAVED = "saved"
    APPLIED = "applied"
    OA = "oa"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class User(Base):
    """
    用户表（users）

    每一行 = 一个注册用户。

    字段说明：
    - id:             主键
    - email:          邮箱（登录用，必须唯一）
    - hashed_password: 加密后的密码（永远不存明文！）
    - created_at:     注册时间
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}'>"


class Job(Base):
    """
    岗位表（jobs）

    每一行 = 一个实习岗位的记录。

    字段说明：
    - id:          主键，自动递增的数字编号
    - user_id:     属于哪个用户（阶段 3 加入登录后才有意义）
    - company_name: 公司名称
    - title:       岗位名称
    - location:    工作地点（可选）
    - job_url:     岗位链接（可选）
    - jd_text:     岗位描述全文（可选，可能很长）
    - salary_range: 薪资范围（可选，如 "15k-25k"）
    - status:      投递状态，默认 "saved"
    - created_at:  创建时间，自动填入
    - updated_at:  最后修改时间，自动更新
    """

    __tablename__ = "jobs"  # 数据库里的表名

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    jd_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="saved", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<Job id={self.id} title='{self.title}'>"


class Application(Base):
    """
    投递记录表（applications）

    每一行 = 一次投递记录。
    一个岗位可以有多次投递流程（如：保存 → 投递 → 面试 → offer）。

    字段说明：
    - id:             主键
    - job_id:         关联哪个岗位（外键 → jobs.id）
    - status:         当前投递状态（严格枚举，7 种）
    - applied_at:     投递时间（从 saved 转为 applied 时记录）
    - interview_date: 面试时间（可选）
    - notes:          备注（可选）
    - created_at:     创建时间
    - updated_at:     最后修改时间
    """

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default=ApplicationStatus.SAVED, nullable=False
    )
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    interview_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # relationship 让 SQLAlchemy 知道 Application 和 Job 的关联
    # 这样可以直接用 application.job.company_name 获取岗位信息
    job: Mapped["Job"] = relationship("Job")

    def __repr__(self):
        return f"<Application id={self.id} job_id={self.job_id} status='{self.status}'>"


class Resume(Base):
    """
    简历表（resumes）

    每一行 = 一份上传的简历文件。
    """

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<Resume id={self.id} name='{self.name}'>"
