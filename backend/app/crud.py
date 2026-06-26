"""
CRUD 操作模块

CRUD = Create（创建） + Read（读取） + Update（更新） + Delete（删除）

这个文件包含所有对 jobs 表的数据库操作。
接口代码（main.py）调用这里的函数，不直接操作数据库。

这样做的好处：
    把"业务逻辑"和"数据库操作"分开，代码更容易维护。
"""

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models import User, Job, Application, Resume
from app.schemas import (
    UserRegister,
    JobCreate,
    JobUpdate,
    ApplicationCreate,
    ApplicationUpdate,
)
from app.auth import hash_password


# ==================== 用户 CRUD ====================

def create_user(db: Session, user_data: UserRegister) -> User:
    """
    注册新用户。

    参数：
        db:        数据库会话
        user_data: 注册表单数据（email + password）

    返回：
        创建成功的 User 对象

    注意：密码在存入数据库之前已经加密（hash）
    """
    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    按邮箱查找用户（登录时用）。
    """
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """
    按 ID 查找用户。
    """
    return db.scalar(select(User).where(User.id == user_id))


# ==================== 岗位 CRUD ====================

def create_job(db: Session, job_data: JobCreate, user_id: int) -> Job:
    """
    创建一条新的岗位记录。

    参数：
        db:       数据库会话
        job_data: 前端传来的创建数据（已经过 Pydantic 验证）
        user_id:  当前登录用户的 ID（从 JWT 中获取）

    返回：
        创建成功的 Job 对象
    """
    job = Job(user_id=user_id, **job_data.model_dump())
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_jobs(db: Session, user_id: int | None = None) -> list[Job]:
    """
    查询岗位列表。

    参数：
        db:      数据库会话
        user_id: 可选，按用户过滤（阶段 3 后强制按当前用户过滤）

    返回：
        Job 对象列表
    """
    query = select(Job).order_by(Job.created_at.desc())
    if user_id is not None:
        query = query.where(Job.user_id == user_id)
    return list(db.scalars(query).all())


def get_job(db: Session, job_id: int) -> Job | None:
    """
    按 id 查询单个岗位。

    返回：
        找到了返回 Job 对象，没找到返回 None
    """
    return db.scalar(select(Job).where(Job.id == job_id))


def update_job(db: Session, job: Job, update_data: JobUpdate) -> Job:
    """
    更新岗位信息。

    参数：
        db:         数据库会话
        job:        要更新的 Job 对象（已经从数据库查出来的）
        update_data: 要修改哪些字段

    返回：
        更新后的 Job 对象
    """
    # model_dump(exclude_unset=True) 只取用户实际传了值的字段
    # 比如只传了 title，那就只改 title，不改别的
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(job, key, value)

    db.commit()
    db.refresh(job)
    return job


def delete_job(db: Session, job: Job) -> None:
    """
    删除一个岗位。
    """
    db.delete(job)
    db.commit()


# ==================== 投递记录 CRUD ====================

def create_application(
    db: Session, app_data: ApplicationCreate, user_id: int
) -> Application:
    """
    创建投递记录。

    会先检查 job 是否属于当前用户，防止给别人的岗位创建投递。
    """
    # 查岗位是否存在且属于当前用户
    job = db.scalar(select(Job).where(Job.id == app_data.job_id))
    if job is None:
        raise ValueError("岗位不存在")
    if job.user_id != user_id:
        raise PermissionError("无权操作此岗位")

    application = Application(**app_data.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def get_applications(db: Session, user_id: int) -> list[Application]:
    """
    查询当前用户的所有投递记录。

    通过 JOIN Job 表来过滤：只返回 job.user_id == user_id 的投递。
    """
    return list(
        db.scalars(
            select(Application)
            .join(Job)
            .where(Job.user_id == user_id)
            .order_by(Application.created_at.desc())
        ).all()
    )


def get_application(db: Session, app_id: int) -> Application | None:
    """
    按 ID 查询单个投递记录。
    """
    return db.scalar(select(Application).where(Application.id == app_id))


def update_application(
    db: Session, application: Application, update_data: ApplicationUpdate
) -> Application:
    """
    更新投递记录。
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(application, key, value)

    db.commit()
    db.refresh(application)
    return application


# ==================== 简历 CRUD ====================

def save_resume(db: Session, user_id: int, name: str, file_path: str) -> Resume:
    """
    保存简历上传记录到数据库。
    """
    resume = Resume(user_id=user_id, name=name, file_path=file_path)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def get_resumes(db: Session, user_id: int) -> list[Resume]:
    """
    查询当前用户的所有简历。
    """
    return list(
        db.scalars(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
        ).all()
    )


# ==================== Dashboard 统计 ====================

def get_stats(db: Session, user_id: int) -> dict:
    """
    获取当前用户的 Dashboard 统计数据。

    使用 SQL 聚合函数 COUNT 来统计数量。
    """
    # 岗位总数（直接过滤 user_id）
    total_jobs = db.scalar(
        select(func.count(Job.id)).where(Job.user_id == user_id)
    )

    # 投递状态统计（通过 JOIN Job 表过滤用户）
    def count_apps_by_status(status: str) -> int:
        return db.scalar(
            select(func.count(Application.id))
            .join(Job)
            .where(Job.user_id == user_id, Application.status == status)
        ) or 0

    return {
        "total_jobs": total_jobs or 0,
        "total_applied": count_apps_by_status("applied"),
        "total_interview": count_apps_by_status("interview"),
        "total_offer": count_apps_by_status("offer"),
        "total_rejected": count_apps_by_status("rejected"),
    }
