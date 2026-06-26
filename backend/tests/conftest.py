"""
共享测试配置（conftest.py）

所有 test_*.py 自动共享这里定义的 fixtures。
无需在每个测试文件中重复定义 db / client / auth_client。

CI 运行：
    export TEST_DATABASE_URL=postgresql://user:pass@host:5432/test_db
    uv run pytest -v
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# 测试数据库地址（可通过环境变量覆盖，CI 友好）
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres@localhost:5433/internship_tracker",
)

test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

# 确保表已创建
Base.metadata.create_all(bind=test_engine)


@pytest.fixture()
def db():
    """事务回滚的数据库会话，测试互不干扰"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """已注入测试数据库的 HTTP 客户端"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def auth_client(client):
    """已登录的客户端，返回 (client, headers, user_id)"""
    client.post("/auth/register", json={
        "email": "ci_test@example.com",
        "password": "test123456",
    })
    login_resp = client.post("/auth/login", json={
        "email": "ci_test@example.com",
        "password": "test123456",
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = client.get("/auth/me", headers=headers)
    user_id = me.json()["id"]
    return client, headers, user_id
