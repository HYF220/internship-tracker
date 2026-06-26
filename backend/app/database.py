"""
数据库连接模块

这个文件负责：
1. 连接到 PostgreSQL 数据库
2. 管理"会话"（Session）—— 每次请求借一个连接，用完归还
3. 提供 get_db 函数，供接口使用

============================================================
新手理解：
    "连接"   = 就像打电话，拨通后可以说很多句话（执行多条 SQL）
    "会话"   = 一次通话过程
    "连接池" = 预先把几个电话拨通等着，来请求了就分配一个
============================================================
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 从环境变量读取数据库地址
# 如果找不到，就用默认值（方便开发时不用每次设环境变量）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres@localhost:5433/internship_tracker",
)

# engine = 数据库引擎，负责和 PostgreSQL 通信
# pool_size=5 表示最多保持 5 个空闲连接
# echo=True 会打印所有 SQL 语句（调试时很有用，正式环境关掉）
engine = create_engine(DATABASE_URL, pool_size=5, echo=False)

# SessionLocal = 会话工厂
# 每次调用它都会创建一个新的数据库会话
# 就像每次打电话都要重新拨号
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# Base = 所有数据模型的"祖先"
# 每个表对应的类都要继承 Base
# SQLAlchemy 用 Base 来知道"哪些类对应数据库表"
Base = declarative_base()


def get_db():
    """
    获取数据库会话的"依赖注入"函数。

    工作流程：
    1. 创建一个会话
    2. 交给接口函数使用
    3. 接口函数执行完后自动关闭会话

    为什么这样设计？
    - 确保每次请求用完都"挂断电话"，不会泄漏连接
    - FastAPI 的依赖注入会自动调用这个函数
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
