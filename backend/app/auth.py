"""
认证模块

负责两件事：
1. 密码哈希 —— 把密码"加密"存储，即使数据库泄露也不会暴露明文密码
2. JWT 令牌 —— 生成和验证登录凭证，用户登录后发 token，之后每次请求带 token

============================================================
新手理解：
    密码哈希 = 把 "123456" 变成 "$2b$12$abc...xyz"（单向不可逆）
    JWT     = 一张"电子身份证"，里面记录了你是谁，服务器可以验证真伪
============================================================
"""

import os
import warnings
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User

# ==================== 配置 ====================

# 密钥 —— 用于签名 JWT。实际部署时应该放在环境变量中
SECRET_KEY = os.getenv("SECRET_KEY")
if SECRET_KEY is None:
    warnings.warn(
        "⚠️  SECRET_KEY 未设置！使用不安全的默认值。\n"
        "    请在 backend/.env 中设置 SECRET_KEY=你的随机字符串\n"
        "    生成方式: python -c \"import secrets; print(secrets.token_urlsafe(32))\"",
        RuntimeWarning,
    )
    SECRET_KEY = "dev-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # token 有效期：60 分钟

# ==================== 密码哈希 ====================


def hash_password(password: str) -> str:
    """
    将明文密码加密成哈希值。

    例如：
        "123456" → "$2b$12$LJ3m...很长的乱码..."

    bcrypt 会自动生成随机"盐值"（salt），所以同样的密码两次加密结果不同。
    """
    # bcrypt 限制密码最长 72 字节
    password_bytes = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配。

    参数：
        plain_password:  用户输入的明文密码
        hashed_password: 数据库中存储的哈希值

    返回：
        True 表示密码正确，False 表示错误
    """
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


# ==================== JWT 令牌 ====================

def create_access_token(user_id: int) -> str:
    """
    为用户创建 JWT 访问令牌。

    令牌内容：
    {
        "sub": "1",          # sub = subject，表示"这个 token 属于谁"
        "exp": 1710000000    # exp = expiration，过期时间戳
    }
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """
    解析 JWT 令牌，返回 user_id。

    返回：
        成功 → user_id (int)
        失败 → None（token 过期、无效等）
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            return None
        return int(user_id_str)
    except (JWTError, ValueError):
        return None


# ==================== FastAPI 依赖：获取当前用户 ====================

# HTTPBearer 会自动从请求头 Authorization: Bearer <token> 中提取 token
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    从请求的 JWT token 中解析出当前用户。

    这是保护接口的关键：
    - 如果请求没有 token → 返回 401
    - 如果 token 无效或过期 → 返回 401
    - 如果 token 有效但用户不存在 → 返回 404
    - 一切正常 → 返回 User 对象

    用法：
        @app.get("/jobs")
        def list_jobs(current_user: User = Depends(get_current_user)):
            ...
            # 这里 current_user 就是登录用户，current_user.id 就是他的 ID
    """
    token = credentials.credentials
    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="登录凭证无效或已过期，请重新登录",
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user
