"""
测试文件：认证系统测试

测试注册、登录、获取当前用户、以及未登录被拒绝访问。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# ==================== 测试数据库设置 ====================

TEST_DATABASE_URL = "postgresql://postgres@localhost:5433/internship_tracker"
test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)

Base.metadata.create_all(bind=test_engine)


@pytest.fixture()
def db():
    """每个测试独立的数据库会话（事务回滚）"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """提供 TestClient，使用测试数据库"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


# ==================== 注册测试 ====================

class TestRegister:
    """测试 POST /auth/register"""

    def test_register_success(self, client):
        """测试：注册成功应返回 201 + 用户信息"""
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "123456",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "created_at" in data
        # 最重要：密码绝对不能出现在返回结果中
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client):
        """测试：重复邮箱应返回 409"""
        # 第一次注册
        client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "123456",
        })

        # 第二次注册同邮箱
        response = client.post("/auth/register", json={
            "email": "dup@example.com",
            "password": "654321",
        })

        assert response.status_code == 409
        assert "已被注册" in response.json()["detail"]

    def test_register_short_password(self, client):
        """测试：密码太短应返回 422"""
        response = client.post("/auth/register", json={
            "email": "short@example.com",
            "password": "12345",  # 少于 6 位
        })

        assert response.status_code == 422

    def test_register_invalid_email(self, client):
        """测试：无效邮箱格式应返回 422"""
        response = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "123456",
        })

        assert response.status_code == 422


# ==================== 登录测试 ====================

class TestLogin:
    """测试 POST /auth/login"""

    @pytest.fixture()
    def registered_user(self, client):
        """先注册一个用户，供登录测试使用"""
        client.post("/auth/register", json={
            "email": "login_test@example.com",
            "password": "mypassword",
        })

    def test_login_success(self, client, registered_user):
        """测试：正确密码登录成功，返回 JWT token"""
        response = client.post("/auth/login", json={
            "email": "login_test@example.com",
            "password": "mypassword",
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, registered_user):
        """测试：错误密码应返回 401"""
        response = client.post("/auth/login", json={
            "email": "login_test@example.com",
            "password": "wrongpassword",
        })

        assert response.status_code == 401
        assert "错误" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """测试：不存在的用户应返回 401"""
        response = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "123456",
        })

        assert response.status_code == 401


# ==================== 获取当前用户测试 ====================

class TestGetMe:
    """测试 GET /auth/me"""

    def test_get_me_with_valid_token(self, client):
        """测试：有效 token 应返回当前用户信息"""
        # 注册 + 登录
        client.post("/auth/register", json={
            "email": "me_test@example.com",
            "password": "123456",
        })
        login_resp = client.post("/auth/login", json={
            "email": "me_test@example.com",
            "password": "123456",
        })
        token = login_resp.json()["access_token"]

        # 带 token 访问 /auth/me
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })

        assert response.status_code == 200
        assert response.json()["email"] == "me_test@example.com"

    def test_get_me_without_token(self, client):
        """测试：不带 token 应返回 401"""
        response = client.get("/auth/me")
        assert response.status_code == 401


# ==================== 鉴权保护测试 ====================

class TestAuthProtection:
    """测试未登录时 /jobs 接口被拦截"""

    def test_jobs_no_token(self, client):
        """测试：不带 token 访问 /jobs 应返回 401"""
        response = client.get("/jobs")
        assert response.status_code == 401

    def test_jobs_with_token(self, client):
        """测试：带有效 token 访问 /jobs 应成功"""
        # 注册 + 登录
        client.post("/auth/register", json={
            "email": "protect_test@example.com",
            "password": "123456",
        })
        login_resp = client.post("/auth/login", json={
            "email": "protect_test@example.com",
            "password": "123456",
        })
        token = login_resp.json()["access_token"]

        # 带 token 访问
        response = client.get("/jobs", headers={
            "Authorization": f"Bearer {token}",
        })

        assert response.status_code == 200

    def test_create_job_with_token(self, client):
        """测试：带 token 创建岗位，自动绑定当前用户"""
        # 注册 + 登录
        client.post("/auth/register", json={
            "email": "create_test@example.com",
            "password": "123456",
        })
        login_resp = client.post("/auth/login", json={
            "email": "create_test@example.com",
            "password": "123456",
        })
        token = login_resp.json()["access_token"]

        # 创建岗位（不需要传 user_id）
        response = client.post("/jobs", json={
            "company_name": "我的公司",
            "title": "前端实习生",
        }, headers={"Authorization": f"Bearer {token}"})

        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "我的公司"
        # user_id 应该被自动设置为当前用户的 ID
        assert data["user_id"] is not None
